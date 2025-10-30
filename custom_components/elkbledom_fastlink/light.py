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

# ВАЖНО: из const берем и «сырые» effect-ключи/ID, и красивые лейблы
from .const import (
    DOMAIN,
    EFFECTS_MAP,        # {"crossfade_red": 0x8B, ...}
    EFFECT_LABELS,      # {"crossfade_red": "🔴 Fade Red", ...}
)
from .elkbledom import BLEDOMInstance

_LOGGER = logging.getLogger(__name__)


# =========================
# Регистрация платформы
# =========================
async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    instance: BLEDOMInstance = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BLEDOMLight(instance, entry.data["name"], entry.entry_id)])


class BLEDOMLight(LightEntity):
    """ELK-BLEDOM RGB/CCT light с красивыми лейблами эффектов."""

    _attr_supported_color_modes = {ColorMode.RGB, ColorMode.COLOR_TEMP}
    _attr_color_mode = ColorMode.RGB
    _attr_min_color_temp_kelvin = 1800
    _attr_max_color_temp_kelvin = 7000
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(self, instance: BLEDOMInstance, name: str, entry_id: str) -> None:
        self._instance = instance
        self._attr_name = name
        self._entry_id = entry_id
        self._attr_unique_id = f"{self._instance.address}_light"
        self._last_color_mode = ColorMode.RGB

        # Текущее «сырое» имя эффекта (ключ из const), по умолчанию none
        self._current_effect_key: str = "none"

        # Подготовим красивые списки/мапы для UI
        # порядок: "none" первым, далее остальные по исходному EFFECTS_MAP
        pretty = []
        for key in ["none"] + [k for k in EFFECTS_MAP.keys() if k != "none"]:
            pretty.append(EFFECT_LABELS.get(key, key))

        self._pretty_effect_list = pretty                          # список красивых строк
        self._key2pretty = {k: EFFECT_LABELS.get(k, k) for k in EFFECTS_MAP.keys()}
        # обратная мапа: красивая строка -> «сырой» ключ
        self._pretty2key = {v: k for k, v in self._key2pretty.items()}

    # -----------------------
    # Обязательные свойства
    # -----------------------
    @property
    def is_on(self):
        return self._instance.is_on

    @property
    def brightness(self):
        return self._instance.brightness

    @property
    def rgb_color(self):
        return self._instance.rgb_color

    @property
    def color_temp_kelvin(self):
        return self._instance.color_temp_kelvin

    @property
    def color_mode(self):
        return self._last_color_mode

    # Красивый текущий эффект:
    @property
    def effect(self) -> str | None:
        return self._key2pretty.get(self._current_effect_key, "none")

    # Список эффектов для селектора — красивые лейблы:
    @property
    def effect_list(self) -> list[str] | None:
        return self._pretty_effect_list

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._instance.address)},
            name=self._attr_name,
            manufacturer="ELK-BLEDOM",
            model="RGB Controller",
            connections={(device_registry.CONNECTION_NETWORK_MAC, self._instance.address)},
        )

    # --------------------------------
    # Управление
    # --------------------------------
    async def async_turn_on(self, **kwargs):
        _LOGGER.debug("Turn ON with kwargs: %s", kwargs)
        await self._instance.turn_on()

        if ATTR_BRIGHTNESS in kwargs:
            await self._instance.set_brightness(kwargs[ATTR_BRIGHTNESS])

        if ATTR_RGB_COLOR in kwargs:
            self._last_color_mode = ColorMode.RGB
            await self._instance.set_color(kwargs[ATTR_RGB_COLOR])
            self._current_effect_key = "none"

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._last_color_mode = ColorMode.COLOR_TEMP
            await self._instance.set_color_temp_kelvin(kwargs[ATTR_COLOR_TEMP_KELVIN])
            self._current_effect_key = "none"

        if ATTR_EFFECT in kwargs:
            # Пользователь присылает КРАСИВОЕ имя (из effect_list)
            pretty_name = kwargs[ATTR_EFFECT]
            # Конвертим в «сырой» ключ, если возможно
            effect_key = self._pretty2key.get(pretty_name, pretty_name)
            if effect_key in EFFECTS_MAP:
                effect_id = EFFECTS_MAP[effect_key]
                await self._instance.set_effect(effect_id)
                self._current_effect_key = effect_key
                _LOGGER.debug("Applied effect: key=%s id=0x%02X", effect_key, effect_id)

        if not kwargs:
            await self._instance.set_color(self._instance.rgb_color)

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._instance.turn_off()
        # оставляем запомненным последний выбранный эффект; UI сам его покажет
        self.async_write_ha_state()
