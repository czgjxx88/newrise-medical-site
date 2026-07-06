import cv2
import numpy as np

img = cv2.imread("/Users/lobster/workspace/lali/face_swapped.png")
h, w = img.shape[:2]

# Based on visual inspection of the 800x400 image:
# Face center: roughly x=400, y=140
# Glasses area:
# - Left lens: x~350-400, y~120-150
# - Right lens: x~410-470, y~118-148
# - Bridge: x~400-410, y~125-145
# - Arms extend to sides

# Create precise glasses mask
mask = np.zeros((h, w), dtype=np.uint8)

# Main glasses area - cover both lenses and bridge
# Left lens region (including dark frames)
pts_left = np.array([
    [340, 115], [405, 112], [408, 155], [340, 152]
], dtype=np.int32)
cv2.fillPoly(mask, [pts_left], 255)

# Right lens region
pts_right = np.array([
    [415, 110], [475, 115], [478, 152], [412, 148]
], dtype=np.int32)
cv2.fillPoly(mask, [pts_right], 255)

# Bridge
cv2.rectangle(mask, (398, 122), (420, 142), 255, -1)

# Left arm
cv2.rectangle(mask, (310, 125), (345, 142), 255, -1)

# Right arm  
cv2.rectangle(mask, (472, 120), (510, 138), 255, -1)

# Dilate to cover frame edges
mask = cv2.dilate(mask, np.ones((5,5), np.uint8), iterations=2)

# Save mask for verification
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_final.png", mask)

# Sample skin color from the cheek area (below glasses, avoiding shadows)
# Left cheek area
cheek_left = img[165:195, 350:390]
skin_left = np.median(cheek_left.reshape(-1, 3), axis=0)
# Right cheek area
cheek_right = img[160:190, 420:460]
skin_right = np.median(cheek_right.reshape(-1, 3), axis=0)

skin_color = ((skin_left + skin_right) / 2).astype(np.uint8)
print(f"Skin color: {skin_color}")

# Create smooth blend mask
mask_float = mask.astype(np.float32) / 255.0
mask_blur = cv2.GaussianBlur(mask_float, (35, 35), 12)

# Create result
result = img.copy()
for c in range(3):
    channel = img[:,:,c].astype(np.float32)
    blended = channel * (1 - mask_blur) + skin_color[c] * mask_blur
    result[:,:,c] = np.clip(blended, 0, 255).astype(np.uint8)

# Save
cv2.imwrite("/Users/lobster/workspace/lali/face_swapped_no_glasses.png", result)
print("Saved!")

# Debug: show mask overlay
overlay = img.copy()
overlay[mask > 0] = [0, 0, 255]
cv2.addWeighted(overlay, 0.4, img, 0.6, 0, overlay)
cv2.imwrite("/Users/lobster/workspace/lali/glasses_overlay_final.png", overlay)
