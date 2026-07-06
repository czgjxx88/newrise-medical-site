import cv2
import numpy as np

# Work directly on the face swap result
img = cv2.imread("/Users/lobster/workspace/lali/face_swapped.png")
h, w = img.shape[:2]
print(f"Image: {w}x{h}")

# The face is roughly in the upper-middle area of the image
# Let me find the face by looking for the head region
# Convert to grayscale for analysis
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# The face/skin area can be detected by color
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Broader skin detection for Asian skin tones
lower_skin = np.array([0, 15, 80])
upper_skin = np.array([35, 150, 255])
skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)

# Clean up
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel, iterations=2)

# Find contours
contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if contours:
    # Sort by area
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    for i, cnt in enumerate(contours[:3]):
        area = cv2.contourArea(cnt)
        x, y, fw, fh = cv2.boundingRect(cnt)
        aspect = fw / fh if fh > 0 else 0
        print(f"Contour {i}: area={area}, bbox=({x},{y},{fw},{fh}), aspect={aspect:.2f}")
    
    # The face should be roughly square-ish and in the upper portion
    face_cnt = None
    for cnt in contours[:5]:
        x, y, fw, fh = cv2.boundingRect(cnt)
        aspect = fw / fh if fh > 0 else 0
        area = cv2.contourArea(cnt)
        # Face-like: aspect ratio 0.6-1.5, area > 2000
        if 0.5 < aspect < 2.0 and area > 2000 and y < h * 0.6:
            face_cnt = cnt
            break
    
    if face_cnt is None:
        # Fallback: use largest contour in upper half
        for cnt in contours[:3]:
            x, y, fw, fh = cv2.boundingRect(cnt)
            if y < h * 0.6:
                face_cnt = cnt
                break
    
    if face_cnt is not None:
        x, y, fw, fh = cv2.boundingRect(face_cnt)
        print(f"\nSelected face region: ({x},{y},{fw},{fh})")
        
        # Draw face region on debug image
        debug = img.copy()
        cv2.rectangle(debug, (x, y), (x+fw, y+fh), (0, 255, 0), 2)
        cv2.imwrite("/Users/lobster/workspace/lali/face_region_debug.png", debug)
        
        # Glasses are in the upper-middle of the face region
        # roughly y + 0.25*fh to y + 0.45*fh
        glasses_y1 = y + int(fh * 0.25)
        glasses_y2 = y + int(fh * 0.45)
        
        # Create glasses mask
        glasses_mask = np.zeros((h, w), dtype=np.uint8)
        
        # The glasses span roughly the middle 60% of the face width
        glasses_x1 = x + int(fw * 0.2)
        glasses_x2 = x + int(fw * 0.8)
        
        cv2.rectangle(glasses_mask, (glasses_x1, glasses_y1), (glasses_x2, glasses_y2), 255, -1)
        
        # Dilate slightly
        glasses_mask = cv2.dilate(glasses_mask, np.ones((5,5), np.uint8), iterations=2)
        
        # Save mask debug
        cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_v3.png", glasses_mask)
        
        # Sample skin color from the forehead area (above glasses)
        forehead_y1 = max(0, y)
        forehead_y2 = max(glasses_y1 - 10, forehead_y1 + 10)
        forehead_region = img[forehead_y1:forehead_y2, glasses_x1:glasses_x2]
        
        if forehead_region.size > 0:
            skin_color = np.median(forehead_region.reshape(-1, 3), axis=0).astype(np.uint8)
            print(f"Skin color from forehead: {skin_color}")
        else:
            # Fallback: sample from cheek area
            cheek_y1 = glasses_y2 + int(fh * 0.15)
            cheek_y2 = cheek_y1 + int(fh * 0.2)
            cheek_region = img[cheek_y1:cheek_y2, x + int(fw*0.1):x + int(fw*0.4)]
            skin_color = np.median(cheek_region.reshape(-1, 3), axis=0).astype(np.uint8)
            print(f"Skin color from cheek: {skin_color}")
        
        # Create smooth blend mask
        mask_float = glasses_mask.astype(np.float32) / 255.0
        mask_blur = cv2.GaussianBlur(mask_float, (31, 31), 10)
        
        # Replace with skin color
        result = img.copy()
        for c in range(3):
            channel = img[:,:,c].astype(np.float32)
            blended = channel * (1 - mask_blur) + skin_color[c] * mask_blur
            result[:,:,c] = np.clip(blended, 0, 255).astype(np.uint8)
        
        # Add subtle texture
        roi = result[glasses_y1:glasses_y2, glasses_x1:glasses_x2]
        noise = np.random.normal(0, 3, roi.shape).astype(np.float32)
        result[glasses_y1:glasses_y2, glasses_x1:glasses_x2] = np.clip(
            result[glasses_y1:glasses_y2, glasses_x1:glasses_x2].astype(np.float32) + noise, 0, 255
        ).astype(np.uint8)
        
        # Save debug
        cv2.imwrite("/Users/lobster/workspace/lali/face_swapped_no_glasses_v3.png", result)
        print("Saved face_swapped_no_glasses_v3.png")
        
        # Also save a debug image showing the mask overlay
        overlay = img.copy()
        overlay[glasses_mask > 0] = [0, 0, 255]
        cv2.addWeighted(overlay, 0.3, img, 0.7, 0, overlay)
        cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_overlay.png", overlay)
    else:
        print("No face-like contour found!")
else:
    print("No contours found!")
