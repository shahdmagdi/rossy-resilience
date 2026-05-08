from flask import Blueprint, request, jsonify
from middleware.auth_middleware import jwt_required_middleware
from services.notification_read_service import (
    get_my_notifications,
    mark_notification_read,
    mark_all_read,
)

notification_bp = Blueprint("notification", __name__, url_prefix="/api/notifications")


# ══════════════════════════════════════════════════════════
#  GET /api/notifications
#  → Get all notifications for the logged-in user
#  → Optional filter: ?unread=true
# ══════════════════════════════════════════════════════════

@notification_bp.route("", methods=["GET"])
@jwt_required_middleware
def get_notifications():
    """
    Returns all notifications for the logged-in user.
    Works for patient, doctor, and admin.
    Optional: ?unread=true → only unread notifications
    """
    unread_only = request.args.get("unread", "").lower() == "true"
    response, status = get_my_notifications(unread_only)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  PUT /api/notifications/<notification_id>/read
#  → Mark a single notification as read
# ══════════════════════════════════════════════════════════

@notification_bp.route("/<string:notification_id>/read", methods=["PUT"])
@jwt_required_middleware
def read_notification(notification_id):
    response, status = mark_notification_read(notification_id)
    return jsonify(response), status


# ══════════════════════════════════════════════════════════
#  PUT /api/notifications/read-all
#  → Mark all notifications as read
# ══════════════════════════════════════════════════════════

@notification_bp.route("/read-all", methods=["PUT"])
@jwt_required_middleware
def read_all_notifications():
    response, status = mark_all_read()
    return jsonify(response), status