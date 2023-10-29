#!/bin/bash
yolo detect train data=train.yaml model=yolov8n.pt epochs=10 lr0=0.01