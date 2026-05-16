import uuid
from datetime import datetime
from app import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id         = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    messages   = db.relationship(
        "ChatMessage",
        back_populates = "session",
        cascade        = "all, delete-orphan",
        order_by       = "ChatMessage.created_at",
    )

    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "session_id": str(self.id),
            "user_id":    str(self.user_id),
            "created_at": self.created_at.isoformat(),
            "messages":   [m.to_dict() for m in self.messages],
        }


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id         = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    role       = db.Column(db.String(20),  nullable=False)   # "user" or "assistant"
    content    = db.Column(db.Text,        nullable=False)
    created_at = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    session = db.relationship("ChatSession", back_populates="messages")

    def to_dict(self):
        return {
            "id":         str(self.id),
            "role":       self.role,
            "content":    self.content,
            "created_at": self.created_at.isoformat(),
        }