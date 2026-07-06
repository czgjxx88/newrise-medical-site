import cv2
import numpy as np

# Read the face-swapped result (800x400)
img = cv2.imread("/Users/lobster/workspace/lali/face_swapped.png")
h, w = img.shape[:2]
print(f"Image: {w}x{h}")

# Create mask for glasses area
# The person's face is roughly centered-left in the image
# Glasses are around the eyes - based on the swapped result
mask = np.zeros((h, w), dtype=np.uint8)

# Approximate glasses position on the face in the swapped image
# Left lens area
cv2.ellipse(mask, (370, 140), (45, 18), -5, 0, 360, 255, -1)
# Right lens area  
cv2.ellipse(mask, (440, 138), (45, 18), 5, 0, 360, 255, -1)
# Bridge
cv2.rectangle(mask, (400, 130), (420, 148), 255, -1)
# Left arm
cv2.rectangle(mask, (310, 135), (340, 150), 255, -1)
# Right arm
cv2.rectangle(mask, (480, 132), (510, 148), 255, -1)

# Dilate mask slightly to cover edges
mask = cv2.dilate(mask, np.ones((5,5), np.uint8), iterations=2)

# Save mask for debugging
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_result.png", mask)

# Inpaint using both methods and blend
result_telea = cv2.inpaint(img, mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)
result_ns = cv2.inpaint(img, mask, inpaintRadius=7, flags=cv2.INPAINT_NS)

# Use NAVIER-STOKES for more natural texture
result = result_ns

# Save
output = "/Users/lobster/workspace/lali/face_swapped_no_glasses.png"
cv2.imwrite(output, result)
print(f"Saved to {output}")
