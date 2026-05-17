from __future__ import annotations

import collections
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.components.containers.landmark import NormalizedLandmark

from position_analyzer.perf_timer import PerfTimer

VISIBILITY_THRESHOLD = 0.5
COM_COLOR = (255, 0, 0)
TRAIL_COLOR = (0, 0, 255)
LANDMARK_COLOR = (0, 255, 0)
CONNECTION_COLOR = (255, 255, 255)

INFERENCE_MAX_DIMENSION = 720


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "pose_landmarker_lite.task"
)
MODEL_DOWNLOAD_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"


@dataclass
class AppOptions:
    input_path: str
    output_path: str
    trail: int
    keep_trail: bool
    model_path: str
    use_gpu: bool


class Analyzer:
    def __init__(self, input_path: str, model_path: str, trail_length: int | None, use_gpu: bool):
        self.filename: str = input_path
        self.landmarker: Any = self._create_landmarker(model_path, use_gpu)
        self.com_history: collections.deque[tuple[int, int]] = collections.deque(
            maxlen=trail_length
        )

        self.cap: cv2.VideoCapture = cv2.VideoCapture(input_path)
        self.width: int = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height: int = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps: float = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames: int = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fourcc: int = cv2.VideoWriter_fourcc(*"mp4v")

    def _build_landmarker(self, model_path: str, delegate: Any, num_threads: int = 4) -> Any:
        base_options = mp_python.BaseOptions(
            model_asset_path=model_path, delegate=delegate
        )
        if delegate == mp_python.BaseOptions.Delegate.CPU:
            base_options.num_threads = num_threads

        options = mp_vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False,
        )
        return mp_vision.PoseLandmarker.create_from_options(options)

    def _create_landmarker(self, model_path: str, use_gpu: bool) -> Any:
        cpu_threads = os.cpu_count() or 4
        if use_gpu:
            try:
                landmarker = self._build_landmarker(
                    model_path, mp_python.BaseOptions.Delegate.GPU
                )
                logger.info("GPU delegate initialized successfully")
                return landmarker
            except Exception as e:
                logger.warning(
                    f"Failed to initialize GPU delegate. Using CPU with {cpu_threads} threads ({e})"
                )
                return self._build_landmarker(
                    model_path, mp_python.BaseOptions.Delegate.CPU, num_threads=cpu_threads
                )
        else:
            logger.info(f"Using CPU with {cpu_threads} threads")
            return self._build_landmarker(
                model_path, mp_python.BaseOptions.Delegate.CPU, num_threads=cpu_threads
            )

    def calculate_com(
        self, landmarks: list[NormalizedLandmark]
    ) -> tuple[int, int] | None:
        l_hip = landmarks[mp_vision.PoseLandmark.LEFT_HIP]
        r_hip = landmarks[mp_vision.PoseLandmark.RIGHT_HIP]

        if (
            l_hip.visibility > VISIBILITY_THRESHOLD
            and r_hip.visibility > VISIBILITY_THRESHOLD
        ):
            com_x = int((l_hip.x + r_hip.x) / 2 * self.width)
            com_y = int((l_hip.y + r_hip.y) / 2 * self.height)
            return (com_x, com_y)
        return None

    def preprocess_frame(
        self, frame: np.ndarray, frame_index: int
    ) -> tuple[mp.Image, int]:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int(frame_index * 1000.0 / self.fps)

        return mp_image, timestamp_ms

    def run_inference(
        self, mp_image: mp.Image, timestamp_ms: int
    ) -> list[list[NormalizedLandmark]]:
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        return result.pose_landmarks

    def close(self) -> None:
        self.cap.release()
        self.landmarker.close()


class Renderer:
    def __init__(self, output_path: str, fps: float, width: int, height: int):
        self.specs = {
            "landmark": mp_vision.drawing_utils.DrawingSpec(
                color=LANDMARK_COLOR, thickness=4, circle_radius=6
            ),
            "connection": mp_vision.drawing_utils.DrawingSpec(
                color=CONNECTION_COLOR, thickness=3
            ),
        }
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    def draw_trail(
        self, image: np.ndarray, history: collections.deque[tuple[int, int]]
    ) -> None:
        if len(history) <= 1:
            return
        for i in range(1, len(history)):
            alpha = i / len(history)
            thickness = int(1 + 4 * alpha)
            cv2.line(image, history[i - 1], history[i], TRAIL_COLOR, thickness)

    def draw_pose(self, image: np.ndarray, landmarks: list[NormalizedLandmark]) -> None:
        mp_vision.drawing_utils.draw_landmarks(
            image,
            landmarks,
            mp_vision.PoseLandmarksConnections.POSE_LANDMARKS,
            landmark_drawing_spec=self.specs["landmark"],
            connection_drawing_spec=self.specs["connection"],
        )

    def draw_results(
        self,
        frame: np.ndarray,
        pose_landmarks: list[list[NormalizedLandmark]],
        com_point: tuple[int, int] | None,
        com_history: collections.deque[tuple[int, int]],
    ) -> None:
        overlay = frame.copy()

        if pose_landmarks:
            landmarks = pose_landmarks[0]
            if com_point:
                com_history.append(com_point)
                self.draw_trail(overlay, com_history)
                cv2.circle(frame, com_point, 10, COM_COLOR, -1)
            self.draw_pose(frame, landmarks)

        _ = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    def write(self, frame: np.ndarray) -> None:
        self.out.write(frame)

    def close(self) -> None:
        self.out.release()


def app(options: AppOptions, progress_callback=None) -> None:
    timer = PerfTimer()

    timer.checkin("setup")
    trail_length = None if options.keep_trail else options.trail
    analyzer = Analyzer(options.input_path, options.model_path, trail_length, options.use_gpu)
    renderer = Renderer(
        options.output_path, analyzer.fps, analyzer.width, analyzer.height
    )
    timer.checkout("setup")

    logger.info(f"Starting analysis... (total {analyzer.total_frames} frames)")

    timer.checkin("loop")
    frame_index = 0
    while analyzer.cap.isOpened():
        timer.checkin("read")
        success, frame = analyzer.cap.read()
        timer.checkout("read")
        if not success:
            break

        timer.checkin("preprocess")
        mp_image, timestamp_ms = analyzer.preprocess_frame(frame, frame_index)
        timer.checkout("preprocess")

        timer.checkin("inference")
        pose_landmarks = analyzer.run_inference(mp_image, timestamp_ms)
        timer.checkout("inference")

        com_point = None
        if pose_landmarks:
            com_point = analyzer.calculate_com(pose_landmarks[0])

        timer.checkin("draw")
        renderer.draw_results(frame, pose_landmarks, com_point, analyzer.com_history)
        timer.checkout("draw")

        timer.checkin("write")
        renderer.write(frame)
        timer.checkout("write")

        frame_index += 1
        if frame_index % 30 == 0:
            loop_elapsed = timer.get_total("loop") + (
                time.perf_counter() - timer._active.get("loop", time.perf_counter())
            )
            current_fps = frame_index / loop_elapsed if loop_elapsed > 0 else 0.0
            logger.info(
                f"Progress: {frame_index} / {analyzer.total_frames} frames processed ({current_fps:.2f} FPS)"
            )

            if progress_callback:
                progress_callback(frame_index, analyzer.total_frames)

    timer.checkout("loop")

    analyzer.close()
    renderer.close()
    print_timing_report(timer, frame_index)


def print_timing_report(timer: PerfTimer, frame_count: int) -> None:
    timings = timer.to_dict()
    setup_elapsed = timings.get("setup", {}).get("total_sec", 0.0)
    loop_elapsed = timings.get("loop", {}).get("total_sec", 0.0)
    total_elapsed = setup_elapsed + loop_elapsed

    avg_fps = frame_count / loop_elapsed if loop_elapsed > 0 else 0.0
    avg_ms = (loop_elapsed / frame_count * 1000) if frame_count > 0 else 0.0

    stages = {}
    for key in ["read", "preprocess", "inference", "draw", "write"]:
        if key in timings:
            elapsed = timings[key]["total_sec"]
            ratio = (elapsed / loop_elapsed * 100) if loop_elapsed > 0 else 0.0
            per_frame_ms = (elapsed / frame_count * 1000) if frame_count > 0 else 0.0
            stages[key] = {
                "elapsed_sec": elapsed,
                "ratio_percent": round(ratio, 1),
                "per_frame_ms": round(per_frame_ms, 1),
            }

    report = {
        "setup_sec": setup_elapsed,
        "loop_sec": loop_elapsed,
        "total_sec": round(total_elapsed, 2),
        "frame_count": frame_count,
        "avg_fps": round(avg_fps, 2),
        "avg_ms_per_frame": round(avg_ms, 1),
        "stages": stages,
    }

    logger.info(f"Timing report: {json.dumps(report, ensure_ascii=False, indent=2)}")
