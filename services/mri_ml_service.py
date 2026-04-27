import os
import tempfile
import requests
from gradio_client import Client, handle_file

# ── HF Space URL ──────────────────────────────────────────
MRI_SPACE_URL = os.getenv("HF_MRI_URL")  # set in .env when space is ready
_client = None

def _get_client():
    """Returns cached Gradio client. Raises if space not configured."""
    global _client
    if _client is None:
        if not MRI_SPACE_URL:
            raise NotImplementedError(
                "MRI staging space is not configured. "
                "Set HF_MRI_URL in environment variables."
            )
        _client = Client(MRI_SPACE_URL)
        print(f"[mri_ml_service] Connected to MRI space: {MRI_SPACE_URL}")
    return _client


def _download_to_temp(url: str) -> str:
    """
    Downloads a NIfTI file from a public URL to a local temp file.
    Preserves .nii or .nii.gz extension so nibabel reads it correctly.
    Returns the temp file path.
    """
    # Detect extension from URL path
    url_path = url.split("?")[0].lower()   # strip query params if any
    suffix   = ".nii.gz" if url_path.endswith(".nii.gz") else ".nii"

    response = requests.get(url, timeout=120, stream=True)
    response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    for chunk in response.iter_content(chunk_size=8192):
        tmp.write(chunk)
    tmp.close()
    return tmp.name


def _cleanup(*paths):
    """Removes temp files silently."""
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass


# ══════════════════════════════════════════════════════════
#  MRI STAGING — called from backend (URLs)
#  Downloads NIfTI files from Supabase public URLs,
#  saves them to temp files, then sends to HF Space.
#
#  HF Space output (via /run_inference):
#  {
#    "T_stage":                  "T3" | "T2" | ... | None,
#    "size_cm":                  float,
#    "volume_cc":                float,
#    "segmentation_consistency": float,
#    "uncertainty_mean":         float
#  }
# ══════════════════════════════════════════════════════════

# mri_ml_service.py

# mri_ml_service.py — only predict_mri needs to change

from gradio_client import Client
import httpx

MRI_SPACE_URL = os.getenv("HF_MRI_URL")
_client = None

def _get_client():
    global _client
    if _client is None:
        if not MRI_SPACE_URL:
            raise NotImplementedError(
                "MRI staging space is not configured. "
                "Set HF_MRI_URL in environment variables."
            )
        # Set a long httpx timeout — inference can take 2-5 min
        _client = Client(
            MRI_SPACE_URL,
            httpx_kwargs={"timeout": httpx.Timeout(600.0)}  # 10 minutes
        )
        print(f"[mri_ml_service] Connected to MRI space: {MRI_SPACE_URL}")
    return _client


def predict_mri(acq0_url: str, acq2_url: str, acq1_url: str | None = None) -> dict:
    client = _get_client()

    result = client.predict(
        acq0_url,
        acq2_url,
        acq1_url or "",
        api_name="/run_inference_from_urls",
    )

    if isinstance(result, dict) and "error" in result:
        raise ValueError(f"MRI model error: {result['error']}")

    return {
        "t_stage":                  result.get("T_stage"),
        "size_cm":                  result.get("size_cm"),
        "volume_cc":                result.get("volume_cc"),
        "segmentation_consistency": result.get("segmentation_consistency"),
        "uncertainty_mean":         result.get("uncertainty_mean"),
        "model_version":            "mri_unet_resnet34_v1",
    }