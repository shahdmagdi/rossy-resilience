from flask import Blueprint, jsonify
from middleware.auth_middleware import jwt_required_middleware
 
from services.patient_service import (
    toggle_mental_health_mode,
    get_mental_health_mode
)

patient_bp = Blueprint("patient", __name__, url_prefix="/api/patient")




# ══════════════════════════════════════════════════════════
#  MENTAL HEALTH MODE ROUTES
# ══════════════════════════════════════════════════════════

@patient_bp.route("/mental-health-mode", methods=["GET"])
@jwt_required_middleware
def mental_health_status():
    """Patient checks their mental health mode status."""
    response, status = get_mental_health_mode()
    return jsonify(response), status


@patient_bp.route("/mental-health-mode/toggle", methods=["POST"])
@jwt_required_middleware
def mental_health_toggle():
    """
    Patient toggles mental health mode on/off.

    When ON:
        - Scan results show recommendation only
        - Raw prediction/confidence hidden
        - Doctor still sees full results

    When OFF:
        - Patient sees full diagnosis
    """
    response, status = toggle_mental_health_mode()
    return jsonify(response), status