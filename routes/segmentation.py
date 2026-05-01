from flask import Blueprint, jsonify
from app import limiter
from middleware.auth_middleware import jwt_required_middleware
from services.segmentation_service import get_segmentation, delete_segmentation

segmentation_bp = Blueprint("segmentation", __name__, url_prefix="/api/segmentation")


# ══════════════════════════════════════════════════════════
#  POST /api/segmentation/<scan_id>
#  → Doctor requests segmentation for a specific scan
#  → Patient never calls this endpoint
#
#  Behaviour:
#    - If segmentation already exists → returns cached result instantly
#    - If not → calls HF Space → stores result → returns it
#
#  No body needed — scan_id in URL is enough
#
#  Response:
#    {
#      "success":          true,
#      "cached":           false,
#      "scan_id":          "...",
#      "image_type":       "ultrasound",
#      "original_url":     "https://cloudinary.com/...",   ← original scan
#      "segmentation_url": "https://cloudinary.com/...",   ← mask image
#      "confidence":       0.9458                          ← tumor region confidence
#    }
# ══════════════════════════════════════════════════════════

@segmentation_bp.route("/<string:scan_id>", methods=["POST"])
@jwt_required_middleware
@limiter.limit("20 per hour")
def request_segmentation(scan_id):
    response, status = get_segmentation(scan_id)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  DELETE /api/segmentation/<scan_id>
#  → Doctor deletes segmentation result
#  → Mask image removed from Cloudinary
#  → Can be re-requested anytime via POST
# ══════════════════════════════════════════════════════════

@segmentation_bp.route("/<string:scan_id>", methods=["DELETE"])
@jwt_required_middleware
def remove_segmentation(scan_id):
    response, status = delete_segmentation(scan_id)
    return jsonify(response), status