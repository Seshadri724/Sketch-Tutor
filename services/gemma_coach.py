import sys
import os

# This adds the project root folder to the Python path
# It looks for the folder containing 'services' and 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from google import genai
from core.prompts import COACH_SYSTEM_PROMPT, COACH_USER_PROMPT_TEMPLATE
from core.schemas import SketchCoachFeedback
from services.landmark_extractor import LandmarkExtractor

def generate_gemma_coaching(api_key, ref_img, annotated_img, payload, context):
    # --- 1. DETERMINISTIC SCALE GUARD ---
    extractor = LandmarkExtractor()
    ref_pts, ref_occ, _ = extractor.extract(ref_img)
    sketch_pts, sketch_occ, _ = extractor.extract(annotated_img)

    # If both are faces, compare their "occupancy" (how much they fill the image)
    if ref_occ and sketch_occ:
        if abs(ref_occ - sketch_occ) > 0.30: # 30% difference threshold
            # We can still call Gemma, but we will flag it as a scale mismatch 
            # or we can return a hard error here. Let's call Gemma but tell it there's a mismatch.
            scale_warning = "DETECTION: Scale mismatch detected. Ref Area: {:.2f}, Sketch Area: {:.2f}".format(ref_occ, sketch_occ)
        else:
            scale_warning = "DETECTION: Scale match."
    else:
        scale_warning = "DETECTION: One or more faces not found."

    client = genai.Client(api_key=api_key)
    
    user_prompt = COACH_USER_PROMPT_TEMPLATE \
        .replace("{{subject_mode}}", str(context.get('mode', 'Unknown'))) \
        .replace("{{attempt_number}}", str(context.get('attempt', 1))) \
        .replace("{{alignment_confidence}}", str(context.get('confidence', 0.0))) \
        .replace("{{measured_proportions_json}}", json.dumps(payload)) \
        .replace("{{previous_attempt_delta_json}}", json.dumps(context.get('prev_delta', {}))) \
        .replace("{{image_quality_json}}", json.dumps(context.get('quality', {})))

    # Append the scale warning to the user prompt so the AI knows the math results
    user_prompt += f"\n\nScale Guard Note: {scale_warning}"

    response = client.models.generate_content(
        model="gemma-4-26b-a4b-it",
        config={
            "system_instruction": COACH_SYSTEM_PROMPT,
            "response_mime_type": "application/json", 
            "response_schema": SketchCoachFeedback
        },
        contents=[user_prompt, ref_img, annotated_img]
    )
    
    return response.parsed