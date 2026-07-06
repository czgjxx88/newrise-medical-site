import cv2
import numpy as np

img = cv2.imread("/Users/lobster/workspace/lali/face_swapped.png")
h, w = img.shape[:2]
print(f"Image: {w}x{h}")

# From pixel analysis and visual inspection of the 800x400 image:
# The face is centered around x=400, y=140
# Glasses frames at:
#   Left lens: ~x:350-410, y:118-148
#   Right lens: ~x:415-475, y:115-145
#   Bridge: ~x:405-420, y:125-140
#   Left arm: ~x:320-355
#   Right arm: ~x:470-505

# Create mask
mask = np.zeros((h, w), dtype=np.uint8)

# Left lens - irregular shape for glasses frame
pts_left = np.array([
    [348, 116], [360, 113], [380, 112], [400, 114], [410, 118],
    [412, 130], [410, 142], [405, 150], [390, 152],
    [370, 150], [355, 148], [348, 142]
], dtype=np.int32)
cv2.fillPoly(mask, [pts_left], 255)

# Right lens
pts_right = np.array([
    [418, 113], [435, 110], [455, 112], [472, 116], [478, 122],
    [480, 135], [478, 145], [470, 150], [450, 148],
    [430, 146], [420, 142], [416, 132]
], dtype=np.int32)
cv2.fillPoly(mask, [pts_right], 255)

# Bridge between lenses
cv2.rectangle(mask, (408, 122), (422, 138), 255, -1)

# Left arm
pts_larm = np.array([
    [320, 125], [350, 118], [352, 140], [320, 140]
], dtype=np.int32)
cv2.fillPoly(mask, [pts_larm], 255)

# Right arm
pts_rarm = np.array([
    [478, 118], [508, 122], [505, 140], [480, 138]
], dtype=np.int32)
cv2.fillPoly(mask, [pts_rarm], 255)

# Dilate slightly
mask = cv2.dilate(mask, np.ones((5,5), np.uint8), iterations=2)

# Save mask
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_v4.png", mask)

# Sample skin color from forehead (above glasses) and cheeks
forehead = img[85:110, 370:430]
cheek_l = img[160:190, 350:390]
cheek_r = img[155:185, 420:460]

skin_colors = []
for region in [forehead, cheek_l, cheek_r]:
    if region.size > 0:
        skin_colors.append(np.median(region.reshape(-1, 3), axis=0))

if skin_colors:
    skin_color = np.mean(skin_colors, axis=0).astype(np.uint8)
    print(f"Skin color: {skin_color}")
else:
    skin_color = np.array([200, 200, 195], dtype=np.uint8)

# Smooth blend mask
mask_float = mask.astype(np.float32) / 255.0
mask_blur = cv2.GaussianBlur(mask_float, (35, 35), 12)

# Replace glasses with skin color
result = img.copy()
for c in range(3):
    channel = img[:,:,c].astype(np.float32)
    blended = channel * (1 - mask_blur) + skin_color[c] * mask_blur
    result[:,:,c] = np.clip(blended, 0, 255).astype(np.uint8)

# Add subtle noise for texture in the blended area
np.random.seed(42)
noise = np.random.normal(0, 4, result.shape).astype(np.float32) * mask_blur[:,:,np.newaxis]
result = np.clip(result.astype(np.float32) + noise, 0, 255).astype(np.uint8)

cv2.imwrite("/Users/lobster/workspace/lali/face_swapped_no_glasses.png", result)
print("Saved result!")

# Debug overlay
overlay = img.copy()
overlay[mask > 0] = [0, 0, 255]
cv2.addWeighted(overlay, 0.4, img, 0.6, 0, overlay)
cv2.imwrite("/Users/lobster/workspace/lali/glasses_debug_v4.png", overlay)
