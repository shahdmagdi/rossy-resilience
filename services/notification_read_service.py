from app import db
from models.notification import Notification
from flask_jwt_extended import get_jwt_identity


def get_my_notifications(unread_only=False):
    """
    Returns all notifications for the logged-in user.
    Optional filter: ?unread=true

    Returns: (response_dict, http_status_code)
    """
    user_id = get_jwt_identity()

    try:
        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        notifications = query.order_by(Notification.created_at.desc()).all()
        unread_count  = Notification.query.filter_by(user_id=user_id, is_read=False).count()

        return {
            "success":      True,
            "unread_count": unread_count,
            "total":        len(notifications),
            "notifications": [n.to_dict() for n in notifications],
        }, 200

    except Exception as e:
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


def mark_notification_read(notification_id):
    """
    Marks a single notification as read.

    Returns: (response_dict, http_status_code)
    """
    user_id = get_jwt_identity()

    notification = Notification.query.filter_by(
        id      = notification_id,
        user_id = user_id,
    ).first()

    if not notification:
        return {"success": False, "message": "Notification not found."}, 404

    try:
        notification.is_read = True
        db.session.commit()
        return {"success": True, "message": "Notification marked as read."}, 200

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


def mark_all_read():
    """
    Marks all notifications as read for the logged-in user.

    Returns: (response_dict, http_status_code)
    """
    user_id = get_jwt_identity()

    try:
        Notification.query.filter_by(
            user_id = user_id,
            is_read = False,
        ).update({"is_read": True})
        db.session.commit()

        return {"success": True, "message": "All notifications marked as read."}, 200

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500