"""Import StokerCloud pellet consumption history as external statistics.

Creates two statistics per boiler account:

* ``hass_stokercloud:pellet_consumption_<id>``  kg
* ``hass_stokercloud:pellet_energy_<id>``       kWh

On the first run the history StokerCloud offers (the last 24 hours plus the
24 rolling 24 h windows before them) is back-filled; after that each completed
hour is appended, continuing from the last stored ``sum``.

Adapted from statistics.py in vurrut/homeassistant-stokercloud (MIT).
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
)
from homeassistant.const import UnitOfEnergy, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

HOUR = timedelta(hours=1)
DAY = timedelta(days=1)


def statistic_ids(serial: str) -> tuple[str, str]:
    """(consumption id, energy id), with the serial lowercased to [a-z0-9_]."""
    ident = re.sub(r"[^a-z0-9_]", "_", str(serial).lower())
    return f"{DOMAIN}:pellet_consumption_{ident}", f"{DOMAIN}:pellet_energy_{ident}"


def _hour_floor(ts: datetime) -> datetime:
    return ts.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def build_rows(hourly, daily, last_start: datetime | None, now: datetime):
    """Return ``(hour start, kg)`` rows to add after ``last_start``, oldest first.

    ``hourly`` and ``daily`` are ``Client.consumption_history`` results (newest
    first). StokerCloud's "days" are rolling 24 h windows ending with the
    hourly window: ``daily[0]`` is the sum of the 24 hourly values, so it is
    skipped, and ``daily[i]`` (i >= 1) is booked as a single row at
    ``oldest_hour - i days``. Only done on the first import
    (``last_start is None``). The newest hour is still running and is skipped
    until it has completed.
    """
    hours = sorted(((_hour_floor(t), kg) for t, kg in hourly), key=lambda r: r[0])
    rows = []
    if last_start is None and hours:
        oldest = hours[0][0]
        rows.extend((oldest - i * DAY, kg) for i, (_, kg) in enumerate(daily) if i)
    rows.extend(
        (t, kg) for t, kg in hours
        if t + HOUR <= now and (last_start is None or t > last_start)
    )
    rows.sort(key=lambda r: r[0])
    return rows


async def _last(hass: HomeAssistant, statistic_id: str) -> tuple[datetime | None, float]:
    result = await get_instance(hass).async_add_executor_job(
        get_last_statistics, hass, 1, statistic_id, False, {"sum"}
    )
    rows = result.get(statistic_id)
    if not rows:
        return None, 0.0
    start = rows[0]["start"]
    if isinstance(start, (int, float)):
        start = datetime.fromtimestamp(start, tz=timezone.utc)
    return start, float(rows[0].get("sum") or 0.0)


async def async_import_pellet_statistics(
    hass: HomeAssistant, client, serial: str, calorific_value: float
) -> None:
    """Fetch consumption history and add any new completed hours.

    Never raises: timeouts, network errors and empty/odd responses are logged
    and the import simply tries again next time.
    """
    try:
        mass_id, energy_id = statistic_ids(serial)
        last_start, mass_sum = await _last(hass, mass_id)
        _, energy_sum = await _last(hass, energy_id)

        hourly = await hass.async_add_executor_job(client.consumption_history, "hours")
        daily = []
        if last_start is None:
            daily = await hass.async_add_executor_job(client.consumption_history, "days")
        rows = build_rows(hourly, daily, last_start, dt_util.utcnow())
        if not rows:
            return

        mass_stats, energy_stats = [], []
        for start, kg in rows:
            kwh = kg * calorific_value
            mass_sum += kg
            energy_sum += kwh
            mass_stats.append(StatisticData(start=start, state=kg, sum=round(mass_sum, 3)))
            energy_stats.append(StatisticData(start=start, state=kwh, sum=round(energy_sum, 3)))

        for statistic_id, name, unit_class, unit, stats in (
            (mass_id, "NBE pellet consumption", "mass", UnitOfMass.KILOGRAMS, mass_stats),
            (energy_id, "NBE pellet energy", "energy", UnitOfEnergy.KILO_WATT_HOUR, energy_stats),
        ):
            async_add_external_statistics(
                hass,
                StatisticMetaData(
                    mean_type=StatisticMeanType.NONE,
                    has_sum=True,
                    name=f"{name} ({serial})",
                    source=DOMAIN,
                    statistic_id=statistic_id,
                    unit_class=unit_class,
                    unit_of_measurement=unit,
                ),
                stats,
            )
        _LOGGER.debug("Imported %d pellet consumption rows up to %s", len(rows), rows[-1][0])
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.warning("Pellet statistics import failed, will retry next hour: %s", err)
