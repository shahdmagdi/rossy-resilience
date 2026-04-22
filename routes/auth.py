# from flask import Blueprint, request, jsonify, make_response
# from app import limiter
# from services.auth_service import (
#     signup_patient,
#     verify_email,
#     resend_verification_code,
# )
# from services.doctor_auth_service import (
#     signup_doctor,
#     verify_doctor_email,
#     resend_doctor_verification_code,
# )
# from services.login_service import login_user, logout_user

# auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# # ── Cookie settings ───────────────────────────────────────
# SIGNUP_COOKIE_NAME     = "signup_session"
# SIGNUP_COOKIE_MAX_AGE  = 60 * 30    # 30 minutes
# ACCESS_COOKIE_MAX_AGE  = 3600       # 1 hour
# REFRESH_COOKIE_MAX_AGE = 2592000    # 30 days


# def _set_jwt_cookies(res, access_token, refresh_token):
#     """Helper to set both JWT cookies on a response."""
#     res.set_cookie("access_token",  access_token,  max_age=ACCESS_COOKIE_MAX_AGE,  httponly=True, samesite="Lax", secure=False)
#     res.set_cookie("refresh_token", refresh_token, max_age=REFRESH_COOKIE_MAX_AGE, httponly=True, samesite="Lax", secure=False)
#     return res


# # ══════════════════════════════════════════════════════════
# #  PATIENT SIGNUP
# # ══════════════════════════════════════════════════════════

# @auth_bp.route("/patient/signup", methods=["POST"])
# @limiter.limit("5 per minute; 20 per hour")
# def patient_signup():
#     data = request.get_json()
#     if not data:
#         return jsonify({"success": False, "message": "No data provided."}), 400

#     response, status, user_id = signup_patient(data)
#     res = make_response(jsonify(response), status)

#     if user_id:
#         res.set_cookie(SIGNUP_COOKIE_NAME, value=user_id, max_age=SIGNUP_COOKIE_MAX_AGE, httponly=True, samesite="Lax", secure=False)

#     return res


# @auth_bp.route("/patient/verify-email", methods=["POST"])
# @limiter.limit("5 per minute; 10 per hour")
# def patient_verify_email():
#     data = request.get_json()
#     if not data:
#         return jsonify({"success": False, "message": "No data provided."}), 400

#     user_id = request.cookies.get(SIGNUP_COOKIE_NAME)
#     code    = data.get("code", "").strip()

#     response, status, should_clear_cookie = verify_email(code, user_id)
#     res = make_response(jsonify(response), status)

#     if should_clear_cookie:
#         res.delete_cookie(SIGNUP_COOKIE_NAME)
#         _set_jwt_cookies(res, response["access_token"], response["refresh_token"])

#     return res


# @auth_bp.route("/patient/resend-code", methods=["POST"])
# @limiter.limit("3 per minute; 5 per hour")
# def patient_resend_code():
#     user_id  = request.cookies.get(SIGNUP_COOKIE_NAME)
#     response, status = resend_verification_code(user_id)
#     return jsonify(response), status


# # ══════════════════════════════════════════════════════════
# #  DOCTOR SIGNUP
# # ══════════════════════════════════════════════════════════

# @auth_bp.route("/doctor/signup", methods=["POST"])
# @limiter.limit("3 per minute; 10 per hour")
# def doctor_signup():
#     data = request.get_json()
#     if not data:
#         return jsonify({"success": False, "message": "No data provided."}), 400

#     response, status, user_id = signup_doctor(data)
#     res = make_response(jsonify(response), status)

#     if user_id:
#         res.set_cookie(SIGNUP_COOKIE_NAME, value=user_id, max_age=SIGNUP_COOKIE_MAX_AGE, httponly=True, samesite="Lax", secure=False)

#     return res


# @auth_bp.route("/doctor/verify-email", methods=["POST"])
# @limiter.limit("5 per minute; 10 per hour")
# def doctor_verify_email():
#     data = request.get_json()
#     if not data:
#         return jsonify({"success": False, "message": "No data provided."}), 400

#     user_id = request.cookies.get(SIGNUP_COOKIE_NAME)
#     code    = data.get("code", "").strip()

#     response, status, should_clear_cookie = verify_doctor_email(code, user_id)
#     res = make_response(jsonify(response), status)

#     if should_clear_cookie:
#         res.delete_cookie(SIGNUP_COOKIE_NAME)

#     return res


# @auth_bp.route("/doctor/resend-code", methods=["POST"])
# @limiter.limit("3 per minute; 5 per hour")
# def doctor_resend_code():
#     user_id  = request.cookies.get(SIGNUP_COOKIE_NAME)
#     response, status = resend_doctor_verification_code(user_id)
#     return jsonify(response), status


# # ══════════════════════════════════════════════════════════
# #  UNIFIED LOGIN — one route for all roles
# # ══════════════════════════════════════════════════════════

# @auth_bp.route("/login", methods=["POST"])
# @limiter.limit("10 per minute; 50 per hour")
# def login():
#     """
#     Single login for patient, doctor, and admin.
#     Role is detected automatically from the database.

#     Required: email, password
#     """
#     data = request.get_json()
#     if not data:
#         return jsonify({"success": False, "message": "No data provided."}), 400

#     response, status, tokens = login_user(data)
#     res = make_response(jsonify(response), status)

#     if tokens:
#         _set_jwt_cookies(res, *tokens)

#     return res


# # ══════════════════════════════════════════════════════════
# #  LOGOUT — works for all roles
# # ══════════════════════════════════════════════════════════

# @auth_bp.route("/logout", methods=["POST"])
# def logout():
#     """Clears JWT cookies. Works for patient, doctor, and admin."""
#     response, status = logout_user()
#     res = make_response(jsonify(response), status)
#     res.delete_cookie("access_token")
#     res.delete_cookie("refresh_token")
#     return res
















from flask import Blueprint, request, jsonify, make_response
from app import limiter
from services.auth_service import (
    signup_patient,
    verify_email,
    resend_verification_code,
)
from services.doctor_auth_service import (
    signup_doctor,
    verify_doctor_email,
    resend_doctor_verification_code,
)
from services.login_service import login_user, logout_user
from models import User, UserRole
from models.doctor import Doctor, VerificationStatus
from services.account_service import forgot_password, verify_reset_code, resend_reset_code

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

SIGNUP_COOKIE_NAME     = "signup_session"
SIGNUP_COOKIE_MAX_AGE  = 60 * 30
ACCESS_COOKIE_MAX_AGE  = 3600
REFRESH_COOKIE_MAX_AGE = 2592000
RESET_COOKIE_NAME      = "reset_session"
RESET_COOKIE_MAX_AGE   = 60 * 20


def _set_jwt_cookies(res, access_token, refresh_token):
    res.set_cookie("access_token",  access_token,  max_age=ACCESS_COOKIE_MAX_AGE,  httponly=True, samesite="Lax", secure=False)
    res.set_cookie("refresh_token", refresh_token, max_age=REFRESH_COOKIE_MAX_AGE, httponly=True, samesite="Lax", secure=False)
    return res


@auth_bp.route("/patient/signup", methods=["POST", "OPTIONS"])
@limiter.limit("5 per minute; 20 per hour")
def patient_signup():
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "message": "No data provided."}), 400
    response, status, user_id = signup_patient(data)
    res = make_response(jsonify(response), status)
    if user_id:
        res.set_cookie(SIGNUP_COOKIE_NAME, value=user_id, max_age=SIGNUP_COOKIE_MAX_AGE, httponly=True, samesite="Lax", secure=False)
    return res


@auth_bp.route("/patient/verify-email", methods=["POST", "OPTIONS"])
@limiter.limit("5 per minute; 10 per hour")
def patient_verify_email():
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "message": "No data provided."}), 400
    user_id = request.cookies.get(SIGNUP_COOKIE_NAME)
    code    = data.get("code", "").strip()
    response, status, should_clear_cookie = verify_email(code, user_id)
    res = make_response(jsonify(response), status)
    if should_clear_cookie:
        res.delete_cookie(SIGNUP_COOKIE_NAME)
        _set_jwt_cookies(res, response["access_token"], response["refresh_token"])
    return res


@auth_bp.route("/patient/resend-code", methods=["POST", "OPTIONS"])
@limiter.limit("3 per minute; 5 per hour")
def patient_resend_code():
    user_id = request.cookies.get(SIGNUP_COOKIE_NAME)
    response, status = resend_verification_code(user_id)
    return jsonify(response), status


@auth_bp.route("/doctor/signup", methods=["POST", "OPTIONS"])
@limiter.limit("3 per minute; 10 per hour")
def doctor_signup():
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "message": "No data provided."}), 400
    response, status, user_id = signup_doctor(data)
    res = make_response(jsonify(response), status)
    if user_id:
        res.set_cookie(SIGNUP_COOKIE_NAME, value=user_id, max_age=SIGNUP_COOKIE_MAX_AGE, httponly=True, samesite="Lax", secure=False)
    return res


@auth_bp.route("/doctor/verify-email", methods=["POST", "OPTIONS"])
@limiter.limit("5 per minute; 10 per hour")
def doctor_verify_email():
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "message": "No data provided."}), 400
    user_id = request.cookies.get(SIGNUP_COOKIE_NAME)
    code    = data.get("code", "").strip()
    response, status, should_clear_cookie = verify_doctor_email(code, user_id)
    res = make_response(jsonify(response), status)
    if should_clear_cookie:
        res.delete_cookie(SIGNUP_COOKIE_NAME)
    return res


@auth_bp.route("/doctor/resend-code", methods=["POST", "OPTIONS"])
@limiter.limit("3 per minute; 5 per hour")
def doctor_resend_code():
    user_id = request.cookies.get(SIGNUP_COOKIE_NAME)
    response, status = resend_doctor_verification_code(user_id)
    return jsonify(response), status


@auth_bp.route("/login", methods=["POST", "OPTIONS"])
@limiter.limit("10 per minute; 50 per hour")
def login():
    # Try multiple ways to get the data
    data = request.get_json(force=True, silent=True)
    
    if not data:
        # fallback: try reading raw body
        try:
            import json
            data = json.loads(request.data.decode('utf-8'))
        except Exception:
            data = None

    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "message": "No data provided."}), 400

    response, status, tokens = login_user(data)
    res = make_response(jsonify(response), status)
    if tokens:
        _set_jwt_cookies(res, *tokens)
    return res

@auth_bp.route("/logout", methods=["POST", "OPTIONS"])
def logout():
    response, status = logout_user()
    res = make_response(jsonify(response), status)
    res.delete_cookie("access_token")
    res.delete_cookie("refresh_token")
    return res


@auth_bp.route("/signup", methods=["POST", "OPTIONS"])
@limiter.limit("5 per minute; 20 per hour")
def unified_signup():
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "message": "No data provided."}), 400

    role = data.get("role", "patient").lower()

    if "name" in data and "full_name" not in data:
        data["full_name"] = data.pop("name")

    if "confirm_password" not in data:
        data["confirm_password"] = data.get("password", "")

    if role == "doctor":
        response, status, user_id = signup_doctor(data)
    else:
        response, status, user_id = signup_patient(data)

    res = make_response(jsonify(response), status)
    if user_id:
        res.set_cookie(
            SIGNUP_COOKIE_NAME,
            value=user_id,
            max_age=SIGNUP_COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
            secure=False,
        )
    return res


@auth_bp.route("/verify-email", methods=["POST", "OPTIONS"])
@limiter.limit("5 per minute; 10 per hour")
def unified_verify_email():
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "message": "No data provided."}), 400

    code    = data.get("code", "").strip()
    user_id = request.cookies.get(SIGNUP_COOKIE_NAME)

    if not user_id:
        return jsonify({"success": False, "message": "Session expired. Please sign up again."}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    if user.role == UserRole.doctor:
        response, status, should_clear_cookie = verify_doctor_email(code, user_id)
    else:
        response, status, should_clear_cookie = verify_email(code, user_id)

    res = make_response(jsonify(response), status)

    if should_clear_cookie:
        res.delete_cookie(SIGNUP_COOKIE_NAME)
        if user and user.role == UserRole.patient:
            _set_jwt_cookies(res, response.get("access_token"), response.get("refresh_token"))

    return res


@auth_bp.route("/resend-verification", methods=["POST", "OPTIONS"])
@limiter.limit("3 per minute; 5 per hour")
def unified_resend_verification():
    user_id = request.cookies.get(SIGNUP_COOKIE_NAME)
    if not user_id:
        return jsonify({"success": False, "message": "Session expired. Please sign up again."}), 401

    user = User.query.get(user_id)
    if user and user.role == UserRole.doctor:
        response, status = resend_doctor_verification_code(user_id)
    else:
        response, status = resend_verification_code(user_id)

    return jsonify(response), status


@auth_bp.route("/forgot-password", methods=["POST", "OPTIONS"])
@limiter.limit("3 per minute; 5 per hour")
def auth_forgot_password():
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "message": "No data provided."}), 400

    response, status, user_id = forgot_password(data)
    res = make_response(jsonify(response), status)

    if user_id:
        res.set_cookie(
            RESET_COOKIE_NAME,
            value=user_id,
            max_age=RESET_COOKIE_MAX_AGE,
            httponly=True,
            samesite="Lax",
            secure=False,
        )
    return res


@auth_bp.route("/reset-password", methods=["POST", "OPTIONS"])
@limiter.limit("5 per minute; 10 per hour")
def auth_reset_password():
    data = request.get_json(force=True, silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"success": False, "message": "No data provided."}), 400

    user_id = request.cookies.get(RESET_COOKIE_NAME)
    response, status, should_clear_cookie = verify_reset_code(data, user_id)
    res = make_response(jsonify(response), status)

    if should_clear_cookie:
        res.delete_cookie(RESET_COOKIE_NAME)

    return res


@auth_bp.route("/debug-route", methods=["GET"])
def debug_route():
    return jsonify({"message": "Auth blueprint is working!", "endpoint": "/api/auth/debug-route"}), 200


@auth_bp.route("/doctor/approval-status", methods=["GET", "OPTIONS"])
def doctor_approval_status():
    user_id = request.cookies.get(SIGNUP_COOKIE_NAME)
    if not user_id:
        return jsonify({"success": False, "message": "Session expired."}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    if user.role != UserRole.doctor:
        return jsonify({"success": False, "message": "Not a doctor."}), 403

    doctor = Doctor.query.filter_by(doctor_id=user_id).first()
    if not doctor:
        return jsonify({"success": False, "message": "Doctor profile not found."}), 404

    return jsonify({
        "success": True,
        "user": {
            "user_id":             str(user.user_id),
            "email":               user.email,
            "full_name":           user.full_name,
            "role":                "doctor",
            "verification_status": doctor.verification_status.value,
            "is_approved":         doctor.verification_status == VerificationStatus.approved,
        }
    }), 200


@auth_bp.route("/verification-status", methods=["GET", "OPTIONS"])
def verification_status():
    user_id = request.cookies.get(SIGNUP_COOKIE_NAME)
    if not user_id:
        return jsonify({"success": False, "message": "Session expired."}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    return jsonify({
        "success": True,
        "user": {
            "user_id":        str(user.user_id),
            "email":          user.email,
            "full_name":      user.full_name,
            "role":           user.role.value,
            "email_verified": user.email_verified,
            "is_active":      user.is_active,
        }
    }), 200