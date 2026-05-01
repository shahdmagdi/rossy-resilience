# from datetime import datetime
# from app import db, bcrypt
# from models import User, Doctor, UserRole, VerificationStatus
# from flask_jwt_extended import create_access_token, create_refresh_token


# # ══════════════════════════════════════════════════════════
# #  HELPERS
# # ══════════════════════════════════════════════════════════

# def _generate_tokens(user_id):
#     access_token  = create_access_token(identity=str(user_id))
#     refresh_token = create_refresh_token(identity=str(user_id))
#     return access_token, refresh_token


# def _update_last_login(user):
#     user.last_login = datetime.utcnow()
#     db.session.commit()


# # ══════════════════════════════════════════════════════════
# #  UNIFIED LOGIN — handles patient, doctor, and admin
# # ══════════════════════════════════════════════════════════

# def login_user(data):
#     """
#     Single login endpoint for all roles.
#     Role is detected automatically from the database.

#     Returns: (response_dict, http_status_code, tokens_or_None)
#     tokens = (access_token, refresh_token) on success, None on failure
#     """

#     email    = data.get("email", "").strip().lower()
#     password = data.get("password", "")

#     # 1. Validate required fields
#     if not email or not password:
#         return {"success": False, "message": "Email and password are required."}, 400, None

#     # 2. Find user — same error for wrong email or wrong password
#     #    (prevents attackers from knowing which emails are registered)
#     user = User.query.filter_by(email=email).first()
#     if not user or not bcrypt.check_password_hash(user.password_hash, password):
#         return {"success": False, "message": "Invalid email or password."}, 401, None

#     # 3. Email must be verified for all roles
#     if not user.email_verified:
#         return {
#             "success":    False,
#             "message":    "Please verify your email before logging in.",
#             "user_id":    str(user.user_id),
#             "unverified": True,
#         }, 403, None

#     # 4. Run role-specific checks
#     if user.role == UserRole.patient:
#         return _patient_checks(user)

#     elif user.role == UserRole.doctor:
#         return _doctor_checks(user)

#     elif user.role == UserRole.admin:
#         return _admin_checks(user)

#     return {"success": False, "message": "Unknown role."}, 400, None


# # ══════════════════════════════════════════════════════════
# #  ROLE-SPECIFIC CHECKS
# # ══════════════════════════════════════════════════════════

# def _patient_checks(user):
#     if not user.is_active:
#         return {
#             "success": False,
#             "message": "Your account has been deactivated. Please contact support."
#         }, 403, None

#     _update_last_login(user)
#     access_token, refresh_token = _generate_tokens(user.user_id)

#     return {
#         "success": True,
#         "message": f"Welcome back, {user.full_name}!",
#         "role":    "patient",
#         "user":    user.to_dict(),
#     }, 200, (access_token, refresh_token)


# def _doctor_checks(user):
#     doctor = Doctor.query.get(user.user_id)

#     if doctor.verification_status == VerificationStatus.pending:
#         return {
#             "success": False,
#             "message": "Your account is pending admin approval. We will notify you by email once reviewed.",
#             "status":  "pending_approval",
#         }, 403, None

#     if doctor.verification_status == VerificationStatus.rejected:
#         return {
#             "success": False,
#             "message": "Your account was not approved. Please contact support.",
#             "status":  "rejected",
#         }, 403, None

#     if not user.is_active:
#         return {
#             "success": False,
#             "message": "Your account has been deactivated. Please contact support."
#         }, 403, None

#     _update_last_login(user)
#     access_token, refresh_token = _generate_tokens(user.user_id)

#     return {
#         "success": True,
#         "message": f"Welcome back, Dr. {user.full_name}!",
#         "role":    "doctor",
#         "user":    {**user.to_dict(), **doctor.to_dict()},
#     }, 200, (access_token, refresh_token)


# def _admin_checks(user):
#     if not user.is_active:
#         return {
#             "success": False,
#             "message": "Your account has been deactivated."
#         }, 403, None

#     _update_last_login(user)
#     access_token, refresh_token = _generate_tokens(user.user_id)

#     return {
#         "success": True,
#         "message": f"Welcome back, {user.full_name}!",
#         "role":    "admin",
#         "user":    user.to_dict(),
#     }, 200, (access_token, refresh_token)


# # ══════════════════════════════════════════════════════════
# #  LOGOUT
# # ══════════════════════════════════════════════════════════

# def logout_user():
#     return {"success": True, "message": "Logged out successfully."}, 200











# from datetime import datetime
# from app import db, bcrypt
# from models import User, Doctor, UserRole, VerificationStatus
# from flask_jwt_extended import create_access_token, create_refresh_token
# from flask_jwt_extended import get_jwt
# from app import redis_client

# # ================= HELPERS =================

# def _generate_tokens(user_id):
#     access_token = create_access_token(identity=str(user_id))
#     refresh_token = create_refresh_token(identity=str(user_id))
#     return access_token, refresh_token


# def _update_last_login(user):
#     user.last_login = datetime.utcnow()
#     db.session.commit()


# # ================= LOGIN =================

# def login_user(data):
#     email    = str(data.get("email") or "").strip().lower()
#     password = str(data.get("password") or "")

#     # ---------- VALIDATION ----------
#     if not email or not password:
#         return {"success": False, "message": "Email and password are required."}, 400, None

#     # ---------- FIND USER ----------
#     user = User.query.filter_by(email=email).first()

#     # ---------- SAFE PASSWORD CHECK ----------
#     if not user:
#         return {"success": False, "message": "Invalid email or password."}, 401, None

#     if not user.password_hash:
#         return {"success": False, "message": "Invalid email or password."}, 401, None

#     if not bcrypt.check_password_hash(user.password_hash, password):
#         return {"success": False, "message": "Invalid email or password."}, 401, None

#     # ---------- EMAIL VERIFICATION ----------
#     if not user.email_verified:
#         return {
#             "success": False,
#             "message": "Please verify your email before logging in.",
#             "user_id": str(user.user_id),
#         }, 403, None

#     # ---------- ROLE ROUTING ----------
#     if user.role == UserRole.patient:
#         return _patient_login(user)

#     if user.role == UserRole.doctor:
#         return _doctor_login(user)

#     if user.role == UserRole.admin:
#         return _admin_login(user)

#     return {"success": False, "message": "Invalid role."}, 400, None


# # ================= PATIENT =================

# def _patient_login(user):
#     try:
#         _update_last_login(user)
#         tokens = _generate_tokens(user.user_id)

#         return {
#             "success": True,
#             "message": "Login successful",
#             "role": "patient",
#             "user": user.to_dict(),
#         }, 200, tokens

#     except Exception as e:
#         return {"success": False, "message": str(e)}, 500, None


# # ================= DOCTOR =================

# def _doctor_login(user):
#     try:
#         doctor = Doctor.query.get(user.user_id)

#         # SAFE CHECK
#         if not doctor:
#             return {
#                 "success": False,
#                 "message": "Doctor profile not found."
#             }, 404, None

#         if doctor.verification_status == VerificationStatus.pending:
#             return {
#                 "success": False,
#                 "message": "Account pending admin approval.",
#                 "status": "pending_approval",
#             }, 403, None

#         if doctor.verification_status == VerificationStatus.rejected:
#             return {
#                 "success": False,
#                 "message": "Account rejected by admin."
#             }, 403, None

#         _update_last_login(user)
#         tokens = _generate_tokens(user.user_id)

#         return {
#             "success": True,
#             "message": "Login successful",
#             "role": "doctor",
#             "user": {**user.to_dict(), **doctor.to_dict()},
#         }, 200, tokens

#     except Exception as e:
#         return {"success": False, "message": str(e)}, 500, None


# # ================= ADMIN =================

# def _admin_login(user):
#     try:
#         _update_last_login(user)
#         tokens = _generate_tokens(user.user_id)

#         return {
#             "success": True,
#             "message": "Login successful",
#             "role": "admin",
#             "user": user.to_dict(),
#         }, 200, tokens

#     except Exception as e:
#         return {"success": False, "message": str(e)}, 500, None


# # ================= LOGOUT =================

# # def logout_user():
# #     return {"success": True, "message": "Logged out successfully."}, 200

# def logout_user():
#     try:
#         jti = get_jwt()["jti"]
#         # Blacklist for 1 hour — matches access token lifetime
#         redis_client.setex(f"blacklist:{jti}", 3600, "true")
#     except Exception:
#         pass   # still logout cleanly even if Redis fails
#     return {"success": True, "message": "Logged out successfully."}, 200






from datetime import datetime, timedelta
from app import db, bcrypt
from models import User, Doctor, Patient, UserRole, VerificationStatus
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
)
from app import redis_client


# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════

def _generate_tokens(user_id):
    access_token  = create_access_token(identity=str(user_id))
    refresh_token = create_refresh_token(identity=str(user_id))
    return access_token, refresh_token


def _generate_temp_token(user_id):
    """
    Short-lived token (10 minutes) used ONLY for the consent step.
    Cannot access any other protected route — enforced via the
    'scope': 'consent_only' claim checked in the consent endpoint.
    """
    return create_access_token(
        identity=str(user_id),
        expires_delta=timedelta(minutes=10),
        additional_claims={"temp": True, "scope": "consent_only"},
    )


def _update_last_login(user):
    user.last_login = datetime.utcnow()
    db.session.commit()


# ══════════════════════════════════════════════════════════
#  UNIFIED LOGIN
# ══════════════════════════════════════════════════════════

def login_user(data):
    email    = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")

    if not email or not password:
        return {"success": False, "message": "Email and password are required."}, 400, None

    user = User.query.filter_by(email=email).first()

    if not user:
        return {"success": False, "message": "Invalid email or password."}, 401, None

    if not user.password_hash:
        return {"success": False, "message": "Invalid email or password."}, 401, None

    if not bcrypt.check_password_hash(user.password_hash, password):
        return {"success": False, "message": "Invalid email or password."}, 401, None

    if not user.email_verified:
        return {
            "success":    False,
            "message":    "Please verify your email before logging in.",
            "user_id":    str(user.user_id),
            "unverified": True,
        }, 403, None

    if user.role == UserRole.patient:
        return _patient_login(user)

    if user.role == UserRole.doctor:
        return _doctor_login(user)

    if user.role == UserRole.admin:
        return _admin_login(user)

    return {"success": False, "message": "Invalid role."}, 400, None


# ══════════════════════════════════════════════════════════
#  PATIENT LOGIN
#  If consent not given → return temp_token only (no cookies).
#  Frontend must POST to /api/auth/patient/consent next,
#  sending the temp_token in the Authorization header.
#  That endpoint stamps app_consent=True and returns full JWTs.
# ══════════════════════════════════════════════════════════

def _patient_login(user):
    try:
        if not user.is_active:
            return {
                "success": False,
                "message": "Your account has been deactivated. Please contact support.",
            }, 403, None

        patient = Patient.query.get(user.user_id)

        # ── Consent check ─────────────────────────────────
        if not patient or not patient.app_consent:
            temp_token = _generate_temp_token(user.user_id)

            return {
                "success":          False,
                "consent_required": True,
                "message":          "Please accept the terms and conditions to continue.",
                "temp_token":       temp_token,   # used ONLY for POST /api/auth/patient/consent
                "user": {
                    "user_id":   str(user.user_id),
                    "full_name": user.full_name,
                    "email":     user.email,
                    "role":      "patient",
                },
            }, 403, None   # tokens=None → no cookies set by the route

        # ── Full login ────────────────────────────────────
        _update_last_login(user)
        tokens = _generate_tokens(user.user_id)

        return {
            "success": True,
            "message": "Login successful",
            "role":    "patient",
            "user":    user.to_dict(),
        }, 200, tokens

    except Exception as e:
        return {"success": False, "message": str(e)}, 500, None


# ══════════════════════════════════════════════════════════
#  PATIENT CONSENT  (called from the consent route)
#  Validates the temp token's scope, stamps consent,
#  and returns full access + refresh tokens.
# ══════════════════════════════════════════════════════════

def accept_patient_consent(user_id, jwt_claims):
    """
    Call this from POST /api/auth/patient/consent after
    verify_jwt_in_request() has already run.

    Returns (response_dict, http_status, tokens | None)
    so the route can set cookies exactly like login does.
    """
    # Enforce scope — reject any token that wasn't issued for consent
    if not jwt_claims.get("temp") or jwt_claims.get("scope") != "consent_only":
        return {"success": False, "message": "Invalid or expired consent token."}, 403, None

    try:
        user = User.query.get(user_id)
        if not user:
            return {"success": False, "message": "User not found."}, 404, None

        if not user.is_active:
            return {
                "success": False,
                "message": "Your account has been deactivated. Please contact support.",
            }, 403, None

        patient = Patient.query.get(user_id)
        if not patient:
            return {"success": False, "message": "Patient profile not found."}, 404, None

        # Stamp consent
        patient.app_consent    = True
        patient.consent_given_at = datetime.utcnow()
        _update_last_login(user)          # also commits the consent changes

        tokens = _generate_tokens(user_id)

        return {
            "success": True,
            "message": "Consent accepted. Login successful.",
            "role":    "patient",
            "user":    user.to_dict(),
        }, 200, tokens

    except Exception as e:
        return {"success": False, "message": str(e)}, 500, None


# ══════════════════════════════════════════════════════════
#  DOCTOR LOGIN
# ══════════════════════════════════════════════════════════

def _doctor_login(user):
    try:
        doctor = Doctor.query.get(user.user_id)

        if not doctor:
            return {"success": False, "message": "Doctor profile not found."}, 404, None

        if doctor.verification_status == VerificationStatus.pending:
            return {
                "success": False,
                "message": "Account pending admin approval.",
                "status":  "pending_approval",
            }, 403, None

        if doctor.verification_status == VerificationStatus.rejected:
            return {
                "success": False,
                "message": "Account rejected by admin.",
            }, 403, None

        _update_last_login(user)
        tokens = _generate_tokens(user.user_id)

        return {
            "success": True,
            "message": "Login successful",
            "role":    "doctor",
            "user":    {**user.to_dict(), **doctor.to_dict()},
        }, 200, tokens

    except Exception as e:
        return {"success": False, "message": str(e)}, 500, None


# ══════════════════════════════════════════════════════════
#  ADMIN LOGIN
# ══════════════════════════════════════════════════════════

def _admin_login(user):
    try:
        _update_last_login(user)
        tokens = _generate_tokens(user.user_id)

        return {
            "success": True,
            "message": "Login successful",
            "role":    "admin",
            "user":    user.to_dict(),
        }, 200, tokens

    except Exception as e:
        return {"success": False, "message": str(e)}, 500, None


# ══════════════════════════════════════════════════════════
#  LOGOUT  — blacklists the JTI in Redis
# ══════════════════════════════════════════════════════════

def logout_user():
    try:
        jti = get_jwt()["jti"]
        redis_client.setex(f"blacklist:{jti}", 3600, "true")
    except Exception:
        pass   # still logout cleanly even if Redis fails
    return {"success": True, "message": "Logged out successfully."}, 200