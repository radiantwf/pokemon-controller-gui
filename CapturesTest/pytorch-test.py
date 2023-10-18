import torch
import torchvision.transforms as transforms
import cv2
import numpy as np
from sklearn.cluster import KMeans

# Load pre-trained ResNet model
model = torch.hub.load('pytorch/vision:v0.9.0', 'resnet18', pretrained=True)
model.eval()

# Define image transforms
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# Load video
cap = cv2.VideoCapture('video.mp4')

# Define K-Means clustering algorithm
kmeans = KMeans(n_clusters=2)

# Loop through video frames
while True:
    # Read frame
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert frame to tensor
    tensor = transform(frame).unsqueeze(0)
    
    # Extract features using ResNet model
    with torch.no_grad():
        features = model(tensor).squeeze().numpy()
    
    # Cluster features using K-Means
    labels = kmeans.fit_predict(features)
    
    # Generate binary mask
    mask = np.zeros((224, 224), dtype=np.uint8)
    mask[labels == 0] = 255
    
    # Apply mask to original frame
    result = cv2.bitwise_and(frame, frame, mask=mask)
    
    # Display result
    cv2.imshow('Result', result)
    if cv2.waitKey(1) == ord('q'):
        break

# Release video capture and close windows
cap.release()
cv2.destroyAllWindows()