import cv2
import numpy as np

# Read the source image
source = cv2.imread("/Users/lobster/.openclaw/media/inbound/ed7dbd50-654f-4aaa-b755-f997b2f2c5f3.jpg")
h, w = source.shape[:2]
print(f"Source: {w}x{h}")

# Work on a smaller region - focus on the face area (left person in the photo)
# The person is on the left side, roughly x: 1400-3400, y: 800-3200
# Let's use a mask-based inpainting approach

# Create a mask for the glasses area on the left person's face
mask = np.zeros((h, w), dtype=np.uint8)

# Glasses area - left person (approximate coordinates based on 6570x4380 image)
# The glasses are around the eye region of the person on the left
# Based on the image, the face center is roughly at x=2400, y=2000
# Glasses span approximately:
cv2.ellipse(mask, (2400, 2000), (600, 200), 0, 0, 360, 255, -1)

# Also cover the right lens area
cv2.ellipse(mask, (3100, 2000), (600, 200), 0, 0, 360, 255, -1)

# Bridge of glasses
cv2.rectangle(mask, (2900, 1900), (3200, 2100), 255, -1)

# Glasses arms going to ears
cv2.rectangle(mask, (1600, 1950), (2000, 2050), 255, -1)
cv2.rectangle(mask, (3700, 1950), (4000, 2050), 255, -1)

# Inpaint
result = cv2.inpaint(source, mask, inpaintRadius=15, flags=cv2.INPAINT_TELEA)

# Save
output = "/Users/lobster/workspace/lali/source_no_glasses.jpg"
cv2.imwrite(output, result)
print(f"Saved to {output}")

# Also save the mask for debugging
cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask.png", mask)
