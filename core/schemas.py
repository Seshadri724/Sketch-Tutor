from pydantic import BaseModel, Field
from typing import List, Optional

class CorrectionCard(BaseModel):
    feature_id: str = Field(..., description="The ID of the feature (e.g., 'eye_line_vertical' or 'beak_length')")
    headline: str = Field(..., description="Short actionable headline (e.g., 'Lower the eyes')")
    explanation: str = Field(..., description="1-2 sentences explaining the proportional drift")
    next_step_drill: str = Field(..., description="One concrete physical pencil action for the next attempt")
    severity: str = Field(..., description="One of: 'critical', 'minor', 'on_target'")

class CompositionFeedback(BaseModel):
    reasoning_process: str = Field(
        ..., 
        description="MANDATORY STEP-BY-STEP LOGIC: 1. Describe reference zoom/scale. 2. Describe learner zoom/scale. 3. Compare and conclude match/mismatch."
    )
    detected_category: str = Field(..., description="The subject category (e.g., 'Faces', 'Animals', 'Architecture')")
    is_category_match: bool = Field(..., description="True if ref and learner match in both category AND framing scale")
    is_valid_subject: bool = Field(..., description="True if the learner image is actually a drawing of the subject")
    global_balance_score: float = Field(..., description="Score (0-100) for overall centering and scale on page")
    composition_notes: str = Field(..., description="Feedback on overall size and placement")

class SketchCoachFeedback(BaseModel):
    composition: CompositionFeedback = Field(..., description="The results of the first-pass global and category check")
    overall_accuracy_score: Optional[float] = Field(
        None, 
        description="Score 0-100. Must be null if is_category_match is False"
    )
    encouraging_summary: str = Field(..., description="Supportive summary. If mismatch, explain why analysis stopped.")
    top_priority_corrections: List[CorrectionCard] = Field(default=[])
    uncertainty_notice: Optional[str] = Field(None)