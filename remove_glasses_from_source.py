import cv2
import numpy as np

# Step 1: Detect face in source and crop it
source = cv2.imread("/Users/lobster/.openclaw/media/inbound/ed7dbd50-654f-4aaa-b755-f997b2f2c5f3.jpg")
h, w = source.shape[:2]
print(f"Source: {w}x{h}")

# The person with glasses is in the middle-left of the photo
# Let's use face detection to find the face
import insightface
from insightface.app import FaceAnalysis

app = FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0)

faces = app.get(source)
print(f"Found {len(faces)} faces")

# Find the face with glasses (middle person in the group)
# Sort by x position - we want the middle one
for i, face in enumerate(faces):
    bbox = face.bbox
    print(f"Face {i}: bbox={bbox}, center_x={bbox[0]+(bbox[2]-bbox[0])/2}")

# Sort faces by x center
sorted_faces = sorted(faces, key=lambda f: (f.bbox[0]+f.bbox[2])/2)
print(f"\nSorted faces:")
for i, face in enumerate(sorted_faces):
    bbox = face.bbox
    print(f"Face {i}: x_center={(bbox[0]+bbox[2])/2:.0f}")

# The middle face (index 1 after sorting) has the glasses
target_face = sorted_faces[1]
bbox = target_face.bbox
print(f"\nTarget face bbox: {bbox}")

# Crop a larger region around the face for editing
margin = 100
x1 = max(0, int(bbox[0]) - margin)
y1 = max(0, int(bbox[1]) - margin)
x2 = min(w, int(bbox[2]) + margin)
y2 = min(h, int(bbox[3]) + margin)

face_crop = source[y1:y2, x1:x2].copy()
crop_h, crop_w = face_crop.shape[:2]
print(f"Crop: {crop_w}x{crop_h}")

# In the cropped image, the face center is at:
face_cx = (bbox[0]+bbox[2])/2 - x1
face_cy = (bbox[1]+bbox[3])/2 - y1
print(f"Face center in crop: ({face_cx:.0f}, {face_cy:.0f})")

# Glasses are roughly in the upper 1/3 of the face
# Create a mask for the glasses in the cropped image
mask = np.zeros((crop_h, crop_w), dtype=np.uint8)

# Glasses position relative to the crop
# Eyes are roughly at 35-45% from top of face bounding box
glasses_y_center = int(bbox[1] + (bbox[3]-bbox[1])*0.38 - y1)
glasses_height = int((bbox[3]-bbox[1]) * 0.15)
glasses_width = int((bbox[2]-bbox[0]) * 0.4)

# Left lens
cv2.ellipse(mask, (int(face_cx - glasses_width*0.25), glasses_y_center), 
            (glasses_width//3, glasses_height//2), 0, 0, 360, 255, -1)
# Right lens
cv2.ellipse(mask, (int(face_cx + glasses_width*0.25), glasses_y_center), 
            (glasses_width//3, glasses_height//2), 0, 0, 360, 255, -1)
# Bridge
cv2.rectangle(mask, 
    (int(face_cx - glasses_width*0.08), glasses_y_center - glasses_height//3),
    (int(face_cx + glasses_width*0.08), glasses_y_center + glasses_height//3),
    255, -1)
# Arms
cv2.rectangle(mask, 
    (int(face_cx - glasses_width*0.5), glasses_y_center - glasses_height//4),
    (int(face_cx - glasses_width*0.25), glasses_y_center + glasses_height//4),
    255, -1)
cv2.rectangle(mask, 
    (int(face_cx + glasses_width*0.25), glasses_y_center - glasses_height//4),
    (int(face_cx + glasses_width*0.5), glasses_y_center + glasses_height//4),
    255, -1)

# Dilate mask
mask = cv2.dilate(mask, np.ones((7,7), np.uint8), iterations=2)

# Save mask for debugging
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_crop.png", mask)

# Inpaint
result_crop = cv2.inpaint(face_crop, mask, inpaintRadius=15, flags=cv2.INPAINT_NS)

# Put the edited crop back into the source image
source_no_glasses = source.copy()
source_no_glasses[y1:y2, x1:x2] = result_crop

cv2.imwrite("/Users/lobster/workspace/lali/source_no_glasses.jpg", source_no_glasses)
print("Saved source_no_glasses.jpg")
cv2.imwrite("/Users/lobster/workspace/lali/face_crop_edited.jpg", result_crop)
print("Saved face_crop_edited.jpg")
