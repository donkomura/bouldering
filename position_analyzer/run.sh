#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA

IMAGE_NAME="bouldering:latest"

if [[ "$1" == "--build" ]] || ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo "Building Docker image..."
    docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
    shift 2>/dev/null || true
fi

DOCKER_ARGS=(
    -it --rm
    --runtime=nvidia
    --gpus all
    --env DISPLAY=$DISPLAY
    --env WAYLAND_DISPLAY=$WAYLAND_DISPLAY
    --env XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR
    --env PULSE_SERVER=$PULSE_SERVER
    --volume "$SCRIPT_DIR":/workspace
)

[[ -e /dev/dxg ]] && DOCKER_ARGS+=(--device /dev/dxg)
[[ -e /dev/dri/card0 ]] && DOCKER_ARGS+=(--device /dev/dri/card0)
[[ -e /dev/dri/renderD128 ]] && DOCKER_ARGS+=(--device /dev/dri/renderD128)
[[ -d /tmp/.X11-unix ]] && DOCKER_ARGS+=(--volume /tmp/.X11-unix:/tmp/.X11-unix)
[[ -d /mnt/wslg ]] && DOCKER_ARGS+=(--volume /mnt/wslg:/mnt/wslg)
[[ -d /usr/lib/wsl ]] && DOCKER_ARGS+=(--volume /usr/lib/wsl:/usr/lib/wsl)

docker run "${DOCKER_ARGS[@]}" "$IMAGE_NAME" "$@"
