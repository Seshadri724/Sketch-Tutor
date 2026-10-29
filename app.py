import streamlit as st
from PIL import Image
import os
from dotenv import load_dotenv

# Import custom services
from services.image_gatekeeper import check_image_quality, enhance_sketch
from services.landmark_extractor import LandmarkExtractor
from services.proportion_math import compute_proportion_deltas
from services.visual_compositor import render_annotated_overlay
from services.gemma_coach import generate_gemma_coaching

# Load API Key from .env
load_dotenv()

# --- PAGE CONFIG ---
st.set_page_config(page_title="SketchCoach — Gemma 4 Drawing Tutor", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if "init" not in st.session_state:
    st.session_state.update({
        "init": True,
        "attempt_number": 1,
        "ref_landmarks": None,          
        "sketch_landmarks": None,       
        "measured_payload": None,       
        "annotated_sketch_img": None,   
        "gemma_feedback": None,         
    })

# Initialize the MediaPipe Extractor
extractor = LandmarkExtractor()

# --- UI HEADER ---
st.title("🎨 SketchCoach: Gemma 4 Drawing Tutor")
st.markdown("Upload a reference photo and your sketch. The AI will check for category and scale match before providing detailed coaching.")

# --- TOP CONTROL BAR ---
mode = st.segmented_control(
    "Subject Mode", 
    ["Portrait - Front", "Portrait - 3/4", "Still Life", "General Anime"], 
    default="Portrait - Front"
)

col_up1, col_up2 = st.columns(2, gap="large")
with col_up1:
    uploaded_ref = st.file_uploader("1. Upload Reference Image", type=['jpg', 'png', 'jpeg'])
with col_up2:
    uploaded_sketch = st.file_uploader("2. Upload Your Sketch", type=['jpg', 'png', 'jpeg'])

# --- MAIN LOGIC ---
if uploaded_ref and uploaded_sketch:
    # Load images
    ref_img = Image.open(uploaded_ref)
    sketch_raw = Image.open(uploaded_sketch)
    
    # 1. Image Quality Check & Enhancement
    quality = check_image_quality(sketch_raw)
    if quality["warning_flag"]:
        st.warning(f"⚠️ {quality['message']}. The AI might struggle to detect lines; please use manual sliders if needed.")
    
    sketch_enhanced = enhance_sketch(sketch_raw)

    # 2. Landmark Extraction with UPDATED UNPACKING (3 values)
    if st.session_state.ref_landmarks is None:
        # We now receive: pts, occupancy, confidence
        ref_pts, ref_occ, _ = extractor.extract(ref_img)
        sketch_pts, sketch_occ, _ = extractor.extract(sketch_enhanced)

        default_face = {
            "crown": [0.5, 0.2], "chin": [0.5, 0.8], "face_left": [0.3, 0.5], 
            "face_right": [0.7, 0.5], "eye_line": [0.5, 0.4], "nose_base": [0.5, 0.6], "mouth": [0.5, 0.7]
        }
        
        st.session_state.ref_landmarks = ref_pts if ref_pts is not None else default_face
        st.session_state.sketch_landmarks = sketch_pts if sketch_pts is not None else default_face

    # 3. Interactive Workspace Fragment
    @st.fragment
    def render_workspace():
        col_ref, col_sketch = st.columns(2, gap="medium")
        
        with col_ref:
            st.subheader("Reference")
            st.image(ref_img, use_container_width=True)
            st.caption("Target proportions are derived from this image.")

        with col_sketch:
            st.subheader("Analysis & Adjustment")
            
            t1, t2 = st.columns(2)
            show_target = t1.checkbox("Show Green Target Guides", value=True)
            show_drift = t2.checkbox("Show Red Measured Drift", value=True)
            
            with st.expander("🛠️ Fine-Tune Detected Landmarks"):
                st.info("Drag these to align the guides with your actual drawing.")
                pts = st.session_state.sketch_landmarks
                
                pts["crown"][1] = st.slider("Crown Top (Y)", 0.0, 1.0, float(pts["crown"][1]), 0.005)
                pts["eye_line"][1] = st.slider("Eye Line (Y)", 0.0, 1.0, float(pts["eye_line"][1]), 0.005)
                pts["nose_base"][1] = st.slider("Nose Base (Y)", 0.0, 1.0, float(pts["nose_base"][1]), 0.005)
                pts["mouth"][1] = st.slider("Mouth Center (Y)", 0.0, 1.0, float(pts["mouth"][1]), 0.005)
                pts["chin"][1] = st.slider("Chin Bottom (Y)", 0.0, 1.0, float(pts["chin"][1]), 0.005)

            st.session_state.measured_payload = compute_proportion_deltas(
                st.session_state.ref_landmarks, 
                st.session_state.sketch_landmarks
            )
            
            annotated = render_annotated_overlay(
                sketch_raw, 
                st.session_state.sketch_landmarks, 
                st.session_state.measured_payload, 
                show_target, 
                show_drift
            )
            st.session_state.annotated_sketch_img = annotated
            st.image(annotated, use_container_width=True)

    render_workspace()

    # 4. Gemma 4 Coaching Trigger
    st.divider()
    if st.button("Ask Gemma 4 Coach for Feedback", type="primary", use_container_width=True):
        with st.spinner("Gemma 4 is performing Identity and Scale audit..."):
            try:
                context = {
                    "mode": mode, 
                    "attempt": st.session_state.attempt_number, 
                    "confidence": 0.95, 
                    "quality": quality
                }
                
                feedback = generate_gemma_coaching(
                    os.getenv("GEMINI_API_KEY"), 
                    ref_img, 
                    st.session_state.annotated_sketch_img, 
                    st.session_state.measured_payload, 
                    context
                )
                st.session_state.gemma_feedback = feedback
            except Exception as e:
                st.error(f"API Error: {e}")

    # 5. Updated Coaching Results Display (Handles Gatekeeper/Mismatches)
    if st.session_state.gemma_feedback:
        fb = st.session_state.gemma_feedback
        
        # CHECK: Did the Gatekeeper fail?
        if not fb.composition.is_category_match:
            # Show a warning box instead of a score if categories or scales don't match
            st.warning(f"### ⚠️ Subject Mismatch Detected")
            st.markdown(f"**Coach's Note:** {fb.encouraging_summary}")
            st.info(f"**Reason:** {fb.composition.composition_notes}")
        else:
            # Everything passed! Show the success bar and score
            st.success(f"### Analysis Complete! Overall Score: {fb.overall_accuracy_score}/100")
            st.markdown(f"**Coach's Note:** {fb.encouraging_summary}")
            
            if fb.uncertainty_notice:
                st.caption(f"📝 {fb.uncertainty_notice}")

            st.markdown("#### 🎯 Priority Corrections")
            if not fb.top_priority_corrections:
                st.markdown("Everything is on target! Keep refining your details.")
            else:
                cols = st.columns(min(len(fb.top_priority_corrections), 3))
                for i, card in enumerate(fb.top_priority_corrections):
                    with cols[i]:
                        border_color = "red" if card.severity == "critical" else "orange" if card.severity == "minor" else "green"
                        st.container(border=True).markdown(
                            f"**{card.headline}**\n\n{card.explanation}\n\n**Next Step:**\n{card.next_step_drill}"
                        )

else:
    st.info("Please upload both a reference image and your sketch to begin the analysis.")
    st.markdown("""
    **How to use SketchCoach:**
    1. Upload a professional reference.
    2. Upload your sketch.
    3. Adjust sliders if markers aren't aligned.
    4. Click **Ask Gemma 4 Coach** for an audited critique.
    """)