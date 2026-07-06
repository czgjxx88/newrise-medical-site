import cv2
import numpy as np

# Read the face-swapped result
img = cv2.imread("/Users/lobster/workspace/lali/face_swapped.png")
h, w = img.shape[:2]
print(f"Image: {w}x{h}")

# Let me create a mask by analyzing the face region
# First, let's find the face area by looking for skin-colored regions
# Then identify the glasses by dark rectangular features

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Skin mask (typical skin color range)
lower_skin = np.array([0, 20, 70])
upper_skin = np.array([20, 120, 255])
skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)

# Clean up
skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))
skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))

# Find largest skin region (face)
contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
if contours:
    largest = max(contours, key=cv2.contourArea)
    x, y, fw, fh = cv2.boundingRect(largest)
    print(f"Face region: x={x}, y={y}, w={fw}, h={fh}")
    
    # Glasses are typically in the upper-middle part of the face
    # roughly y+0.3*fh to y+0.55*fh
    glasses_y1 = y + int(fh * 0.30)
    glasses_y2 = y + int(fh * 0.50)
    
    # Create glasses mask - look for dark regions in the glasses band
    glasses_band = img[glasses_y1:glasses_y2, x:x+fw]
    gray_band = cv2.cvtColor(glasses_band, cv2.COLOR_BGR2GRAY)
    
    # Dark threshold for glasses frames
    _, dark_mask = cv2.threshold(gray_band, 60, 255, cv2.THRESH_BINARY_INV)
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8))
    
    # Find horizontal line-like structures (glasses frames)
    # Glasses are typically thin horizontal features
    kernel_h = np.ones((2, 15), np.uint8)
    glasses_h = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel_h)
    
    # Create full mask
    full_mask = np.zeros((h, w), dtype=np.uint8)
    full_mask[glasses_y1:glasses_y2, x:x+fw] = glasses_h
    
    # Dilate slightly
    full_mask = cv2.dilate(full_mask, np.ones((3,3), np.uint8), iterations=2)
    
    # Save mask for debugging
    cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_v2.png", full_mask)
    print(f"Glasses mask area: {cv2.countNonZero(full_mask)} pixels")
    
    # Inpaint
    result = cv2.inpaint(img, full_mask, inpaintRadius=5, flags=cv2.INPAINT_NS)
    
    # Also try with larger radius
    result2 = cv2.inpaint(img, full_mask, inpaintRadius=10, flags=cv2.INPAINT_NS)
    
    output = "/Users/lobster/workspace/lali/face_swapped_no_glasses.png"
    cv2.imwrite(output, result2)
    print(f"Saved to {output}")
else:
    print("No face region found!")
