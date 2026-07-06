import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis

# Step 1: Detect face in the original source image and crop a high-res face region
source = cv2.imread("/Users/lobster/.openclaw/media/inbound/ed7dbd50-654f-4aaa-b755-f997b2f2c5f3.jpg")
h, w = source.shape[:2]
print(f"Source: {w}x{h}")

app = FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0)

faces = app.get(source)
print(f"Detected {len(faces)} faces")

if len(faces) == 0:
    print("No face detected!")
    exit(1)

# The person we want is the one with glasses - should be the most prominent face
# Since insightface only detected 1 face in this image, use that
face = faces[0]
bbox = face.bbox
kps = face.kps

print(f"Face bbox: {bbox}")
print(f"Keypoints: {kps}")

# Crop a generous region around the face
margin = 200
x1 = max(0, int(bbox[0]) - margin)
y1 = max(0, int(bbox[1]) - margin)
x2 = min(w, int(bbox[2]) + margin)
y2 = min(h, int(bbox[3]) + margin)

face_crop = source[y1:y2, x1:x2].copy()
crop_h, crop_w = face_crop.shape[:2]
print(f"Cropped: {crop_w}x{crop_h}")

# Adjust keypoints to cropped coordinates
kps_crop = kps.copy()
kps_crop[:, 0] -= x1
kps_crop[:, 1] -= y1

print(f"Keypoints in crop: {kps_crop}")

# The 5 keypoints are: left_eye, right_eye, nose, left_mouth, right_mouth
left_eye = kps_crop[0]
right_eye = kps_crop[1]

print(f"Left eye: ({left_eye[0]:.0f}, {left_eye[1]:.0f})")
print(f"Right eye: ({right_eye[0]:.0f}, {right_eye[1]:.0f})")

# Create a glasses mask around the eyes
# Glasses extend beyond the eye keypoints
eye_dist = np.linalg.norm(right_eye - left_eye)
glasses_h = int(eye_dist * 0.4)
glasses_w = int(eye_dist * 0.5)
arm_w = int(eye_dist * 0.3)

mask = np.zeros((crop_h, crop_w), dtype=np.uint8)

# Left lens area - extend around left eye
lx, ly = int(left_eye[0]), int(left_eye[1])
cv2.rectangle(mask, 
    (lx - glasses_w, ly - glasses_h),
    (lx + int(glasses_w * 0.3), ly + glasses_h),
    255, -1)

# Right lens area
rx, ry = int(right_eye[0]), int(right_eye[1])
cv2.rectangle(mask,
    (rx - int(glasses_w * 0.3), ry - glasses_h),
    (rx + glasses_w, ry + glasses_h),
    255, -1)

# Bridge between lenses
bridge_y = int((ly + ry) / 2)
cv2.rectangle(mask,
    (lx + int(glasses_w * 0.2), bridge_y - int(glasses_h * 0.4)),
    (rx - int(glasses_w * 0.2), bridge_y + int(glasses_h * 0.4)),
    255, -1)

# Left arm
cv2.rectangle(mask,
    (lx - glasses_w - arm_w, ly - int(glasses_h * 0.5)),
    (lx - glasses_w, ly + int(glasses_h * 0.5)),
    255, -1)

# Right arm
cv2.rectangle(mask,
    (rx + glasses_w, ry - int(glasses_h * 0.5)),
    (rx + glasses_w + arm_w, ry + int(glasses_h * 0.5)),
    255, -1)

# Dilate to cover frame edges
mask = cv2.dilate(mask, np.ones((9, 9), np.uint8), iterations=2)

# Save mask for debugging
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_hires.png", mask)

# Now use a smarter inpainting approach:
# 1. Use Navier-Stokes inpainting for the masked area
# 2. Then use bilateral filtering to smooth the result naturally

# First pass: inpaint with large radius
result_crop = cv2.inpaint(face_crop, mask, inpaintRadius=25, flags=cv2.INPAINT_NS)

# Second pass: inpaint remaining artifacts with smaller radius
# Create a tighter mask from the first result
gray_result = cv2.cvtColor(result_crop, cv2.COLOR_BGR2GRAY)
gray_orig = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
diff = cv2.absdiff(gray_orig, gray_result)
_, residual_mask = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)
residual_mask = cv2.dilate(residual_mask, np.ones((5, 5), np.uint8), iterations=1)

result_crop = cv2.inpaint(result_crop, residual_mask, inpaintRadius=10, flags=cv2.INPAINT_TELEA)

# Apply subtle bilateral filter to the inpainted area for natural skin texture
mask_blur = cv2.GaussianBlur(mask.astype(np.float32), (21, 21), 7) / 255.0
mask_blur_3d = mask_blur[:, :, np.newaxis]

# Bilateral filter on the inpainted region
bilateral = cv2.bilateralFilter(result_crop, d=9, sigmaColor=50, sigmaSpace=50)
result_crop = (result_crop * (1 - mask_blur_3d) + bilateral * mask_blur_3d).astype(np.uint8)

# Put the edited face back into the full source image
source_no_glasses = source.copy()
source_no_glasses[y1:y2, x1:x2] = result_crop

cv2.imwrite("/Users/lobster/workspace/lali/source_no_glasses.jpg", source_no_glasses)
cv2.imwrite("/Users/lobster/workspace/lali/face_crop_no_glasses.jpg", result_crop)

print("Saved source_no_glasses.jpg and face_crop_no_glasses.jpg")

# Debug: show mask overlay
overlay = face_crop.copy()
overlay[mask > 0] = [0, 0, 255]
cv2.addWeighted(overlay, 0.4, face_crop, 0.6, 0, overlay)
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_overlay_hires.png", overlay)

print("Done with glasses removal!")
print("\nNow doing face swap with the no-glasses source...")

# Step 2: Face swap using the no-glasses source
swapper = insightface.model_zoo.get_model(
    "/Users/lobster/.insightface/models/inswapper_128.onnx",
    providers=['CPUExecutionProvider']
)

target_path = "/Users/lobster/.openclaw/media/inbound/1f28214d-6617-43a4-945b-7d28b017829a.png"
target_img = cv2.imread(target_path)

# Detect faces in the no-glasses source
source_faces = app.get(source_no_glasses)
target_faces = app.get(target_img)

if len(source_faces) == 0:
    print("No face in source_no_glasses!")
    exit(1)
if len(target_faces) == 0:
    print("No face in target!")
    exit(1)

source_face = sorted(source_faces, key=lambda x: x.bbox[2] * x.bbox[3], reverse=True)[0]
target_face = sorted(target_faces, key=lambda x: x.bbox[2] * x.bbox[3], reverse=True)[0]

result = swapper.get(target_img, target_face, source_face, paste_back=True)

output = "/Users/lobster/workspace/lali/face_swapped_no_glasses_final.png"
cv2.imwrite(output, result)
print(f"Saved {output}")
