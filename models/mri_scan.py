import uuid
from datetime import datetime
from app import db
import enum


# ── Tumor staging enum ────────────────────────────────────
class TumorStage(enum.Enum):
    T1mi = "T1mi"   # ≤ 0.1 cm
    T1a  = "T1a"    # 0.1 – 0.5 cm
    T1b  = "T1b"    # 0.5 – 1.0 cm
    T1c  = "T1c"    # 1.0 – 2.0 cm
    T2   = "T2"     # 2.0 – 5.0 cm
    T3   = "T3"     # > 5.0 cm


# ══════════════════════════════════════════════════════════
#  MRI SCAN
#  Uploaded by doctor for their assigned patient.
#  Takes 3 NIfTI acquisition files (acq0, acq1, acq2).
#  Results shown to doctor ONLY — never to patient.
#  Separate table from detection_scans.
#  Files stored in Supabase bucket "mri_files".
# ══════════════════════════════════════════════════════════

class MriScan(db.Model):
    __tablename__ = "mri_scans"

    scan_id      = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id   = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    doctor_id    = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True    # kept even if doctor is removed
    )

    # ── Uploaded NIfTI files (stored in Supabase) ─────────
    # acq0 and acq2 are required, acq1 is optional.
    # _url      → public URL used to pass to HF Space
    # _path     → storage path used for deletion  e.g. "<patient_id>/acq0.nii.gz"
    acq0_url          = db.Column(db.String(500), nullable=False)
    acq0_storage_path = db.Column(db.String(300), nullable=False)

    acq1_url          = db.Column(db.String(500), nullable=True)   # optional
    acq1_storage_path = db.Column(db.String(300), nullable=True)

    acq2_url          = db.Column(db.String(500), nullable=False)
    acq2_storage_path = db.Column(db.String(300), nullable=False)

    # ── MRI staging results ───────────────────────────────
    t_stage                  = db.Column(db.Enum(TumorStage), nullable=True)   # None if no tumor found
    size_cm                  = db.Column(db.Float,             nullable=True)
    volume_cc                = db.Column(db.Float,             nullable=True)
    segmentation_consistency = db.Column(db.Float,             nullable=True)   # 0.0 – 1.0
    uncertainty_mean         = db.Column(db.Float,             nullable=True)

    model_version = db.Column(db.String(50),  nullable=False, default="mri_unet_resnet34_v1")
    created_at    = db.Column(db.DateTime,    nullable=False,  default=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────
    patient = db.relationship("User", foreign_keys=[patient_id])
    doctor  = db.relationship("User", foreign_keys=[doctor_id])

    # ─────────────────────────────────────────────────────
    #  DOCTOR VIEW — full results
    #  Patient never sees MRI results
    # ─────────────────────────────────────────────────────
    def to_dict_doctor(self):
        return {
            "scan_id":    str(self.scan_id),
            "patient_id": str(self.patient_id),
            "doctor_id":  str(self.doctor_id) if self.doctor_id else None,

            # NIfTI file URLs (doctor can download and view)
            "files": {
                "acq0_url": self.acq0_url,
                "acq1_url": self.acq1_url,
                "acq2_url": self.acq2_url,
            },

            # Staging results
            "results": {
                "t_stage":                  self.t_stage.value if self.t_stage else None,
                "size_cm":                  self.size_cm,
                "volume_cc":                self.volume_cc,
                "segmentation_consistency": self.segmentation_consistency,
                "uncertainty_mean":         self.uncertainty_mean,
                "tumor_detected":           self.t_stage is not None,
            },

            "model_version": self.model_version,
            "created_at":    self.created_at.isoformat(),
        }

    def to_dict(self):
        return self.to_dict_doctor()