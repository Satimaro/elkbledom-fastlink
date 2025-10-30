import asyncio
import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_MAC
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
    async_ble_device_from_address,
)
import voluptuous as vol
from homeassistant.helpers.device_registry import format_mac

from .const import (
    DOMAIN,
    CONF_RESET,
    CONF_DELAY,
    CONF_BRIGHTNESS_MODE,
    BRIGHTNESS_MODES,
    DEFAULT_BRIGHTNESS_MODE,
)

LOGGER = logging.getLogger(__name__)
MANUAL_MAC = "manual"


class BLEDOMFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Основной поток настройки интеграции ELK-BLEDOM FastLink."""
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        self.mac: str | None = None
        self.name: str | None = None
        self._discovered_devices: list[dict[str, str]] = []

    # =========================================================
    # Автообнаружение Bluetooth
    # =========================================================
    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Обработка найденного BLE устройства."""
        LOGGER.debug(
            "Discovered Bluetooth device: %s (%s)",
            discovery_info.name,
            discovery_info.address,
        )

        if not discovery_info.address or not discovery_info.name:
            return self.async_abort(reason="invalid_discovery_info")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        # Проверяем имя без использования DeviceData
        if any(x in discovery_info.name.upper() for x in ["ELK", "LED", "MELK"]):
            return await self.async_step_bluetooth_confirm()

        return self.async_abort(reason="not_supported")

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Подтверждение добавления BLE устройства."""
        self._set_confirm_only()
        return await self.async_step_user()

    # =========================================================
    # Выбор устройства вручную или из списка
    # =========================================================
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Выбор устройства из списка или ввод MAC вручную."""
        if user_input is not None:
            if user_input[CONF_MAC] == MANUAL_MAC:
                return await self.async_step_manual()

            self.mac = user_input[CONF_MAC]
            self.name = user_input["name"]

            result = await self.async_set_unique_id(self.mac, raise_on_progress=False)
            if result is not None:
                return self.async_abort(reason="already_in_progress")

            self._abort_if_unique_id_configured()
            return await self.async_step_validate()

        # Сканируем BLE устройства
        current_addresses = self._async_current_ids()
        discovered_devices = async_discovered_service_info(self.hass)

        for d in discovered_devices:
            if d.address in current_addresses:
                continue
            if any(dev["address"] == d.address for dev in self._discovered_devices):
                continue
            if d.name and any(x in d.name.upper() for x in ["ELK", "LED", "MELK"]):
                self._discovered_devices.append({"address": d.address, "name": d.name})

        if not self._discovered_devices:
            return await self.async_step_manual()

        mac_dict = {dev["address"]: dev["name"] for dev in self._discovered_devices}
        mac_dict[MANUAL_MAC] = "Manually add MAC address"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MAC): vol.In(mac_dict),
                    vol.Required("name"): str,
                }
            ),
            errors={},
        )

    # =========================================================
    # Проверка доступности устройства
    # =========================================================
    async def async_step_validate(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Проверка, что устройство доступно по BLE адресу."""
        LOGGER.debug("Validating device: %s (%s)", self.name, self.mac)

        try:
            device = async_ble_device_from_address(self.hass, self.mac)
            if not device:
                LOGGER.warning("Device %s not found", self.mac)
                return self.async_abort(reason="cannot_connect")

            LOGGER.info("Validated ELK-BLEDOM: %s (%s)", self.name, self.mac)
            return self.async_create_entry(
                title=self.name,
                data={
                    CONF_MAC: self.mac,
                    "name": self.name,
                    CONF_RESET: False,
                    CONF_DELAY: 0,
                },
                options={
                    CONF_BRIGHTNESS_MODE: DEFAULT_BRIGHTNESS_MODE
                }
            )
        except Exception as e:
            LOGGER.error("Validation error for %s: %s", self.mac, e)
            return self.async_abort(reason="cannot_connect")

    # =========================================================
    # Ввод MAC вручную
    # =========================================================
    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ручной ввод MAC адреса."""
        if user_input is not None:
            self.mac = format_mac(user_input[CONF_MAC])
            self.name = user_input["name"]
            return await self.async_step_validate()

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_MAC): str,
                    vol.Required("name"): str,
                }
            ),
            errors={},
        )

    # =========================================================
    # Опции интеграции
    # =========================================================
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Возврат обработчика опций."""
        return OptionsFlowHandler(config_entry)


# =========================================================
# Меню опций интеграции (Options Flow)
# =========================================================
class OptionsFlowHandler(config_entries.OptionsFlow):
    """Меню настроек интеграции."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__()
        self._config_entry = config_entry

    async def async_step_init(self, _user_input=None):
        """Начальный шаг."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Основной экран опций."""
        errors = {}
        options = self._config_entry.options or {
            CONF_RESET: False,
            CONF_DELAY: 0,
            CONF_BRIGHTNESS_MODE: DEFAULT_BRIGHTNESS_MODE,
        }

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_RESET: user_input[CONF_RESET],
                    CONF_DELAY: user_input[CONF_DELAY],
                    CONF_BRIGHTNESS_MODE: user_input[CONF_BRIGHTNESS_MODE],
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_RESET, default=options.get(CONF_RESET)): bool,
                    vol.Optional(CONF_DELAY, default=options.get(CONF_DELAY)): int,
                    vol.Required(
                        CONF_BRIGHTNESS_MODE,
                        default=options.get(CONF_BRIGHTNESS_MODE, DEFAULT_BRIGHTNESS_MODE),
                    ): vol.In(BRIGHTNESS_MODES),
                }
            ),
            errors=errors,
        )
