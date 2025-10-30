import logging
from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import device_registry
from homeassistant.const import Platform

from .const import DOMAIN, BRIGHTNESS_MODES, CONF_BRIGHTNESS_MODE
from .elkbledom import BLEDOMInstance

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up brightness mode selector for ELK-BLEDOM."""
    instance: BLEDOMInstance = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BLEDOMBrightnessModeSelect(instance, entry)], True)


class BLEDOMBrightnessModeSelect(SelectEntity):
    """Select entity for choosing brightness mode."""

    _attr_options = BRIGHTNESS_MODES
    _attr_should_poll = False

    def __init__(self, instance: BLEDOMInstance, entry: ConfigEntry) -> None:
        self._instance = instance
        self._entry = entry
        self._attr_name = f"{entry.data.get('name', 'ELK-BLEDOM')} Brightness Mode"
        self._attr_unique_id = f"{instance.address}_brightness_mode"
        self._current_option = entry.options.get(CONF_BRIGHTNESS_MODE, "auto")

    @property
    def current_option(self) -> str:
        """Return the current brightness mode."""
        return self._current_option

    @property
    def device_info(self) -> DeviceInfo:
        """Link select to the same device as light entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._instance.address)},
            name=self._entry.data.get("name", "ELK-BLEDOM"),
            manufacturer="ELK-BLEDOM",
            model="RGB Controller",
            connections={(device_registry.CONNECTION_NETWORK_MAC, self._instance.address)},
        )

    async def async_select_option(self, option: str) -> None:
        """Handle user selecting a brightness mode."""
        if option not in BRIGHTNESS_MODES:
            _LOGGER.warning("Invalid brightness mode selected: %s", option)
            return

        if option == self._current_option:
            return  # nothing to change

        _LOGGER.info("Changing brightness mode to %s for %s", option, self._instance.address)
        self._current_option = option

        # Update HA entry options
        data = dict(self._entry.options)
        data[CONF_BRIGHTNESS_MODE] = option
        self.hass.config_entries.async_update_entry(self._entry, options=data)

        # Trigger reconnect for mode change
        await self._instance.stop()
        await self._instance._ensure_connected()

        self.async_write_ha_state()
