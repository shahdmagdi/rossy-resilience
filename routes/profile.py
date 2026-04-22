from flask import Blueprint, jsonify
from middleware.auth_middleware import jwt_required_middleware
from services.profile_service import (
    get_my_assigned_doctor,
    get_my_assigned_patients,
    get_patient_profile,
)

profile_bp = Blueprint("profile", __name__, url_prefix="/api")


# ══════════════════════════════════════════════════════════
#  GET /api/patient/my-doctor
#  → Patient views their assigned doctor's full profile
# ══════════════════════════════════════════════════════════

@profile_bp.route("/patient/my-doctor", methods=["GET"])
@jwt_required_middleware
def my_assigned_doctor():
    response, status = get_my_assigned_doctor()
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  GET /api/doctor/my-patients
#  → Doctor views all their assigned patients
# ══════════════════════════════════════════════════════════

@profile_bp.route("/doctor/my-patients", methods=["GET"])
@jwt_required_middleware
def my_assigned_patients():
    response, status = get_my_assigned_patients()
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  GET /api/doctor/my-patients/<patient_id>
#  → Doctor views a single assigned patient's full profile
# ══════════════════════════════════════════════════════════

@profile_bp.route("/doctor/my-patients/<string:patient_id>", methods=["GET"])
@jwt_required_middleware
def patient_profile(patient_id):
    response, status = get_patient_profile(patient_id)
    return jsonify(response), status