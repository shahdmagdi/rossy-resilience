import uuid
from datetime import datetime
from app import db
import enum


# ── AJCC 8th Edition stages ───────────────────────────────
class AJCCStage(enum.Enum):
    IA      = "IA"
    IB      = "IB"
    IIA     = "IIA"
    IIB     = "IIB"
    IIIA    = "IIIA"
    IIIB    = "IIIB"
    IIIC    = "IIIC"
    IV      = "IV"
    Unknown = "Unknown"


# ══════════════════════════════════════════════════════════
#  STAGING
#  Entered by doctor for their assigned patient.
#  Runs AJCC 8th Edition staging algorithm.
#  Results visible to doctor ONLY — never to patient.
# ══════════════════════════════════════════════════════════

class Staging(db.Model):
    __tablename__ = "stagings"

    id         = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    doctor_id  = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )

    # ── Inputs entered by doctor ──────────────────────────
    tumor_size        = db.Column(db.Float,   nullable=True)   # cm — mandatory unless no_primary_tumour
    no_primary_tumour = db.Column(db.Boolean, nullable=False, default=False)
    lymphadenopathy   = db.Column(db.Float,   nullable=True)   # 0 / 0.5 / 1 / 2 / 3
    metastatic        = db.Column(db.Integer, nullable=True)   # 0 / 1
    skin_nipple       = db.Column(db.Integer, nullable=True)   # 0 / 1
    pec_chest         = db.Column(db.Integer, nullable=True)   # 0 / 1

    # ── Biomarkers ────────────────────────────────────────
    er               = db.Column(db.Integer, nullable=True)    # 0 / 1
    pr               = db.Column(db.Integer, nullable=True)    # 0 / 1
    her2             = db.Column(db.Integer, nullable=True)    # 0 / 1 / 2
    histologic_grade = db.Column(db.Integer, nullable=True)    # 1 / 2 / 3

    # ── Staging results ───────────────────────────────────
    cT_stage          = db.Column(db.String(10),  nullable=True)   # T0 / T1 / T2 / T3 / T4
    cN_stage          = db.Column(db.String(10),  nullable=True)   # N0 / N1mi / N1 / N2 / N3
    cM_stage          = db.Column(db.String(5),   nullable=True)   # M0 / M1
    anatomic_stage    = db.Column(db.String(10),  nullable=True)   # IA / IB / IIA / ...
    prognostic_stage  = db.Column(db.String(10),  nullable=True)   # same + * or ?
    result_label      = db.Column(db.Text,        nullable=False)  # full result string
    molecular_subtype = db.Column(db.String(30),  nullable=True)   # HR+/HER2- etc.

    # ── Optional links to scans ───────────────────────────
    detection_scan_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("detection_scans.scan_id", ondelete="SET NULL"),
        nullable=True
    )
    mri_scan_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("mri_scans.scan_id", ondelete="SET NULL"),
        nullable=True
    )

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)

    # ── Relationships ─────────────────────────────────────
    patient = db.relationship("User", foreign_keys=[patient_id])
    doctor  = db.relationship("User", foreign_keys=[doctor_id])

    def to_dict_doctor(self):
        return {
            "id":         str(self.id),
            "patient_id": str(self.patient_id),
            "doctor_id":  str(self.doctor_id) if self.doctor_id else None,

           
            "staging": {
                "cT_stage":          self.cT_stage,
                "cN_stage":          self.cN_stage,
                "cM_stage":          self.cM_stage,
                "anatomic_stage":    self.anatomic_stage,
                "prognostic_stage":  self.prognostic_stage,
                "molecular_subtype": self.molecular_subtype,
                "result_label":      self.result_label,
            },

           

            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict(self):
        return self.to_dict_doctor()