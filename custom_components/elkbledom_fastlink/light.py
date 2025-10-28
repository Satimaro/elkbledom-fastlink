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
from .elkbledom import BLEDOMInstance

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    instance: BLEDOMInstance = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BLEDOMLight(instance, entry.data["name"], entry.entry_id)])


class BLEDOMLight(LightEntity):
    _attr_supported_color_modes = {ColorMode.RGB, ColorMode.COLOR_TEMP}
    _attr_color_mode = ColorMode.RGB
    # Делаем "none" первым пунктом для удобства
    _attr_effect_list = ["none"] + [k for k in EFFECTS_MAP.keys() if k != "none"]
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(self, instance: BLEDOMInstance, name: str, entry_id: str) -> None:
        self._instance = instance
        self._attr_name = name
        self._attr_unique_id = f"{self._instance.address}_light"
        self._entry_id = entry_id
        self._last_color_mode = ColorMode.RGB

    @property
    def is_on(self): return self._instance.is_on
    @property
    def brightness(self): return self._instance.brightness
    @property
    def rgb_color(self): return self._instance.rgb_color
    @property
    def color_temp_kelvin(self): return self._instance.color_temp_kelvin
    @property
    def color_mode(self): return self._last_color_mode

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._instance.address)},
            name=self._attr_name,
            manufacturer="ELK-BLEDOM",
            model="RGB Controller",
            connections={(device_registry.CONNECTION_NETWORK_MAC, self._instance.address)},
        )

    async def async_turn_on(self, **kwargs):
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
                effect_id = EFFECTS_MAP[effect_name]
                # "none" => вернуть статический свет (обработается в set_effect)
                await self._instance.set_effect(effect_id)

        if not kwargs:
            await self._instance.set_color(self._instance.rgb_color)

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._instance.turn_off()
        self.async_write_ha_state()
