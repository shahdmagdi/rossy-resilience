
# from flask import Blueprint, request, jsonify
# from app import limiter
# from middleware.auth_middleware import jwt_required_middleware
# from services.scan_service import (
#     upload_scan,
#     upload_scan_with_doctor,
#     get_my_scan_history,
#     get_scan_by_id,
#     get_patient_scans,
#     delete_scan,
# )

# scan_bp = Blueprint("scan", __name__, url_prefix="/api/scans")


# # ══════════════════════════════════════════════════════════
# #  POST /api/scans/upload
# #  → Any patient can upload (no doctor required)
# #
# #  form-data:
# #    image:      file   (PNG, JPG, JPEG — max 10MB)
# #    image_type: text   ("ultrasound" or "mammogram")
# # ══════════════════════════════════════════════════════════

# @scan_bp.route("/upload", methods=["POST"])
# @jwt_required_middleware
# @limiter.limit("10 per hour")
# def upload():
#     if "image" not in request.files:
#         return jsonify({"success": False, "message": "No image provided. Use field name 'image'."}), 400

#     image_type = request.form.get("image_type", "").strip().lower()
#     if not image_type:
#         return jsonify({"success": False, "message": "image_type is required: 'ultrasound' or 'mammogram'."}), 400

#     response, status = upload_scan(request.files["image"], image_type)
#     return jsonify(response), status


# # ══════════════════════════════════════════════════════════
# #  POST /api/scans/upload-with-doctor
# #  → Only patients WITH an assigned doctor can use this
# #  → The assigned doctor will be able to see the results
# #
# #  form-data:
# #    image:      file   (PNG, JPG, JPEG — max 10MB)
# #    image_type: text   ("ultrasound" or "mammogram")
# # ══════════════════════════════════════════════════════════

# @scan_bp.route("/upload-with-doctor", methods=["POST"])
# @jwt_required_middleware
# @limiter.limit("10 per hour")
# def upload_with_doctor():
#     if "image" not in request.files:
#         return jsonify({"success": False, "message": "No image provided. Use field name 'image'."}), 400

#     image_type = request.form.get("image_type", "").strip().lower()
#     if not image_type:
#         return jsonify({"success": False, "message": "image_type is required: 'ultrasound' or 'mammogram'."}), 400

#     response, status = upload_scan_with_doctor(request.files["image"], image_type)
#     return jsonify(response), status


# # ══════════════════════════════════════════════════════════
# #  GET /api/scans/history
# #  → Patient views their full scan history
# #  → Optional filter: ?type=ultrasound or ?type=mammogram
# # ══════════════════════════════════════════════════════════

# @scan_bp.route("/history", methods=["GET"])
# @jwt_required_middleware
# def scan_history():
#     image_type = request.args.get("type", "").strip().lower() or None
#     response, status = get_my_scan_history(image_type)
#     return jsonify(response), status


# # ══════════════════════════════════════════════════════════
# #  GET /api/scans/<scan_id>
# #  → Patient or assigned doctor views a single scan result
# # ══════════════════════════════════════════════════════════

# @scan_bp.route("/<string:scan_id>", methods=["GET"])
# @jwt_required_middleware
# def single_scan(scan_id):
#     response, status = get_scan_by_id(scan_id)
#     return jsonify(response), status


# # ══════════════════════════════════════════════════════════
# #  GET /api/scans/patient/<patient_id>
# #  → Doctor views their assigned patient's scan history
# #  → Optional filter: ?type=ultrasound or ?type=mammogram
# # ══════════════════════════════════════════════════════════

# @scan_bp.route("/patient/<string:patient_id>", methods=["GET"])
# @jwt_required_middleware
# def patient_scans(patient_id):
#     image_type = request.args.get("type", "").strip().lower() or None
#     response, status = get_patient_scans(patient_id, image_type)
#     return jsonify(response), status


# # ══════════════════════════════════════════════════════════
# #  DELETE /api/scans/<scan_id>
# #  → Patient deletes their own scan
# # ══════════════════════════════════════════════════════════

# @scan_bp.route("/<string:scan_id>", methods=["DELETE"])
# @jwt_required_middleware
# def remove_scan(scan_id):
#     response, status = delete_scan(scan_id)
#     return jsonify(response), status



from flask import Blueprint, request, jsonify
from app import limiter
from middleware.auth_middleware import jwt_required_middleware
from services.detection_service import (
    upload_scan,
    upload_scan_with_doctor,
    get_my_scan_history,
    get_scan_by_id,
    get_patient_scans,
    delete_scan,
    upload_multimodal_scan,
    upload_multimodal_scan_with_doctor
)
from services.notification_service import notify_doctor_scan_uploaded
from models import User, Patient
from flask_jwt_extended import get_jwt_identity

detection_bp = Blueprint("detection", __name__, url_prefix="/api/detection")


# ══════════════════════════════════════════════════════════
#  POST /api/detection/upload
#  → Any patient — results private (no doctor access)
#
#  form-data:
#    image:      file   PNG/JPG/JPEG max 10MB
#    image_type: text   "ultrasound" or "mammogram"
#
#  Routing:
#    ultrasound → HF_ULTRASOUND_URL space
#    mammogram  → HF_MAMMOGRAM_URL space
#    after upload: checks if patient has both → triggers multimodal
# ══════════════════════════════════════════════════════════

@detection_bp.route("/upload", methods=["POST"])
@jwt_required_middleware
@limiter.limit("10 per hour")
def patient_upload():

    # ── Multimodal upload ──────────────────────────────
    if (
        "ultrasound_image" in request.files and
        "mammogram_image" in request.files
    ):
        response, status = upload_multimodal_scan(
            request.files["ultrasound_image"],
            request.files["mammogram_image"]
        )
        return jsonify(response), status

    # ── Single-modality upload (existing behavior) ─────
    if "image" not in request.files:
        return jsonify({
            "success": False,
            "message": (
                "No image provided. Use either:\n"
                "- image + image_type (single model)\n"
                "- ultrasound_image + mammogram_image (multimodal)"
            )
        }), 400

    image_type = request.form.get("image_type", "").strip().lower()
    if not image_type:
        return jsonify({
            "success": False,
            "message": "image_type is required for single-model upload."
        }), 400

    response, status = upload_scan(
        request.files["image"],
        image_type
    )
    return jsonify(response), status

# ══════════════════════════════════════════════════════════
#  POST /api/detection/upload-with-doctor
#  → Assigned patients only — doctor can view results
#
#  form-data:
#    image:      file   PNG/JPG/JPEG max 10MB
#    image_type: text   "ultrasound" or "mammogram"
# ══════════════════════════════════════════════════════════

@detection_bp.route("/upload-with-doctor", methods=["POST"])
@jwt_required_middleware
@limiter.limit("10 per hour")
def patient_upload_with_doctor():
    """
    Supports both:
    1. Single model:
       - image
       - image_type

    2. Multimodal:
       - ultrasound_image
       - mammogram_image
    """

    image_type = None
    scan_id = None

    # ─────────────────────────────────────────────────────
    # MULTIMODAL UPLOAD
    # ─────────────────────────────────────────────────────
    if (
        "ultrasound_image" in request.files and
        "mammogram_image" in request.files
    ):
        response, status = upload_multimodal_scan_with_doctor(
            request.files["ultrasound_image"],
            request.files["mammogram_image"]
        )

        # Used for doctor notification
        image_type = "multimodal"
        scan_id = response.get("multimodal", {}).get("multimodal_id")

    # ─────────────────────────────────────────────────────
    # SINGLE-MODEL UPLOAD (existing behavior)
    # ─────────────────────────────────────────────────────
    else:
        if "image" not in request.files:
            return jsonify({
                "success": False,
                "message": (
                    "No image provided. Use either:\n"
                    "- image + image_type\n"
                    "- ultrasound_image + mammogram_image"
                )
            }), 400

        image_type = request.form.get("image_type", "").strip().lower()
        if not image_type:
            return jsonify({
                "success": False,
                "message": (
                    "image_type is required: "
                    "'ultrasound' or 'mammogram'."
                )
            }), 400

        response, status = upload_scan_with_doctor(
            request.files["image"],
            image_type
        )

        scan_id = response.get("diagnosis", {}).get("scan_id")

    # ─────────────────────────────────────────────────────
    # NOTIFY DOCTOR (works for both single and multimodal)
    # ─────────────────────────────────────────────────────
    if status == 201:
        try:
            patient_id = get_jwt_identity()
            patient_user = User.query.get(patient_id)
            patient = Patient.query.get(patient_id)

            if patient and patient.current_assigned_doctor_id:
                notify_doctor_scan_uploaded(
                    doctor_id=str(patient.current_assigned_doctor_id),
                    patient_full_name=patient_user.full_name,
                    scan_id=scan_id,
                    image_type=image_type,  # ultrasound / mammogram / multimodal
                )
        except Exception:
            pass  # Notification failure never blocks response

    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  GET /api/detection/history
#  → Patient views their full detection scan history
#  → Optional filter: ?type=ultrasound or ?type=mammogram
#  → Includes multimodal results if available
# ══════════════════════════════════════════════════════════

@detection_bp.route("/history", methods=["GET"])
@jwt_required_middleware
def scan_history():
    image_type = request.args.get("type", "").strip().lower() or None
    response, status = get_my_scan_history(image_type)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  GET /api/detection/<scan_id>
#  → Patient → mental health mode respected
#  → Doctor  → full results including segmentation status
# ══════════════════════════════════════════════════════════

@detection_bp.route("/<string:scan_id>", methods=["GET"])
@jwt_required_middleware
def single_scan(scan_id):
    response, status = get_scan_by_id(scan_id)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  GET /api/detection/patient/<patient_id>
#  → Doctor views shared scans of their assigned patient
#  → Optional filter: ?type=ultrasound or ?type=mammogram
#  → Includes multimodal results
# ══════════════════════════════════════════════════════════

@detection_bp.route("/patient/<string:patient_id>", methods=["GET"])
@jwt_required_middleware
def patient_scans(patient_id):
    image_type = request.args.get("type", "").strip().lower() or None
    response, status = get_patient_scans(patient_id, image_type)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  DELETE /api/detection/<scan_id>
#  → Patient deletes their own scan
# ══════════════════════════════════════════════════════════

@detection_bp.route("/<string:scan_id>", methods=["DELETE"])
@jwt_required_middleware
def remove_scan(scan_id):
    response, status = delete_scan(scan_id)
    return jsonify(response), status