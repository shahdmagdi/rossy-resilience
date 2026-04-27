import os
import tempfile
from app import db
from models import User, UserRole, Patient
from models.mri_scan import MriScan, TumorStage
from services.mri_ml_service import predict_mri
from services.cloudinary_service import (
    validate_mri_file,
    upload_mri_file,
    delete_mri_file,
)
from flask_jwt_extended import get_jwt_identity


# ══════════════════════════════════════════════════════════
#  UPLOAD MRI — DOCTOR ONLY
#  Doctor uploads 3 NIfTI files for their assigned patient.
#  acq0 and acq2 are required — acq1 is optional.
#  Files are uploaded to Supabase first; their public URLs
#  are then passed to the HF Space for inference.
#  Results shown to doctor only — never to patient.
# ══════════════════════════════════════════════════════════

def upload_mri(acq0_file, acq2_file, patient_id, acq1_file=None):
    """
    Validates and uploads NIfTI files to Supabase, then calls the
    MRI staging model via the stored public URLs, and saves results.

    Args:
        acq0_file  (FileStorage): required NIfTI acquisition 0
        acq2_file  (FileStorage): required NIfTI acquisition 2
        patient_id (str):         patient's user_id
        acq1_file  (FileStorage): optional NIfTI acquisition 1

    Returns: (response_dict, http_status_code)
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    # 1. Doctor only
    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    # 2. Patient must be assigned to this doctor
    patient = Patient.query.get(patient_id)
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "This patient is not assigned to you."}, 403

    # 3. Validate required files
    for label, file in [("acq0", acq0_file), ("acq2", acq2_file)]:
        is_valid, error_msg = validate_mri_file(file)
        if not is_valid:
            return {"success": False, "message": f"{label}: {error_msg}"}, 400

    # 4. Validate optional acq1
    if acq1_file:
        is_valid, error_msg = validate_mri_file(acq1_file)
        if not is_valid:
            return {"success": False, "message": f"acq1: {error_msg}"}, 400

    acq0_url = acq0_path = None
    acq1_url = acq1_path = None
    acq2_url = acq2_path = None

    try:
        # 5. Upload NIfTI files to Supabase — get back public URLs + storage paths
        acq0_url, acq0_path = upload_mri_file(acq0_file, patient_id, "acq0")
        acq2_url, acq2_path = upload_mri_file(acq2_file, patient_id, "acq2")

        if acq1_file:
            acq1_url, acq1_path = upload_mri_file(acq1_file, patient_id, "acq1")

        # 6. Call MRI staging model — pass public URLs instead of temp file paths.
        #    The HF Space downloads the files itself using these URLs.
        mri_result = predict_mri(
            acq0_url  = acq0_url,
            acq2_url  = acq2_url,
            acq1_url  = acq1_url,   # None if not uploaded
        )

        # 7. Parse T_stage — None means no tumor detected
        t_stage_value = mri_result.get("t_stage")
        t_stage       = TumorStage(t_stage_value) if t_stage_value else None

        # 8. Save to mri_scans table
        scan = MriScan(
            patient_id               = patient_id,
            doctor_id                = user_id,
            acq0_url                 = acq0_url,
            acq0_storage_path        = acq0_path,
            acq1_url                 = acq1_url,
            acq1_storage_path        = acq1_path,
            acq2_url                 = acq2_url,
            acq2_storage_path        = acq2_path,
            t_stage                  = t_stage,
            size_cm                  = mri_result.get("size_cm"),
            volume_cc                = mri_result.get("volume_cc"),
            segmentation_consistency = mri_result.get("segmentation_consistency"),
            uncertainty_mean         = mri_result.get("uncertainty_mean"),
            model_version            = mri_result.get("model_version"),
        )
        db.session.add(scan)
        db.session.commit()

        patient_user = User.query.get(patient_id)

        return {
            "success":  True,
            "message":  f"MRI scan uploaded and analyzed for {patient_user.full_name}.",
            "scan":     scan.to_dict_doctor(),
            "note":     "MRI results are visible to you only — not shown to the patient.",
        }, 201

    except NotImplementedError as e:
        return {"success": False, "message": str(e)}, 503

    except ValueError as e:
        return {"success": False, "message": str(e)}, 422

    except Exception as e:
        db.session.rollback()
        # If files were already uploaded to Supabase, clean them up
        for path in [acq0_path, acq1_path, acq2_path]:
            if path:
                try:
                    delete_mri_file(path)
                except Exception:
                    pass
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


# ══════════════════════════════════════════════════════════
#  GET MRI HISTORY — DOCTOR
# ══════════════════════════════════════════════════════════

def get_patient_mri_history(patient_id):
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    patient = Patient.query.get(patient_id)
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "This patient is not assigned to you."}, 403

    try:
        scans        = MriScan.query.filter_by(patient_id=patient_id).order_by(MriScan.created_at.desc()).all()
        patient_user = User.query.get(patient_id)

        return {
            "success": True,
            "patient": {
                "patient_id": patient_id,
                "full_name":  patient_user.full_name,
            },
            "total": len(scans),
            "scans": [s.to_dict_doctor() for s in scans],
        }, 200

    except Exception as e:
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


# ══════════════════════════════════════════════════════════
#  GET SINGLE MRI SCAN — DOCTOR
# ══════════════════════════════════════════════════════════

def get_mri_scan(scan_id):
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    scan = MriScan.query.get(scan_id)
    if not scan:
        return {"success": False, "message": "MRI scan not found."}, 404

    patient = Patient.query.get(str(scan.patient_id))
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "Access denied."}, 403

    patient_user = User.query.get(str(scan.patient_id))

    return {
        "success": True,
        "patient": {
            "patient_id": str(scan.patient_id),
            "full_name":  patient_user.full_name,
        },
        "scan": scan.to_dict_doctor(),
    }, 200


# ══════════════════════════════════════════════════════════
#  DELETE MRI SCAN — DOCTOR
#  Removes scan from DB + all NIfTI files from Supabase
# ══════════════════════════════════════════════════════════

def delete_mri_scan(scan_id):
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    scan = MriScan.query.get(scan_id)
    if not scan:
        return {"success": False, "message": "MRI scan not found."}, 404

    patient = Patient.query.get(str(scan.patient_id))
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "Access denied."}, 403

    try:
        delete_mri_file(scan.acq0_storage_path)
        delete_mri_file(scan.acq2_storage_path)
        if scan.acq1_storage_path:
            delete_mri_file(scan.acq1_storage_path)

        db.session.delete(scan)
        db.session.commit()

        return {"success": True, "message": "MRI scan deleted successfully."}, 200

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500