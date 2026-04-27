from flask import Blueprint, request, jsonify
from app import limiter
from middleware.auth_middleware import jwt_required_middleware
from services.mri_service import (
    upload_mri,
    get_patient_mri_history,
    get_mri_scan,
    delete_mri_scan,
)

mri_bp = Blueprint("mri", __name__, url_prefix="/api/mri")


# ══════════════════════════════════════════════════════════
#  POST /api/mri/upload/<patient_id>
#  → Doctor uploads MRI NIfTI files for their assigned patient
#  → Results visible to doctor only — never to patient
#
#  Request: multipart/form-data
#    acq0: file  (.nii or .nii.gz) — REQUIRED
#    acq2: file  (.nii or .nii.gz) — REQUIRED
#    acq1: file  (.nii or .nii.gz) — OPTIONAL
#
#  Response:
#    {
#      "success": true,
#      "scan": {
#        "scan_id":    "...",
#        "patient_id": "...",
#        "files": {
#          "acq0_url": "...",
#          "acq1_url": "...",
#          "acq2_url": "..."
#        },
#        "results": {
#          "tumor_detected":           true,
#          "t_stage":                  "T3",
#          "size_cm":                  10.63,
#          "volume_cc":                25.36,
#          "segmentation_consistency": 0.967,
#          "uncertainty_mean":         0.037
#        }
#      }
#    }
# ══════════════════════════════════════════════════════════

@mri_bp.route("/upload/<string:patient_id>", methods=["POST"])
@jwt_required_middleware
@limiter.limit("5 per hour")
def upload_mri_scan(patient_id):
    # acq0 and acq2 are required
    if "acq0" not in request.files:
        return jsonify({"success": False, "message": "acq0 file is required."}), 400

    if "acq2" not in request.files:
        return jsonify({"success": False, "message": "acq2 file is required."}), 400

    acq0_file = request.files["acq0"]
    acq2_file = request.files["acq2"]
    acq1_file = request.files.get("acq1")   # optional

    response, status = upload_mri(acq0_file, acq2_file, patient_id, acq1_file)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  GET /api/mri/patient/<patient_id>
#  → Doctor views all MRI scans for their assigned patient
# ══════════════════════════════════════════════════════════

@mri_bp.route("/patient/<string:patient_id>", methods=["GET"])
@jwt_required_middleware
def patient_mri_history(patient_id):
    response, status = get_patient_mri_history(patient_id)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  GET /api/mri/<scan_id>
#  → Doctor views a single MRI scan result
# ══════════════════════════════════════════════════════════

@mri_bp.route("/<string:scan_id>", methods=["GET"])
@jwt_required_middleware
def single_mri_scan(scan_id):
    response, status = get_mri_scan(scan_id)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  DELETE /api/mri/<scan_id>
#  → Doctor deletes MRI scan + removes NIfTI files from Cloudinary
# ══════════════════════════════════════════════════════════

@mri_bp.route("/<string:scan_id>", methods=["DELETE"])
@jwt_required_middleware
def remove_mri_scan(scan_id):
    response, status = delete_mri_scan(scan_id)
    return jsonify(response), status