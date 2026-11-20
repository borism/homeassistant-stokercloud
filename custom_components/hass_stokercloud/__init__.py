"""
NBE Stoker Cloud
"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN, PLATFORMS
from homeassistant.config_entries import ConfigEntry
import asyncio
from stokercloud.client import Client as StokerCloudClient
from homeassistant.const import CONF_USERNAME
from homeassistant.helpers.event import async_track_time_change
from .const import CALORIFIC_VALUE_KWH_PER_KG
from .pellet_statistics import async_import_pellet_statistics


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data[DOMAIN][entry.entry_id] = StokerCloudClient(entry.data[CONF_USERNAME])
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    client = hass.data[DOMAIN][entry.entry_id]

    async def _import_statistics(now=None):
        await async_import_pellet_statistics(
            hass, client, entry.data[CONF_USERNAME], CALORIFIC_VALUE_KWH_PER_KG
        )

    # Backfill / catch up in the background so a slow API can't delay setup,
    # then append each completed hour shortly after it ends.
    entry.async_create_background_task(hass, _import_statistics(), "pellet statistics import")
    entry.async_on_unload(async_track_time_change(hass, _import_statistics, minute=5, second=0))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok