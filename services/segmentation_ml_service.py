import os
from gradio_client import Client, handle_file

# ── HF Space URL ──────────────────────────────────────────
SEGMENTATION_SPACE_URLS = {
    "ultrasound": os.getenv("HF_ULTRASOUND_SEG_URL", "https://mai1222-ultrasound-segmentation.hf.space"),
     "mammogram":  os.getenv("HF_MAMMOGRAM_SEG_URL"),  
}

_clients = {}

def _get_client(space_key):
    if space_key not in _clients:
        url = SEGMENTATION_SPACE_URLS.get(space_key)
        if not url:
            return None
        _clients[space_key] = Client(url)
    return _clients[space_key]

def predict_segmentation(image_path, image_type="ultrasound"):
    client = _get_client(image_type)
    if not client:
        raise NotImplementedError(
            f"{image_type.capitalize()} segmentation space is not configured. "
            f"Set HF_{image_type.upper()}_SEG_URL in environment variables."
        )

    result = client.predict(
        image    = handle_file(image_path),
        api_name = "/predict"
    )
    return {
        "mask_image_path": result[0],
        "confidence":      result[1].get("confidence", 0.0),
    }