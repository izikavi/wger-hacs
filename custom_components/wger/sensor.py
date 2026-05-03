"""wger sensor platform."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WgerDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class WgerSensorEntityDescription(SensorEntityDescription):
    """Describes a wger sensor."""

    value_fn: Callable[[dict[str, Any]], Any]
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _latest_weight(data: dict[str, Any]) -> float | None:
    entry = data.get("latest_weight")
    if not entry:
        return None
    try:
        return float(entry.get("weight"))
    except (TypeError, ValueError):
        return None


def _latest_weight_attrs(data: dict[str, Any]) -> dict[str, Any]:
    entry = data.get("latest_weight") or {}
    return {"date": entry.get("date"), "id": entry.get("id")}


def _latest_session_date(data: dict[str, Any]) -> str | None:
    entry = data.get("latest_session")
    return entry.get("date") if entry else None


def _latest_session_attrs(data: dict[str, Any]) -> dict[str, Any]:
    entry = data.get("latest_session") or {}
    return {
        "workout": entry.get("workout"),
        "notes": entry.get("notes"),
        "impression": entry.get("impression"),
        "time_start": entry.get("time_start"),
        "time_end": entry.get("time_end"),
    }


def _body_fat_value(data: dict[str, Any]) -> float | None:
    entry = data.get("body_fat")
    if not entry:
        return None
    try:
        return float(entry.get("value"))
    except (TypeError, ValueError):
        return None


def _body_fat_attrs(data: dict[str, Any]) -> dict[str, Any]:
    entry = data.get("body_fat") or {}
    return {"date": entry.get("date"), "notes": entry.get("notes")}


def _delta_last_attrs(data: dict[str, Any]) -> dict[str, Any]:
    return {"compared_to": data.get("weight_delta_last_from_date")}


def _delta_30d_attrs(data: dict[str, Any]) -> dict[str, Any]:
    return {"compared_to": data.get("weight_delta_30d_from_date")}


def _pr_value(data: dict[str, Any]) -> float | None:
    entry = data.get("top_log")
    if not entry:
        return None
    try:
        return float(entry.get("weight"))
    except (TypeError, ValueError):
        return None


def _pr_attrs(data: dict[str, Any]) -> dict[str, Any]:
    entry = data.get("top_log") or {}
    return {
        "exercise_base": entry.get("exercise_base"),
        "exercise": entry.get("exercise"),
        "reps": entry.get("reps"),
        "date": entry.get("date"),
        "workout": entry.get("workout"),
    }


SENSORS: tuple[WgerSensorEntityDescription, ...] = (
    WgerSensorEntityDescription(
        key="latest_weight",
        translation_key="latest_weight",
        name="Latest Weight",
        icon="mdi:scale-bathroom",
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        value_fn=_latest_weight,
        attrs_fn=_latest_weight_attrs,
    ),
    WgerSensorEntityDescription(
        key="workout_count",
        translation_key="workout_count",
        name="Workouts",
        icon="mdi:dumbbell",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("workout_count"),
    ),
    WgerSensorEntityDescription(
        key="session_count",
        translation_key="session_count",
        name="Workout Sessions",
        icon="mdi:calendar-check",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("session_count"),
    ),
    WgerSensorEntityDescription(
        key="latest_session",
        translation_key="latest_session",
        name="Last Session",
        icon="mdi:calendar-clock",
        device_class=SensorDeviceClass.DATE,
        value_fn=_latest_session_date,
        attrs_fn=_latest_session_attrs,
    ),
    WgerSensorEntityDescription(
        key="nutrition_plans",
        translation_key="nutrition_plans",
        name="Nutrition Plans",
        icon="mdi:food-apple",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: len(data.get("nutrition_plans") or []),
    ),
    WgerSensorEntityDescription(
        key="bmi",
        translation_key="bmi",
        name="BMI",
        icon="mdi:human",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("bmi"),
    ),
    WgerSensorEntityDescription(
        key="body_fat",
        translation_key="body_fat",
        name="Body Fat",
        icon="mdi:percent",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        suggested_display_precision=1,
        value_fn=_body_fat_value,
        attrs_fn=_body_fat_attrs,
    ),
    WgerSensorEntityDescription(
        key="weight_delta_last",
        translation_key="weight_delta_last",
        name="Weight Change (vs previous)",
        icon="mdi:scale-balance",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("weight_delta_last"),
        attrs_fn=_delta_last_attrs,
    ),
    WgerSensorEntityDescription(
        key="weight_delta_30d",
        translation_key="weight_delta_30d",
        name="Weight Change (30 days)",
        icon="mdi:chart-line-variant",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        suggested_display_precision=2,
        value_fn=lambda data: data.get("weight_delta_30d"),
        attrs_fn=_delta_30d_attrs,
    ),
    WgerSensorEntityDescription(
        key="pr_max_weight",
        translation_key="pr_max_weight",
        name="Personal Record (max weight)",
        icon="mdi:trophy",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        suggested_display_precision=2,
        value_fn=_pr_value,
        attrs_fn=_pr_attrs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up wger sensors from a config entry."""
    coordinator: WgerDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(WgerSensor(coordinator, entry, desc) for desc in SENSORS)


class WgerSensor(CoordinatorEntity[WgerDataUpdateCoordinator], SensorEntity):
    """Sensor backed by the wger coordinator."""

    _attr_has_entity_name = True
    entity_description: WgerSensorEntityDescription

    def __init__(
        self,
        coordinator: WgerDataUpdateCoordinator,
        entry: ConfigEntry,
        description: WgerSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="wger.de",
            configuration_url=entry.data.get("url"),
        )

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        try:
            value = self.entity_description.value_fn(self.coordinator.data)
        except Exception:  # noqa: BLE001
            return None
        if isinstance(value, str) and self.device_class == SensorDeviceClass.DATE:
            from datetime import date

            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self.entity_description.attrs_fn or self.coordinator.data is None:
            return None
        try:
            return self.entity_description.attrs_fn(self.coordinator.data)
        except Exception:  # noqa: BLE001
            return None
