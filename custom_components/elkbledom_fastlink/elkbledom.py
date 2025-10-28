import asyncio
import logging
import json
import os
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

NAME_ARRAY = ["ELK-BLEDDM", "ELK-BLE", "LEDBLE", "MELK", "ELK-BULB2", "ELK-BULB", "ELK-LAMPL"]
WRITE_CHARACTERISTIC_UUIDS = ["0000fff3-0000-1000-8000-00805f9b34fb"] * 7
TURN_ON_CMD = [[0x7E, 0x00, 0x04, 0xF0, 0x00, 0x01, 0xFF, 0x00, 0xEF]] * 7
TURN_OFF_CMD = [[0x7E, 0x00, 0x04, 0x00, 0x00, 0x00, 0xFF, 0x00, 0xEF]] * 7
MIN_COLOR_TEMPS_K = [2700] * 7
MAX_COLOR_TEMPS_K = [6500] * 7

DEFAULT_ATTEMPTS = 3
BLEAK_BACKOFF_TIME = 0.25
STATE_FILE = "/config/.storage/elkbledom_fastlink_state.json"
RETRY_BACKOFF_EXCEPTIONS = (BleakDBusError,)
WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., any])


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
            except BLEAK_EXCEPTIONS as err:
                if attempt == DEFAULT_ATTEMPTS - 1:
                    LOGGER.error("%s: BLE exception: %s", self.name, err)
                    raise
    return cast(WrapFuncType, _async_wrap_retry)


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
        self._write_uuid = None

        state = self._load_state()
        self._is_on = False
        self._rgb_color: Tuple[int, int, int] = tuple(state.get("rgb", (255, 255, 255)))
        self._brightness: int = state.get("brightness", 255)
        self._color_temp_kelvin: int = state.get("color_temp", 5000)

        self._effect_speed: int = 16
        self._last_effect: int | None = None  # эффекты не сохраняем в JSON

        self._min_color_temp_kelvin = 2700
        self._max_color_temp_kelvin = 6500

        self._detect_model()
        asyncio.create_task(self._delayed_connect())
        asyncio.create_task(self._heartbeat())

    # ---------------- JSON state ----------------
    def _load_state(self):
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get(self.address, {})
        except Exception as e:
            LOGGER.warning("Failed to load state for %s: %s", self.address, e)
        return {}

    def _save_state(self):
        try:
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            data = {}
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = {}
            data[self.address] = {
                "rgb": self._rgb_color,
                "brightness": self._brightness,
                "color_temp": self._color_temp_kelvin,
            }
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            LOGGER.error("Failed to save state for %s: %s", self.address, e)

    # ---------------- Properties (нужны light/number) ----------------
    @property
    def name(self):
        return self._device.name if self._device else self.address

    @property
    def is_on(self) -> bool:
        return getattr(self, "_is_on", False)

    @property
    def brightness(self) -> int:
        return getattr(self, "_brightness", 255)

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        return getattr(self, "_rgb_color", (255, 255, 255))

    @property
    def color_temp_kelvin(self) -> int:
        return getattr(self, "_color_temp_kelvin", 5000)

    # ---------------- BLE ----------------
    async def _delayed_connect(self):
        await asyncio.sleep(3)
        await self._ensure_connected()

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
            if not self._client or not self._client.is_connected:
                await self._ensure_connected()
            await asyncio.sleep(30)

    # ---------------- Commands ----------------
    @retry_bluetooth_connection_error
    async def _write(self, data: list[int]):
        await self._ensure_connected()
        await self._client.write_gatt_char(self._write_uuid, bytearray(data), False)

    @retry_bluetooth_connection_error
    async def turn_on(self):
        await self._write(self._turn_on_cmd)
        # Короткая пауза, чтобы контроллер «отпустил» заводской белый
        await asyncio.sleep(0.2)
        # Восстанавливаем одним пакетом RGB с учётом яркости
        await self.set_color(self._rgb_color, self._brightness)
        self._is_on = True

    @retry_bluetooth_connection_error
    async def turn_off(self):
        self._save_state()
        await self._write(self._turn_off_cmd)
        self._is_on = False

    @retry_bluetooth_connection_error
    async def set_brightness(self, value: int):
        self._brightness = max(1, min(int(value), 255))
        r, g, b = self._rgb_color
        scale = self._brightness / 255.0
        rr, gg, bb = int(r * scale), int(g * scale), int(b * scale)
        await self._write([0x7E, 0x00, 0x05, 0x03, rr, gg, bb, 0x00, 0xEF])
        self._save_state()

    @retry_bluetooth_connection_error
    async def set_color(self, rgb: Tuple[int, int, int], brightness: int | None = None):
        if brightness is not None:
            self._brightness = max(1, min(int(brightness), 255))
        r, g, b = (max(0, min(255, c)) for c in rgb)
        self._rgb_color = (int(r), int(g), int(b))
        scale = self._brightness / 255.0
        rr, gg, bb = int(r * scale), int(g * scale), int(b * scale)
        await self._write([0x7E, 0x00, 0x05, 0x03, rr, gg, bb, 0x00, 0xEF])
        self._is_on = True
        self._save_state()

    @retry_bluetooth_connection_error
    async def set_color_temp_kelvin(self, value: int, brightness: int | None = None):
        """Эмуляция CCT на RGB: интерполяция между 'warm' и 'cool' + масштаб по яркости."""
        k_min, k_max = self._min_color_temp_kelvin, self._max_color_temp_kelvin
        k = max(k_min, min(int(value), k_max))
        self._color_temp_kelvin = k

        warm = (255, 77, 12)       # тёплый
        cool = (255, 255, 255)     # холодный
        t = (k - k_min) / (k_max - k_min) if k_max > k_min else 1.0

        r = int(warm[0] + (cool[0] - warm[0]) * t)
        g = int(warm[1] + (cool[1] - warm[1]) * t)
        b = int(warm[2] + (cool[2] - warm[2]) * t)

        if brightness is not None:
            self._brightness = max(1, min(int(brightness), 255))

        scale = self._brightness / 255.0
        rr, gg, bb = int(r * scale), int(g * scale), int(b * scale)

        self._rgb_color = (r, g, b)  # логическое RGB без масштаба
        await self._write([0x7E, 0x00, 0x05, 0x03, rr, gg, bb, 0x00, 0xEF])
        self._is_on = True
        self._save_state()

    @retry_bluetooth_connection_error
    async def set_effect(self, value: int):
        """Включение/отключение эффекта (в JSON не сохраняем).
        value == 0x00 или None => отключить эффект и вернуться к статике.
        """
        try:
            await self._ensure_connected()
            if value in (0x00, None):
                # Возврат к статическому цвету и яркости
                await self.set_color(self._rgb_color, self._brightness)
                self._last_effect = None
                return
            # Иначе — отправляем команду включения эффекта
            await self._write([0x7E, 0x00, 0x03, value, 0x03, 0x00, 0x00, 0x00, 0xEF])
            self._last_effect = value
        except Exception as e:
            LOGGER.error("%s: set_effect error: %s", self.name, e)

    @retry_bluetooth_connection_error
    async def set_effect_speed(self, speed: int):
        """Установка скорости эффекта (1..31), без сохранения в JSON."""
        s = max(1, min(int(speed), 31))
        self._effect_speed = s
        await self._write([0x7E, 0x00, 0x02, s, 0x03, 0x00, 0x00, 0x00, 0xEF])

    async def stop(self):
        self._save_state()
        if self._client and self._client.is_connected:
            await self._client.disconnect()
