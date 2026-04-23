# from flask import Blueprint, request, jsonify
# from app import limiter
# from middleware.auth_middleware import jwt_required_middleware
# from services.scan_service import (
#     upload_scan,
#     get_my_scans,
#     get_scan_by_id,
#     get_patient_scans,
#     delete_scan,
# )

# scan_bp = Blueprint("scan", __name__, url_prefix="/api/scans")


# # ══════════════════════════════════════════════════════════
# #  POST /api/scans/upload
# #
# #  Request: multipart/form-data
# #    image:      file     (PNG, JPG, JPEG — max 10MB)
# #    image_type: string   ("ultrasound" or "mammogram")
# #
# #  Response:
# #    {
# #      "success": true,
# #      "diagnosis": {
# #        "scan_id":    "...",
# #        "image_type": "ultrasound" | "mammogram",
# #        "image_url":  "...",
# #        "prediction": "malignant" | "benign" | "normal",
# #        "confidence": 98.46,
# #        "probabilities": {
# #          "benign":    1.38,
# #          "malignant": 98.46,
# #          "normal":    0.17
# #        },
# #        "model_version": "ultrasound_resnet50_v1",
# #        "created_at": "..."
# #      }
# #    }
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

#     file = request.files["image"]
#     response, status = upload_scan(file, image_type)
#     return jsonify(response), status


# # ══════════════════════════════════════════════════════════
# #  GET /api/scans/my-scans?type=ultrasound|mammogram
# #  → Patient views all their scans (optional type filter)
# # ══════════════════════════════════════════════════════════

# @scan_bp.route("/my-scans", methods=["GET"])
# @jwt_required_middleware
# def my_scans():
#     image_type = request.args.get("type", "").strip().lower() or None
#     response, status = get_my_scans(image_type)
#     return jsonify(response), status


# # ══════════════════════════════════════════════════════════
# #  GET /api/scans/<scan_id>
# #  → Patient or assigned doctor views a single result
# # ══════════════════════════════════════════════════════════

# @scan_bp.route("/<string:scan_id>", methods=["GET"])
# @jwt_required_middleware
# def single_scan(scan_id):
#     response, status = get_scan_by_id(scan_id)
#     return jsonify(response), status


# # ══════════════════════════════════════════════════════════
# #  GET /api/scans/patient/<patient_id>?type=ultrasound|mammogram
# #  → Doctor views assigned patient's scans (optional type filter)
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
from services.scan_service import (
    upload_scan,
    upload_scan_with_doctor,
    get_my_scan_history,
    get_scan_by_id,
    get_patient_scans,
    delete_scan,
)

scan_bp = Blueprint("scan", __name__, url_prefix="/api/scans")


# ══════════════════════════════════════════════════════════
#  POST /api/scans/upload
#  → Any patient can upload (no doctor required)
#
#  form-data:
#    image:      file   (PNG, JPG, JPEG — max 10MB)
#    image_type: text   ("ultrasound" or "mammogram")
# ══════════════════════════════════════════════════════════

@scan_bp.route("/upload", methods=["POST"])
@jwt_required_middleware
@limiter.limit("10 per hour")
def upload():
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No image provided. Use field name 'image'."}), 400

    image_type = request.form.get("image_type", "").strip().lower()
    if not image_type:
        return jsonify({"success": False, "message": "image_type is required: 'ultrasound' or 'mammogram'."}), 400

    response, status = upload_scan(request.files["image"], image_type)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  POST /api/scans/upload-with-doctor
#  → Only patients WITH an assigned doctor can use this
#  → The assigned doctor will be able to see the results
#
#  form-data:
#    image:      file   (PNG, JPG, JPEG — max 10MB)
#    image_type: text   ("ultrasound" or "mammogram")
# ══════════════════════════════════════════════════════════

@scan_bp.route("/upload-with-doctor", methods=["POST"])
@jwt_required_middleware
@limiter.limit("10 per hour")
def upload_with_doctor():
    if "image" not in request.files:
        return jsonify({"success": False, "message": "No image provided. Use field name 'image'."}), 400

    image_type = request.form.get("image_type", "").strip().lower()
    if not image_type:
        return jsonify({"success": False, "message": "image_type is required: 'ultrasound' or 'mammogram'."}), 400

    response, status = upload_scan_with_doctor(request.files["image"], image_type)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  GET /api/scans/history
#  → Patient views their full scan history
#  → Optional filter: ?type=ultrasound or ?type=mammogram
# ══════════════════════════════════════════════════════════

@scan_bp.route("/history", methods=["GET"])
@jwt_required_middleware
def scan_history():
    image_type = request.args.get("type", "").strip().lower() or None
    response, status = get_my_scan_history(image_type)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  GET /api/scans/<scan_id>
#  → Patient or assigned doctor views a single scan result
# ══════════════════════════════════════════════════════════

@scan_bp.route("/<string:scan_id>", methods=["GET"])
@jwt_required_middleware
def single_scan(scan_id):
    response, status = get_scan_by_id(scan_id)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  GET /api/scans/patient/<patient_id>
#  → Doctor views their assigned patient's scan history
#  → Optional filter: ?type=ultrasound or ?type=mammogram
# ══════════════════════════════════════════════════════════

@scan_bp.route("/patient/<string:patient_id>", methods=["GET"])
@jwt_required_middleware
def patient_scans(patient_id):
    image_type = request.args.get("type", "").strip().lower() or None
    response, status = get_patient_scans(patient_id, image_type)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  DELETE /api/scans/<scan_id>
#  → Patient deletes their own scan
# ══════════════════════════════════════════════════════════

@scan_bp.route("/<string:scan_id>", methods=["DELETE"])
@jwt_required_middleware
def remove_scan(scan_id):
    response, status = delete_scan(scan_id)
    return jsonify(response), status