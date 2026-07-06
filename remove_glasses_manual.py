import cv2
import numpy as np

# Read the source image
source = cv2.imread("/Users/lobster/.openclaw/media/inbound/ed7dbd50-654f-4aaa-b755-f997b2f2c5f3.jpg")
h, w = source.shape[:2]
print(f"Source: {w}x{h}")

# Resize to a manageable size for face detection
scale = 0.15
small = cv2.resize(source, (int(w*scale), int(h*scale)))
sh, sw = small.shape[:2]

# Use a pre-trained face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Try different scales
faces = face_cascade.detectMultiScale(small, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
print(f"Haar detected {len(faces)} faces at scale {scale}")

for (fx, fy, fw, fh) in faces:
    sx, sy, ex, ey = int(fx/scale), int(fy/scale), int((fx+fw)/scale), int((fy+fh)/scale)
    print(f"  Face at ({sx},{sy})-({ex},{ey}), center=({(sx+ex)/2:.0f},{(sy+ey)/2:.0f})")

# Also try on a larger version
scale2 = 0.3
small2 = cv2.resize(source, (int(w*scale2), int(h*scale2)))
faces2 = face_cascade.detectMultiScale(small2, scaleFactor=1.05, minNeighbors=3, minSize=(20, 20))
print(f"Haar detected {len(faces2)} faces at scale {scale2}")

for (fx, fy, fw, fh) in faces2:
    sx, sy, ex, ey = int(fx/scale2), int(fy/scale2), int((fx+fw)/scale2), int((fy+fh)/scale2)
    print(f"  Face at ({sx},{sy})-({ex},{ey})")

# If Haar didn't work well, use manual coordinates based on the image
# The photo has 3 men, glasses on middle person
# From visual inspection: middle person's face is roughly at:
# x: 3600-4400, y: 1500-2800 (on the 6570x4380 image)

# Let's manually define the face region for the middle person with glasses
# Based on the original photo
face_x1 = 3650
face_y1 = 1400
face_x2 = 4450
face_y2 = 2700

# Crop the face region
face_crop = source[face_y1:face_y2, face_x1:face_x2].copy()
crop_h, crop_w = face_crop.shape[:2]
print(f"\nManual crop: {crop_w}x{crop_h}")

# Create glasses mask
# In the cropped image:
# Face center is roughly at center of crop
fcx = crop_w // 2
fcy = crop_h // 2

# Glasses are in the upper portion, around y=30-45% of face height
glasses_y = int(crop_h * 0.35)
glasses_half_h = int(crop_h * 0.06)
lens_half_w = int(crop_w * 0.15)
bridge_w = int(crop_w * 0.05)
arm_w = int(crop_w * 0.12)

mask = np.zeros((crop_h, crop_w), dtype=np.uint8)

# Left lens - slightly rectangular
cv2.rectangle(mask, 
    (fcx - lens_half_w - bridge_w, glasses_y - glasses_half_h),
    (fcx - bridge_w, glasses_y + glasses_half_h),
    255, -1)
cv2.ellipse(mask, (fcx - lens_half_w//2 - bridge_w, glasses_y), 
    (lens_half_w, glasses_half_h + 5), 0, 0, 360, 255, 5)

# Right lens
cv2.rectangle(mask, 
    (fcx + bridge_w, glasses_y - glasses_half_h),
    (fcx + lens_half_w + bridge_w, glasses_y + glasses_half_h),
    255, -1)
cv2.ellipse(mask, (fcx + lens_half_w//2 + bridge_w, glasses_y), 
    (lens_half_w, glasses_half_h + 5), 0, 0, 360, 255, 5)

# Bridge
cv2.rectangle(mask, 
    (fcx - bridge_w, glasses_y - 3),
    (fcx + bridge_w, glasses_y + 3),
    255, -1)

# Left arm
cv2.rectangle(mask, 
    (fcx - lens_half_w - bridge_w - arm_w, glasses_y - glasses_half_h//2),
    (fcx - lens_half_w - bridge_w, glasses_y + glasses_half_h//2),
    255, -1)

# Right arm
cv2.rectangle(mask, 
    (fcx + lens_half_w + bridge_w, glasses_y - glasses_half_h//2),
    (fcx + lens_half_w + bridge_w + arm_w, glasses_y + glasses_half_h//2),
    255, -1)

# Dilate
mask = cv2.dilate(mask, np.ones((5,5), np.uint8), iterations=3)

# Save crop and mask for debugging
cv2.imwrite("/Users/lobster/workspace/lali/face_crop_check.jpg", face_crop)
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_check.png", mask)

# Blend the mask area with surrounding skin color
# Sample skin color from cheeks area
cheek_sample = face_crop[int(crop_h*0.55):int(crop_h*0.7), int(crop_w*0.1):int(crop_w*0.3)]
skin_color = np.median(cheek_sample.reshape(-1, 3), axis=0).astype(np.uint8)
print(f"Sampled skin color: {skin_color}")

# Create a smooth transition mask
mask_float = mask.astype(np.float32) / 255.0
mask_blur = cv2.GaussianBlur(mask_float, (21, 21), 7)

# Replace glasses area with skin color + some texture
result = face_crop.copy()
# Use color transfer: replace glasses region with average skin color
for c in range(3):
    channel = face_crop[:,:,c].astype(np.float32)
    blended = channel * (1 - mask_blur) + skin_color[c] * mask_blur
    result[:,:,c] = np.clip(blended, 0, 255).astype(np.uint8)

# Add some noise for texture
noise = np.random.normal(0, 5, result.shape).astype(np.float32)
result = np.clip(result.astype(np.float32) + noise, 0, 255).astype(np.uint8)

# Save edited crop
cv2.imwrite("/Users/lobster/workspace/lali/face_crop_no_glasses.jpg", result)

# Put back into source
source_no_glasses = source.copy()
source_no_glasses[face_y1:face_y2, face_x1:face_x2] = result
cv2.imwrite("/Users/lobster/workspace/lali/source_no_glasses.jpg", source_no_glasses)

print("Done! Saved files:")
print("  - face_crop_check.jpg (original crop)")
print("  - glasses_mask_check.png (mask)")
print("  - face_crop_no_glasses.jpg (edited crop)")
print("  - source_no_glasses.jpg (full image with glasses removed)")
