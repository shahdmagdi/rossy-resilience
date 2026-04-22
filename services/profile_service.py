from app import db
from models import User, Doctor, Patient, UserRole
from models.doctor_assignment import DoctorAssignment, AssignmentStatus
from flask_jwt_extended import get_jwt_identity


# ══════════════════════════════════════════════════════════
#  PATIENT → VIEW ASSIGNED DOCTOR INFO
# ══════════════════════════════════════════════════════════

def get_my_assigned_doctor():
    """
    Patient views the full profile of their assigned doctor.

    Returns: (response_dict, http_status_code)
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.patient:
        return {"success": False, "message": "Access denied. Patients only."}, 403

    patient = Patient.query.get(user_id)

    if not patient.current_assigned_doctor_id:
        return {
            "success": False,
            "message": "You do not have an assigned doctor yet."
        }, 404

    doctor      = Doctor.query.get(str(patient.current_assigned_doctor_id))
    doctor_user = User.query.get(str(patient.current_assigned_doctor_id))

    if not doctor or not doctor_user:
        return {"success": False, "message": "Assigned doctor not found."}, 404

    return {
        "success": True,
        "doctor": {
            "doctor_id":       str(doctor.doctor_id),
            "full_name":       doctor_user.full_name,
            "email":           doctor_user.email,
            "phone_number":    doctor_user.phone_number,
            "gender":          doctor_user.gender.value if doctor_user.gender else None,
            "specialization":  doctor.specialization,
            "hospital":        doctor.hospital,
            "bio":             doctor.bio,
            "profile_image_url": doctor.profile_image_url,
            "whatsapp_link": f"https://wa.me/{doctor_user.phone_number.replace('+', '')}" 
                 if doctor_user.phone_number else None,
            
        }
    }, 200


# ══════════════════════════════════════════════════════════
#  DOCTOR → VIEW ALL ASSIGNED PATIENTS INFO
# ══════════════════════════════════════════════════════════

def get_my_assigned_patients():
    """
    Doctor views the full list of their assigned patients.

    Returns: (response_dict, http_status_code)
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    # Find all patients assigned to this doctor
    patients = Patient.query.filter_by(
        current_assigned_doctor_id=user_id
    ).all()

    if not patients:
        return {
            "success":  True,
            "count":    0,
            "patients": [],
            "message":  "You have no assigned patients yet."
        }, 200

    patients_list = []
    for patient in patients:
        patient_user = User.query.get(str(patient.patient_id))
        if not patient_user:
            continue

        patients_list.append({
            "patient_id":        str(patient.patient_id),
            "full_name":         patient_user.full_name,
            "email":             patient_user.email,
            "phone_number":      patient_user.phone_number,
            "gender":            patient_user.gender.value if patient_user.gender else None,
            "date_of_birth":     patient_user.date_of_birth.isoformat() if patient_user.date_of_birth else None,
            "whatsapp_number":   patient.whatsapp_number,
            "mental_health_mode": patient.mental_health_mode,
            "whatsapp_link": f"https://wa.me/{patient_user.phone_number.replace('+', '')}" 
                 if patient_user.phone_number else None,
        })

    return {
        "success":  True,
        "count":    len(patients_list),
        "patients": patients_list,
    }, 200


# ══════════════════════════════════════════════════════════
#  DOCTOR → VIEW SINGLE PATIENT INFO
# ══════════════════════════════════════════════════════════

def get_patient_profile(patient_id):
    """
    Doctor views the full profile of one of their assigned patients.

    Returns: (response_dict, http_status_code)
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    # Confirm patient is assigned to this doctor
    patient = Patient.query.filter_by(
        patient_id                 = patient_id,
        current_assigned_doctor_id = user_id,
    ).first()

    if not patient:
        return {
            "success": False,
            "message": "Patient not found or not assigned to you."
        }, 404

    patient_user = User.query.get(patient_id)

    return {
        "success": True,
        "patient": {
            "patient_id":        str(patient.patient_id),
            "full_name":         patient_user.full_name,
            "email":             patient_user.email,
            "phone_number":      patient_user.phone_number,
            "gender":            patient_user.gender.value if patient_user.gender else None,
            "date_of_birth":     patient_user.date_of_birth.isoformat() if patient_user.date_of_birth else None,
            "whatsapp_number":   patient.whatsapp_number,
            "mental_health_mode": patient.mental_health_mode,
            # WhatsApp link ready for frontend to use directly
            "whatsapp_link": f"https://wa.me/{patient_user.phone_number.replace('+', '')}" 
                 if patient_user.phone_number else None,
        }
    }, 200