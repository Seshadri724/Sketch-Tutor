import mediapipe as mp
import numpy as np
from PIL import Image

class LandmarkExtractor:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1, refine_landmarks=True
        )

    def extract(self, pil_img: Image.Image):
        img = np.array(pil_img.convert('RGB'))
        results = self.mp_face_mesh.process(img)
        
        if not results.multi_face_landmarks:
            return None, None, 0.0
            
        landmarks = results.multi_face_landmarks[0].landmark
        
        # Bounding box for occupancy calculation
        x_coords = [lm.x for lm in landmarks]
        y_coords = [lm.y for lm in landmarks]
        occupancy = (max(x_coords) - min(x_coords)) * (max(y_coords) - min(y_coords))
        
        mapping = {
            "crown": landmarks[10], "chin": landmarks[152],
            "face_left": landmarks[234], "face_right": landmarks[454],
            "eye_line": landmarks[168], "nose_base": landmarks[2], "mouth": landmarks[13],
        }
        
        pts = {k: [v.x, v.y] for k, v in mapping.items()}
        return pts, occupancy, 0.95