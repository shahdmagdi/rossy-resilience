
# import os
# from gradio_client import Client, handle_file

# # ── HF Space URL ──────────────────────────────────────────
# HF_SPACE_URL = os.getenv(
#     "HF_SPACE_URL",
#     "https://mai1222-rosy-resslience.hf.space"
# )

# MODEL_CONFIG = {
#     "ultrasound": {
#         "version": "ultrasound_resnet50_v1",
#     },
#     # "mammogram": {
#     #     "version": "mammogram_resnet50_v1",
#     # },
# }

# # ── Client cache — created once, reused ──────────────────
# _client = None


# def get_client():
#     """Creates Gradio client once and reuses it."""
#     global _client
#     if _client is None:
#         # hf_token = os.getenv("HF_TOKEN")   # only needed if Space is private
#         _client  = Client(HF_SPACE_URL)
#         print(f"[ml_service] Connected to HF Space: {HF_SPACE_URL}")
#     return _client


# # ══════════════════════════════════════════════════════════
# #  PREDICT
# #  Sends image file directly to HF Space — no base64 needed
# # ══════════════════════════════════════════════════════════

# def predict(image_path, image_type):
#     """
#     Calls the HF Space Gradio API with the image file.

#     Args:
#         image_path (str): path to the temp image file
#         image_type (str): "ultrasound" or "mammogram"

#     Returns:
#         dict: {
#             predicted_class, confidence,
#             probabilities, model_version
#         }
#     """

#     if image_type not in MODEL_CONFIG:
#         raise ValueError(f"Unknown image type: '{image_type}'. Must be 'ultrasound' or 'mammogram'.")

#     client = get_client()

#     # Send image file directly — gradio_client handles upload automatically
#     result = client.predict(
#         image      = handle_file(image_path),
#         api_name   = "/predict"
#     )

#     # result is the dict returned by HF Space predict function:
#     # {"predicted_class": "malignant", "confidence (%)": 98.46}
#     predicted_class = result.get("predicted_class")
#     confidence      = result.get("confidence (%)")

#     return {
#         "predicted_class": predicted_class,
#         "confidence":      confidence,
#         "probabilities":   _build_probabilities(predicted_class, confidence),
#         "model_version":   MODEL_CONFIG[image_type]["version"],
#     }


# # ══════════════════════════════════════════════════════════
# #  HELPER
# # ══════════════════════════════════════════════════════════

# def _build_probabilities(predicted_class, confidence):
#     """
#     HF Space only returns the top class confidence.
#     We distribute the remaining % evenly across other classes.
#     """
#     all_classes   = ["benign", "malignant", "normal"]
#     remaining     = round(100 - confidence, 2)
#     other_classes = [c for c in all_classes if c != predicted_class]
#     other_prob    = round(remaining / len(other_classes), 2)

#     probabilities = {c: other_prob for c in all_classes}
#     probabilities[predicted_class] = confidence

#     return probabilities





# import os
# from gradio_client import Client, handle_file

# # ── HF Space URLs ─────────────────────────────────────────
# SPACE_URLS = {
#     "ultrasound":  os.getenv("HF_ULTRASOUND_URL",  "https://mai1222-rosy-resslience.hf.space"),
#     "mammogram":   os.getenv("HF_MAMMOGRAM_URL"),   # set when mammogram space is ready
#     # "multimodal":  os.getenv("HF_MULTIMODAL_URL"),  # set when multimodal space is ready
# }

# # ── Client cache — one client per space, created once ─────
# _clients = {}

# LABELS = {
#     0: "benign",
#     1: "malignant",
#     2: "normal",
# }


# def _get_client(space_key):
#     """
#     Returns a cached Gradio client for the given space.
#     Returns None if the space URL is not configured yet.
#     """
#     if space_key not in _clients:
#         url = SPACE_URLS.get(space_key)
#         if not url:
#             return None
#         _clients[space_key] = Client(url)
#         print(f"[ml_service] Connected to {space_key}: {url}")
#     return _clients[space_key]


# def _build_probabilities(predicted_class, confidence):
#     """Distributes remaining % evenly across other classes."""
#     all_classes   = ["benign", "malignant", "normal"]
#     remaining     = round(100 - confidence, 2)
#     other_classes = [c for c in all_classes if c != predicted_class]
#     other_prob    = round(remaining / len(other_classes), 2)
#     probs         = {c: other_prob for c in all_classes}
#     probs[predicted_class] = confidence
#     return probs


# # ══════════════════════════════════════════════════════════
# #  ULTRASOUND CLASSIFICATION
# #  Calls existing HF Space (rosy_resslience)
# # ══════════════════════════════════════════════════════════

# def predict_ultrasound(image_path):
#     """
#     Calls the ultrasound classification HF Space.

#     Args:
#         image_path (str): path to temp image file

#     Returns:
#         dict: { predicted_class, confidence, probabilities, model_version }
#     """
#     client = _get_client("ultrasound")
#     if not client:
#         raise NotImplementedError(
#             "Ultrasound classification space is not configured. "
#             "Set HF_ULTRASOUND_URL in environment variables."
#         )

#     result = client.predict(
#         image    = handle_file(image_path),
#         api_name = "/predict"
#     )

#     predicted_class = result.get("predicted_class")
#     confidence      = result.get("confidence (%)")

#     return {
#         "predicted_class": predicted_class,
#         "confidence":      confidence,
#         "probabilities":   _build_probabilities(predicted_class, confidence),
#         "model_version":   "ultrasound_resnet50_v1",
#     }


# # ══════════════════════════════════════════════════════════
# #  MAMMOGRAM CLASSIFICATION
# #  ⚠️  Space not ready yet — placeholder
# #  Update api_name once DL team shares the Space
# # ══════════════════════════════════════════════════════════

# def predict_mammogram(image_path):
#     """
#     Calls the mammogram classification HF Space.

#     ⚠️  PLACEHOLDER — update when DL team shares:
#         - HF Space URL → set HF_MAMMOGRAM_URL in .env
#         - api_name (confirm with: client.view_api())

#     Args:
#         image_path (str): path to temp image file

#     Returns:
#         dict: { predicted_class, confidence, probabilities, model_version }
#     """
#     client = _get_client("mammogram")
#     if not client:
#         raise NotImplementedError(
#             "Mammogram classification space is not ready yet. "
#             "Set HF_MAMMOGRAM_URL in environment variables when available."
#         )

#     # ── Update api_name when DL team shares the Space ────
#     result = client.predict(
#         image    = handle_file(image_path),
#         api_name = "/predict"   # ← confirm with DL team
#     )

#     predicted_class = result.get("predicted_class")
#     confidence      = result.get("confidence (%)")

#     return {
#         "predicted_class": predicted_class,
#         "confidence":      confidence,
#         "probabilities":   _build_probabilities(predicted_class, confidence),
#         "model_version":   "mammogram_resnet50_v1",
#     }


# # ══════════════════════════════════════════════════════════
# #  MULTIMODAL CLASSIFICATION
# #  Called automatically when patient has BOTH ultrasound + mammogram
# #  ⚠️  Space not ready yet — placeholder
# # ══════════════════════════════════════════════════════════

# def predict_multimodal(ultrasound_path, mammogram_path):
#     """
#     Calls the multimodal HF Space using both images.
#     Triggered automatically after upload when patient has both scan types.

#     ⚠️  PLACEHOLDER — update when DL team shares:
#         - HF Space URL → set HF_MULTIMODAL_URL in .env
#         - Input param names (ultrasound + mammogram or different?)
#         - api_name

#     Args:
#         ultrasound_path (str): path or Cloudinary URL of ultrasound image
#         mammogram_path  (str): path or Cloudinary URL of mammogram image

#     Returns:
#         dict | None: { predicted_class, confidence, probabilities, model_version }
#                      None if space not configured — skipped silently
#     """
#     client = _get_client("multimodal")
#     if not client:
#         print("[ml_service] Multimodal space not configured yet — skipping.")
#         return None

#     try:
#         # ── Update param names when DL team shares the Space ──
#         result = client.predict(
#             ultrasound = handle_file(ultrasound_path),
#             mammogram  = handle_file(mammogram_path),
#             api_name   = "/predict"   # ← confirm with DL team
#         )

#         predicted_class = result.get("predicted_class")
#         confidence      = result.get("confidence (%)")

#         return {
#             "predicted_class": predicted_class,
#             "confidence":      confidence,
#             "probabilities":   _build_probabilities(predicted_class, confidence),
#             "model_version":   "multimodal_v1",
#         }

#     except Exception as e:
#         print(f"[ml_service] Multimodal prediction failed: {e}")
#         return None   # never block the main upload flow


# # ══════════════════════════════════════════════════════════
# #  ROUTE TO CORRECT MODEL
# #  Called by detection_service — picks the right function
# # ══════════════════════════════════════════════════════════

# def predict_detection(image_path, image_type):
#     """
#     Routes to the correct classification model based on image_type.

#     Args:
#         image_path (str): path to temp image file
#         image_type (str): "ultrasound" or "mammogram"

#     Returns:
#         dict: { predicted_class, confidence, probabilities, model_version }
#     """
#     if image_type == "ultrasound":
#         return predict_ultrasound(image_path)
#     elif image_type == "mammogram":
#         return predict_mammogram(image_path)
#     else:
#         raise ValueError(f"Unknown image_type: '{image_type}'. Must be 'ultrasound' or 'mammogram'.")


# # ══════════════════════════════════════════════════════════
# #  FALLBACK RECOMMENDATION
# #  Used until recommendation model is ready
# # ══════════════════════════════════════════════════════════

# def get_fallback_recommendation(predicted_class):
#     """
#     Returns a gentle recommendation text based on prediction.
#     Replace with actual recommendation model call when DL team shares it.
#     """
#     recommendations = {
#         "normal":    "Your scan looks good. Continue with regular check-ups as advised by your doctor.",
#         "benign":    "Your scan shows some findings. Please follow up with your doctor for further guidance.",
#         "malignant": "Your scan requires medical attention. Please contact your doctor as soon as possible.",
#     }
#     return recommendations.get(
#         predicted_class,
#         "Please consult your doctor to discuss your scan results."
#     )



import os
from typing import Literal
from gradio_client import Client, handle_file

# ── HF Space URLs ─────────────────────────────────────────
SPACE_URLS = {
    "ultrasound":  os.getenv("HF_ULTRASOUND_URL",  "https://mai1222-rosy-resslience.hf.space"),
    "mammogram":   os.getenv("HF_MAMMOGRAM_URL"),   # set when mammogram space is ready
    # "multimodal":  os.getenv("HF_MULTIMODAL_URL"),  # set when multimodal space is ready
}

# ── Client cache — one client per space, created once ─────
_clients = {}

LABELS = {
    0: "benign",
    1: "malignant",
    2: "normal",
}


def _get_client(space_key):
    """
    Returns a cached Gradio client for the given space.
    Returns None if the space URL is not configured yet.
    """
    if space_key not in _clients:
        url = SPACE_URLS.get(space_key)
        if not url:
            return None
        _clients[space_key] = Client(url)
        print(f"[ml_service] Connected to {space_key}: {url}")
    return _clients[space_key]


def _build_probabilities(predicted_class, confidence):
    """Distributes remaining % evenly across other classes."""
    all_classes   = ["benign", "malignant", "normal"]
    remaining     = round(100 - confidence, 2)
    other_classes = [c for c in all_classes if c != predicted_class]
    other_prob    = round(remaining / len(other_classes), 2)
    probs         = {c: other_prob for c in all_classes}
    probs[predicted_class] = confidence
    return probs


# ══════════════════════════════════════════════════════════
#  ULTRASOUND CLASSIFICATION
#  Calls existing HF Space (rosy_resslience)
# ══════════════════════════════════════════════════════════

def predict_ultrasound(image_path):
    """
    Calls the ultrasound classification HF Space.

    Args:
        image_path (str): path to temp image file

    Returns:
        dict: { predicted_class, confidence, probabilities, model_version }
    """
    client = _get_client("ultrasound")
    if not client:
        raise NotImplementedError(
            "Ultrasound classification space is not configured. "
            "Set HF_ULTRASOUND_URL in environment variables."
        )

    result = client.predict(
        image    = handle_file(image_path),
        api_name = "/predict"
    )

    predicted_class = result.get("predicted_class")
    confidence      = result.get("confidence (%)")

    return {
        "predicted_class": predicted_class,
        "confidence":      confidence,
        "probabilities":   _build_probabilities(predicted_class, confidence),
        "model_version":   "ultrasound_resnet50_v1",
    }


# ══════════════════════════════════════════════════════════
#  MAMMOGRAM CLASSIFICATION
#  ⚠️  Space not ready yet — placeholder
#  Update api_name once DL team shares the Space
# ══════════════════════════════════════════════════════════

def predict_mammogram(image_path):
    """
    Calls the mammogram classification HF Space.

    ⚠️  PLACEHOLDER — update when DL team shares:
        - HF Space URL → set HF_MAMMOGRAM_URL in .env
        - api_name (confirm with: client.view_api())

    Args:
        image_path (str): path to temp image file

    Returns:
        dict: { predicted_class, confidence, probabilities, model_version }
    """
    client = _get_client("mammogram")
    if not client:
        raise NotImplementedError(
            "Mammogram classification space is not ready yet. "
            "Set HF_MAMMOGRAM_URL in environment variables when available."
        )

    # ── Update api_name when DL team shares the Space ────
    result = client.predict(
        image    = handle_file(image_path),
        api_name = "/predict"   # ← confirm with DL team
    )

    predicted_class = result.get("predicted_class")
    confidence      = result.get("confidence (%)")

    return {
        "predicted_class": predicted_class,
        "confidence":      confidence,
        "probabilities":   _build_probabilities(predicted_class, confidence),
        "model_version":   "mammogram_resnet50_v1",
    }


# ══════════════════════════════════════════════════════════
#  MULTIMODAL CLASSIFICATION
#  Called automatically when patient has BOTH ultrasound + mammogram
#  ⚠️  Space not ready yet — placeholder
# ══════════════════════════════════════════════════════════

def predict_multimodal(ultrasound_path, mammogram_path):
    """
    Calls the multimodal HF Space using both images.
    Triggered automatically after upload when patient has both scan types.

    ⚠️  PLACEHOLDER — update when DL team shares:
        - HF Space URL → set HF_MULTIMODAL_URL in .env
        - Input param names (ultrasound + mammogram or different?)
        - api_name

    Args:
        ultrasound_path (str): path or Cloudinary URL of ultrasound image
        mammogram_path  (str): path or Cloudinary URL of mammogram image

    Returns:
        dict | None: { predicted_class, confidence, probabilities, model_version }
                     None if space not configured — skipped silently
    """
    client = _get_client("multimodal")
    if not client:
        print("[ml_service] Multimodal space not configured yet — skipping.")
        return None

    try:
        # ── Update param names when DL team shares the Space ──
        result = client.predict(
            ultrasound = handle_file(ultrasound_path),
            mammogram  = handle_file(mammogram_path),
            api_name   = "/predict"   # ← confirm with DL team
        )

        predicted_class = result.get("predicted_class")
        confidence      = result.get("confidence (%)")

        return {
            "predicted_class": predicted_class,
            "confidence":      confidence,
            "probabilities":   _build_probabilities(predicted_class, confidence),
            "model_version":   "multimodal_v1",
        }

    except Exception as e:
        print(f"[ml_service] Multimodal prediction failed: {e}")
        return None   # never block the main upload flow


# ══════════════════════════════════════════════════════════
#  ROUTE TO CORRECT MODEL
#  Called by detection_service — picks the right function
# ══════════════════════════════════════════════════════════

def predict_detection(image_path, image_type):
    """
    Routes to the correct classification model based on image_type.

    Args:
        image_path (str): path to temp image file
        image_type (str): "ultrasound" or "mammogram"

    Returns:
        dict: { predicted_class, confidence, probabilities, model_version }
    """
    if image_type == "ultrasound":
        return predict_ultrasound(image_path)
    elif image_type == "mammogram":
        return predict_mammogram(image_path)
    else:
        raise ValueError(f"Unknown image_type: '{image_type}'. Must be 'ultrasound' or 'mammogram'.")


# ══════════════════════════════════════════════════════════
#  RECOMMENDATION SYSTEM
#  Hybrid rule-based + risk-score system
#  Aligned with ACR BI-RADS guidelines
# ══════════════════════════════════════════════════════════

def _compute_risk_cnn(
    p_normal: float,
    p_benign: float,
    p_malignant: float,
    confidence: float,
) -> float:
    """
    Risk_CNN = (0.0 * P_normal) + (0.4 * P_benign) + (1.0 * P_malignant)
               + (0.3 * Uncertainty)

    Uncertainty = (1 - max(p_normal, p_benign, p_malignant)) * (1 - confidence)

    High confidence → uncertainty scaled down → model trusted more.
    Low confidence  → uncertainty scaled up   → risk nudged higher.
    """
    uncertainty = (1.0 - max(p_normal, p_benign, p_malignant)) * (1.0 - confidence)
    risk = (
        0.0 * p_normal
        + 0.4 * p_benign
        + 1.0 * p_malignant
        + 0.3 * uncertainty
    )
    return round(risk, 4)


def _device_weight(modality: str) -> float:
    """
    Reliability weight per modality:
      mammogram  → 0.70  (lower soft-tissue resolution)
      ultrasound → 0.85  (better soft-tissue resolution)
      multimodal → 0.95  (fuses both — highest reliability)
    """
    weights = {
        "mammogram":  0.70,
        "ultrasound": 0.85,
        "multimodal": 0.95,
    }
    return weights[modality]


def _age_risk(age: int) -> float:
    """
    Age risk — increases with age to reflect rising baseline breast cancer risk:
      < 40  → 0.3
      40–50 → 0.5
      50–60 → 0.7
      > 60  → 0.9
    """
    if age < 40:
        return 0.3
    elif age <= 50:
        return 0.5
    elif age <= 60:
        return 0.7
    else:
        return 0.9


def _risk_level(final_risk: float) -> str:
    if final_risk < 0.30:
        return "Low"
    elif final_risk < 0.60:
        return "Medium"
    elif final_risk < 0.85:
        return "High"
    else:
        return "Very High"


def _get_recommendation_text(
    predicted_label: str,
    modality: str,
    risk_level: str,
) -> str:
    """
    Returns a clinical recommendation based on predicted label,
    modality, and risk level — aligned with ACR BI-RADS guidelines.

    Key clinical rules:
      - Malignant → always biopsy regardless of risk level
      - Normal    → never escalate to additional imaging
      - Benign / High → biopsy, not MRI
    """
    label = predicted_label
    mod   = modality
    rl    = risk_level

    # ── Normal ────────────────────────────────────────────
    if label == "normal":
        if rl == "Low":
            return "Routine screening in 1–2 years"
        elif rl == "Medium":
            return "Routine screening in 12 months"
        else:   # High or Very High
            return "Routine screening in 12 months — consider clinical review given elevated risk factors"

    # ── Benign ────────────────────────────────────────────
    elif label == "benign":
        if mod == "mammogram":
            if rl == "Low":
                return "Short-interval follow-up in 6 months"
            elif rl == "Medium":
                return "Diagnostic ultrasound for further characterization"
            elif rl == "High":
                return "Biopsy recommended"
            else:  # Very High
                return "Biopsy recommended"

        elif mod in ("ultrasound", "multimodal"):
            if rl == "Low":
                return "Short-interval follow-up in 6 months"
            elif rl == "Medium":
                return "Short-term follow-up in 3 months"
            elif rl == "High":
                return "Ultrasound-guided biopsy recommended"
            else:  # Very High
                return "Ultrasound-guided biopsy recommended"

    # ── Malignant ─────────────────────────────────────────
    elif label == "malignant":
        if mod == "mammogram":
            return "Biopsy recommended"
        elif mod in ("ultrasound", "multimodal"):
            return "Ultrasound-guided biopsy recommended"

    # Fallback
    return "Incomplete — additional imaging evaluation needed"


def get_recommendation(
    modality: Literal["mammogram", "ultrasound", "multimodal"],
    age: int,
    predicted_label: Literal["normal", "benign", "malignant"],
    p_normal: float,
    p_benign: float,
    p_malignant: float,
    confidence: float,
) -> dict:
    """
    Compute a clinical recommendation for breast imaging results.

    Parameters
    ----------
    modality        : "mammogram", "ultrasound", or "multimodal"
    age             : Patient age in years (derived from date_of_birth)
    predicted_label : "normal", "benign", or "malignant"
    p_normal        : Model probability for Normal    (0.0 – 1.0)
    p_benign        : Model probability for Benign    (0.0 – 1.0)
    p_malignant     : Model probability for Malignant (0.0 – 1.0)
    confidence      : Overall model confidence        (0.0 – 1.0)

    Note: probabilities and confidence from the HF Space are percentages
    (e.g. 62.08). Divide by 100 before passing them here.

    Returns
    -------
    dict:
        "recommendation" : Clinical recommendation string
    """
    modality        = modality.lower()
    predicted_label = predicted_label.lower()

    # ── Validate modality ─────────────────────────────────
    if modality not in ("mammogram", "ultrasound", "multimodal"):
        raise ValueError("modality must be 'mammogram', 'ultrasound', or 'multimodal'")

    # ── Validate predicted label ──────────────────────────
    if predicted_label not in ("normal", "benign", "malignant"):
        raise ValueError("predicted_label must be 'normal', 'benign', or 'malignant'")

    # ── Validate probability ranges ───────────────────────
    for name, val in [
        ("p_normal",    p_normal),
        ("p_benign",    p_benign),
        ("p_malignant", p_malignant),
        ("confidence",  confidence),
    ]:
        if not (0.0 <= val <= 1.0):
            raise ValueError(f"{name} must be between 0.0 and 1.0, got {val}")

    # ── CNN risk (confidence-adjusted uncertainty) ────────
    risk_cnn = _compute_risk_cnn(p_normal, p_benign, p_malignant, confidence)

    # ── Device-adjusted risk ──────────────────────────────
    risk_device = round(risk_cnn * _device_weight(modality), 4)

    # ── Age risk ──────────────────────────────────────────
    risk_age = _age_risk(age)

    # ── Final risk score: 0.7 (device/CNN) + 0.3 (age) ───
    final_risk = round(0.7 * risk_device + 0.3 * risk_age, 4)

    # ── Risk level ────────────────────────────────────────
    rl = _risk_level(final_risk)

    # ── Recommendation ────────────────────────────────────
    recommendation = _get_recommendation_text(predicted_label, modality, rl)

    return {
        "recommendation": recommendation,
    }