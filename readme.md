# FireGuard_AI

Comprehensive project documentation for FireGuard_AI — an end-to-end fire and smoke detection system that uses computer vision and machine learning to detect, alert, and assist in early fire detection for indoor and outdoor environments.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Training a Model](#training-a-model)
- [Running Inference](#running-inference)
- [API](#api)
- [Evaluation](#evaluation)
- [Deployment](#deployment)
- [Docker](#docker)
- [Data Management](#data-management)
- [Security & Privacy](#security--privacy)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Contact](#contact)

---

## Project Overview

FireGuard_AI is designed to provide reliable, real-time detection of fire and smoke from camera feeds. It combines deep-learning-based object detection and segmentation with an alerting and logging pipeline to notify operators or integrated systems when a potential fire or smoke is detected.

Intended use cases:
- Industrial and warehouse monitoring
- Forest and perimeter surveillance
- Smart building safety systems
- Home security and IoT devices

This repository contains code, model training scripts, inference utilities, evaluation tools, and deployment examples.

---

## Key Features

- Real-time detection from video streams and static images
- Support for object detection and segmentation models
- Model training and evaluation scripts
- Inference server and REST API for integration
- Dockerfile and deployment examples
- Logging, alerting, and post-processing utilities

---

## Architecture

A typical pipeline implemented by this project:

1. Camera or video source (RTSP/IP camera, USB camera, or video file)
2. Preprocessing (resize, normalize, augment for training)
3. ML model (object detection / segmentation)
4. Post-processing (non-maximum suppression, temporal smoothing)
5. Alerting & logging (webhooks, emails, local logs, dashboard)
6. Optional: cloud upload for analytics and model improvement

Refer to architecture diagrams (if present) and code in the repository for specifics.

---

## How It Works

- Models are trained on annotated datasets containing fire, smoke, and relevant negative examples.
- During inference, frames are passed to the trained model. Predictions above configurable confidence thresholds trigger alerts.
- Temporal filtering reduces false positives by requiring detections to persist across multiple frames and/or cameras.

---

## Requirements

- Python 3.8+ (3.10+ recommended)
- CUDA-capable GPU for model training and fast inference (optional but recommended)
- pip
- ffmpeg (for handling video inputs)

Python dependencies are listed in requirements.txt (if present). If this repository contains a [requirements.txt](D:/fire_detection.worktrees/complete-project-docs-readme/requirements.txt) or environment file, use that to install exact versions.

---

## Installation

1. Clone the repository:

   git clone https://github.com/rithik-dev31/FireGuard_AI.git
   cd FireGuard_AI

2. (Optional) Create a virtual environment and activate it:

   python -m venv .venv
   .venv\Scripts\activate   # Windows

3. Install Python dependencies:

   pip install -r requirements.txt

4. Install or verify ffmpeg availability (system package manager or download binary).

---

## Quick Start

1. Run inference on a sample image or video (example command — adapt to your project layout):

   python inference/run_inference.py --source data/samples/sample1.mp4 --weights models/latest.pt --conf 0.5

2. Start the API server (example):

   python api/server.py --host 0.0.0.0 --port 8000 --weights models/latest.pt

3. Open the dashboard or integrate the REST API into your monitoring stack.

Note: Replace paths and parameters with files present in the repository. See the [API](#api) section for endpoints and payloads.

---

## Training a Model

High-level steps to train a model on custom data:

1. Prepare an annotated dataset in COCO, Pascal VOC, or YOLO format.
2. Configure dataset paths and hyperparameters in the config file (e.g., configs/train.yaml).
3. Launch training:

   python training/train.py --config configs/train.yaml --device 0

4. Monitor training logs and TensorBoard (if configured). Models will be saved into the `models/` directory by default.

Tips:
- Use data augmentation to increase model robustness (brightness, blur, scaling, rotation)
- Balance positive and negative examples
- Consider transfer learning / fine-tuning from a pre-trained backbone

---

## Running Inference

Supported input sources:
- Single image
- Video file
- RTSP/HTTP camera stream
- Directory of images

Example CLI:

   python inference/run_inference.py --source 0 --weights models/latest.pt --conf 0.6 --save-output output/ --gpu

Key flags:
- --source: camera index, file path, or stream URL
- --weights: path to the model weights
- --conf: confidence threshold
- --save-output: directory to save annotated frames or video
- --gpu: enable GPU inference

---

## API

If the repository includes an API server, typical endpoints:

- POST /infer - run inference on an uploaded image or URL
- POST /stream - register a camera stream for continuous inference
- GET /status - health check
- GET /metrics - detection statistics and recent alerts

Example request to /infer (application/json):

{
  "image_url": "https://example.com/frame.jpg",
  "confidence": 0.5
}

Response: JSON with bounding boxes, scores, and class labels.

---

## Evaluation

Scripts are included to evaluate model performance on hold-out test sets. Example metrics to measure:

- Precision / Recall
- mAP (mean Average Precision)
- F1 score
- Per-class AP (fire, smoke)

Run evaluation (example):

   python evaluation/evaluate.py --weights models/best.pt --dataset data/test --format coco

Record results and visualize confusion matrices to understand common failure modes.

---

## Deployment

Deployment options provided in this repository may include:
- Docker container for the inference server
- Systemd service example for Linux hosts
- Kubernetes deployment manifests (example)

General steps for production deployment:
1. Build or pull the Docker image.
2. Run the container with access to the camera stream(s) and GPU (if needed).
3. Configure monitoring and logging (Prometheus, Grafana, ELK).
4. Set up alerting (webhooks, email, SMS, or integration with incident management tools).

---

## Docker

If a Dockerfile is included, build and run with:

   docker build -t fireguard_ai:latest .
   docker run --gpus all -p 8000:8000 -v /path/to/data:/app/data fireguard_ai:latest

Adjust flags for GPU or device access as required.

---

## Data Management

- Keep raw videos and images stored separately from annotations.
- Version datasets and model checkpoints (consider DVC or git-lfs for large files).
- Log metadata for each training run: dataset version, hyperparameters, model commit hash.

---

## Security & Privacy

- Secure camera streams and API endpoints using TLS.
- Limit access with API keys or OAuth where appropriate.
- Be mindful of privacy when storing or transmitting camera footage — redact or encrypt PII where required.

---

## Troubleshooting

- Low detection accuracy: check dataset balance, annotation quality, and augmentations.
- High false positive rate: raise confidence threshold, apply temporal filtering, or add negative samples to training data.
- Performance issues: optimize input resolution, enable GPU inference, or use a lighter backbone.

---

## Contributing

Contributions are welcome. Please follow these guidelines:
1. Open an issue to discuss major changes first.
2. Create a feature branch and submit a pull request.
3. Write tests for new functionality when applicable.
4. Keep commits small and focused.

See CONTRIBUTING.md (if present) for repository-specific rules.

---

## License

This project is provided under the MIT License unless otherwise specified in a LICENSE file in the repository.

---

## Acknowledgements

- Inspired by open-source object detection frameworks and community datasets.
- Thanks to contributors and maintainers.

---

## Contact

For questions or support, open an issue or contact the maintainers listed in the repository.

---

Notes:
- Replace example file paths and commands with the real scripts and locations present in this repository.
- If specific files like `inference/run_inference.py`, `training/train.py`, or `api/server.py` do not exist in the repo, update commands to match actual filenames.

