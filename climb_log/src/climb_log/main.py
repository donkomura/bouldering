from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from climb_log.dashboard import (
    compute_stats,
    focus_points,
    render_image,
    render_terminal,
)
from climb_log.models import ClimbResult, FallCause, Record, WallAngle
from climb_log.store import TryStore


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="climb_log",
        description="BetaLog - ボルダリングトライ記録・分析ツール",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    record_p = sub.add_parser("record", help="トライを記録する")
    record_p.add_argument(
        "-i", "--input", required=True, metavar="VIDEO", help="動画ファイルパス"
    )
    record_p.add_argument(
        "--result",
        required=True,
        choices=["top", "fall"],
        help="結果（top=完登, fall=フォール）",
    )
    record_p.add_argument(
        "--cause",
        nargs="+",
        choices=[c.value for c in FallCause],
        metavar="CAUSE",
        help="フォール原因（複数可）",
    )
    record_p.add_argument("--grade", metavar="GRADE", help="グレード（例: 3級, 初段）")
    record_p.add_argument(
        "--angle",
        choices=[a.value for a in WallAngle],
        metavar="ANGLE",
        help="傾斜（slab/vertical/overhang/roof）",
    )
    record_p.add_argument("--note", metavar="NOTE", help="メモ")

    dash_p = sub.add_parser("dashboard", help="悪癖ダッシュボードを表示する")
    dash_p.add_argument(
        "--period",
        choices=["week", "month"],
        default="week",
        help="集計期間（デフォルト: week）",
    )
    dash_p.add_argument(
        "--image", metavar="PATH", help="ダッシュボード画像の出力先パス"
    )

    sub.add_parser("list", help="トライ記録一覧を表示する")

    return parser


def _cmd_record(args: argparse.Namespace, store: TryStore) -> None:
    record = Record(
        id=str(uuid.uuid4()),
        video_path=args.input,
        result=ClimbResult(args.result),
        recorded_at=datetime.now(tz=timezone.utc).replace(tzinfo=None),
        fall_causes=[FallCause(c) for c in (args.cause or [])],
        grade=args.grade,
        wall_angle=WallAngle(args.angle) if args.angle else None,
        note=args.note,
    )
    store.add(record)
    print(f"記録しました: {record.id} ({record.result.value})")


def _cmd_dashboard(args: argparse.Namespace, store: TryStore) -> None:
    now = datetime.now()
    if args.period == "week":
        since = now - timedelta(days=7)
        label = "直近7日間"
    else:
        since = now - timedelta(days=30)
        label = "直近30日間"

    records = store.list_since(since)
    stats = compute_stats(records, period_label=label)
    print(render_terminal(stats))

    for point in focus_points(stats):
        print(f"\n★ {point}")

    if args.image:
        output = Path(args.image)
    else:
        date_str = now.strftime("%Y%m%d")
        output = Path(f"betalog_dashboard_{date_str}.png")

    render_image(stats, output)
    print(f"\nダッシュボード画像を保存しました: {output}")


def _cmd_list(store: TryStore) -> None:
    records = store.list_all()
    if not records:
        print("記録がありません。")
        return
    for r in records:
        causes = ", ".join(c.value for c in r.fall_causes) if r.fall_causes else "-"
        grade = r.grade or "-"
        print(
            f"[{r.recorded_at.strftime('%Y-%m-%d %H:%M')}] {r.result.value:4s}  grade={grade}  cause={causes}  {r.video_path}"
        )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    store = TryStore()

    if args.command == "record":
        _cmd_record(args, store)
    elif args.command == "dashboard":
        _cmd_dashboard(args, store)
    elif args.command == "list":
        _cmd_list(store)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
