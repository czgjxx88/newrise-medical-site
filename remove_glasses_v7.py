import cv2
import numpy as np

# Use the already-cropped face image
face_crop = cv2.imread("/Users/lobster/workspace/lali/face_crop_guy.jpg")
crop_h, crop_w = face_crop.shape[:2]
print(f"Crop: {crop_w}x{crop_h}")

# From visual inspection of the cropped image:
# The glasses are clearly visible
# - Frame spans roughly x: 200-420
# - Glasses height: y: 480-570
# - Left lens: x ~200-300
# - Right lens: x ~320-420
# - Bridge: x ~300-320
# - Arms extend to sides

mask = np.zeros((crop_h, crop_w), dtype=np.uint8)

# Glasses frame - use a precise polygon based on visual inspection
# Top of glasses frame
top_y = 485
# Bottom of glasses frame  
bottom_y = 570
# Left edge of left lens
left_x = 195
# Right edge of right lens
right_x = 425
# Left lens / right lens divider (bridge area)
bridge_left = 290
bridge_right = 330
# Left arm
left_arm_x = 150
# Right arm
right_arm_x = 460

# Left lens area (rectangular with rounded corners)
pts_left = np.array([
    [left_x + 10, top_y], [bridge_left, top_y - 5],
    [bridge_left, bottom_y], [left_x, bottom_y - 5],
    [left_x - 5, top_y + 10]
], dtype=np.int32)
cv2.fillPoly(mask, [pts_left], 255)

# Right lens area
pts_right = np.array([
    [bridge_right, top_y - 5], [right_x - 10, top_y],
    [right_x + 5, top_y + 10], [right_x, bottom_y - 5],
    [bridge_right, bottom_y]
], dtype=np.int32)
cv2.fillPoly(mask, [pts_right], 255)

# Bridge
cv2.rectangle(mask, (bridge_left, top_y + 5), (bridge_right, bottom_y - 5), 255, -1)

# Left arm
pts_larm = np.array([
    [left_arm_x, top_y + 20], [left_x, top_y + 5],
    [left_x, bottom_y - 15], [left_arm_x, bottom_y - 5]
], dtype=np.int32)
cv2.fillPoly(mask, [pts_larm], 255)

# Right arm
pts_rarm = np.array([
    [right_x, top_y + 5], [right_arm_x, top_y + 20],
    [right_arm_x, bottom_y - 5], [right_x, bottom_y - 15]
], dtype=np.int32)
cv2.fillPoly(mask, [pts_rarm], 255)

# Dilate to cover frame edges
mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)

# Save debug
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_manual.png", mask)

overlay = face_crop.copy()
overlay[mask > 0] = [0, 0, 255]
cv2.addWeighted(overlay, 0.5, face_crop, 0.5, 0, overlay)
cv2.imwrite("/Users/lobster/workspace/lali/glasses_overlay_manual.png", overlay)

print("Saved debug images. Checking mask position...")

# Sample skin color from the forehead and cheeks for inpainting reference
forehead = face_crop[400:470, 250:380]
cheek_l = face_crop[600:680, 200:280]
cheek_r = face_crop[590:670, 340:420]

skin_colors = []
for name, region in [("forehead", forehead), ("cheek_l", cheek_l), ("cheek_r", cheek_r)]:
    if region.size > 0:
        color = np.median(region.reshape(-1, 3), axis=0)
        print(f"  {name} skin color: {color.astype(np.uint8)}")
        skin_colors.append(color)

if skin_colors:
    skin_color = np.mean(skin_colors, axis=0).astype(np.uint8)
    print(f"Average skin color: {skin_color}")
else:
    skin_color = np.array([180, 160, 140], dtype=np.uint8)

# Multi-pass inpainting
# Pass 1: Large radius Navier-Stokes
result = cv2.inpaint(face_crop, mask, inpaintRadius=20, flags=cv2.INPAINT_NS)

# Pass 2: Medium radius Telea for refinement
# Create residual mask from diff
gray_diff = cv2.absdiff(cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY), 
                         cv2.cvtColor(result, cv2.COLOR_BGR2GRAY))
_, residual = cv2.threshold(gray_diff, 10, 255, cv2.THRESH_BINARY)
residual = cv2.dilate(residual, np.ones((3, 3), np.uint8), iterations=1)
result = cv2.inpaint(result, residual, inpaintRadius=10, flags=cv2.INPAINT_TELEA)

# Pass 3: Smooth the inpainted region with bilateral filter
mask_smooth = cv2.GaussianBlur(mask.astype(np.float32), (15, 15), 5) / 255.0
mask_smooth_3d = mask_smooth[:, :, np.newaxis]

bilateral = cv2.bilateralFilter(result, d=11, sigmaColor=75, sigmaSpace=75)
result = (result * (1 - mask_smooth_3d) + bilateral * mask_smooth_3d).astype(np.uint8)

# Save the no-glasses face crop
cv2.imwrite("/Users/lobster/workspace/lali/face_crop_no_glasses.jpg", result)

print("Saved face_crop_no_glasses.jpg")

# Compare side by side
comparison = np.hstack([face_crop, result])
cv2.imwrite("/Users/lobster/workspace/lali/glasses_comparison.jpg", comparison)
print("Saved glasses_comparison.jpg (left=original, right=no glasses)")
