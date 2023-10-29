from ultralytics import YOLO

# Load a model
model = YOLO('yolo_training/yolov8n.pt')  # load a pretrained model (recommended for training)

# Train the model
results = model.train(data='yolo_training/train.yaml', epochs=100, imgsz=640, device='mps')