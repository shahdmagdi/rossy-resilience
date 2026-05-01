from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from models import User, UserRole
from models.patient import Patient


# ══════════════════════════════════════════════════════════
#  CONSENT REQUIRED DECORATOR
#
#  Applies to any route that requires patient consent.
#  Returns a specific 403 with consent_required: true
#  so the frontend knows to redirect to the consent page.
#
#  Does NOT affect:
#    - Auth routes (signup, login, verify)
#    - Doctor routes (MRI upload, patient view)
#    - Admin routes
#    - Scan upload itself (patient chooses to upload)
#
#  DOES affect:
#    - Doctor viewing patient detection scans
#    - Doctor requesting segmentation
#    - Any future feature requiring explicit patient consent
# ══════════════════════════════════════════════════════════

def consent_required(f):
    """
    Checks that the patient has given app-level consent.

    For patient routes → checks the requesting patient's own consent.
    For doctor routes  → checks the target patient's consent.

    The route must pass patient_id as a URL param OR
    the service resolves it from the scan/resource being accessed.

    Usage — on routes where consent is needed:
        @detection_bp.route("/patient/<string:patient_id>")
        @jwt_required_middleware
        @consent_required_for_patient("patient_id")   ← see below
        def get_patient_scans(patient_id): ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        user    = User.query.get(user_id)

        if user.role == UserRole.patient:
            # Patient accessing their own data — check their own consent
            patient = Patient.query.get(user_id)
            if not patient or not patient.app_consent:
                return jsonify({
                    "success":          False,
                    "consent_required": True,
                    "message":          "You need to accept the terms and give consent before using this feature.",
                }), 403

        return f(*args, **kwargs)
    return decorated


def doctor_patient_consent_required(patient_id_param="patient_id"):
    """
    Decorator factory for doctor routes.
    Checks the TARGET patient's consent (not the doctor's).

    Usage:
        @mri_bp.route("/upload/<string:patient_id>")
        @jwt_required_middleware
        @doctor_patient_consent_required("patient_id")
        def upload_mri_scan(patient_id): ...

    Args:
        patient_id_param (str): name of the URL param containing patient_id
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            patient_id = kwargs.get(patient_id_param)
            if not patient_id:
                return f(*args, **kwargs)   # no patient_id — skip check

            patient = Patient.query.get(patient_id)
            if not patient or not patient.app_consent:
                return jsonify({
                    "success":          False,
                    "consent_required": True,
                    "message":          "This patient has not given consent to share their data. "
                                        "Please ask them to accept the consent in their app.",
                }), 403

            return f(*args, **kwargs)
        return decorated
    return decorator