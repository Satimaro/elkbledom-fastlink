from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event
from homeassistant.const import CONF_MAC, EVENT_HOMEASSISTANT_STOP, Platform

from .const import DOMAIN, CONF_RESET, CONF_DELAY
from .elkbledom_fastlink import BLEDOMInstance

LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.NUMBER,
]


# =========================================================
# Основная инициализация интеграции
# =========================================================
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ELK-BLEDOM from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Получаем параметры (опции приоритетнее)
    reset = entry.options.get(CONF_RESET, entry.data.get(CONF_RESET, False))
    delay = entry.options.get(CONF_DELAY, entry.data.get(CONF_DELAY, 120))
    mac = entry.data.get(CONF_MAC) or entry.options.get(CONF_MAC)

    if not mac:
        LOGGER.error("ELK-BLEDOM: MAC address missing in entry %s", entry.entry_id)
        return False

    LOGGER.info("Initializing ELK-BLEDOM: MAC=%s | reset=%s | delay=%s", mac, reset, delay)

    # Создаем экземпляр устройства
    instance = BLEDOMInstance(mac, reset, delay, hass)
    hass.data[DOMAIN][entry.entry_id] = instance

    # Регистрируем платформы
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Обработчик обновления параметров
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Гарантированное отключение при остановке HA
    async def _async_stop(event: Event) -> None:
        LOGGER.debug("Stopping ELK-BLEDOM (%s) due to HA shutdown", mac)
        await instance.stop()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    LOGGER.info("ELK-BLEDOM integration successfully loaded for %s", mac)
    return True


# =========================================================
# Выгрузка интеграции
# =========================================================
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    LOGGER.info("Unloading ELK-BLEDOM: %s", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        instance: BLEDOMInstance = hass.data[DOMAIN].pop(entry.entry_id, None)
        if instance:
            await instance.stop()
    return unload_ok


# =========================================================
# Перезагрузка при изменении опций
# =========================================================
async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update (reset/delay)."""
    LOGGER.debug("Reloading ELK-BLEDOM after options change")
    await hass.config_entries.async_reload(entry.entry_id)
