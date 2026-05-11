# import os
# import tempfile
# from datetime import date
# from app import db
# from models import User, UserRole, Patient
# from models.detection_scan import DetectionScan, MultimodalResult, DetectionImageType, DetectionPrediction
# from services.ml_service import predict_detection, predict_multimodal, get_recommendation
# from services.cloudinary_service import validate_scan_image, upload_scan_image, delete_scan_image
# from flask_jwt_extended import get_jwt_identity

# VALID_IMAGE_TYPES = [t.value for t in DetectionImageType]


# # ══════════════════════════════════════════════════════════
# #  HELPERS
# # ══════════════════════════════════════════════════════════

# def _save_temp_file(file):
#     """Saves uploaded file to a temp path. Returns path."""
#     suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
#     tmp    = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
#     file.save(tmp)
#     tmp.close()
#     return tmp.name


# def _get_patient_age(user):
#     """Calculates age in years from user.date_of_birth. Returns 50 as safe default."""
#     if not user.date_of_birth:
#         return 50  # safe clinical default if DOB not set
#     today = date.today()
#     dob   = user.date_of_birth
#     return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# def _check_and_run_multimodal(patient_id, new_scan, new_scan_tmp_path):
#     """
#     After a new scan is saved, checks if the patient now has BOTH
#     ultrasound + mammogram. If yes, runs the multimodal model and
#     creates a MultimodalResult linked to both scans.

#     Called internally — never blocks the main upload flow.
#     Failures are caught and logged silently.
#     """
#     try:
#         # Find the complementary scan type
#         other_type = (
#             DetectionImageType.mammogram
#             if new_scan.image_type == DetectionImageType.ultrasound
#             else DetectionImageType.ultrasound
#         )

#         other_scan = (
#             DetectionScan.query
#             .filter_by(patient_id=patient_id)
#             .filter(DetectionScan.image_type == other_type)
#             .order_by(DetectionScan.created_at.desc())
#             .first()
#         )

#         if not other_scan:
#             return   # patient doesn't have both scan types yet

#         # Determine which is ultrasound and which is mammogram
#         if new_scan.image_type == DetectionImageType.ultrasound:
#             us_path    = new_scan_tmp_path
#             mm_path    = other_scan.image_url   # Cloudinary URL of existing mammogram
#             us_scan_id = new_scan.scan_id
#             mm_scan_id = other_scan.scan_id
#         else:
#             us_path    = other_scan.image_url   # Cloudinary URL of existing ultrasound
#             mm_path    = new_scan_tmp_path
#             us_scan_id = other_scan.scan_id
#             mm_scan_id = new_scan.scan_id

#         # Run multimodal model — returns None if space not ready
#         multimodal = predict_multimodal(us_path, mm_path)
#         if not multimodal:
#             return   # multimodal space not configured yet — skip silently

#         # Get patient age from date_of_birth for recommendation
#         patient_user  = User.query.get(str(patient_id))
#         age           = _get_patient_age(patient_user)
#         probabilities = multimodal["probabilities"]

#         # Compute recommendation using multimodal modality weight (0.95)
#         rec_result = get_recommendation(
#             modality        = "multimodal",
#             age             = age,
#             predicted_label = multimodal["predicted_class"],
#             p_normal        = probabilities["normal"]    / 100,
#             p_benign        = probabilities["benign"]    / 100,
#             p_malignant     = probabilities["malignant"] / 100,
#             confidence      = multimodal["confidence"]   / 100,
#         )
#         recommendation = rec_result["recommendation"]

#         mm_result = MultimodalResult(
#             patient_id         = patient_id,
#             ultrasound_scan_id = us_scan_id,
#             mammogram_scan_id  = mm_scan_id,
#             prediction         = DetectionPrediction(multimodal["predicted_class"]),
#             confidence         = multimodal["confidence"],
#             prob_benign        = probabilities["benign"],
#             prob_malignant     = probabilities["malignant"],
#             prob_normal        = probabilities["normal"],
#             recommendation     = recommendation,
#             model_version      = multimodal["model_version"],
#         )
#         db.session.add(mm_result)
#         db.session.commit()

#         print(f"[detection_service] Multimodal result created for patient {patient_id}")

#     except Exception as e:
#         db.session.rollback()
#         print(f"[detection_service] Multimodal check failed (non-blocking): {e}")


# # ══════════════════════════════════════════════════════════
# #  CORE UPLOAD PIPELINE
# #  Used by both upload_scan and upload_scan_with_doctor
# # ══════════════════════════════════════════════════════════

# def _run_detection_pipeline(file, image_type, user_id, shared_with_doctor=False):
#     """
#     Core pipeline:
#         1. Validate image type and file
#         2. Save to temp file
#         3. Run classification (routes to correct HF Space)
#         4. Generate recommendation
#         5. Upload original image to Cloudinary
#         6. Save result to detection_scans table
#         7. Check if multimodal should run (has both scan types now?)

#     Args:
#         file               (FileStorage): uploaded image
#         image_type         (str):         "ultrasound" or "mammogram"
#         user_id            (str):         patient user_id
#         shared_with_doctor (bool):        True = doctor can view results

#     Returns: (response_dict, http_status_code)
#     """

#     # 1. Validate image type
#     if image_type not in VALID_IMAGE_TYPES:
#         return {
#             "success": False,
#             "message": f"Invalid image_type. Must be one of: {', '.join(VALID_IMAGE_TYPES)}."
#         }, 400

#     # 2. Validate file
#     is_valid, error_msg = validate_scan_image(file)
#     if not is_valid:
#         return {"success": False, "message": error_msg}, 400

#     tmp_path = None

#     try:
#         # 3. Save to temp file for HF Space
#         tmp_path = _save_temp_file(file)

#         # 4. Run classification — routes to correct HF Space
#         result = predict_detection(tmp_path, image_type)

#         # 5. Get patient age from date_of_birth for recommendation
#         patient_user  = User.query.get(user_id)
#         age           = _get_patient_age(patient_user)
#         probabilities = result["probabilities"]

#         # 6. Compute recommendation using the new risk-based system
#         rec_result = get_recommendation(
#             modality        = image_type,
#             age             = age,
#             predicted_label = result["predicted_class"],
#             p_normal        = probabilities["normal"]    / 100,
#             p_benign        = probabilities["benign"]    / 100,
#             p_malignant     = probabilities["malignant"] / 100,
#             confidence      = result["confidence"]       / 100,
#         )
#         recommendation = rec_result["recommendation"]

#         # 7. Upload original image to Cloudinary
#         file.seek(0)
#         image_url, public_id = upload_scan_image(file, user_id, image_type)

#         # 8. Snapshot mental_health_mode at upload time
#         patient            = Patient.query.get(user_id)
#         mental_health_mode = patient.mental_health_mode

#         # 9. Save to detection_scans table
#         scan = DetectionScan(
#             patient_id         = user_id,
#             image_type         = DetectionImageType(image_type),
#             image_url          = image_url,
#             image_public_id    = public_id,
#             prediction         = DetectionPrediction(result["predicted_class"]),
#             confidence         = result["confidence"],
#             prob_benign        = probabilities["benign"],
#             prob_malignant     = probabilities["malignant"],
#             prob_normal        = probabilities["normal"],
#             recommendation     = recommendation,
#             shared_with_doctor = shared_with_doctor,
#             mental_health_mode = mental_health_mode,
#             model_version      = result["model_version"],
#         )
#         db.session.add(scan)
#         db.session.commit()

#         # 10. Check if multimodal should run (non-blocking)
#         _check_and_run_multimodal(user_id, scan, tmp_path)

#         return {
#             "success":   True,
#             "message":   f"{image_type.capitalize()} scan analyzed successfully.",
#             "diagnosis": scan.to_dict_patient(),   # respects mental health mode
#         }, 201

#     except NotImplementedError as e:
#         return {"success": False, "message": str(e)}, 503

#     except Exception as e:
#         db.session.rollback()
#         return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500

#     finally:
#         if tmp_path and os.path.exists(tmp_path):
#             os.remove(tmp_path)


# # ══════════════════════════════════════════════════════════
# #  UPLOAD SCAN — ANY PATIENT
# #  No doctor assignment required
# # ══════════════════════════════════════════════════════════

# def upload_scan(file, image_type):
#     """
#     Any verified patient can upload ultrasound or mammogram.
#     Results are private — no doctor can view them.

#     Routes:
#         ultrasound → HF_ULTRASOUND_URL space
#         mammogram  → HF_MAMMOGRAM_URL space
#         both exist → multimodal triggered automatically
#     """
#     user_id = get_jwt_identity()
#     user    = User.query.get(user_id)

#     if user.role != UserRole.patient:
#         return {"success": False, "message": "Access denied. Patients only."}, 403

#     response, status = _run_detection_pipeline(
#         file, image_type, user_id, shared_with_doctor=False
#     )
#     return response, status


# # ══════════════════════════════════════════════════════════
# #  UPLOAD SCAN WITH DOCTOR — ASSIGNED PATIENTS ONLY
# #  Patient must have an assigned doctor.
# #  Doctor will be able to view the results.
# # ══════════════════════════════════════════════════════════

# def upload_scan_with_doctor(file, image_type):
#     """
#     Only patients with an assigned doctor can use this endpoint.
#     Results are shared — doctor can view full diagnosis + segmentation.

#     Routes:
#         ultrasound → HF_ULTRASOUND_URL space
#         mammogram  → HF_MAMMOGRAM_URL space
#         both exist → multimodal triggered automatically
#     """
#     user_id = get_jwt_identity()
#     user    = User.query.get(user_id)

#     if user.role != UserRole.patient:
#         return {"success": False, "message": "Access denied. Patients only."}, 403

#     # Must have an assigned doctor
#     patient = Patient.query.get(user_id)
#     if not patient.current_assigned_doctor_id:
#         return {
#             "success": False,
#             "message": "You must have an assigned doctor to use this endpoint. "
#                        "Please request a doctor assignment first."
#         }, 403

#     response, status = _run_detection_pipeline(
#         file, image_type, user_id, shared_with_doctor=True
#     )

#     # On success add doctor info to response
#     if status == 201:
#         doctor_user = User.query.get(str(patient.current_assigned_doctor_id))
#         if doctor_user:
#             response["assigned_doctor"] = {
#                 "doctor_id": str(patient.current_assigned_doctor_id),
#                 "full_name": doctor_user.full_name,
#             }
#             response["note"] = (
#                 f"Dr. {doctor_user.full_name} can now view your full results."
#             )

#     return response, status


# # ══════════════════════════════════════════════════════════
# #  GET SCAN HISTORY — PATIENT
# # ══════════════════════════════════════════════════════════

# def get_my_scan_history(image_type=None):
#     """
#     Patient views their full detection scan history.
#     Results respect mental_health_mode per scan.
#     Optional filter: ?type=ultrasound or ?type=mammogram
#     """
#     user_id = get_jwt_identity()
#     user    = User.query.get(user_id)

#     if user.role != UserRole.patient:
#         return {"success": False, "message": "Access denied. Patients only."}, 403

#     try:
#         query = DetectionScan.query.filter_by(patient_id=user_id)

#         if image_type:
#             if image_type not in VALID_IMAGE_TYPES:
#                 return {
#                     "success": False,
#                     "message": f"Invalid type. Must be: {', '.join(VALID_IMAGE_TYPES)}."
#                 }, 400
#             query = query.filter_by(image_type=DetectionImageType(image_type))

#         scans = query.order_by(DetectionScan.created_at.desc()).all()

#         # Group by type for frontend tabs
#         grouped = {}
#         for scan in scans:
#             t = scan.image_type.value
#             if t not in grouped:
#                 grouped[t] = []
#             grouped[t].append(scan.to_dict_patient())

#         # Also fetch multimodal results for this patient
#         multimodal_results = (
#             MultimodalResult.query
#             .filter_by(patient_id=user_id)
#             .order_by(MultimodalResult.created_at.desc())
#             .all()
#         )

#         # Use the patient's current mental_health_mode for multimodal
#         patient            = Patient.query.get(user_id)
#         mental_health_mode = patient.mental_health_mode

#         return {
#             "success":   True,
#             "total":     len(scans),
#             "history":   [s.to_dict_patient() for s in scans],
#             "by_type":   grouped,
#             "multimodal": [
#                 m.to_dict_patient(mental_health_mode)
#                 for m in multimodal_results
#             ],
#         }, 200

#     except Exception as e:
#         return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


# # ══════════════════════════════════════════════════════════
# #  GET SINGLE SCAN — PATIENT OR DOCTOR
# # ══════════════════════════════════════════════════════════

# def get_scan_by_id(scan_id):
#     """
#     Patient → to_dict_patient() — respects mental health mode
#     Doctor  → to_dict_doctor()  — full results including segmentation
#     """
#     user_id = get_jwt_identity()
#     user    = User.query.get(user_id)

#     scan = DetectionScan.query.get(scan_id)
#     if not scan:
#         return {"success": False, "message": "Scan not found."}, 404

#     if user.role == UserRole.patient:
#         if str(scan.patient_id) != user_id:
#             return {"success": False, "message": "Access denied."}, 403
#         return {"success": True, "scan": scan.to_dict_patient()}, 200

#     if user.role == UserRole.doctor:
#         patient = Patient.query.get(str(scan.patient_id))
#         if not patient or str(patient.current_assigned_doctor_id) != user_id:
#             return {"success": False, "message": "Access denied."}, 403
#         if not scan.shared_with_doctor:
#             return {"success": False, "message": "This scan was not shared with a doctor."}, 403
#         return {"success": True, "scan": scan.to_dict_doctor()}, 200

#     return {"success": False, "message": "Access denied."}, 403


# # ══════════════════════════════════════════════════════════
# #  GET PATIENT SCANS — DOCTOR VIEW
# # ══════════════════════════════════════════════════════════

# def get_patient_scans(patient_id, image_type=None):
#     """
#     Doctor views all shared detection scans of their assigned patient.
#     Includes multimodal results.
#     Optional filter: ?type=ultrasound or ?type=mammogram
#     """
#     user_id = get_jwt_identity()
#     user    = User.query.get(user_id)

#     if user.role != UserRole.doctor:
#         return {"success": False, "message": "Access denied. Doctors only."}, 403

#     patient = Patient.query.get(patient_id)
#     if not patient or str(patient.current_assigned_doctor_id) != user_id:
#         return {"success": False, "message": "This patient is not assigned to you."}, 403

#     try:
#         # Doctor only sees scans shared with them
#         query = DetectionScan.query.filter_by(
#             patient_id         = patient_id,
#             shared_with_doctor = True,
#         )

#         if image_type:
#             if image_type not in VALID_IMAGE_TYPES:
#                 return {
#                     "success": False,
#                     "message": f"Invalid type. Must be: {', '.join(VALID_IMAGE_TYPES)}."
#                 }, 400
#             query = query.filter_by(image_type=DetectionImageType(image_type))

#         scans        = query.order_by(DetectionScan.created_at.desc()).all()
#         patient_user = User.query.get(patient_id)

#         grouped = {}
#         for scan in scans:
#             t = scan.image_type.value
#             if t not in grouped:
#                 grouped[t] = []
#             grouped[t].append(scan.to_dict_doctor())

#         # Multimodal results for this patient
#         multimodal_results = (
#             MultimodalResult.query
#             .filter_by(patient_id=patient_id)
#             .order_by(MultimodalResult.created_at.desc())
#             .all()
#         )

#         return {
#             "success": True,
#             "patient": {
#                 "patient_id": patient_id,
#                 "full_name":  patient_user.full_name,
#                 "email":      patient_user.email,
#             },
#             "total":      len(scans),
#             "scans":      [s.to_dict_doctor() for s in scans],
#             "by_type":    grouped,
#             "multimodal": [m.to_dict_doctor() for m in multimodal_results],
#         }, 200

#     except Exception as e:
#         return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


# # ══════════════════════════════════════════════════════════
# #  DELETE SCAN — PATIENT
# # ══════════════════════════════════════════════════════════

# def delete_scan(scan_id):
#     """Patient deletes their own scan + removes from Cloudinary."""
#     user_id = get_jwt_identity()
#     user    = User.query.get(user_id)

#     if user.role != UserRole.patient:
#         return {"success": False, "message": "Access denied. Patients only."}, 403

#     scan = DetectionScan.query.filter_by(
#         scan_id    = scan_id,
#         patient_id = user_id,
#     ).first()

#     if not scan:
#         return {"success": False, "message": "Scan not found."}, 404

#     try:
#         delete_scan_image(scan.image_public_id)
#         if scan.segmentation_public_id:
#             delete_scan_image(scan.segmentation_public_id)
#         db.session.delete(scan)
#         db.session.commit()
#         return {"success": True, "message": "Scan deleted successfully."}, 200

#     except Exception as e:
#         db.session.rollback()
#         return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500





import os
import tempfile
from datetime import date
from app import db
from models import User, UserRole, Patient
from models.detection_scan import DetectionScan, MultimodalResult, DetectionImageType, DetectionPrediction
from services.ml_service import predict_detection, predict_multimodal, get_recommendation
from services.cloudinary_service import validate_scan_image, upload_scan_image, delete_scan_image
from flask_jwt_extended import get_jwt_identity

VALID_IMAGE_TYPES = [t.value for t in DetectionImageType]


# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════

def _save_temp_file(file):
    """Saves uploaded file to a temp path. Returns path."""
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower()
    tmp    = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    file.save(tmp)
    tmp.close()
    return tmp.name


def _get_patient_age(user):
    """Calculates age in years from user.date_of_birth. Returns 50 as safe default."""
    if not user.date_of_birth:
        return 50
    today = date.today()
    dob   = user.date_of_birth
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _cleanup(*paths):
    """Removes temp files safely — ignores missing files."""
    for path in paths:
        if path and os.path.exists(path):
            os.remove(path)


# ══════════════════════════════════════════════════════════
#  CORE SINGLE-MODALITY PIPELINE
#  Used by upload_scan and upload_scan_with_doctor
# ══════════════════════════════════════════════════════════

def _run_detection_pipeline(file, image_type, user_id, shared_with_doctor=False):
    """
    Single-modality pipeline:
        1. Validate image type and file
        2. Save to temp file
        3. Run single-modality classification
        4. Generate recommendation
        5. Upload image to Cloudinary
        6. Save DetectionScan to DB

    Returns: (response_dict, http_status_code)
    """
    if image_type not in VALID_IMAGE_TYPES:
        return {
            "success": False,
            "message": f"Invalid image_type. Must be one of: {', '.join(VALID_IMAGE_TYPES)}."
        }, 400

    is_valid, error_msg = validate_scan_image(file)
    if not is_valid:
        return {"success": False, "message": error_msg}, 400

    tmp_path = None

    try:
        tmp_path = _save_temp_file(file)

        result        = predict_detection(tmp_path, image_type)
        patient_user  = User.query.get(user_id)
        age           = _get_patient_age(patient_user)
        probabilities = result["probabilities"]

        rec_result = get_recommendation(
            modality        = image_type,
            age             = age,
            predicted_label = result["predicted_class"],
            p_normal        = probabilities["normal"]    / 100,
            p_benign        = probabilities["benign"]    / 100,
            p_malignant     = probabilities["malignant"] / 100,
            confidence      = result["confidence"]       / 100,
        )
        recommendation = rec_result["recommendation"]

        file.seek(0)
        image_url, public_id = upload_scan_image(file, user_id, image_type)

        patient            = Patient.query.get(user_id)
        mental_health_mode = patient.mental_health_mode

        scan = DetectionScan(
            patient_id         = user_id,
            image_type         = DetectionImageType(image_type),
            image_url          = image_url,
            image_public_id    = public_id,
            prediction         = DetectionPrediction(result["predicted_class"]),
            confidence         = result["confidence"],
            prob_benign        = probabilities["benign"],
            prob_malignant     = probabilities["malignant"],
            prob_normal        = probabilities["normal"],
            recommendation     = recommendation,
            shared_with_doctor = shared_with_doctor,
            mental_health_mode = mental_health_mode,
            model_version      = result["model_version"],
        )
        db.session.add(scan)
        db.session.commit()

        return {
            "success":   True,
            "message":   f"{image_type.capitalize()} scan analyzed successfully.",
            "diagnosis": scan.to_dict_patient(),
        }, 201

    except NotImplementedError as e:
        return {"success": False, "message": str(e)}, 503

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500

    finally:
        _cleanup(tmp_path)


def _run_multimodal_pipeline(
    ultrasound_file,
    mammogram_file,
    user_id,
    shared_with_doctor=False,
):
    """
    Runs ONLY the multimodal fusion model using both ultrasound and mammogram.
    Does NOT run or save separate ultrasound and mammogram DetectionScan records.

    Flow:
        1. Validate both files
        2. Save both to temp files
        3. Run multimodal model only
        4. Generate recommendation
        5. Upload both images to Cloudinary
        6. Save one MultimodalResult row
        7. Commit atomically
    """

    # ── Validate both files ──────────────────────────────
    for file, label in [
        (ultrasound_file, "ultrasound"),
        (mammogram_file, "mammogram"),
    ]:
        is_valid, error_msg = validate_scan_image(file)
        if not is_valid:
            return {
                "success": False,
                "message": f"{label} image: {error_msg}"
            }, 400

    us_tmp = None
    mm_tmp = None
    us_pub_id = None
    mm_pub_id = None

    try:
        # ── Save temp files ──────────────────────────────
        us_tmp = _save_temp_file(ultrasound_file)
        mm_tmp = _save_temp_file(mammogram_file)

        patient_user = User.query.get(user_id)
        age = _get_patient_age(patient_user)

        patient = Patient.query.get(user_id)
        mental_health_mode = patient.mental_health_mode

        # ── Run multimodal model ONLY ────────────────────
        # Signature: predict_multimodal(mammogram_path, ultrasound_path)
        multi_result = predict_multimodal(mm_tmp, us_tmp)

        if not multi_result:
            return {
                "success": False,
                "message": (
                    "Multimodal model is not configured yet. "
                    "Set HF_MULTIMODAL_URL in environment variables."
                ),
            }, 503

        multi_probs = multi_result["probabilities"]

        multi_rec = get_recommendation(
            modality="multimodal",
            age=age,
            predicted_label=multi_result["predicted_class"],
            p_normal=multi_probs["normal"] / 100,
            p_benign=multi_probs["benign"] / 100,
            p_malignant=multi_probs["malignant"] / 100,
            confidence=multi_result["confidence"] / 100,
        )["recommendation"]

        # ── Upload both images to Cloudinary ─────────────
        ultrasound_file.seek(0)
        mammogram_file.seek(0)

        us_url, us_pub_id = upload_scan_image(
            ultrasound_file,
            user_id,
            "ultrasound"
        )

        mm_url, mm_pub_id = upload_scan_image(
            mammogram_file,
            user_id,
            "mammogram"
        )

        # ── Save only MultimodalResult ───────────────────
        multimodal_record = MultimodalResult(
            patient_id=user_id,

            # No linked DetectionScan rows
            ultrasound_scan_id=None,
            mammogram_scan_id=None,

            # Store uploaded image URLs directly
            ultrasound_image_url=us_url,
            ultrasound_image_public_id=us_pub_id,
            mammogram_image_url=mm_url,
            mammogram_image_public_id=mm_pub_id,

            prediction=DetectionPrediction(
                multi_result["predicted_class"]
            ),
            confidence=multi_result["confidence"],

            prob_benign=multi_probs["benign"],
            prob_malignant=multi_probs["malignant"],
            prob_normal=multi_probs["normal"],

            recommendation=multi_rec,
            model_version=multi_result["model_version"],
            shared_with_doctor=shared_with_doctor,
            mental_health_mode=mental_health_mode,
        )

        db.session.add(multimodal_record)
        db.session.commit()

        return {
            "success": True,
            "message": "Multimodal scan analyzed successfully.",
            "multimodal": multimodal_record.to_dict_patient(
                mental_health_mode
            ),
        }, 201

    except NotImplementedError as e:
        db.session.rollback()
        return {
            "success": False,
            "message": str(e)
        }, 503

    except Exception as e:
        db.session.rollback()

        # Cleanup uploaded images if DB save fails
        if us_pub_id:
            delete_scan_image(us_pub_id)
        if mm_pub_id:
            delete_scan_image(mm_pub_id)

        return {
            "success": False,
            "message": "Something went wrong.",
            "error": str(e),
        }, 500

    finally:
        _cleanup(us_tmp, mm_tmp)
# ══════════════════════════════════════════════════════════
#  UPLOAD SCAN — ANY PATIENT (single modality)
# ══════════════════════════════════════════════════════════

def upload_scan(file, image_type):
    """Any verified patient — results private."""
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.patient:
        return {"success": False, "message": "Access denied. Patients only."}, 403

    return _run_detection_pipeline(file, image_type, user_id, shared_with_doctor=False)


# ══════════════════════════════════════════════════════════
#  UPLOAD SCAN WITH DOCTOR — ASSIGNED PATIENTS (single modality)
# ══════════════════════════════════════════════════════════

def upload_scan_with_doctor(file, image_type):
    """Assigned patients only — doctor can view results."""
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.patient:
        return {"success": False, "message": "Access denied. Patients only."}, 403

    patient = Patient.query.get(user_id)
    if not patient.current_assigned_doctor_id:
        return {
            "success": False,
            "message": "You must have an assigned doctor to use this endpoint."
        }, 403

    response, status = _run_detection_pipeline(
        file, image_type, user_id, shared_with_doctor=True
    )

    if status == 201:
        doctor_user = User.query.get(str(patient.current_assigned_doctor_id))
        if doctor_user:
            response["assigned_doctor"] = {
                "doctor_id": str(patient.current_assigned_doctor_id),
                "full_name": doctor_user.full_name,
            }
            response["note"] = f"Dr. {doctor_user.full_name} can now view your full results."

    return response, status


# ══════════════════════════════════════════════════════════
#  UPLOAD MULTIMODAL — ANY PATIENT
#  Both images in one request — private results
# ══════════════════════════════════════════════════════════

def upload_multimodal_scan(ultrasound_file, mammogram_file):
    """
    Patient uploads ultrasound + mammogram at once.
    Runs all three models and returns all three results.
    Results are private — no doctor access.
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.patient:
        return {"success": False, "message": "Access denied. Patients only."}, 403

    return _run_multimodal_pipeline(
        ultrasound_file, mammogram_file, user_id, shared_with_doctor=False
    )


# ══════════════════════════════════════════════════════════
#  UPLOAD MULTIMODAL WITH DOCTOR — ASSIGNED PATIENTS
#  Both images in one request — doctor can view results
# ══════════════════════════════════════════════════════════

def upload_multimodal_scan_with_doctor(ultrasound_file, mammogram_file):
    """
    Assigned patients only.
    Runs all three models and shares all results with doctor.
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.patient:
        return {"success": False, "message": "Access denied. Patients only."}, 403

    patient = Patient.query.get(user_id)
    if not patient.current_assigned_doctor_id:
        return {
            "success": False,
            "message": "You must have an assigned doctor to use this endpoint."
        }, 403

    response, status = _run_multimodal_pipeline(
        ultrasound_file, mammogram_file, user_id, shared_with_doctor=True
    )

    if status == 201:
        doctor_user = User.query.get(str(patient.current_assigned_doctor_id))
        if doctor_user:
            response["assigned_doctor"] = {
                "doctor_id": str(patient.current_assigned_doctor_id),
                "full_name": doctor_user.full_name,
            }
            response["note"] = f"Dr. {doctor_user.full_name} can now view your full results."

    return response, status


# ══════════════════════════════════════════════════════════
#  GET SCAN HISTORY — PATIENT
# ══════════════════════════════════════════════════════════

def get_my_scan_history(image_type=None):
    """
    Patient views full detection history.
    Optional filter: ?type=ultrasound or ?type=mammogram
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.patient:
        return {"success": False, "message": "Access denied. Patients only."}, 403

    try:
        query = DetectionScan.query.filter_by(patient_id=user_id)

        if image_type:
            if image_type not in VALID_IMAGE_TYPES:
                return {
                    "success": False,
                    "message": f"Invalid type. Must be: {', '.join(VALID_IMAGE_TYPES)}."
                }, 400
            query = query.filter_by(image_type=DetectionImageType(image_type))

        scans = query.order_by(DetectionScan.created_at.desc()).all()

        grouped = {}
        for scan in scans:
            t = scan.image_type.value
            grouped.setdefault(t, []).append(scan.to_dict_patient())

        multimodal_results = (
            MultimodalResult.query
            .filter_by(patient_id=user_id)
            .order_by(MultimodalResult.created_at.desc())
            .all()
        )

        patient            = Patient.query.get(user_id)
        mental_health_mode = patient.mental_health_mode

        return {
            "success":    True,
            "total":      len(scans),
            "history":    [s.to_dict_patient() for s in scans],
            "by_type":    grouped,
            "multimodal": [m.to_dict_patient(mental_health_mode) for m in multimodal_results],
        }, 200

    except Exception as e:
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


# ══════════════════════════════════════════════════════════
#  GET SINGLE SCAN — PATIENT OR DOCTOR
# ══════════════════════════════════════════════════════════

def get_scan_by_id(scan_id):
    """
    Patient → to_dict_patient() — respects mental health mode
    Doctor  → to_dict_doctor()  — full results
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    scan = DetectionScan.query.get(scan_id)
    if not scan:
        return {"success": False, "message": "Scan not found."}, 404

    if user.role == UserRole.patient:
        if str(scan.patient_id) != user_id:
            return {"success": False, "message": "Access denied."}, 403
        return {"success": True, "scan": scan.to_dict_patient()}, 200

    if user.role == UserRole.doctor:
        patient = Patient.query.get(str(scan.patient_id))
        if not patient or str(patient.current_assigned_doctor_id) != user_id:
            return {"success": False, "message": "Access denied."}, 403
        if not scan.shared_with_doctor:
            return {"success": False, "message": "This scan was not shared with a doctor."}, 403
        return {"success": True, "scan": scan.to_dict_doctor()}, 200

    return {"success": False, "message": "Access denied."}, 403


# ══════════════════════════════════════════════════════════
#  GET PATIENT SCANS — DOCTOR VIEW
# ══════════════════════════════════════════════════════════

def get_patient_scans(patient_id, image_type=None):
    """Doctor views shared scans of their assigned patient."""
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    patient = Patient.query.get(patient_id)
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "This patient is not assigned to you."}, 403

    try:
        query = DetectionScan.query.filter_by(
            patient_id         = patient_id,
            shared_with_doctor = True,
        )

        if image_type:
            if image_type not in VALID_IMAGE_TYPES:
                return {
                    "success": False,
                    "message": f"Invalid type. Must be: {', '.join(VALID_IMAGE_TYPES)}."
                }, 400
            query = query.filter_by(image_type=DetectionImageType(image_type))

        scans        = query.order_by(DetectionScan.created_at.desc()).all()
        patient_user = User.query.get(patient_id)

        grouped = {}
        for scan in scans:
            t = scan.image_type.value
            grouped.setdefault(t, []).append(scan.to_dict_doctor())

        multimodal_results = (
            MultimodalResult.query
            .filter_by(patient_id=patient_id)
            .order_by(MultimodalResult.created_at.desc())
            .all()
        )

        return {
            "success": True,
            "patient": {
                "patient_id": patient_id,
                "full_name":  patient_user.full_name,
                "email":      patient_user.email,
            },
            "total":      len(scans),
            "scans":      [s.to_dict_doctor() for s in scans],
            "by_type":    grouped,
            "multimodal": [m.to_dict_doctor() for m in multimodal_results],
        }, 200

    except Exception as e:
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


# ══════════════════════════════════════════════════════════
#  DELETE SCAN — PATIENT
# ══════════════════════════════════════════════════════════

def delete_scan(scan_id):
    """Patient deletes their own scan + removes from Cloudinary."""
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.patient:
        return {"success": False, "message": "Access denied. Patients only."}, 403

    scan = DetectionScan.query.filter_by(
        scan_id    = scan_id,
        patient_id = user_id,
    ).first()

    if not scan:
        return {"success": False, "message": "Scan not found."}, 404

    try:
        delete_scan_image(scan.image_public_id)
        if scan.segmentation_public_id:
            delete_scan_image(scan.segmentation_public_id)
        db.session.delete(scan)
        db.session.commit()
        return {"success": True, "message": "Scan deleted successfully."}, 200

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500