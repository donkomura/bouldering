from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from climb_log.models import ClimbResult, FallCause, TryRecord

_CAUSE_LABELS: dict[FallCause, str] = {
    FallCause.FOOT_SLIP: "足切れ",
    FallCause.PUMP: "パンプ",
    FallCause.SWEATY_HANDS: "手汗",
    FallCause.WRONG_MOVE: "ムーブミス",
    FallCause.OTHER: "その他",
}


@dataclass
class DashboardStats:
    total_tries: int
    top_count: int
    fall_count: int
    fall_cause_counts: dict[FallCause, int]
    period_label: str = ""


def compute_stats(records: list[TryRecord], period_label: str = "") -> DashboardStats:
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
        period_label=period_label,
    )


def focus_points(stats: DashboardStats) -> list[str]:
    if not stats.fall_cause_counts:
        return []
    top_cause = max(stats.fall_cause_counts, key=lambda c: stats.fall_cause_counts[c])
    label = _CAUSE_LABELS.get(top_cause, top_cause.value)
    return [f"「{label}」を意識して登りましょう（全フォールの {_cause_ratio(stats, top_cause):.0f}%）"]


def render_terminal(stats: DashboardStats) -> str:
    fall_rate = (stats.fall_count / stats.total_tries * 100) if stats.total_tries > 0 else 0.0
    lines = [
        f"期間: {stats.period_label}" if stats.period_label else "",
        f"トライ数: {stats.total_tries}  完登: {stats.top_count}  フォール: {stats.fall_count}  フォール率: {fall_rate:.0f}%",
    ]
    if stats.fall_cause_counts:
        lines.append("フォール原因:")
        for cause, count in sorted(stats.fall_cause_counts.items(), key=lambda x: -x[1]):
            label = _CAUSE_LABELS.get(cause, cause.value)
            lines.append(f"  {label}: {count}回")
    points = focus_points(stats)
    if points:
        lines.append("フォーカスポイント:")
        for p in points:
            lines.append(f"  {p}")
    return "\n".join(l for l in lines if l)


def render_image(stats: DashboardStats, output_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    _draw_result_pie(axes[0], stats)
    _draw_cause_pie(axes[1], stats)

    title = f"BetaLog ダッシュボード {stats.period_label}".strip()
    fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    fig.savefig(output_path, dpi=100)
    plt.close(fig)


def _draw_result_pie(ax: plt.Axes, stats: DashboardStats) -> None:
    ax.set_title("結果")
    if stats.total_tries == 0:
        ax.text(0.5, 0.5, "データなし", ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        return
    sizes = [stats.top_count, stats.fall_count]
    labels = ["完登", "フォール"]
    colors = ["#4CAF50", "#F44336"]
    non_zero = [(s, l, c) for s, l, c in zip(sizes, labels, colors) if s > 0]
    if non_zero:
        s, l, c = zip(*non_zero)
        ax.pie(s, labels=l, colors=c, autopct="%1.0f%%", startangle=90)


def _draw_cause_pie(ax: plt.Axes, stats: DashboardStats) -> None:
    ax.set_title("フォール原因")
    if not stats.fall_cause_counts:
        ax.text(0.5, 0.5, "データなし", ha="center", va="center", transform=ax.transAxes)
        ax.axis("off")
        return
    sorted_causes = sorted(stats.fall_cause_counts.items(), key=lambda x: -x[1])
    sizes = [count for _, count in sorted_causes]
    labels = [_CAUSE_LABELS.get(cause, cause.value) for cause, _ in sorted_causes]
    ax.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=90)


def _cause_ratio(stats: DashboardStats, cause: FallCause) -> float:
    total_causes = sum(stats.fall_cause_counts.values())
    if total_causes == 0:
        return 0.0
    return stats.fall_cause_counts.get(cause, 0) / total_causes * 100
