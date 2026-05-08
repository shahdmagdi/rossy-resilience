import uuid
from datetime import datetime
from app import db
import enum


class NoteVisibility(enum.Enum):
    private = "private"   # doctor only
    shared  = "shared"    # doctor + patient (care plan)


class DoctorNote(db.Model):
    __tablename__ = "doctor_notes"

    id         = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id  = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    patient_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )

    # Optional link to a specific detection scan
    scan_id    = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("detection_scans.scan_id", ondelete="SET NULL"),
        nullable=True
    )

    title      = db.Column(db.String(200),         nullable=False)
    content    = db.Column(db.Text,                nullable=False)
    visibility = db.Column(db.Enum(NoteVisibility), nullable=False, default=NoteVisibility.private)
    created_at = db.Column(db.DateTime,            nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,            nullable=True)

    doctor  = db.relationship("User",          foreign_keys=[doctor_id])
    patient = db.relationship("User",          foreign_keys=[patient_id])
    scan    = db.relationship("DetectionScan", foreign_keys=[scan_id])

    # ─────────────────────────────────────────────────────
    #  DOCTOR VIEW — all fields
    # ─────────────────────────────────────────────────────
    def to_dict_doctor(self):
        return {
            "id":         str(self.id),
            "doctor_id":  str(self.doctor_id),
            "patient_id": str(self.patient_id),
            "scan_id":    str(self.scan_id) if self.scan_id else None,
            "title":      self.title,
            "content":    self.content,
            "visibility": self.visibility.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    # ─────────────────────────────────────────────────────
    #  PATIENT VIEW — shared notes only (care plans)
    #  No doctor_id exposed
    # ─────────────────────────────────────────────────────
    def to_dict_patient(self):
        return {
            "id":         str(self.id),
            "scan_id":    str(self.scan_id) if self.scan_id else None,
            "title":      self.title,
            "content":    self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict(self):
        return self.to_dict_doctor()