
import logging
from flask import Blueprint, request, jsonify
from middleware.auth_middleware import jwt_required_middleware
from flask_jwt_extended import get_jwt_identity
from models.chat import ChatSession, ChatMessage
from services.chatbot_service import ask_rossy
from app import db, limiter

logger     = logging.getLogger(__name__)
chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")


# ══════════════════════════════════════════════════════════
#  POST /api/chatbot/session
#  → Creates a new chat session for the logged-in user
# ══════════════════════════════════════════════════════════

@chatbot_bp.route("/session", methods=["POST"])
@jwt_required_middleware
def create_session():
    user_id = get_jwt_identity()   # ← from JWT, not request body
    try:
        session = ChatSession(user_id=user_id)
        db.session.add(session)
        db.session.commit()
        return jsonify({
            "session_id": str(session.id),
            "created_at": session.created_at.isoformat(),
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Could not create session.", "error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  GET /api/chatbot/session/<session_id>
#  → Get full session with all messages
# ══════════════════════════════════════════════════════════

@chatbot_bp.route("/session/<string:session_id>", methods=["GET"])
@jwt_required_middleware
def get_session(session_id):
    user_id = get_jwt_identity()

    session = ChatSession.query.get(session_id)
    if not session:
        return jsonify({"success": False, "message": "Session not found."}), 404

    # Users can only view their own sessions
    if str(session.user_id) != user_id:
        return jsonify({"success": False, "message": "Access denied."}), 403

    return jsonify(session.to_dict()), 200


# ══════════════════════════════════════════════════════════
#  GET /api/chatbot/sessions
#  → Get all sessions for the logged-in user
# ══════════════════════════════════════════════════════════

@chatbot_bp.route("/sessions", methods=["GET"])
@jwt_required_middleware
def get_user_sessions():
    user_id  = get_jwt_identity()
    sessions = (
        ChatSession.query
        .filter_by(user_id=user_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return jsonify({
        "success":  True,
        "total":    len(sessions),
        "sessions": [s.to_dict() for s in sessions],
    }), 200


# ══════════════════════════════════════════════════════════
#  POST /api/chatbot/message
#  → Main chat endpoint — send a message, get ROSSY's answer
# ══════════════════════════════════════════════════════════

@chatbot_bp.route("/message", methods=["POST"])
@jwt_required_middleware
@limiter.limit("30 per minute; 200 per hour")   # prevent abuse
def send_message():
    """
    Required: { "session_id": str, "message": str }
    user_id comes from JWT — not from request body
    """
    user_id = get_jwt_identity()
    data    = request.get_json(silent=True)

    if not data:
        return jsonify({"success": False, "message": "No data provided."}), 400

    session_id = data.get("session_id", "").strip()
    message    = data.get("message", "").strip()

    if not session_id:
        return jsonify({"success": False, "message": "session_id is required."}), 400
    if not message:
        return jsonify({"success": False, "message": "message cannot be empty."}), 400

    # Verify session belongs to this user
    session = ChatSession.query.get(session_id)
    if not session:
        return jsonify({"success": False, "message": "Session not found."}), 404
    if str(session.user_id) != user_id:
        return jsonify({"success": False, "message": "Access denied."}), 403

    try:
        # 1. Save user message
        user_msg = ChatMessage(
            session_id = session_id,
            role       = "user",
            content    = message,
        )
        db.session.add(user_msg)
        db.session.flush()

        # 2. Load last 6 messages for context (3 turns)
        history_rows = (
            ChatMessage.query
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(6)
            .all()
        )
        history = [{"role": m.role, "content": m.content} for m in history_rows]

        # 3. Call RAG pipeline
        answer = ask_rossy(query=message, history=history, k=3)

        # 4. Save ROSSY's answer
        assistant_msg = ChatMessage(
            session_id = session_id,
            role       = "assistant",
            content    = answer,
        )
        db.session.add(assistant_msg)
        db.session.commit()

        return jsonify({
            "success":           True,
            "user_message":      user_msg.to_dict(),
            "assistant_message": assistant_msg.to_dict(),
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.exception("Error in send_message")
        return jsonify({"success": False, "message": "Something went wrong.", "error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  DELETE /api/chatbot/session/<session_id>
#  → Delete a session and all its messages
# ══════════════════════════════════════════════════════════

@chatbot_bp.route("/session/<string:session_id>", methods=["DELETE"])
@jwt_required_middleware
def delete_session(session_id):
    user_id = get_jwt_identity()

    session = ChatSession.query.get(session_id)
    if not session:
        return jsonify({"success": False, "message": "Session not found."}), 404
    if str(session.user_id) != user_id:
        return jsonify({"success": False, "message": "Access denied."}), 403

    try:
        db.session.delete(session)
        db.session.commit()
        return jsonify({"success": True, "message": "Session deleted."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": "Could not delete session.", "error": str(e)}), 500
