import asyncio
import logging
from typing import Tuple, TypeVar, Callable, cast
from bleak.backends.service import BleakGATTServiceCollection
from bleak.exc import BleakDBusError
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    BleakNotFoundError,
    BLEAK_RETRY_EXCEPTIONS as BLEAK_EXCEPTIONS,
    establish_connection,
)
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.exceptions import ConfigEntryNotReady

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------
# Базовые параметры BLE-команд
# --------------------------------------------------------------------
NAME_ARRAY = ["ELK-BLEDDM", "ELK-BLE", "LEDBLE", "MELK", "ELK-BULB2", "ELK-BULB", "ELK-LAMPL"]
WRITE_CHARACTERISTIC_UUIDS = ["0000fff3-0000-1000-8000-00805f9b34fb"] * 7
TURN_ON_CMD = [[0x7E, 0x00, 0x04, 0xF0, 0x00, 0x01, 0xFF, 0x00, 0xEF]] * 7
TURN_OFF_CMD = [[0x7E, 0x00, 0x04, 0x00, 0x00, 0x00, 0xFF, 0x00, 0xEF]] * 7
MIN_COLOR_TEMPS_K = [2700] * 7
MAX_COLOR_TEMPS_K = [6500] * 7

DEFAULT_ATTEMPTS = 3
BLEAK_BACKOFF_TIME = 0.25
RETRY_BACKOFF_EXCEPTIONS = (BleakDBusError,)
WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., any])


# --------------------------------------------------------------------
# Декоратор повторных попыток при BLE ошибках
# --------------------------------------------------------------------
def retry_bluetooth_connection_error(func: WrapFuncType) -> WrapFuncType:
    async def _async_wrap_retry(self: "BLEDOMInstance", *args, **kwargs):
        for attempt in range(DEFAULT_ATTEMPTS):
            try:
                return await func(self, *args, **kwargs)
            except BleakNotFoundError:
                raise
            except RETRY_BACKOFF_EXCEPTIONS as err:
                if attempt == DEFAULT_ATTEMPTS - 1:
                    LOGGER.error("%s: BLE retry exhausted: %s", self.name, err)
                    raise
                await asyncio.sleep(BLEAK_BACKOFF_TIME)
            except BLEAK_RETRY_EXCEPTIONS as err:
                if attempt == DEFAULT_ATTEMPTS - 1:
                    LOGGER.error("%s: BLE exception: %s", self.name, err)
                    raise
    return cast(WrapFuncType, _async_wrap_retry)


# --------------------------------------------------------------------
# Основной класс устройства
# --------------------------------------------------------------------
class BLEDOMInstance:
    def __init__(self, address, reset: bool, delay: int, hass) -> None:
        self.address = address
        self._reset = reset
        self._delay = delay
        self._hass = hass

        self._device = async_ble_device_from_address(hass, address)
        if not self._device:
            raise ConfigEntryNotReady(f"Bluetooth device {address} not found.")

        self._client: BleakClientWithServiceCache | None = None
        self._connect_lock = asyncio.Lock()
        self._cached_services: BleakGATTServiceCollection | None = None

        # Текущее состояние
        self._is_on = False
        self._rgb_color: Tuple[int, int, int] = (255, 255, 255)
        self._brightness: int = 255
        self._color_temp_kelvin: int = 5000
        self._effect_speed: int = 16
        self._last_effect: int | None = None

        # Температурный диапазон
        self._min_color_temp_kelvin = 2700
        self._max_color_temp_kelvin = 6500

        self._detect_model()
        asyncio.create_task(self._ensure_connected())
        asyncio.create_task(self._heartbeat())

    # ----------------------------------------------------------------
    # Свойства
    # ----------------------------------------------------------------
    @property
    def name(self): return self._device.name if self._device else self.address
    @property
    def is_on(self): return self._is_on
    @property
    def brightness(self): return self._brightness
    @property
    def rgb_color(self): return self._rgb_color
    @property
    def color_temp_kelvin(self): return self._color_temp_kelvin
    @property
    def min_color_temp_kelvin(self): return self._min_color_temp_kelvin
    @property
    def max_color_temp_kelvin(self): return self._max_color_temp_kelvin
    @property
    def reset(self): return self._reset
    @property
    def delay(self): return self._delay

    # ----------------------------------------------------------------
    # Модель устройства
    # ----------------------------------------------------------------
    def _detect_model(self):
        for i, name in enumerate(NAME_ARRAY):
            if self._device.name and self._device.name.lower().startswith(name.lower()):
                self._turn_on_cmd = TURN_ON_CMD[i]
                self._turn_off_cmd = TURN_OFF_CMD[i]
                self._min_color_temp_kelvin = MIN_COLOR_TEMPS_K[i]
                self._max_color_temp_kelvin = MAX_COLOR_TEMPS_K[i]
                return
        self._turn_on_cmd = TURN_ON_CMD[0]
        self._turn_off_cmd = TURN_OFF_CMD[0]

    # ----------------------------------------------------------------
    # Подключение BLE
    # ----------------------------------------------------------------
    async def _ensure_connected(self):
        if self._client and self._client.is_connected:
            return
        async with self._connect_lock:
            try:
                client = await establish_connection(
                    BleakClientWithServiceCache,
                    self._device,
                    self._device.name,
                    self._disconnected,
                    cached_services=self._cached_services,
                )
                self._client = client
                self._cached_services = client.services
                for ch in WRITE_CHARACTERISTIC_UUIDS:
                    c = client.services.get_characteristic(ch)
                    if c:
                        self._write_uuid = c
                        break
                LOGGER.info("%s connected", self._device.name)
            except Exception as e:
                LOGGER.error("%s: connection failed: %s", self._device.name, e)
                await asyncio.sleep(5)
                asyncio.create_task(self._ensure_connected())

    def _disconnected(self, _client):
        asyncio.create_task(self._ensure_connected())

    async def _heartbeat(self):
        while True:
            try:
                if not self._client or not self._client.is_connected:
                    await self._ensure_connected()
            except Exception:
                pass
            await asyncio.sleep(30)

    # ----------------------------------------------------------------
    # Отправка команд
    # ----------------------------------------------------------------
    @retry_bluetooth_connection_error
    async def _write(self, data: list[int]):
        await self._ensure_connected()
        await self._client.write_gatt_char(self._write_uuid, bytearray(data), False)

    # ----------------------------------------------------------------
    # Базовые действия
    # ----------------------------------------------------------------
    @retry_bluetooth_connection_error
    async def turn_on(self):
        await self._write(self._turn_on_cmd)
        self._is_on = True

    @retry_bluetooth_connection_error
    async def turn_off(self):
        await self._write(self._turn_off_cmd)
        self._is_on = False

    # ----------------------------------------------------------------
    # Яркость
    # ----------------------------------------------------------------
    @retry_bluetooth_connection_error
    async def set_brightness(self, value: int):
        """Плавная регулировка яркости."""
        self._brightness = max(1, min(value, 255))
        r, g, b = self._rgb_color
        white_like = abs(r - g) < 15 and abs(g - b) < 15 and max(r, g, b) > 100
        level = int(self._brightness * 100 / 255)

        if white_like:
            await self._write([0x7E, 0x04, 0x01, level, 0xFF, 0x00, 0xFF, 0x00, 0xEF])
        else:
            scale = self._brightness / 255
            rr, gg, bb = int(r * scale), int(g * scale), int(b * scale)
            await self._write([0x7E, 0x00, 0x05, 0x03, rr, gg, bb, 0x00, 0xEF])

    # ----------------------------------------------------------------
    # Цвет RGB
    # ----------------------------------------------------------------
    @retry_bluetooth_connection_error
    async def set_color(self, rgb: Tuple[int, int, int]):
        r, g, b = rgb
        self._rgb_color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        await self._write([0x7E, 0x00, 0x05, 0x03, r, g, b, 0x00, 0xEF])
        self._is_on = True

    # ----------------------------------------------------------------
    # Симуляция цветовой температуры (лампово-оранжевая)
    # ----------------------------------------------------------------
    @retry_bluetooth_connection_error
    async def set_color_temp_kelvin(self, value: int, brightness: int = 255):
        """Симуляция CCT через RGB для 5050 RGB."""
        k_min = self._min_color_temp_kelvin
        k_max = self._max_color_temp_kelvin
        k = max(k_min, min(value, k_max))
        self._color_temp_kelvin = k

        warm = (255, 77, 12)   # насыщенно-оранжевый, ламповый
        cool = (255, 255, 255) # холодный белый
        t = (k - k_min) / (k_max - k_min) if k_max > k_min else 1.0

        r = int(warm[0] + (cool[0] - warm[0]) * t)
        g = int(warm[1] + (cool[1] - warm[1]) * t)
        b = int(warm[2] + (cool[2] - warm[2]) * t)

        level = max(1, min(brightness if brightness is not None else self._brightness, 255))
        scale = level / 255.0
        r, g, b = int(r * scale), int(g * scale), int(b * scale)

        self._rgb_color = (r, g, b)
        await self._write([0x7E, 0x00, 0x05, 0x03, r, g, b, 0x00, 0xEF])
        self._is_on = True

    # ----------------------------------------------------------------
    # Эффекты (с авто-применением скорости)
    # ----------------------------------------------------------------
    @retry_bluetooth_connection_error
    async def set_effect(self, value: int):
        """Установка эффекта с автоматической скоростью."""
        try:
            await self._ensure_connected()
            await self._write([0x7E, 0x00, 0x03, 0x01, 0x03, 0x00, 0x00, 0x00, 0xEF])
            await asyncio.sleep(0.1)
            await self._write([0x7E, 0x00, 0x03, value, 0x03, 0x00, 0x00, 0x00, 0xEF])
            await asyncio.sleep(0.1)
            await self.set_effect_speed(self._effect_speed)
            self._last_effect = value
            self._is_on = True
            LOGGER.debug("%s: эффект %s, скорость %d", self.name, hex(value), self._effect_speed)
        except Exception as e:
            LOGGER.error("%s: ошибка установки эффекта: %s", self.name, e)

    # ----------------------------------------------------------------
    # Скорость эффектов (1–31)
    # ----------------------------------------------------------------
    @retry_bluetooth_connection_error
    async def set_effect_speed(self, speed: int):
        """Регулировка скорости эффектов."""
        self._effect_speed = max(1, min(int(speed), 31))
        await self._write([0x7E, 0x00, 0x02, self._effect_speed, 0x03, 0x00, 0x00, 0x00, 0xEF])
        LOGGER.debug("%s: скорость эффекта %d", self.name, self._effect_speed)
        # если эффект уже активен — обновим его
        if self._last_effect:
            await asyncio.sleep(0.05)
            await self._write([0x7E, 0x00, 0x03, self._last_effect, 0x03, 0x00, 0x00, 0x00, 0xEF])

    # ----------------------------------------------------------------
    # Завершение
    # ----------------------------------------------------------------
    async def stop(self):
        try:
            if self._client and self._client.is_connected:
                await self._client.disconnect()
        except Exception:
            pass
