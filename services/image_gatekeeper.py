import cv2
import numpy as np
from PIL import Image

def check_image_quality(pil_img: Image.Image):
    open_cv_image = np.array(pil_img.convert('RGB'))
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    brightness = np.mean(gray)
    
    # FORCE these to standard Python bools using bool()
    is_blurry = bool(variance < 80)
    is_dark = bool(brightness < 40)
    
    return {
        "warning_flag": is_blurry or is_dark, 
        "blur_score": float(variance), # Force to python float
        "brightness": float(brightness), # Force to python float
        "message": "Image too blurry" if is_blurry else "Image too dark" if is_dark else "Clear"
    }

def enhance_sketch(pil_img: Image.Image):
    img = np.array(pil_img.convert('RGB'))
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl,a,b))
    final = cv2.cvtColor(limg, cv2.COLOR_LAB2RGB)
    return Image.fromarray(final)