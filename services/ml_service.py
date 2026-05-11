# import os
# from typing import Literal
# from gradio_client import Client, handle_file

# # ── HF Space URLs ─────────────────────────────────────────
# SPACE_URLS = {
#     "ultrasound":  os.getenv("HF_ULTRASOUND_URL",  "https://mai1222-rosy-resslience.hf.space"),
#     "mammogram":   os.getenv("HF_MAMMOGRAM_URL"),   
#     "multimodal":  os.getenv("HF_MULTIMODAL_URL"),  
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
# # ══════════════════════════════════════════════════════════

# def predict_multimodal(mammogram_path, ultrasound_path):
#     """
#     Calls the late fusion HF Space with both mammogram and ultrasound images.
 
#     The space uses EfficientNetV2L for mammogram + ResNet50 for ultrasound
#     combined with a Logistic Regression fusion model.
 
#     Args:
#         mammogram_path  (str): local path to mammogram image
#         ultrasound_path (str): local path to ultrasound image
 
#     Returns:
#         dict | None: {
#             predicted_class, confidence, probabilities, model_version
#         }
#         None if space not configured — skipped silently
#     """
#     client = _get_client("multimodal")
#     if not client:
#         print("[ml_service] Multimodal space not configured — skipping.")
#         return None
 
#     try:
#         # Space uses run_inference(mammo_img, us_img) with numpy inputs
#         # gradio_client handles numpy spaces with handle_file
#         result = client.predict(
#             mammo_img = handle_file(mammogram_path),
#             us_img    = handle_file(ultrasound_path),
#             api_name  = "/run_inference"
#         )
 
#         # Check for error response from space
#         if isinstance(result, dict) and "error" in result:
#             print(f"[ml_service] Multimodal space error: {result['error']}")
#             return None
 
#         predicted_class = result.get("predicted_class")
#         confidence      = result.get("confidence (%)")
 
#         # Space returns full probabilities including normal: 0
#         probabilities = result.get("probabilities") or _build_probabilities(
#             predicted_class, confidence
#         )
 
#         return {
#             "predicted_class": predicted_class,
#             "confidence":      confidence,
#             "probabilities":   probabilities,
#             "model_version":   "multimodal_late_fusion_v1",
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
# #  RECOMMENDATION SYSTEM
# #  Hybrid rule-based + risk-score system
# #  Aligned with ACR BI-RADS guidelines
# # ══════════════════════════════════════════════════════════

# def _compute_risk_cnn(
#     p_normal: float,
#     p_benign: float,
#     p_malignant: float,
#     confidence: float,
# ) -> float:
#     """
#     Risk_CNN = (0.0 * P_normal) + (0.4 * P_benign) + (1.0 * P_malignant)
#                + (0.3 * Uncertainty)

#     Uncertainty = (1 - max(p_normal, p_benign, p_malignant)) * (1 - confidence)

#     High confidence → uncertainty scaled down → model trusted more.
#     Low confidence  → uncertainty scaled up   → risk nudged higher.
#     """
#     uncertainty = (1.0 - max(p_normal, p_benign, p_malignant)) * (1.0 - confidence)
#     risk = (
#         0.0 * p_normal
#         + 0.4 * p_benign
#         + 1.0 * p_malignant
#         + 0.3 * uncertainty
#     )
#     return round(risk, 4)


# def _device_weight(modality: str) -> float:
#     """
#     Reliability weight per modality:
#       mammogram  → 0.70  (lower soft-tissue resolution)
#       ultrasound → 0.85  (better soft-tissue resolution)
#       multimodal → 0.95  (fuses both — highest reliability)
#     """
#     weights = {
#         "mammogram":  0.70,
#         "ultrasound": 0.85,
#         "multimodal": 0.95,
#     }
#     return weights[modality]


# def _age_risk(age: int) -> float:
#     """
#     Age risk — increases with age to reflect rising baseline breast cancer risk:
#       < 40  → 0.3
#       40–50 → 0.5
#       50–60 → 0.7
#       > 60  → 0.9
#     """
#     if age < 40:
#         return 0.3
#     elif age <= 50:
#         return 0.5
#     elif age <= 60:
#         return 0.7
#     else:
#         return 0.9


# def _risk_level(final_risk: float) -> str:
#     if final_risk < 0.30:
#         return "Low"
#     elif final_risk < 0.60:
#         return "Medium"
#     elif final_risk < 0.85:
#         return "High"
#     else:
#         return "Very High"


# def _get_recommendation_text(
#     predicted_label: str,
#     modality: str,
#     risk_level: str,
# ) -> str:
#     """
#     Returns a clinical recommendation based on predicted label,
#     modality, and risk level — aligned with ACR BI-RADS guidelines.

#     Key clinical rules:
#       - Malignant → always biopsy regardless of risk level
#       - Normal    → never escalate to additional imaging
#       - Benign / High → biopsy, not MRI
#     """
#     label = predicted_label
#     mod   = modality
#     rl    = risk_level

#     # ── Normal ────────────────────────────────────────────
#     if label == "normal":
#         if rl == "Low":
#             return "Routine screening in 1–2 years"
#         elif rl == "Medium":
#             return "Routine screening in 12 months"
#         else:   # High or Very High
#             return "Routine screening in 12 months — consider clinical review given elevated risk factors"

#     # ── Benign ────────────────────────────────────────────
#     elif label == "benign":
#         if mod == "mammogram":
#             if rl == "Low":
#                 return "Short-interval follow-up in 6 months"
#             elif rl == "Medium":
#                 return "Diagnostic ultrasound for further characterization"
#             elif rl == "High":
#                 return "Biopsy recommended"
#             else:  # Very High
#                 return "Biopsy recommended"

#         elif mod in ("ultrasound", "multimodal"):
#             if rl == "Low":
#                 return "Short-interval follow-up in 6 months"
#             elif rl == "Medium":
#                 return "Short-term follow-up in 3 months"
#             elif rl == "High":
#                 return "Ultrasound-guided biopsy recommended"
#             else:  # Very High
#                 return "Ultrasound-guided biopsy recommended"

#     # ── Malignant ─────────────────────────────────────────
#     elif label == "malignant":
#         if mod == "mammogram":
#             return "Biopsy recommended"
#         elif mod in ("ultrasound", "multimodal"):
#             return "Ultrasound-guided biopsy recommended"

#     # Fallback
#     return "Incomplete — additional imaging evaluation needed"


# def get_recommendation(
#     modality: Literal["mammogram", "ultrasound", "multimodal"],
#     age: int,
#     predicted_label: Literal["normal", "benign", "malignant"],
#     p_normal: float,
#     p_benign: float,
#     p_malignant: float,
#     confidence: float,
# ) -> dict:
#     """
#     Compute a clinical recommendation for breast imaging results.

#     Parameters
#     ----------
#     modality        : "mammogram", "ultrasound", or "multimodal"
#     age             : Patient age in years (derived from date_of_birth)
#     predicted_label : "normal", "benign", or "malignant"
#     p_normal        : Model probability for Normal    (0.0 – 1.0)
#     p_benign        : Model probability for Benign    (0.0 – 1.0)
#     p_malignant     : Model probability for Malignant (0.0 – 1.0)
#     confidence      : Overall model confidence        (0.0 – 1.0)

#     Note: probabilities and confidence from the HF Space are percentages
#     (e.g. 62.08). Divide by 100 before passing them here.

#     Returns
#     -------
#     dict:
#         "recommendation" : Clinical recommendation string
#     """
#     modality        = modality.lower()
#     predicted_label = predicted_label.lower()

#     # ── Validate modality ─────────────────────────────────
#     if modality not in ("mammogram", "ultrasound", "multimodal"):
#         raise ValueError("modality must be 'mammogram', 'ultrasound', or 'multimodal'")

#     # ── Validate predicted label ──────────────────────────
#     if predicted_label not in ("normal", "benign", "malignant"):
#         raise ValueError("predicted_label must be 'normal', 'benign', or 'malignant'")

#     # ── Validate probability ranges ───────────────────────
#     for name, val in [
#         ("p_normal",    p_normal),
#         ("p_benign",    p_benign),
#         ("p_malignant", p_malignant),
#         ("confidence",  confidence),
#     ]:
#         if not (0.0 <= val <= 1.0):
#             raise ValueError(f"{name} must be between 0.0 and 1.0, got {val}")

#     # ── CNN risk (confidence-adjusted uncertainty) ────────
#     risk_cnn = _compute_risk_cnn(p_normal, p_benign, p_malignant, confidence)

#     # ── Device-adjusted risk ──────────────────────────────
#     risk_device = round(risk_cnn * _device_weight(modality), 4)

#     # ── Age risk ──────────────────────────────────────────
#     risk_age = _age_risk(age)

#     # ── Final risk score: 0.7 (device/CNN) + 0.3 (age) ───
#     final_risk = round(0.7 * risk_device + 0.3 * risk_age, 4)

#     # ── Risk level ────────────────────────────────────────
#     rl = _risk_level(final_risk)

#     # ── Recommendation ────────────────────────────────────
#     recommendation = _get_recommendation_text(predicted_label, modality, rl)

#     return {
#         "recommendation": recommendation,
#     }


import os
from typing import Literal
from gradio_client import Client, handle_file

# ── HF Space URLs ─────────────────────────────────────────
SPACE_URLS = {
    "ultrasound": os.getenv("HF_ULTRASOUND_URL", "https://mai1222-rosy-resslience.hf.space"),
    "mammogram":  os.getenv("HF_MAMMOGRAM_URL"),
    "multimodal": os.getenv("HF_MULTIMODAL_URL"),
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
    """
    Distributes remaining probability evenly across the other two classes.

    Args:
        predicted_class (str): "normal", "benign", or "malignant"
        confidence      (float): percentage, e.g. 62.08 — stored as-is;
                                 callers divide by 100 before get_recommendation

    Returns:
        dict: { "normal": float, "benign": float, "malignant": float }
              values are percentages, e.g. { "malignant": 62.08, "benign": 18.96, "normal": 18.96 }
    """
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
        image_path (str): local path to temp image file

    Returns:
        dict: {
            predicted_class (str):   "normal" | "benign" | "malignant"
            confidence      (float): percentage, e.g. 62.08
            probabilities   (dict):  { "normal": %, "benign": %, "malignant": % }
            model_version   (str)
        }
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
# ══════════════════════════════════════════════════════════

def predict_mammogram(image_path):
    """
    Calls the mammogram classification HF Space.

    ⚠️  PLACEHOLDER — update when DL team shares:
        - HF Space URL → set HF_MAMMOGRAM_URL in .env
        - api_name     → confirm with: client.view_api()

    Args:
        image_path (str): local path to temp image file

    Returns:
        dict: {
            predicted_class (str):   "normal" | "benign" | "malignant"
            confidence      (float): percentage, e.g. 62.08
            probabilities   (dict):  { "normal": %, "benign": %, "malignant": % }
            model_version   (str)
        }
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
#  Called automatically when patient has BOTH ultrasound + mammogram.
#
#  Signature:  predict_multimodal(mammogram_path, ultrasound_path)
#
#  IMPORTANT — argument order:
#    mammogram_path first, ultrasound_path second.
#    This matches the HF Space's run_inference(mammo_img, us_img) API.
#    _check_and_run_multimodal in detection_service.py must call this
#    in the same order.
#
#  Path types accepted by handle_file():
#    - Local filesystem path (str)  → used for the newly uploaded scan
#    - Public URL (str)             → used for the existing Cloudinary scan
#  Both are valid; gradio_client handles the difference transparently.
# ══════════════════════════════════════════════════════════

def predict_multimodal(mammogram_path, ultrasound_path):
    """
    Calls the late-fusion HF Space with both mammogram and ultrasound images.

    The space uses EfficientNetV2L (mammogram) + ResNet50 (ultrasound)
    combined with a Logistic Regression fusion model.

    Args:
        mammogram_path  (str): local path OR public Cloudinary URL for mammogram
        ultrasound_path (str): local path OR public Cloudinary URL for ultrasound

    Returns:
        dict | None: {
            predicted_class (str):   "normal" | "benign" | "malignant"
            confidence      (float): percentage, e.g. 62.08
            probabilities   (dict):  { "normal": %, "benign": %, "malignant": % }
            model_version   (str)
        }
        Returns None if the space is not configured or if prediction fails
        — the main upload flow continues unaffected.
    """
    client = _get_client("multimodal")
    if not client:
        print("[ml_service] Multimodal space not configured — skipping.")
        return None

    try:
        result = client.predict(
            mammo_img = handle_file(mammogram_path),
            us_img    = handle_file(ultrasound_path),
            api_name  = "/run_inference"
        )

        # Guard against error responses from the space
        if isinstance(result, dict) and "error" in result:
            print(f"[ml_service] Multimodal space returned error: {result['error']}")
            return None

        predicted_class = result.get("predicted_class")
        confidence      = result.get("confidence (%)")

        # Space may return full per-class probabilities (preferred).
        # Fall back to _build_probabilities if absent.
        raw_probs    = result.get("probabilities")
        probabilities = raw_probs if raw_probs else _build_probabilities(
            predicted_class, confidence
        )

        # Normalise key name: some space versions use "normal: 0" inside
        # probabilities — ensure the three expected keys are always present.
        for key in ("normal", "benign", "malignant"):
            probabilities.setdefault(key, 0.0)

        return {
            "predicted_class": predicted_class,
            "confidence":      confidence,
            "probabilities":   probabilities,
            "model_version":   "multimodal_late_fusion_v1",
        }

    except Exception as e:
        print(f"[ml_service] Multimodal prediction failed: {e}")
        return None  # never block the main upload flow


# ══════════════════════════════════════════════════════════
#  ROUTE TO CORRECT MODEL
#  Called by detection_service — picks the right function
# ══════════════════════════════════════════════════════════

def predict_detection(image_path, image_type):
    """
    Routes to the correct single-modality classification model.

    Args:
        image_path (str): local path to temp image file
        image_type (str): "ultrasound" or "mammogram"

    Returns:
        dict: { predicted_class, confidence, probabilities, model_version }

    Raises:
        NotImplementedError: if the target HF Space is not configured
        ValueError:          if image_type is unrecognised
    """
    if image_type == "ultrasound":
        return predict_ultrasound(image_path)
    elif image_type == "mammogram":
        return predict_mammogram(image_path)
    else:
        raise ValueError(
            f"Unknown image_type: '{image_type}'. Must be 'ultrasound' or 'mammogram'."
        )


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

    All inputs must be in [0.0, 1.0].
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

    IMPORTANT: probabilities and confidence returned by the HF Spaces are
    percentages (e.g. 62.08). Always divide by 100 before passing them here.
    This applies to both single-modality and multimodal results.

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