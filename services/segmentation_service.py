import os
import tempfile
import requests
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

    # Detect extension from content type
    content_type = response.headers.get("Content-Type", "image/jpeg")
    ext          = ".jpg" if "jpeg" in content_type else ".png"

    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tmp.write(response.content)
    tmp.close()
    return tmp.name
from PIL import Image

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


# ══════════════════════════════════════════════════════════
#  REQUEST SEGMENTATION — DOCTOR ONLY, ON DEMAND
#
#  Flow:
#    1. Doctor requests segmentation for a specific scan
#    2. Check if segmentation already exists → return cached result
#    3. If not → download original image from Cloudinary
#    4. Call segmentation HF Space → get mask image + confidence
#    5. Upload mask image to Cloudinary under segmentation folder
#    6. Save segmentation_url + confidence to detection_scans table
#    7. Return result to doctor
# ══════════════════════════════════════════════════════════

def get_segmentation(scan_id):
    """
    On-demand segmentation for a specific ultrasound scan.
    Doctor only — patient never sees segmentation results.

    If segmentation already exists → returns cached result instantly.
    If not → calls HF Space, stores result, returns it.

    Args:
        scan_id (str): detection scan UUID

    Returns: (response_dict, http_status_code)
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    # 1. Doctor only
    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    # 2. Find the scan
    scan = DetectionScan.query.get(scan_id)
    if not scan:
        return {"success": False, "message": "Scan not found."}, 404

    # 3. Doctor must be assigned to this patient
    patient = Patient.query.get(str(scan.patient_id))
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "Access denied."}, 403

    # 4. Scan must be shared with doctor
    if not scan.shared_with_doctor:
        return {
            "success": False,
            "message": "This scan was not shared with a doctor."
        }, 403

    # 5. Check if segmentation already exists — return cached result
    if scan.segmentation_url:
        return {
            "success":           True,
            "message":           "Segmentation result retrieved.",
            "cached":            True,
            "scan_id":           str(scan.scan_id),
            "image_type":        scan.image_type.value,
            "original_url":      scan.image_url,
            "segmentation_url":  scan.segmentation_url,
            "confidence":        scan.segmentation_confidence,
        }, 200

    tmp_original = None
    tmp_mask     = None

    try:
        # 6. Download original image from Cloudinary for the model
        tmp_original = _download_image_from_url(scan.image_url)

        # 7. Call segmentation HF Space
        seg_result = predict_segmentation(tmp_original, scan.image_type.value)
        tmp_mask = seg_result["mask_image_path"]

# Convert webp → png if needed
        if tmp_mask.endswith(".webp"):
            tmp_png  = _convert_to_png(tmp_mask)
            _cleanup(tmp_mask)   # remove original webp
            tmp_mask = tmp_png   # use png instead

        confidence = seg_result["confidence"]

        with open(tmp_mask, "rb") as mask_file:

            class _FileWrapper:
                """Wraps an open file to match Flask FileStorage interface."""
                def __init__(self, f, filename):
                    self._f       = f
                    self.filename = filename
                def read(self, *args):   return self._f.read(*args)
                def seek(self, *args):   return self._f.seek(*args)
                def tell(self, *args):   return self._f.tell(*args)

            wrapper = _FileWrapper(mask_file, "segmentation_mask.png")
            seg_url, seg_public_id = upload_scan_image(
                wrapper,
                str(scan.patient_id),
                f"segmentation_{scan.image_type.value}"   # e.g. segmentation_ultrasound
            )

        # 9. Save segmentation result to DB
        scan.segmentation_url       = seg_url
        scan.segmentation_public_id = seg_public_id
        scan.segmentation_confidence = confidence
        db.session.commit()

        return {
            "success":           True,
            "message":           "Segmentation completed successfully.",
            "cached":            False,
            "scan_id":           str(scan.scan_id),
            "image_type":        scan.image_type.value,
            "original_url":      scan.image_url,
            "segmentation_url":  seg_url,
            "confidence":        confidence,
        }, 200

    except NotImplementedError as e:
        return {"success": False, "message": str(e)}, 503

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500

    finally:
        _cleanup(tmp_original, tmp_mask)


# ══════════════════════════════════════════════════════════
#  DELETE SEGMENTATION RESULT
#  Doctor clears segmentation (can re-run it later)
# ══════════════════════════════════════════════════════════

def delete_segmentation(scan_id):
    """
    Deletes the segmentation result for a scan.
    Removes mask image from Cloudinary.
    Segmentation can be re-requested afterwards.

    Returns: (response_dict, http_status_code)
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    scan = DetectionScan.query.get(scan_id)
    if not scan:
        return {"success": False, "message": "Scan not found."}, 404

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