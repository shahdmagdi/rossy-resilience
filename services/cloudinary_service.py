import cloudinary
import cloudinary.uploader
import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# ── Cloudinary (images: ultrasound / mammogram) ───────────
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key    = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure     = True
)

# ── Supabase (MRI NIfTI files) ────────────────────────────
SUPABASE_URL: str = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
MRI_BUCKET        = "mri-files"

_supabase: Client | None = None

def _get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        logger.debug("[supabase] Creating client — URL: %s", SUPABASE_URL)
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.debug("[supabase] Client created OK")
    return _supabase

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_IMAGE_SIZE_MB         = 10
MAX_MRI_SIZE_MB           = 100

def validate_scan_image(file):
    if not file or file.filename == "":
        return False, "No file provided."
    extension = file.filename.rsplit(".", 1)[-1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}."
    file.seek(0, 2)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    if size_mb > MAX_IMAGE_SIZE_MB:
        return False, f"File too large. Maximum size is {MAX_IMAGE_SIZE_MB}MB."
    return True, None

def validate_mri_file(file):
    if not file or file.filename == "":
        return False, "No file provided."
    filename = file.filename.lower()
    if not (filename.endswith(".nii.gz") or filename.endswith(".nii")):
        return False, "Invalid file type. MRI files must be .nii or .nii.gz (NIfTI format)."
    file.seek(0, 2)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    if size_mb > MAX_MRI_SIZE_MB:
        return False, f"File too large. Maximum MRI file size is {MAX_MRI_SIZE_MB}MB."
    return True, None

def upload_scan_image(file, patient_id, image_type):
    result = cloudinary.uploader.upload(
        file,
        folder          = f"breast_cancer/scans/{image_type}/{patient_id}",
        resource_type   = "image",
        allowed_formats = list(ALLOWED_IMAGE_EXTENSIONS),
        transformation  = [{"quality": "auto", "fetch_format": "auto"}],
    )
    return result["secure_url"], result["public_id"]

def upload_mri_file(file, patient_id, acquisition_label):
    logger.debug("[upload_mri_file] START — patient_id=%s label=%s filename=%s",
                 patient_id, acquisition_label, file.filename)

    sb = _get_supabase()

    filename     = file.filename.lower()
    ext          = ".nii.gz" if filename.endswith(".nii.gz") else ".nii"
    storage_path = f"{patient_id}/{acquisition_label}{ext}"

    logger.debug("[upload_mri_file] storage_path=%s", storage_path)

    file_bytes   = file.read()
    file.seek(0)
    logger.debug("[upload_mri_file] file size = %d bytes", len(file_bytes))

    content_type = "application/gzip" if ext == ".nii.gz" else "application/octet-stream"

    # ── Step 1: Upload ────────────────────────────────────
    logger.debug("[upload_mri_file] Uploading to bucket '%s'...", MRI_BUCKET)
    try:
        upload_response = sb.storage.from_(MRI_BUCKET).upload(
            path         = storage_path,
            file         = file_bytes,
            file_options = {"content-type": content_type, "upsert": "true"},
        )
        logger.debug("[upload_mri_file] upload_response type=%s  value=%s",
                     type(upload_response), upload_response)
    except Exception as e:
        logger.error("[upload_mri_file] UPLOAD FAILED: %s", str(e))
        raise

    # ── Step 2: Create signed URL ─────────────────────────
    logger.debug("[upload_mri_file] Creating signed URL...")
    try:
        signed_response = sb.storage.from_(MRI_BUCKET).create_signed_url(
            storage_path, expires_in=3600
        )
        logger.debug("[upload_mri_file] signed_response type=%s  value=%s",
                     type(signed_response), signed_response)
    except Exception as e:
        logger.error("[upload_mri_file] CREATE SIGNED URL FAILED: %s", str(e))
        raise

    # ── Step 3: Extract URL ───────────────────────────────
    # SDK v1 → dict with key "signedURL"  (capital URL)
    # SDK v2 → dict with key "signedUrl"  (lowercase l)
    # Some builds → object with .signed_url attribute
    if isinstance(signed_response, dict):
        signed_url = (
            signed_response.get("signedURL")
            or signed_response.get("signedUrl")
        )
        logger.debug("[upload_mri_file] extracted from dict: %s", signed_url)
    elif hasattr(signed_response, "signed_url"):
        signed_url = signed_response.signed_url
        logger.debug("[upload_mri_file] extracted from object attr: %s", signed_url)
    else:
        logger.error("[upload_mri_file] UNEXPECTED response: type=%s  value=%s",
                     type(signed_response), signed_response)
        raise ValueError(f"Unexpected create_signed_url response: {signed_response}")

    if not signed_url:
        logger.error("[upload_mri_file] signed_url is empty — full response: %s", signed_response)
        raise ValueError(f"create_signed_url returned no URL. Full response: {signed_response}")

    logger.debug("[upload_mri_file] SUCCESS — url=%s", signed_url)
    return signed_url, storage_path

def create_mri_signed_url(storage_path: str, expires_in: int = 3600) -> str:
    sb = _get_supabase()
    signed_response = sb.storage.from_(MRI_BUCKET).create_signed_url(
        storage_path, expires_in=expires_in
    )
    if isinstance(signed_response, dict):
        signed_url = signed_response.get("signedURL") or signed_response.get("signedUrl")
    elif hasattr(signed_response, "signed_url"):
        signed_url = signed_response.signed_url
    else:
        raise ValueError(f"Unexpected create_signed_url response: {signed_response}")
    if not signed_url:
        raise ValueError(f"create_signed_url returned no URL. Full response: {signed_response}")
    return signed_url

def delete_scan_image(public_id):
    cloudinary.uploader.destroy(public_id, resource_type="image")

def delete_mri_file(storage_path):
    logger.debug("[delete_mri_file] Deleting path=%s", storage_path)
    sb = _get_supabase()
    response = sb.storage.from_(MRI_BUCKET).remove([storage_path])
    logger.debug("[delete_mri_file] response: %s", response)