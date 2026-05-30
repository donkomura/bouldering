FROM ubuntu:jammy

ARG DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get -y upgrade && apt-get -y install \
    software-properties-common \
    && add-apt-repository ppa:kisak/kisak-mesa \
    && apt-get update \
    && apt-get -y install \
    libxext-dev \
    libx11-dev \
    libglvnd-dev \
    libglx-dev \
    libgl1-mesa-dev \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libegl1-mesa-dev \
    libgles2-mesa-dev \
    mesa-va-drivers \
    mesa-vulkan-drivers \
    freeglut3-dev \
    mesa-utils \
    mesa-utils-extra \
    python3 \
    python3-pip \
    libglib2.0-0 \
    libglib2.0-dev \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgomp1 \
    libgtk2.0-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libatlas-base-dev \
    gfortran \
    && apt-get -y autoremove \
    && apt-get clean

ENV LD_LIBRARY_PATH=/usr/lib/wsl/lib
ENV LIBVA_DRIVER_NAME=d3d12
ENV MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
ENV MESA_LOADER_DRIVER_OVERRIDE=d3d12
ENV GALLIUM_DRIVER=d3d12

WORKDIR /workspace

COPY pyproject.toml uv.lock* ./

RUN pip3 install --no-cache-dir uv && \
    uv pip install --system --no-cache -r pyproject.toml

COPY . .

CMD ["python3", "main.py"]
