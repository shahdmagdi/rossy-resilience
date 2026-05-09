from flask import Blueprint, request, jsonify
from middleware.auth_middleware import jwt_required_middleware
from services.staging_service import (
    create_staging_service,
    get_staging_service,
    list_patient_stagings_service,
    update_staging_service,
    delete_staging_service,
)

staging_bp = Blueprint("staging", __name__, url_prefix="/api/staging")


@staging_bp.route("/patient/<uuid:patient_id>", methods=["POST"])
@jwt_required_middleware
def create_staging(patient_id):
    """POST /api/staging/patient/<patient_id>"""
    data = request.get_json(silent=True) or {}
    response, status = create_staging_service(patient_id, data)
    return jsonify(response), status


@staging_bp.route("/<uuid:staging_id>", methods=["GET"])
@jwt_required_middleware
def get_staging(staging_id):
    """GET /api/staging/<staging_id>"""
    response, status = get_staging_service(staging_id)
    return jsonify(response), status


@staging_bp.route("/patient/<uuid:patient_id>/all", methods=["GET"])
@jwt_required_middleware
def list_patient_stagings(patient_id):
    """GET /api/staging/patient/<patient_id>/all"""
    response, status = list_patient_stagings_service(patient_id)
    return jsonify(response), status


@staging_bp.route("/<uuid:staging_id>", methods=["PUT"])
@jwt_required_middleware
def update_staging(staging_id):
    """PUT /api/staging/<staging_id>"""
    data = request.get_json(silent=True) or {}
    response, status = update_staging_service(staging_id, data)
    return jsonify(response), status


@staging_bp.route("/<uuid:staging_id>", methods=["DELETE"])
@jwt_required_middleware
def delete_staging(staging_id):
    """DELETE /api/staging/<staging_id>"""
    response, status = delete_staging_service(staging_id)
    return jsonify(response), status