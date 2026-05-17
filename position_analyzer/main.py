import argparse
import os

from app import DEFAULT_MODEL_PATH, MODEL_DOWNLOAD_URL, AppOptions, app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='ボルダリング動作解析デモ')
    _ = parser.add_argument('-i', '--input', required=True, help='入力動画 (例: IMG_1540.MOV)')
    _ = parser.add_argument('-o', '--output', default='output.mp4', help='出力動画 (例: result.mp4)')
    _ = parser.add_argument('-t', '--trail', type=int, default=120, help='軌跡を残すフレーム数')
    _ = parser.add_argument('-k', '--keep-trail', action='store_true', help='軌跡を動画中ずっと残す')
    _ = parser.add_argument('-m', '--model', default=DEFAULT_MODEL_PATH, help='PoseLandmarker モデル (.task) のパス')
    _ = parser.add_argument('--gpu', action='store_true', help='GPU を使用して推論を実行する')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.input):
        print(f"エラー: 入力ファイル '{args.input}' が見つかりません。")
        return
    if not os.path.exists(args.model):
        print(f"エラー: モデルファイル '{args.model}' が見つかりません。")
        print(f"{MODEL_DOWNLOAD_URL} からダウンロードしてください。")
        return

    options = AppOptions(
        input_path=args.input,
        output_path=args.output,
        trail=args.trail,
        keep_trail=args.keep_trail,
        model_path=args.model,
        use_gpu=args.gpu,
    )
    app(options)


if __name__ == "__main__":
    main()
