# import os
# import tempfile
# import requests
# from app import db
# from models import User, UserRole, Patient
# from models.detection_scan import DetectionScan
# from services.segmentation_ml_service import predict_segmentation
# from services.cloudinary_service import upload_scan_image, delete_scan_image
# from flask_jwt_extended import get_jwt_identity


# # ══════════════════════════════════════════════════════════
# #  HELPERS
# # ══════════════════════════════════════════════════════════

# def _download_image_from_url(url):
#     """
#     Downloads an image from a Cloudinary URL to a temp file.
#     Used when the original image is already uploaded to Cloudinary
#     and we need to pass it to the segmentation model.

#     Returns: local temp file path
#     """
#     response = requests.get(url, timeout=30)
#     response.raise_for_status()

#     # Detect extension from content type
#     content_type = response.headers.get("Content-Type", "image/jpeg")
#     ext          = ".jpg" if "jpeg" in content_type else ".png"

#     tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
#     tmp.write(response.content)
#     tmp.close()
#     return tmp.name
# from PIL import Image

# def _convert_to_png(webp_path):
#     """Converts webp mask to PNG for Cloudinary compatibility."""
#     png_path = webp_path.replace(".webp", ".png")
#     img = Image.open(webp_path)
#     img.save(png_path, "PNG")
#     return png_path

# def _cleanup(*paths):
#     """Removes temp files silently."""
#     for path in paths:
#         if path and os.path.exists(path):
#             try:
#                 os.remove(path)
#             except Exception:
#                 pass


# # ══════════════════════════════════════════════════════════
# #  REQUEST SEGMENTATION — DOCTOR ONLY, ON DEMAND
# #
# #  Flow:
# #    1. Doctor requests segmentation for a specific scan
# #    2. Check if segmentation already exists → return cached result
# #    3. If not → download original image from Cloudinary
# #    4. Call segmentation HF Space → get mask image + confidence
# #    5. Upload mask image to Cloudinary under segmentation folder
# #    6. Save segmentation_url + confidence to detection_scans table
# #    7. Return result to doctor
# # ══════════════════════════════════════════════════════════

# def get_segmentation(scan_id):
#     """
#     On-demand segmentation for:
#       1. Regular DetectionScan rows
#       2. MultimodalResult rows (using multimodal_id)

#     IMPORTANT:
#     - Keeps the exact same API route:
#           POST /api/segmentation/<scan_id>
#     - Frontend does NOT need any changes.
#     - If scan_id belongs to DetectionScan → existing logic runs unchanged.
#     - If scan_id belongs to MultimodalResult → segmentation is generated for:
#           - ultrasound image
#           - mammogram image
#       and returned together.
#     """
#     from models.detection_scan import DetectionScan, MultimodalResult

#     user_id = get_jwt_identity()
#     user = User.query.get(user_id)

#     # ─────────────────────────────────────────────────────
#     # 1. Doctor only
#     # ─────────────────────────────────────────────────────
#     if user.role != UserRole.doctor:
#         return {"success": False, "message": "Access denied. Doctors only."}, 403

#     # ─────────────────────────────────────────────────────
#     # 2. FIRST: try normal DetectionScan
#     # ─────────────────────────────────────────────────────
#     scan = DetectionScan.query.get(scan_id)

#     if scan:
#         # ─────────────────────────────────────────────────
#         # Existing logic (UNCHANGED)
#         # ─────────────────────────────────────────────────
#         patient = Patient.query.get(str(scan.patient_id))
#         if not patient or str(patient.current_assigned_doctor_id) != user_id:
#             return {"success": False, "message": "Access denied."}, 403

#         if not scan.shared_with_doctor:
#             return {
#                 "success": False,
#                 "message": "This scan was not shared with a doctor."
#             }, 403

#         if scan.segmentation_url:
#             return {
#                 "success": True,
#                 "message": "Segmentation result retrieved.",
#                 "cached": True,
#                 "scan_id": str(scan.scan_id),
#                 "image_type": scan.image_type.value,
#                 "original_url": scan.image_url,
#                 "segmentation_url": scan.segmentation_url,
#                 "confidence": scan.segmentation_confidence,
#             }, 200

#         tmp_original = None
#         tmp_mask = None

#         try:
#             tmp_original = _download_image_from_url(scan.image_url)

#             seg_result = predict_segmentation(
#                 tmp_original,
#                 scan.image_type.value
#             )

#             tmp_mask = seg_result["mask_image_path"]

#             if tmp_mask.endswith(".webp"):
#                 tmp_png = _convert_to_png(tmp_mask)
#                 _cleanup(tmp_mask)
#                 tmp_mask = tmp_png

#             confidence = seg_result["confidence"]

#             with open(tmp_mask, "rb") as mask_file:

#                 class _FileWrapper:
#                     def __init__(self, f, filename):
#                         self._f = f
#                         self.filename = filename

#                     def read(self, *args):
#                         return self._f.read(*args)

#                     def seek(self, *args):
#                         return self._f.seek(*args)

#                     def tell(self, *args):
#                         return self._f.tell(*args)

#                 wrapper = _FileWrapper(
#                     mask_file,
#                     "segmentation_mask.png"
#                 )

#                 seg_url, seg_public_id = upload_scan_image(
#                     wrapper,
#                     str(scan.patient_id),
#                     f"segmentation_{scan.image_type.value}"
#                 )

#             scan.segmentation_url = seg_url
#             scan.segmentation_public_id = seg_public_id
#             scan.segmentation_confidence = confidence
#             db.session.commit()

#             return {
#                 "success": True,
#                 "message": "Segmentation completed successfully.",
#                 "cached": False,
#                 "scan_id": str(scan.scan_id),
#                 "image_type": scan.image_type.value,
#                 "original_url": scan.image_url,
#                 "segmentation_url": seg_url,
#                 "confidence": confidence,
#             }, 200

#         except NotImplementedError as e:
#             return {"success": False, "message": str(e)}, 503

#         except Exception as e:
#             db.session.rollback()
#             return {
#                 "success": False,
#                 "message": "Something went wrong.",
#                 "error": str(e),
#             }, 500

#         finally:
#             _cleanup(tmp_original, tmp_mask)

#     # ─────────────────────────────────────────────────────
#     # 3. SECOND: try MultimodalResult
#     # ─────────────────────────────────────────────────────
#     multimodal = MultimodalResult.query.get(scan_id)

#     if not multimodal:
#         return {"success": False, "message": "Scan not found."}, 404

#     # Verify doctor access
#     patient = Patient.query.get(str(multimodal.patient_id))
#     if not patient or str(patient.current_assigned_doctor_id) != user_id:
#         return {"success": False, "message": "Access denied."}, 403

#     if not multimodal.shared_with_doctor:
#         return {
#             "success": False,
#             "message": "This multimodal result was not shared with a doctor."
#         }, 403

#     # Helper to process one modality
#     def process_modality(image_url, image_type):
#         if not image_url:
#             return {
#                 "ready": False,
#                 "url": None,
#                 "confidence": None,
#             }

#         tmp_original = None
#         tmp_mask = None

#         try:
#             tmp_original = _download_image_from_url(image_url)

#             seg_result = predict_segmentation(
#                 tmp_original,
#                 image_type
#             )

#             tmp_mask = seg_result["mask_image_path"]

#             if tmp_mask.endswith(".webp"):
#                 tmp_png = _convert_to_png(tmp_mask)
#                 _cleanup(tmp_mask)
#                 tmp_mask = tmp_png

#             confidence = seg_result["confidence"]

#             with open(tmp_mask, "rb") as mask_file:

#                 class _FileWrapper:
#                     def __init__(self, f, filename):
#                         self._f = f
#                         self.filename = filename

#                     def read(self, *args):
#                         return self._f.read(*args)

#                     def seek(self, *args):
#                         return self._f.seek(*args)

#                     def tell(self, *args):
#                         return self._f.tell(*args)

#                 wrapper = _FileWrapper(
#                     mask_file,
#                     f"{image_type}_segmentation.png"
#                 )

#                 seg_url, _ = upload_scan_image(
#                     wrapper,
#                     str(multimodal.patient_id),
#                     f"segmentation_{image_type}"
#                 )

#             return {
#                 "ready": True,
#                 "url": seg_url,
#                 "confidence": confidence,
#             }

#         finally:
#             _cleanup(tmp_original, tmp_mask)

#     # Generate segmentation for both modalities
#     ultrasound_seg = process_modality(
#         multimodal.ultrasound_image_url,
#         "ultrasound"
#     )

#     mammogram_seg = process_modality(
#         multimodal.mammogram_image_url,
#         "mammogram"
#     )

#     return {
#         "success": True,
#         "message": "Multimodal segmentation completed successfully.",
#         "cached": False,
#         "scan_id": str(multimodal.id),  # frontend still sends same path parameter
#         "image_type": "multimodal",
#         "segmentation": {
#             "ultrasound": ultrasound_seg,
#             "mammogram": mammogram_seg,
#         },
#         "original_images": {
#             "ultrasound": multimodal.ultrasound_image_url,
#             "mammogram": multimodal.mammogram_image_url,
#         },
#     }, 200

# # ══════════════════════════════════════════════════════════
# #  DELETE SEGMENTATION RESULT
# #  Doctor clears segmentation (can re-run it later)
# # ══════════════════════════════════════════════════════════

# def delete_segmentation(scan_id):
#     """
#     Deletes the segmentation result for a scan.
#     Removes mask image from Cloudinary.
#     Segmentation can be re-requested afterwards.

#     Works for both:
#       1. Regular DetectionScan rows
#       2. MultimodalResult rows (clears both ultrasound + mammogram segmentations)

#     Returns: (response_dict, http_status_code)
#     """
#     from models.detection_scan import DetectionScan, MultimodalResult

#     user_id = get_jwt_identity()
#     user    = User.query.get(user_id)

#     if user.role != UserRole.doctor:
#         return {"success": False, "message": "Access denied. Doctors only."}, 403

#     # ─────────────────────────────────────────────────────
#     # 1. FIRST: try normal DetectionScan
#     # ─────────────────────────────────────────────────────
#     scan = DetectionScan.query.get(scan_id)

#     if scan:
#         patient = Patient.query.get(str(scan.patient_id))
#         if not patient or str(patient.current_assigned_doctor_id) != user_id:
#             return {"success": False, "message": "Access denied."}, 403

#         if not scan.segmentation_url:
#             return {"success": False, "message": "No segmentation result to delete."}, 400

#         try:
#             delete_scan_image(scan.segmentation_public_id)

#             scan.segmentation_url        = None
#             scan.segmentation_public_id  = None
#             scan.segmentation_confidence = None
#             db.session.commit()

#             return {
#                 "success": True,
#                 "message": "Segmentation result deleted. You can re-run it anytime."
#             }, 200

#         except Exception as e:
#             db.session.rollback()
#             return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500

#     # ─────────────────────────────────────────────────────
#     # 2. SECOND: try MultimodalResult
#     # ─────────────────────────────────────────────────────
#     multimodal = MultimodalResult.query.get(scan_id)

#     if not multimodal:
#         return {"success": False, "message": "Scan not found."}, 404

#     patient = Patient.query.get(str(multimodal.patient_id))
#     if not patient or str(patient.current_assigned_doctor_id) != user_id:
#         return {"success": False, "message": "Access denied."}, 403

#     # Check at least one segmentation exists before proceeding
#     has_ultrasound_seg = bool(multimodal.ultrasound_segmentation_url)
#     has_mammogram_seg  = bool(multimodal.mammogram_segmentation_url)

#     if not has_ultrasound_seg and not has_mammogram_seg:
#         return {"success": False, "message": "No segmentation results to delete."}, 400

#     try:
#         if has_ultrasound_seg:
#             delete_scan_image(multimodal.ultrasound_segmentation_public_id)
#             multimodal.ultrasound_segmentation_url        = None
#             multimodal.ultrasound_segmentation_public_id  = None
#             multimodal.ultrasound_segmentation_confidence = None

#         if has_mammogram_seg:
#             delete_scan_image(multimodal.mammogram_segmentation_public_id)
#             multimodal.mammogram_segmentation_url        = None
#             multimodal.mammogram_segmentation_public_id  = None
#             multimodal.mammogram_segmentation_confidence = None

#         db.session.commit()

#         return {
#             "success": True,
#             "message": "Multimodal segmentation results deleted. You can re-run them anytime.",
#             "deleted": {
#                 "ultrasound": has_ultrasound_seg,
#                 "mammogram":  has_mammogram_seg,
#             }
#         }, 200

#     except Exception as e:
#         db.session.rollback()
#         return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500



import os
import tempfile
import requests
from PIL import Image
from app import db
from models import User, UserRole, Patient
from models.detection_scan import DetectionScan
from services.segmentation_ml_service import predict_segmentation
from services.cloudinary_service import upload_scan_image, delete_scan_image
from flask_jwt_extended import get_jwt_identity


# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════

def _download_image_from_url(url):
    """
    Downloads an image from a Cloudinary URL to a temp file.
    Used when the original image is already uploaded to Cloudinary
    and we need to pass it to the segmentation model.

    Returns: local temp file path
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "image/jpeg")
    ext          = ".jpg" if "jpeg" in content_type else ".png"

    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tmp.write(response.content)
    tmp.close()
    return tmp.name


def _convert_to_png(webp_path):
    """Converts webp mask to PNG for Cloudinary compatibility."""
    png_path = webp_path.replace(".webp", ".png")
    img = Image.open(webp_path)
    img.save(png_path, "PNG")
    return png_path


def _cleanup(*paths):
    """Removes temp files silently."""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass


class _FileWrapper:
    """Wraps an open file with a filename attribute for Cloudinary upload."""
    def __init__(self, f, filename):
        self._f      = f
        self.filename = filename

    def read(self, *args):  return self._f.read(*args)
    def seek(self, *args):  return self._f.seek(*args)
    def tell(self, *args):  return self._f.tell(*args)


# ══════════════════════════════════════════════════════════
#  REQUEST SEGMENTATION — DOCTOR ONLY, ON DEMAND
#
#  Flow:
#    1. Doctor requests segmentation for a specific scan
#    2. Check if segmentation already exists → return cached result
#    3. If not → download original image from Cloudinary
#    4. Call segmentation HF Space → get mask image + confidence
#    5. Upload mask image to Cloudinary under segmentation folder
#    6. Save segmentation_url + confidence to DB
#    7. Return result to doctor
#
#  Accepts either a scan_id (DetectionScan) or multimodal_id (MultimodalResult).
#  The backend resolves which one it is automatically.
# ══════════════════════════════════════════════════════════

def get_segmentation(scan_id):
    """
    On-demand segmentation for:
      1. Regular DetectionScan rows
      2. MultimodalResult rows (using multimodal_id)

    IMPORTANT:
    - Keeps the exact same API route:
          POST /api/segmentation/<scan_id>
    - Frontend does NOT need any changes.
    - If scan_id belongs to DetectionScan → existing logic runs unchanged.
    - If scan_id belongs to MultimodalResult → segmentation is generated for:
          - ultrasound image
          - mammogram image
      and returned together.
    """
    from models.detection_scan import DetectionScan, MultimodalResult

    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    # ─────────────────────────────────────────────────────
    # 1. Doctor only
    # ─────────────────────────────────────────────────────
    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    # ─────────────────────────────────────────────────────
    # 2. FIRST: try normal DetectionScan
    # ─────────────────────────────────────────────────────
    scan = DetectionScan.query.get(scan_id)

    if scan:
        patient = Patient.query.get(str(scan.patient_id))
        if not patient or str(patient.current_assigned_doctor_id) != user_id:
            return {"success": False, "message": "Access denied."}, 403

        if not scan.shared_with_doctor:
            return {
                "success": False,
                "message": "This scan was not shared with a doctor."
            }, 403

        # Return cached result if already exists
        if scan.segmentation_url:
            return {
                "success":          True,
                "message":          "Segmentation result retrieved.",
                "cached":           True,
                "scan_id":          str(scan.scan_id),
                "image_type":       scan.image_type.value,
                "original_url":     scan.image_url,
                "segmentation_url": scan.segmentation_url,
                "confidence":       scan.segmentation_confidence,
            }, 200

        tmp_original = None
        tmp_mask     = None

        try:
            tmp_original = _download_image_from_url(scan.image_url)

            seg_result = predict_segmentation(tmp_original, scan.image_type.value)
            tmp_mask   = seg_result["mask_image_path"]

            if tmp_mask.endswith(".webp"):
                tmp_png  = _convert_to_png(tmp_mask)
                _cleanup(tmp_mask)
                tmp_mask = tmp_png

            confidence = seg_result["confidence"]

            with open(tmp_mask, "rb") as mask_file:
                wrapper = _FileWrapper(mask_file, "segmentation_mask.png")
                seg_url, seg_public_id = upload_scan_image(
                    wrapper,
                    str(scan.patient_id),
                    f"segmentation_{scan.image_type.value}"
                )

            scan.segmentation_url        = seg_url
            scan.segmentation_public_id  = seg_public_id
            scan.segmentation_confidence = confidence
            db.session.commit()

            return {
                "success":          True,
                "message":          "Segmentation completed successfully.",
                "cached":           False,
                "scan_id":          str(scan.scan_id),
                "image_type":       scan.image_type.value,
                "original_url":     scan.image_url,
                "segmentation_url": seg_url,
                "confidence":       confidence,
            }, 200

        except NotImplementedError as e:
            return {"success": False, "message": str(e)}, 503

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": "Something went wrong.",
                "error":   str(e),
            }, 500

        finally:
            _cleanup(tmp_original, tmp_mask)

    # ─────────────────────────────────────────────────────
    # 3. SECOND: try MultimodalResult
    # ─────────────────────────────────────────────────────
    multimodal = MultimodalResult.query.get(scan_id)

    if not multimodal:
        return {"success": False, "message": "Scan not found."}, 404

    # Verify doctor access
    patient = Patient.query.get(str(multimodal.patient_id))
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "Access denied."}, 403

    if not multimodal.shared_with_doctor:
        return {
            "success": False,
            "message": "This multimodal result was not shared with a doctor."
        }, 403

    # Return cached result if both modalities already have segmentation
    if multimodal.ultrasound_segmentation_url and multimodal.mammogram_segmentation_url:
        return {
            "success":  True,
            "message":  "Segmentation result retrieved.",
            "cached":   True,
            "scan_id":  str(multimodal.id),
            "image_type": "multimodal",
            "segmentation": {
                "ultrasound": {
                    "ready":      True,
                    "url":        multimodal.ultrasound_segmentation_url,
                    "confidence": multimodal.ultrasound_segmentation_confidence,
                },
                "mammogram": {
                    "ready":      True,
                    "url":        multimodal.mammogram_segmentation_url,
                    "confidence": multimodal.mammogram_segmentation_confidence,
                },
            },
            "original_images": {
                "ultrasound": multimodal.ultrasound_image_url,
                "mammogram":  multimodal.mammogram_image_url,
            },
        }, 200

    # Helper to process one modality and persist result to DB
    def process_modality(image_url, image_type):
        if not image_url:
            return {"ready": False, "url": None, "confidence": None}

        tmp_original = None
        tmp_mask     = None

        try:
            tmp_original = _download_image_from_url(image_url)

            seg_result = predict_segmentation(tmp_original, image_type)
            tmp_mask   = seg_result["mask_image_path"]

            if tmp_mask.endswith(".webp"):
                tmp_png  = _convert_to_png(tmp_mask)
                _cleanup(tmp_mask)
                tmp_mask = tmp_png

            confidence = seg_result["confidence"]

            with open(tmp_mask, "rb") as mask_file:
                wrapper = _FileWrapper(mask_file, f"{image_type}_segmentation.png")
                seg_url, seg_public_id = upload_scan_image(
                    wrapper,
                    str(multimodal.patient_id),
                    f"segmentation_{image_type}"
                )

            # ✅ Persist to DB so delete can find and clean up later
            if image_type == "ultrasound":
                multimodal.ultrasound_segmentation_url        = seg_url
                multimodal.ultrasound_segmentation_public_id  = seg_public_id
                multimodal.ultrasound_segmentation_confidence = confidence
            elif image_type == "mammogram":
                multimodal.mammogram_segmentation_url        = seg_url
                multimodal.mammogram_segmentation_public_id  = seg_public_id
                multimodal.mammogram_segmentation_confidence = confidence

            return {"ready": True, "url": seg_url, "confidence": confidence}

        finally:
            _cleanup(tmp_original, tmp_mask)

    try:
        # Generate segmentation for both modalities
        ultrasound_seg = process_modality(multimodal.ultrasound_image_url, "ultrasound")
        mammogram_seg  = process_modality(multimodal.mammogram_image_url,  "mammogram")

        # ✅ Single commit after both modalities are done
        db.session.commit()

        return {
            "success":    True,
            "message":    "Multimodal segmentation completed successfully.",
            "cached":     False,
            "scan_id":    str(multimodal.id),
            "image_type": "multimodal",
            "segmentation": {
                "ultrasound": ultrasound_seg,
                "mammogram":  mammogram_seg,
            },
            "original_images": {
                "ultrasound": multimodal.ultrasound_image_url,
                "mammogram":  multimodal.mammogram_image_url,
            },
        }, 200

    except NotImplementedError as e:
        return {"success": False, "message": str(e)}, 503

    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": "Something went wrong.",
            "error":   str(e),
        }, 500


# ══════════════════════════════════════════════════════════
#  DELETE SEGMENTATION RESULT
#  Doctor clears segmentation (can re-run it later)
#
#  Accepts either a scan_id (DetectionScan) or multimodal_id (MultimodalResult).
#  The backend resolves which one it is automatically.
# ══════════════════════════════════════════════════════════

def delete_segmentation(scan_id):
    """
    Deletes the segmentation result for a scan.
    Removes mask image from Cloudinary.
    Segmentation can be re-requested afterwards.

    Works for both:
      1. Regular DetectionScan rows
      2. MultimodalResult rows (clears both ultrasound + mammogram segmentations)

    Returns: (response_dict, http_status_code)
    """
    from models.detection_scan import DetectionScan, MultimodalResult

    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    # ─────────────────────────────────────────────────────
    # 1. FIRST: try normal DetectionScan
    # ─────────────────────────────────────────────────────
    scan = DetectionScan.query.get(scan_id)

    if scan:
        patient = Patient.query.get(str(scan.patient_id))
        if not patient or str(patient.current_assigned_doctor_id) != user_id:
            return {"success": False, "message": "Access denied."}, 403

        if not scan.segmentation_url:
            return {"success": False, "message": "No segmentation result to delete."}, 400

        try:
            delete_scan_image(scan.segmentation_public_id)

            scan.segmentation_url        = None
            scan.segmentation_public_id  = None
            scan.segmentation_confidence = None
            db.session.commit()

            return {
                "success": True,
                "message": "Segmentation result deleted. You can re-run it anytime."
            }, 200

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500

    # ─────────────────────────────────────────────────────
    # 2. SECOND: try MultimodalResult
    # ─────────────────────────────────────────────────────
    multimodal = MultimodalResult.query.get(scan_id)

    if not multimodal:
        return {"success": False, "message": "Scan not found."}, 404

    patient = Patient.query.get(str(multimodal.patient_id))
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "Access denied."}, 403

    has_ultrasound_seg = bool(multimodal.ultrasound_segmentation_url)
    has_mammogram_seg  = bool(multimodal.mammogram_segmentation_url)

    if not has_ultrasound_seg and not has_mammogram_seg:
        return {"success": False, "message": "No segmentation results to delete."}, 400

    try:
        if has_ultrasound_seg:
            delete_scan_image(multimodal.ultrasound_segmentation_public_id)
            multimodal.ultrasound_segmentation_url        = None
            multimodal.ultrasound_segmentation_public_id  = None
            multimodal.ultrasound_segmentation_confidence = None

        if has_mammogram_seg:
            delete_scan_image(multimodal.mammogram_segmentation_public_id)
            multimodal.mammogram_segmentation_url        = None
            multimodal.mammogram_segmentation_public_id  = None
            multimodal.mammogram_segmentation_confidence = None

        db.session.commit()

        return {
            "success": True,
            "message": "Multimodal segmentation results deleted. You can re-run them anytime.",
            "deleted": {
                "ultrasound": has_ultrasound_seg,
                "mammogram":  has_mammogram_seg,
            }
        }, 200

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500