from flask import Blueprint, request, jsonify
from middleware.auth_middleware import jwt_required_middleware
from services.notes_service import (
    create_note,
    get_patient_notes,
    get_note_by_id_doctor,
    update_note,
    delete_note,
    get_my_care_plans,
    get_care_plan_by_id,
)

notes_bp = Blueprint("notes", __name__, url_prefix="/api")


# ══════════════════════════════════════════════════════════
#  DOCTOR ROUTES
# ══════════════════════════════════════════════════════════

# POST /api/doctor/patients/<patient_id>/notes

@notes_bp.route("/doctor/patients/<string:patient_id>/notes", methods=["POST"])
@jwt_required_middleware
def doctor_create_note(patient_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data provided."
        }), 400

    visibility = request.args.get(
        "visibility",
        "private"
    ).strip().lower()

    response, status = create_note(
        patient_id,
        data,
        visibility
    )

    return jsonify(response), status

def doctor_get_notes(patient_id):
    """
    Doctor views all notes for a patient.
    Optional filter: ?visibility=private|shared
    """
    visibility = request.args.get("visibility", "").strip().lower() or None
    response, status = get_patient_notes(patient_id, visibility)
    return jsonify(response), status


# GET /api/doctor/notes/<note_id>
@notes_bp.route("/doctor/notes/<string:note_id>", methods=["GET"])
@jwt_required_middleware
def doctor_get_single_note(note_id):
    response, status = get_note_by_id_doctor(note_id)
    return jsonify(response), status


# PUT /api/doctor/notes/<note_id>
@notes_bp.route("/doctor/notes/<string:note_id>", methods=["PUT"])
@jwt_required_middleware
def doctor_update_note(note_id):
    """
    Doctor updates a note.
    If visibility changes from private → shared, care plan notification fires.
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided."}), 400

    response, status = update_note(note_id, data)
    return jsonify(response), status


# DELETE /api/doctor/notes/<note_id>
@notes_bp.route("/doctor/notes/<string:note_id>", methods=["DELETE"])
@jwt_required_middleware
def doctor_delete_note(note_id):
    response, status = delete_note(note_id)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  PATIENT ROUTES — care plans only (shared notes)
# ══════════════════════════════════════════════════════════

# GET /api/patient/care-plans
@notes_bp.route("/patient/care-plans", methods=["GET"])
@jwt_required_middleware
def patient_get_care_plans():
    """Patient views all care plans shared by their assigned doctor."""
    response, status = get_my_care_plans()
    return jsonify(response), status


# GET /api/patient/care-plans/<note_id>
@notes_bp.route("/patient/care-plans/<string:note_id>", methods=["GET"])
@jwt_required_middleware
def patient_get_single_care_plan(note_id):
    response, status = get_care_plan_by_id(note_id)
    return jsonify(response), status