import cv2
import numpy as np

img = cv2.imread("/Users/lobster/workspace/lali/face_swapped.png")
h, w = img.shape[:2]
print(f"Image: {w}x{h}")

# Let me try to find the face using a different approach
# Convert to grayscale and use edge detection to find facial features
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Use a more targeted approach: find the eyes using eye cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
glasses_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')

faces = face_cascade.detectMultiScale(gray, 1.1, 3)
print(f"Haar faces: {len(faces)}")
for (x,y,wf,hf) in faces:
    print(f"  Face: ({x},{y},{wf},{hf})")
    # Look for eyes/glasses in this face
    roi_gray = gray[y:y+hf, x:x+wf]
    roi_color = img[y:y+hf, x:x+wf]
    
    eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3)
    print(f"  Eyes: {len(eyes)}")
    for (ex,ey,ew,eh) in eyes:
        print(f"    Eye: ({ex},{ey},{ew},{eh})")
    
    glasses = glasses_cascade.detectMultiScale(roi_gray, 1.1, 3)
    print(f"  Glasses detections: {len(glasses)}")
    for (gx,gy,gw,gh) in glasses:
        print(f"    Glasses: ({gx},{gy},{gw},{gh})")

# If Haar doesn't find eyes/glasses well, let's analyze the image structure
# The face should be the most prominent feature

# Let's just print some debug info about the image
# Sample pixel colors at various positions
positions = [
    (400, 50),   # top center - should be hair/background
    (400, 120),  # upper face - forehead
    (400, 140),  # eye level
    (400, 180),  # nose/mouth
    (400, 220),  # chin
    (350, 140),  # left eye area
    (450, 140),  # right eye area
]

for (px, py) in positions:
    if px < w and py < h:
        pixel = img[py, px]
        print(f"  Pixel({px},{py}): BGR={pixel}")

# Let me try a completely different approach: use the face swap's face landmarks
# Since we know insightface detected a face, let's use its landmarks

import insightface
from insightface.app import FaceAnalysis

app = FaceAnalysis(providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0)

faces_insight = app.get(img)
print(f"\nInsightFace detected: {len(faces_insight)} faces")

if len(faces_insight) > 0:
    face = faces_insight[0]
    bbox = face.bbox
    landmarks = face.kps
    print(f"BBox: {bbox}")
    print(f"Landmarks (5 points): {landmarks}")
    
    # The 5 landmarks are: left eye, right eye, nose, left mouth, right mouth
    # Glasses should be around the eye landmarks
    if landmarks is not None and len(landmarks) >= 2:
        left_eye = landmarks[0]  # [x, y]
        right_eye = landmarks[1]  # [x, y]
        print(f"Left eye: ({left_eye[0]:.0f}, {left_eye[1]:.0f})")
        print(f"Right eye: ({right_eye[0]:.0f}, {right_eye[1]:.0f})")
        
        # Glasses area: around eyes, a bit wider
        eye_y = int((left_eye[1] + right_eye[1]) / 2)
        eye_x_center = int((left_eye[0] + right_eye[0]) / 2)
        
        glasses_width = int(abs(right_eye[0] - left_eye[0]) * 1.5)
        glasses_height = int(abs(right_eye[0] - left_eye[0]) * 0.3)
        
        print(f"Glasses center: ({eye_x_center}, {eye_y})")
        print(f"Glasses size: {glasses_width}x{glasses_height}")
        
        # Create precise glasses mask
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # Left lens area
        lx = int(left_eye[0])
        ly = int(left_eye[1])
        cv2.ellipse(mask, (lx, ly), (int(glasses_width*0.35), int(glasses_height*0.7)), 0, 0, 360, 255, -1)
        
        # Right lens area
        rx = int(right_eye[0])
        ry = int(right_eye[1])
        cv2.ellipse(mask, (rx, ry), (int(glasses_width*0.35), int(glasses_height*0.7)), 0, 0, 360, 255, -1)
        
        # Bridge
        cv2.line(mask, (lx + int(glasses_width*0.25), ly), 
                        (rx - int(glasses_width*0.25), ry), 255, 8)
        
        # Arms
        cv2.line(mask, (lx - int(glasses_width*0.45), ly), 
                        (lx - int(glasses_width*0.35), ly), 255, 6)
        cv2.line(mask, (rx + int(glasses_width*0.35), ry), 
                        (rx + int(glasses_width*0.45), ry), 255, 6)
        
        # Dilate
        mask = cv2.dilate(mask, np.ones((5,5), np.uint8), iterations=2)
        
        # Save mask
        cv2.imwrite("/Users/lobster/workspace/lali/glasses_mask_precise.png", mask)
        
        # Sample skin color from cheek
        cheek_y = eye_y + int(glasses_height * 2)
        cheek_x = lx - int(glasses_width * 0.5)
        cheek_region = img[max(0,cheek_y-15):cheek_y+15, max(0,cheek_x-20):cheek_x+20]
        skin_color = np.median(cheek_region.reshape(-1, 3), axis=0).astype(np.uint8)
        print(f"Skin color: {skin_color}")
        
        # Smooth blend
        mask_float = mask.astype(np.float32) / 255.0
        mask_blur = cv2.GaussianBlur(mask_float, (31, 31), 10)
        
        result = img.copy()
        for c in range(3):
            channel = img[:,:,c].astype(np.float32)
            blended = channel * (1 - mask_blur) + skin_color[c] * mask_blur
            result[:,:,c] = np.clip(blended, 0, 255).astype(np.uint8)
        
        cv2.imwrite("/Users/lobster/workspace/lali/face_swapped_no_glasses.png", result)
        print("Saved result!")
        
        # Debug overlay
        overlay = img.copy()
        overlay[mask > 0] = [0, 0, 255]
        cv2.addWeighted(overlay, 0.4, img, 0.6, 0, overlay)
        cv2.imwrite("/Users/lobster/workspace/lali/glasses_debug.png", overlay)
