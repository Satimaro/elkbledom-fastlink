from __future__ import annotations

import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import device_registry
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .elkbledom import BLEDOMInstance
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup effect speed control entity."""
    instance = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [BLEDOMSpeedControl(instance, f"Effect Speed ({config_entry.data['name']})", config_entry.entry_id)]
    )


class BLEDOMSpeedControl(NumberEntity):
    """Entity for controlling ELK-BLEDOM effect speed."""

    _attr_mode = "slider"
    _attr_native_min_value = 1
    _attr_native_max_value = 31
    _attr_native_step = 1
    _attr_icon = "mdi:speedometer"

    def __init__(self, bledomInstance: BLEDOMInstance, name: str, entry_id: str) -> None:
        self._instance = bledomInstance
        self._attr_name = name
        self._attr_unique_id = f"{self._instance.address}_speed"
        self._effect_speed = getattr(self._instance, "_effect_speed", 16)
        self._entry_id = entry_id

    @property
    def available(self) -> bool:
        """Device is available if BLE client is connected."""
        return bool(getattr(self._instance, "_client", None) and self._instance._client.is_connected)

    @property
    def native_value(self) -> int:
        """Return the current effect speed."""
        return self._effect_speed

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._instance.address)},
            name=self.name,
            connections={(device_registry.CONNECTION_NETWORK_MAC, self._instance.address)},
            manufacturer="ELK-BLEDOM",
            model="RGB Controller",
        )

    async def async_set_native_value(self, value: float) -> None:
        """Send BLE speed command to device."""
        try:
            value_int = int(max(1, min(value, 31)))
            await self._instance.set_effect_speed(value_int)
            self._effect_speed = value_int
            self.async_write_ha_state()
            _LOGGER.debug("%s: effect speed set to %d", self._instance.name, value_int)
        except Exception as e:
            _LOGGER.error("Failed to set effect speed: %s", e)
