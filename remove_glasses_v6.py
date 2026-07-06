import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis

source = cv2.imread("/Users/lobster/.openclaw/media/inbound/ed7dbd50-654f-4aaa-b755-f997b2f2c5f3.jpg")
h, w = source.shape[:2]
print(f"Source: {w}x{h}")

# Use InsightFace to detect the face
app = FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0)

faces = app.get(source)
print(f"Detected {len(faces)} faces")

if len(faces) == 0:
    print("No face detected!")
    exit(1)

# Only 1 face was detected - which is the person with glasses
face = faces[0]
bbox = face.bbox
kps = face.kps

print(f"Face bbox: [{bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}]")
print(f"Keypoints (left_eye, right_eye, nose, mouth_l, mouth_r):")
for i, kp in enumerate(kps):
    print(f"  {i}: ({kp[0]:.0f}, {kp[1]:.0f})")

# Crop around the detected face with margin
margin = 150
x1 = max(0, int(bbox[0]) - margin)
y1 = max(0, int(bbox[1]) - margin)
x2 = min(w, int(bbox[2]) + margin)
y2 = min(h, int(bbox[3]) + margin)

face_crop = source[y1:y2, x1:x2].copy()
crop_h, crop_w = face_crop.shape[:2]
print(f"Crop: {crop_w}x{crop_h}")

# Adjust keypoints to crop coordinates
kps_c = kps.copy()
kps_c[:, 0] -= x1
kps_c[:, 1] -= y1

left_eye = kps_c[0]
right_eye = kps_c[1]

# The glasses frame is around the eye level
# From the original photo, the glasses have dark frames around the eyes
# Eye keypoints give us center of each eye
# Glasses extend beyond the eyes

# Estimate glasses region
eye_center_y = int((left_eye[1] + right_eye[1]) / 2)
eye_dist = int(abs(right_eye[0] - left_eye[0]))

# Glasses frame height (a bit taller than eye)
frame_h = int(eye_dist * 0.6)
# Half-width of each lens
lens_w = int(eye_dist * 0.7)

print(f"Eye center Y: {eye_center_y}")
print(f"Eye distance: {eye_dist}")
print(f"Frame height: {frame_h}")
print(f"Lens width: {lens_w}")

# Create mask
mask = np.zeros((crop_h, crop_w), dtype=np.uint8)

# Left lens - slightly rectangular for glasses frame
cv2.rectangle(mask,
    (int(left_eye[0]) - lens_w, int(left_eye[1]) - frame_h),
    (int(left_eye[0]) + int(lens_w * 0.3), int(left_eye[1]) + frame_h),
    255, -1)

# Right lens
cv2.rectangle(mask,
    (int(right_eye[0]) - int(lens_w * 0.3), int(right_eye[1]) - frame_h),
    (int(right_eye[0]) + lens_w, int(right_eye[1]) + frame_h),
    255, -1)

# Bridge
bridge_y = eye_center_y
cv2.rectangle(mask,
    (int(left_eye[0]) + int(lens_w * 0.2), bridge_y - int(frame_h * 0.3)),
    (int(right_eye[0]) - int(lens_w * 0.2), bridge_y + int(frame_h * 0.3)),
    255, -1)

# Arms
arm_y = eye_center_y
cv2.rectangle(mask,
    (int(left_eye[0]) - lens_w - int(eye_dist * 0.5), arm_y - int(frame_h * 0.4)),
    (int(left_eye[0]) - lens_w, arm_y + int(frame_h * 0.4)),
    255, -1)

cv2.rectangle(mask,
    (int(right_eye[0]) + lens_w, arm_y - int(frame_h * 0.4)),
    (int(right_eye[0]) + lens_w + int(eye_dist * 0.5), arm_y + int(frame_h * 0.4)),
    255, -1)

# Dilate
mask = cv2.dilate(mask, np.ones((7, 7), np.uint8), iterations=2)

# Save debug
cv2.imwrite("/Users/lobster/workspace/lali/face_crop_guy.jpg", face_crop)
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_guy.png", mask)

overlay = face_crop.copy()
overlay[mask > 0] = [0, 0, 255]
cv2.addWeighted(overlay, 0.5, face_crop, 0.5, 0, overlay)
cv2.imwrite("/Users/lobster/workspace/lali/glasses_overlay_guy.png", overlay)

print("Saved debug images. Check before proceeding.")
