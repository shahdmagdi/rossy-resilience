from datetime import datetime
from app import db
from models import User, UserRole, Patient, Doctor
from models.patient import Patient
from flask_jwt_extended import get_jwt_identity
from models.detection_scan import DetectionScan

 
 
# ══════════════════════════════════════════════════════════
#  TOGGLE MENTAL HEALTH MODE
#  Patient toggles their mental health mode on/off.
#  Affects how scan results are displayed going forward.
#  Does NOT retroactively change already saved scans
#  (each scan snapshots mental_health_mode at upload time).
# ══════════════════════════════════════════════════════════
 
def toggle_mental_health_mode():
    """
    Flips the patient's mental_health_mode boolean.
 
    When ON:
        - Scan results show recommendation only
        - Raw prediction/confidence hidden from patient
        - Doctor still sees full results
 
    When OFF:
        - Patient sees full diagnosis results
 
    Returns: (response_dict, http_status_code)
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)
 
    if user.role != UserRole.patient:
        return {"success": False, "message": "Access denied. Patients only."}, 403
 
    patient = Patient.query.get(user_id)
    if not patient:
        return {"success": False, "message": "Patient profile not found."}, 404
 
    try:
        # Flip the mode
        patient.mental_health_mode = not patient.mental_health_mode
        db.session.commit()
 
        status_text = "enabled" if patient.mental_health_mode else "disabled"
 
        return {
            "success":            True,
            "message":            f"Mental health mode {status_text}.",
            "mental_health_mode": patient.mental_health_mode,
        }, 200
 
    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500
 
 
# ══════════════════════════════════════════════════════════
#  GET MENTAL HEALTH MODE STATUS
# ══════════════════════════════════════════════════════════
 
def get_mental_health_mode():
    """Returns the current mental health mode status."""
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)
 
    if user.role != UserRole.patient:
        return {"success": False, "message": "Access denied. Patients only."}, 403
 
    patient = Patient.query.get(user_id)
 
    return {
        "success":            True,
        "mental_health_mode": patient.mental_health_mode,
    }, 200

