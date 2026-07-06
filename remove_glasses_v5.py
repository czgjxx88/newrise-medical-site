import cv2
import numpy as np

# The source photo has 3 men. The person with glasses is the SECOND person from left.
# From visual analysis of the 6570x4380 image:
# Person with glasses face region: approximately x=3600-4400, y=1400-2700

source = cv2.imread("/Users/lobster/.openclaw/media/inbound/ed7dbd50-654f-4aaa-b755-f997b2f2c5f3.jpg")
h, w = source.shape[:2]
print(f"Source: {w}x{h}")

# Manually define face region for the person with glasses
face_x1, face_y1 = 3500, 1350
face_x2, face_y2 = 4500, 2750

face_crop = source[face_y1:face_y2, face_x1:face_x2].copy()
crop_h, crop_w = face_crop.shape[:2]
print(f"Crop: {crop_w}x{crop_h}")

# Glasses position in the cropped image:
# Based on visual inspection: glasses are roughly at y=25-40% of face height
# Glasses span about 60% of face width, centered

glasses_y_center = int(crop_h * 0.35)
glasses_half_h = int(crop_h * 0.06)
glasses_center_x = int(crop_w * 0.5)
glasses_half_w = int(crop_w * 0.30)

print(f"Glasses center: ({glasses_center_x}, {glasses_y_center})")
print(f"Glasses size: {glasses_half_w*2}x{glasses_half_h*2}")

# Create precise glasses mask
mask = np.zeros((crop_h, crop_w), dtype=np.uint8)

# Left lens area
cv2.ellipse(mask, 
    (glasses_center_x - int(glasses_half_w * 0.55), glasses_y_center),
    (int(glasses_half_w * 0.5), glasses_half_h + 10), 0, 0, 360, 255, -1)

# Right lens area
cv2.ellipse(mask,
    (glasses_center_x + int(glasses_half_w * 0.55), glasses_y_center),
    (int(glasses_half_w * 0.5), glasses_half_h + 10), 0, 0, 360, 255, -1)

# Bridge
cv2.rectangle(mask,
    (glasses_center_x - int(glasses_half_w * 0.15), glasses_y_center - 8),
    (glasses_center_x + int(glasses_half_w * 0.15), glasses_y_center + 8),
    255, -1)

# Left arm
cv2.rectangle(mask,
    (glasses_center_x - glasses_half_w - 30, glasses_y_center - 8),
    (glasses_center_x - int(glasses_half_w * 0.8), glasses_y_center + 8),
    255, -1)

# Right arm
cv2.rectangle(mask,
    (glasses_center_x + int(glasses_half_w * 0.8), glasses_y_center - 8),
    (glasses_center_x + glasses_half_w + 30, glasses_y_center + 8),
    255, -1)

# Dilate
mask = cv2.dilate(mask, np.ones((7, 7), np.uint8), iterations=2)

cv2.imwrite("/Users/lobster/workspace/lali/face_crop_original.jpg", face_crop)
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_crop_v2.png", mask)

# Debug overlay
overlay = face_crop.copy()
overlay[mask > 0] = [0, 0, 255]
cv2.addWeighted(overlay, 0.5, face_crop, 0.5, 0, overlay)
cv2.imwrite("/Users/lobster/workspace/lali/glasses_overlay_crop_v2.png", overlay)

print("Saved debug images. Check them before proceeding.")

# Now inpaint
result = cv2.inpaint(face_crop, mask, inpaintRadius=30, flags=cv2.INPAINT_NS)
result2 = cv2.inpaint(result, mask, inpaintRadius=15, flags=cv2.INPAINT_TELEA)

cv2.imwrite("/Users/lobster/workspace/lali/face_crop_no_glasses.jpg", result2)

# Put back
source_no_glasses = source.copy()
source_no_glasses[face_y1:face_y2, face_x1:face_x2] = result2
cv2.imwrite("/Users/lobster/workspace/lali/source_no_glasses.jpg", source_no_glasses)

print("Saved inpainted versions!")
