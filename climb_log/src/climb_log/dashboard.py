from __future__ import annotations

import json
from dataclasses import dataclass

from climb_log.models import ClimbResult, FallCause, Record

_CAUSE_LABELS: dict[FallCause, str] = {
    FallCause.FOOT_SLIP: "Foot slip",
    FallCause.PUMP: "Pump",
    FallCause.SWEATY_HANDS: "Sweaty hands",
    FallCause.WRONG_MOVE: "Wrong move",
    FallCause.OTHER: "Other",
}


@dataclass
class DashboardStats:
    total_tries: int
    top_count: int
    fall_count: int
    fall_cause_counts: dict[FallCause, int]


def compute_stats(records: list[Record]) -> DashboardStats:
    total = len(records)
    top_count = sum(1 for r in records if r.result == ClimbResult.TOP)
    fall_count = total - top_count

    cause_counts: dict[FallCause, int] = {}
    for record in records:
        for cause in record.fall_causes:
            cause_counts[cause] = cause_counts.get(cause, 0) + 1

    return DashboardStats(
        total_tries=total,
        top_count=top_count,
        fall_count=fall_count,
        fall_cause_counts=cause_counts,
    )


def focus_points(stats: DashboardStats) -> list[str]:
    if not stats.fall_cause_counts:
        return []
    top_cause = max(stats.fall_cause_counts, key=lambda c: stats.fall_cause_counts[c])
    label = _CAUSE_LABELS.get(top_cause, top_cause.value)
    return [f'Focus on "{label}" ({_cause_ratio(stats, top_cause):.0f}% of all falls)']


def _fall_rate(stats: DashboardStats) -> float:
    if stats.total_tries == 0:
        return 0.0
    return stats.fall_count / stats.total_tries * 100


def render_terminal(stats: DashboardStats) -> str:
    lines = [
        f"Tries: {stats.total_tries}  Tops: {stats.top_count}  "
        f"Falls: {stats.fall_count}  Fall rate: {_fall_rate(stats):.0f}%",
    ]
    if stats.fall_cause_counts:
        lines.append("Fall causes:")
        for cause, count in sorted(
            stats.fall_cause_counts.items(), key=lambda x: -x[1]
        ):
            label = _CAUSE_LABELS.get(cause, cause.value)
            lines.append(f"  {label}: {count}")
    points = focus_points(stats)
    if points:
        lines.append("Focus points:")
        for p in points:
            lines.append(f"  {p}")
    return "\n".join(line for line in lines if line)


def stats_to_dict(stats: DashboardStats) -> dict[str, object]:
    return {
        "total_tries": stats.total_tries,
        "top_count": stats.top_count,
        "fall_count": stats.fall_count,
        "fall_rate": round(_fall_rate(stats), 2),
        "fall_causes": {
            cause.value: count for cause, count in stats.fall_cause_counts.items()
        },
        "focus_points": focus_points(stats),
    }


def render_json(stats: DashboardStats) -> str:
    return json.dumps(stats_to_dict(stats), ensure_ascii=False, indent=2)


def _cause_ratio(stats: DashboardStats, cause: FallCause) -> float:
    total_causes = sum(stats.fall_cause_counts.values())
    if total_causes == 0:
        return 0.0
    return stats.fall_cause_counts.get(cause, 0) / total_causes * 100
