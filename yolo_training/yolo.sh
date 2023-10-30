#!/bin/bash

# train
yolo train model=yolo_training/yolov8n.pt data=yolo_training/train.yaml device=mps

# val
yolo val model=runs/detect/train/weights/best.pt data=yolo_training/train.yaml device=mps

# predict
yolo predict model=runs/detect/train/weights/best.pt source="yolo_training/data/2023-10-29 01-28-46.mp4" device=mps
yolo predict model=runs/detect/train/weights/last.pt source="yolo_training/data/train/0984-Great Tusk-0001.jpg" device=mps