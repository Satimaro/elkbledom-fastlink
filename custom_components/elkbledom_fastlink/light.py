from __future__ import annotations

import logging
from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityFeature,
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import device_registry

from .const import DOMAIN, EFFECTS_MAP
from .elkbledom_fastlink import BLEDOMInstance

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Setup ELK-BLEDOM light entity."""
    instance: BLEDOMInstance = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BLEDOMLight(instance, entry.data["name"], entry.entry_id)])


class BLEDOMLight(LightEntity):
    """ELK-BLEDOM RGB LED Strip."""

    _attr_supported_color_modes = {ColorMode.RGB, ColorMode.COLOR_TEMP}
    _attr_color_mode = ColorMode.RGB
    _attr_effect_list = list(EFFECTS_MAP.keys())
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(self, instance: BLEDOMInstance, name: str, entry_id: str) -> None:
        self._instance = instance
        self._attr_name = name
        self._attr_unique_id = f"{self._instance.address}_light"
        self._entry_id = entry_id
        self._last_color_mode = ColorMode.RGB

    # ---------------------------------------------------------------
    # Свойства
    # ---------------------------------------------------------------
    @property
    def is_on(self) -> bool:
        return self._instance.is_on

    @property
    def brightness(self) -> int | None:
        return self._instance.brightness

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        return self._instance.rgb_color

    @property
    def color_temp_kelvin(self) -> int | None:
        return self._instance.color_temp_kelvin

    @property
    def effect(self) -> str | None:
        return next((k for k, v in EFFECTS_MAP.items() if v == self._instance._last_effect), None)

    @property
    def supported_color_modes(self):
        return {ColorMode.RGB, ColorMode.COLOR_TEMP}

    @property
    def color_mode(self) -> ColorMode:
        return self._last_color_mode

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._instance.address)},
            name=self._attr_name,
            manufacturer="ELK-BLEDOM",
            model="RGB Controller",
            connections={(device_registry.CONNECTION_NETWORK_MAC, self._instance.address)},
        )

    # ---------------------------------------------------------------
    # Основные действия
    # ---------------------------------------------------------------
    async def async_turn_on(self, **kwargs):
        """Turn on with given parameters."""
        _LOGGER.debug("Turn ON with kwargs: %s", kwargs)
        await self._instance.turn_on()

        if ATTR_BRIGHTNESS in kwargs:
            await self._instance.set_brightness(kwargs[ATTR_BRIGHTNESS])

        if ATTR_RGB_COLOR in kwargs:
            self._last_color_mode = ColorMode.RGB
            await self._instance.set_color(kwargs[ATTR_RGB_COLOR])

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._last_color_mode = ColorMode.COLOR_TEMP
            await self._instance.set_color_temp_kelvin(kwargs[ATTR_COLOR_TEMP_KELVIN])

        if ATTR_EFFECT in kwargs:
            effect_name = kwargs[ATTR_EFFECT]
            if effect_name in EFFECTS_MAP:
                code = EFFECTS_MAP[effect_name]
                await self._instance.set_effect(code)
                self._last_color_mode = ColorMode.RGB

        # Если вообще нет параметров — включаем белый RGB
        if not kwargs:
            self._last_color_mode = ColorMode.RGB
            await self._instance.set_color((255, 255, 255))

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off light."""
        await self._instance.turn_off()
        self.async_write_ha_state()
