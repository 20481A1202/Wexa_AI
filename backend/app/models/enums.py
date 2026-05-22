from enum import StrEnum


class Role(StrEnum):
    owner = "Owner"
    admin = "Admin"
    analyst = "Analyst"
    viewer = "Viewer"


class WidgetType(StrEnum):
    line = "line"
    bar = "bar"
    pie = "pie"
    kpi = "kpi"
    table = "table"


class AlertStatus(StrEnum):
    active = "Active"
    triggered = "Triggered"
    resolved = "Resolved"
    muted = "Muted"
