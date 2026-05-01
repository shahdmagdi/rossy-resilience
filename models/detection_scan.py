# import uuid
# from datetime import datetime
# from app import db
# import enum


# class ImageType(enum.Enum):
#     ultrasound = "ultrasound"
#     mammogram  = "mammogram"


# class PredictionClass(enum.Enum):
#     benign    = "benign"
#     malignant = "malignant"
#     normal    = "normal"


# class Scan(db.Model):
#     __tablename__ = "scans"

#     scan_id         = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     patient_id      = db.Column(
#         db.UUID(as_uuid=True),
#         db.ForeignKey("users.user_id", ondelete="CASCADE"),
#         nullable=False
#     )
#     image_type      = db.Column(db.Enum(ImageType),       nullable=False)   # ultrasound | mammogram
#     image_url       = db.Column(db.String(500),            nullable=False)   # Cloudinary URL
#     image_public_id = db.Column(db.String(300),            nullable=False)   # Cloudinary public_id
#     prediction      = db.Column(db.Enum(PredictionClass),  nullable=False)
#     confidence      = db.Column(db.Float,                  nullable=False)
#     prob_benign     = db.Column(db.Float,                  nullable=False)
#     prob_malignant  = db.Column(db.Float,                  nullable=False)
#     prob_normal     = db.Column(db.Float,                  nullable=False)
#     model_version   = db.Column(db.String(50),             nullable=False)
#     created_at      = db.Column(db.DateTime,               nullable=False, default=datetime.utcnow)
#     shared_with_doctor = db.Column(db.Boolean, nullable=False, default=False)
#     patient = db.relationship("User", foreign_keys=[patient_id])

#     def to_dict(self):
#         return {
#             "scan_id":       str(self.scan_id),
#             "patient_id":    str(self.patient_id),
#             "image_type":    self.image_type.value,
#             "image_url":     self.image_url,
#             "prediction":    self.prediction.value,
#             "confidence":    self.confidence,
#             "probabilities": {
#                 "benign":    self.prob_benign,
#                 "malignant": self.prob_malignant,
#                 "normal":    self.prob_normal,
#             },
#             "model_version": self.model_version,
#             "shared_with_doctor": self.shared_with_doctor,
#             "created_at":    self.created_at.isoformat(),
#         }



# import uuid
# from datetime import datetime
# from app import db
# import enum


# # ── Enums ─────────────────────────────────────────────────

# class DetectionImageType(enum.Enum):
#     ultrasound = "ultrasound"
#     mammogram  = "mammogram"


# class DetectionPrediction(enum.Enum):
#     benign    = "benign"
#     malignant = "malignant"
#     normal    = "normal"


# # ══════════════════════════════════════════════════════════
# #  DETECTION SCAN
# #  Stores ultrasound and mammogram classification results.
# #  Separate from MRI, biopsy, and recommendation tables.
# #  Segmentation results stored on-demand in segmentation_url.
# # ══════════════════════════════════════════════════════════

# class DetectionScan(db.Model):
#     __tablename__ = "detection_scans"

#     scan_id              = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     patient_id           = db.Column(
#         db.UUID(as_uuid=True),
#         db.ForeignKey("users.user_id", ondelete="CASCADE"),
#         nullable=False
#     )
#     image_type           = db.Column(db.Enum(DetectionImageType), nullable=False)

#     # ── Original image ────────────────────────────────────
#     image_url            = db.Column(db.String(500), nullable=False)
#     image_public_id      = db.Column(db.String(300), nullable=False)

#     # ── Classification result ─────────────────────────────
#     prediction           = db.Column(db.Enum(DetectionPrediction), nullable=False)
#     confidence           = db.Column(db.Float,                      nullable=False)
#     prob_benign          = db.Column(db.Float,                      nullable=False)
#     prob_malignant       = db.Column(db.Float,                      nullable=False)
#     prob_normal          = db.Column(db.Float,                      nullable=False)

#     # ── Segmentation (on-demand, doctor only) ─────────────
#     # Populated only when doctor requests segmentation
#     segmentation_url     = db.Column(db.String(500), nullable=True)
#     segmentation_public_id = db.Column(db.String(300), nullable=True)

#     # ── Recommendation ────────────────────────────────────
#     # Shown to patient INSTEAD of raw diagnosis in mental health mode
#     recommendation       = db.Column(db.Text, nullable=True)

#     # ── Flags ─────────────────────────────────────────────
#     shared_with_doctor   = db.Column(db.Boolean, nullable=False, default=False)

#     # Snapshot of patient's mental_health_mode at upload time
#     # So mode changes after upload don't retroactively change visibility
#     mental_health_mode   = db.Column(db.Boolean, nullable=False, default=False)

#     model_version        = db.Column(db.String(50),  nullable=False)
#     created_at           = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

#     # ── Relationships ─────────────────────────────────────
#     patient = db.relationship("User", foreign_keys=[patient_id])

#     # ─────────────────────────────────────────────────────
#     #  PATIENT VIEW
#     #  Mental health mode → hide raw diagnosis → show recommendation only
#     # ─────────────────────────────────────────────────────
#     def to_dict_patient(self):
#         base = {
#             "scan_id":            str(self.scan_id),
#             "image_type":         self.image_type.value,
#             "image_url":          self.image_url,
#             "mental_health_mode": self.mental_health_mode,
#             "created_at":         self.created_at.isoformat(),
#         }

#         if self.mental_health_mode:
#             # Patient sees recommendation only — no raw prediction
#             base["recommendation"] = (
#                 self.recommendation
#                 or "Your scan has been analyzed. Please consult your doctor for your results."
#             )
#         else:
#             # Patient sees full results
#             base["prediction"]    = self.prediction.value
#             base["confidence"]    = self.confidence
#             base["probabilities"] = {
#                 "benign":    self.prob_benign,
#                 "malignant": self.prob_malignant,
#                 "normal":    self.prob_normal,
#             }
#             base["recommendation"] = self.recommendation

#         return base

#     # ─────────────────────────────────────────────────────
#     #  DOCTOR VIEW
#     #  Always full results including segmentation if available
#     # ─────────────────────────────────────────────────────
#     def to_dict_doctor(self):
#         return {
#             "scan_id":             str(self.scan_id),
#             "patient_id":          str(self.patient_id),
#             "image_type":          self.image_type.value,
#             "image_url":           self.image_url,
#             "prediction":          self.prediction.value,
#             "confidence":          self.confidence,
#             "probabilities": {
#                 "benign":    self.prob_benign,
#                 "malignant": self.prob_malignant,
#                 "normal":    self.prob_normal,
#             },
#             "segmentation_url":    self.segmentation_url,
#             "segmentation_ready":  self.segmentation_url is not None,
#             "recommendation":      self.recommendation,
#             "mental_health_mode":  self.mental_health_mode,
#             "shared_with_doctor":  self.shared_with_doctor,
#             "model_version":       self.model_version,
#             "created_at":          self.created_at.isoformat(),
#         }

#     def to_dict(self):
#         return self.to_dict_doctor()


# # ══════════════════════════════════════════════════════════
# #  MULTIMODAL RESULT
# #  Created automatically when patient has uploaded BOTH
# #  ultrasound + mammogram scans.
# #  Linked to both scan records via foreign keys.
# # ══════════════════════════════════════════════════════════

# class MultimodalResult(db.Model):
#     __tablename__ = "multimodal_results"

#     id                   = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     patient_id           = db.Column(
#         db.UUID(as_uuid=True),
#         db.ForeignKey("users.user_id", ondelete="CASCADE"),
#         nullable=False
#     )

#     # The two scans that triggered this result
#     ultrasound_scan_id   = db.Column(
#         db.UUID(as_uuid=True),
#         db.ForeignKey("detection_scans.scan_id", ondelete="CASCADE"),
#         nullable=False
#     )
#     mammogram_scan_id    = db.Column(
#         db.UUID(as_uuid=True),
#         db.ForeignKey("detection_scans.scan_id", ondelete="CASCADE"),
#         nullable=False
#     )

#     # ── Multimodal classification ─────────────────────────
#     prediction           = db.Column(db.Enum(DetectionPrediction), nullable=True)
#     confidence           = db.Column(db.Float,                      nullable=True)
#     prob_benign          = db.Column(db.Float,                      nullable=True)
#     prob_malignant       = db.Column(db.Float,                      nullable=True)
#     prob_normal          = db.Column(db.Float,                      nullable=True)

#     # ── Recommendation ────────────────────────────────────
#     recommendation       = db.Column(db.Text, nullable=True)

#     model_version        = db.Column(db.String(50), nullable=False, default="multimodal_v1")
#     created_at           = db.Column(db.DateTime,   nullable=False, default=datetime.utcnow)

#     # ── Relationships ─────────────────────────────────────
#     patient           = db.relationship("User",          foreign_keys=[patient_id])
#     ultrasound_scan   = db.relationship("DetectionScan", foreign_keys=[ultrasound_scan_id])
#     mammogram_scan    = db.relationship("DetectionScan", foreign_keys=[mammogram_scan_id])

#     # ─────────────────────────────────────────────────────
#     #  PATIENT VIEW — respects mental health mode
#     # ─────────────────────────────────────────────────────
#     def to_dict_patient(self, mental_health_mode=False):
#         base = {
#             "multimodal_id": str(self.id),
#             "created_at":    self.created_at.isoformat(),
#         }

#         if mental_health_mode:
#             base["recommendation"] = (
#                 self.recommendation
#                 or "Your combined scan results are ready. Please consult your doctor."
#             )
#         else:
#             base["prediction"]    = self.prediction.value if self.prediction else None
#             base["confidence"]    = self.confidence
#             base["probabilities"] = {
#                 "benign":    self.prob_benign,
#                 "malignant": self.prob_malignant,
#                 "normal":    self.prob_normal,
#             }
#             base["recommendation"] = self.recommendation

#         return base

#     # ─────────────────────────────────────────────────────
#     #  DOCTOR VIEW — full results
#     # ─────────────────────────────────────────────────────
#     def to_dict_doctor(self):
#         return {
#             "multimodal_id":      str(self.id),
#             "patient_id":         str(self.patient_id),
#             "ultrasound_scan_id": str(self.ultrasound_scan_id),
#             "mammogram_scan_id":  str(self.mammogram_scan_id),
#             "prediction":         self.prediction.value if self.prediction else None,
#             "confidence":         self.confidence,
#             "probabilities": {
#                 "benign":    self.prob_benign,
#                 "malignant": self.prob_malignant,
#                 "normal":    self.prob_normal,
#             },
#             "recommendation":     self.recommendation,
#             "model_version":      self.model_version,
#             "created_at":         self.created_at.isoformat(),
#         }


import uuid
from datetime import datetime
from app import db
import enum


class DetectionImageType(enum.Enum):
    ultrasound = "ultrasound"
    mammogram  = "mammogram"


class DetectionPrediction(enum.Enum):
    benign    = "benign"
    malignant = "malignant"
    normal    = "normal"


class DetectionScan(db.Model):
    __tablename__ = "detection_scans"

    scan_id              = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id           = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    image_type           = db.Column(db.Enum(DetectionImageType), nullable=False)

    # ── Original image ────────────────────────────────────
    image_url            = db.Column(db.String(500), nullable=False)
    image_public_id      = db.Column(db.String(300), nullable=False)

    # ── Classification result ─────────────────────────────
    prediction           = db.Column(db.Enum(DetectionPrediction), nullable=False)
    confidence           = db.Column(db.Float,                      nullable=False)
    prob_benign          = db.Column(db.Float,                      nullable=False)
    prob_malignant       = db.Column(db.Float,                      nullable=False)
    prob_normal          = db.Column(db.Float,                      nullable=False)

    # ── Segmentation (on-demand, doctor only) ─────────────
    # Populated when doctor requests segmentation via POST /api/segmentation/<scan_id>
    # Cleared if doctor deletes it — can always be re-requested
    segmentation_url         = db.Column(db.String(500), nullable=True)
    segmentation_public_id   = db.Column(db.String(300), nullable=True)
    segmentation_confidence  = db.Column(db.Float,       nullable=True)  # mean confidence over tumor region

    # ── Recommendation ────────────────────────────────────
    recommendation       = db.Column(db.Text, nullable=True)

    # ── Flags ─────────────────────────────────────────────
    shared_with_doctor   = db.Column(db.Boolean, nullable=False, default=False)
    mental_health_mode   = db.Column(db.Boolean, nullable=False, default=False)

    model_version        = db.Column(db.String(50),  nullable=False)
    created_at           = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    patient = db.relationship("User", foreign_keys=[patient_id])

    # ─────────────────────────────────────────────────────
    #  PATIENT VIEW — respects mental health mode
    #  Never includes segmentation
    # ─────────────────────────────────────────────────────
    def to_dict_patient(self):
        base = {
            "scan_id":            str(self.scan_id),
            "image_type":         self.image_type.value,
            "image_url":          self.image_url,
            "mental_health_mode": self.mental_health_mode,
            "created_at":         self.created_at.isoformat(),
        }

        if self.mental_health_mode:
            base["recommendation"] = (
                self.recommendation
                or "Your scan has been analyzed. Please consult your doctor for your results."
            )
        else:
            base["prediction"]    = self.prediction.value
            base["confidence"]    = self.confidence
            base["probabilities"] = {
                "benign":    self.prob_benign,
                "malignant": self.prob_malignant,
                "normal":    self.prob_normal,
            }
            base["recommendation"] = self.recommendation

        return base

    # ─────────────────────────────────────────────────────
    #  DOCTOR VIEW — full results + segmentation status
    # ─────────────────────────────────────────────────────
    def to_dict_doctor(self):
        return {
            "scan_id":            str(self.scan_id),
            "patient_id":         str(self.patient_id),
            "image_type":         self.image_type.value,
            "image_url":          self.image_url,
            "prediction":         self.prediction.value,
            "confidence":         self.confidence,
            "probabilities": {
                "benign":    self.prob_benign,
                "malignant": self.prob_malignant,
                "normal":    self.prob_normal,
            },
            "recommendation":     self.recommendation,
            "mental_health_mode": self.mental_health_mode,
            "shared_with_doctor": self.shared_with_doctor,
            "model_version":      self.model_version,
            "created_at":         self.created_at.isoformat(),

            # Segmentation — None until doctor requests it
            "segmentation": {
                "ready":       self.segmentation_url is not None,
                "url":         self.segmentation_url,
                "confidence":  self.segmentation_confidence,
            },
        }

    def to_dict(self):
        return self.to_dict_doctor()


# ══════════════════════════════════════════════════════════
#  MULTIMODAL RESULT
# ══════════════════════════════════════════════════════════

class MultimodalResult(db.Model):
    __tablename__ = "multimodal_results"

    id                   = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id           = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    ultrasound_scan_id   = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("detection_scans.scan_id", ondelete="CASCADE"),
        nullable=False
    )
    mammogram_scan_id    = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("detection_scans.scan_id", ondelete="CASCADE"),
        nullable=False
    )
    prediction           = db.Column(db.Enum(DetectionPrediction), nullable=True)
    confidence           = db.Column(db.Float,                      nullable=True)
    prob_benign          = db.Column(db.Float,                      nullable=True)
    prob_malignant       = db.Column(db.Float,                      nullable=True)
    prob_normal          = db.Column(db.Float,                      nullable=True)
    recommendation       = db.Column(db.Text,                       nullable=True)
    model_version        = db.Column(db.String(50), nullable=False, default="multimodal_v1")
    created_at           = db.Column(db.DateTime,   nullable=False, default=datetime.utcnow)

    patient          = db.relationship("User",          foreign_keys=[patient_id])
    ultrasound_scan  = db.relationship("DetectionScan", foreign_keys=[ultrasound_scan_id])
    mammogram_scan   = db.relationship("DetectionScan", foreign_keys=[mammogram_scan_id])

    def to_dict_patient(self, mental_health_mode=False):
        base = {
            "multimodal_id": str(self.id),
            "created_at":    self.created_at.isoformat(),
        }
        if mental_health_mode:
            base["recommendation"] = (
                self.recommendation
                or "Your combined scan results are ready. Please consult your doctor."
            )
        else:
            base["prediction"]    = self.prediction.value if self.prediction else None
            base["confidence"]    = self.confidence
            base["probabilities"] = {
                "benign":    self.prob_benign,
                "malignant": self.prob_malignant,
                "normal":    self.prob_normal,
            }
            base["recommendation"] = self.recommendation
        return base

    def to_dict_doctor(self):
        return {
            "multimodal_id":      str(self.id),
            "patient_id":         str(self.patient_id),
            "ultrasound_scan_id": str(self.ultrasound_scan_id),
            "mammogram_scan_id":  str(self.mammogram_scan_id),
            "prediction":         self.prediction.value if self.prediction else None,
            "confidence":         self.confidence,
            "probabilities": {
                "benign":    self.prob_benign,
                "malignant": self.prob_malignant,
                "normal":    self.prob_normal,
            },
            "recommendation":  self.recommendation,
            "model_version":   self.model_version,
            "created_at":      self.created_at.isoformat(),
        }