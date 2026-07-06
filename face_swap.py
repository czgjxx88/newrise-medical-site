import os
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis

# Paths
source_path = "/Users/lobster/.openclaw/media/inbound/ed7dbd50-654f-4aaa-b755-f997b2f2c5f3.jpg"
target_path = "/Users/lobster/.openclaw/media/inbound/1f28214d-6617-43a4-945b-7d28b017829a.png"
output_path = "/Users/lobster/workspace/lali/face_swapped.png"

# Initialize face analysis and swapper
app = FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0)

swapper = insightface.model_zoo.get_model(os.path.expanduser('~/.insightface/models/inswapper_128.onnx'), providers=['CPUExecutionProvider'])

# Read images
source_img = cv2.imread(source_path)
target_img = cv2.imread(target_path)

if source_img is None:
    print(f"Failed to read source image: {source_path}")
    exit(1)
if target_img is None:
    print(f"Failed to read target image: {target_path}")
    exit(1)

print(f"Source image shape: {source_img.shape}")
print(f"Target image shape: {target_img.shape}")

# Detect faces
source_faces = app.get(source_img)
target_faces = app.get(target_img)

print(f"Source faces detected: {len(source_faces)}")
print(f"Target faces detected: {len(target_faces)}")

if len(source_faces) == 0:
    print("No source face detected!")
    exit(1)
if len(target_faces) == 0:
    print("No target face detected!")
    exit(1)

# Use the first (largest/most prominent) face from source
source_face = sorted(source_faces, key=lambda x: x.bbox[2]*x.bbox[3], reverse=True)[0]

# Use the first face from target
target_face = sorted(target_faces, key=lambda x: x.bbox[2]*x.bbox[3], reverse=True)[0]

# Perform face swap
result = swapper.get(target_img, target_face, source_face, paste_back=True)

# Save result
cv2.imwrite(output_path, result)
print(f"Saved result to {output_path}")
