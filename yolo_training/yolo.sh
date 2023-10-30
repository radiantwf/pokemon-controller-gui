#!/bin/bash

# train
yolo predict model=yolo_training/yolov8n.pt data=yolo_training/train.yaml device=mps

# val
yolo val model=runs/detect/train/weights/best.pt data=yolo_training/train.yaml device=mps

# predict
yolo predict model=runs/detect/train/weights/best.pt source="yolo_training/data/2023-10-29 01-28-46.mp4" device=mps