import uuid
from datetime import datetime
from app import db
import enum


class NotificationType(enum.Enum):
    patient_assigned_doctor  = "patient_assigned_doctor"
    doctor_accepted_patient  = "doctor_accepted_patient"
    doctor_rejected_patient  = "doctor_rejected_patient"
    patient_uploaded_scan    = "patient_uploaded_scan"
    doctor_created_care_plan = "doctor_created_care_plan"


class Notification(db.Model):
    __tablename__ = "notifications"

    id           = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id      = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )                                                   # who receives the notification
    type         = db.Column(db.Enum(NotificationType), nullable=False)
    title        = db.Column(db.String(200),            nullable=False)
    body         = db.Column(db.Text,                   nullable=False)
    is_read      = db.Column(db.Boolean,                nullable=False, default=False)
    created_at   = db.Column(db.DateTime,               nullable=False, default=datetime.utcnow)

    # Optional reference to related resource
    reference_id = db.Column(db.String(100), nullable=True)   # scan_id, assignment_id etc.

    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id":           str(self.id),
            "type":         self.type.value,
            "title":        self.title,
            "body":         self.body,
            "is_read":      self.is_read,
            "reference_id": self.reference_id,
            "created_at":   self.created_at.isoformat(),
        }