from app import db
from models.notification import Notification, NotificationType


# ══════════════════════════════════════════════════════════
#  INTERNAL HELPER
# ══════════════════════════════════════════════════════════

def _create_notification(user_id, notif_type, title, body, reference_id=None):
    """
    Creates and saves a notification for a user.
    Called internally — never blocks the main flow.
    Failures are caught and logged silently.
    """
    try:
        notification = Notification(
            user_id      = str(user_id),
            type         = notif_type,
            title        = title,
            body         = body,
            reference_id = str(reference_id) if reference_id else None,
        )
        db.session.add(notification)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[notification_service] Failed to create notification: {e}")


# ══════════════════════════════════════════════════════════
#  EVENT 1 — PATIENT ASSIGNS DOCTOR
#  Notifies: Doctor
# ══════════════════════════════════════════════════════════

def notify_doctor_assignment_request(doctor_id, patient_full_name, assignment_id):
    """
    Called from assignment route after patient sends a request to a doctor.

    Args:
        doctor_id        (str): doctor's user_id — receives notification
        patient_full_name (str): patient's full name
        assignment_id    (str): assignment UUID for reference
    """
    _create_notification(
        user_id      = doctor_id,
        notif_type   = NotificationType.patient_assigned_doctor,
        title        = "New Patient Assignment Request",
        body         = f"{patient_full_name} has requested to be assigned to you.",
        reference_id = assignment_id,
    )


# ══════════════════════════════════════════════════════════
#  EVENT 2 — DOCTOR ACCEPTS PATIENT
#  Notifies: Patient
# ══════════════════════════════════════════════════════════

def notify_patient_assignment_accepted(patient_id, doctor_full_name, assignment_id):
    """
    Called from assignment route after doctor accepts a patient.

    Args:
        patient_id       (str): patient's user_id — receives notification
        doctor_full_name (str): doctor's full name
        assignment_id    (str): assignment UUID for reference
    """
    _create_notification(
        user_id      = patient_id,
        notif_type   = NotificationType.doctor_accepted_patient,
        title        = "Assignment Accepted",
        body         = f"Dr. {doctor_full_name} has accepted your assignment request.",
        reference_id = assignment_id,
    )


# ══════════════════════════════════════════════════════════
#  EVENT 3 — DOCTOR REJECTS PATIENT
#  Notifies: Patient
# ══════════════════════════════════════════════════════════

def notify_patient_assignment_rejected(patient_id, doctor_full_name, assignment_id):
    """
    Called from assignment route after doctor rejects a patient.

    Args:
        patient_id       (str): patient's user_id — receives notification
        doctor_full_name (str): doctor's full name
        assignment_id    (str): assignment UUID for reference
    """
    _create_notification(
        user_id      = patient_id,
        notif_type   = NotificationType.doctor_rejected_patient,
        title        = "Assignment Request Update",
        body         = f"Dr. {doctor_full_name} was unable to accept your request at this time.",
        reference_id = assignment_id,
    )


# ══════════════════════════════════════════════════════════
#  EVENT 4 — PATIENT UPLOADS SCAN WITH DOCTOR
#  Notifies: Doctor
# ══════════════════════════════════════════════════════════

def notify_doctor_scan_uploaded(doctor_id, patient_full_name, scan_id, image_type):
    """
    Called from detection route after patient uploads via upload-with-doctor.

    Args:
        doctor_id         (str): doctor's user_id — receives notification
        patient_full_name (str): patient's full name
        scan_id           (str): scan UUID for reference
        image_type        (str): "ultrasound" or "mammogram"
    """
    _create_notification(
        user_id      = doctor_id,
        notif_type   = NotificationType.patient_uploaded_scan,
        title        = "New Scan Available",
        body         = f"{patient_full_name} has uploaded a new {image_type} scan for your review.",
        reference_id = scan_id,
    )


# ══════════════════════════════════════════════════════════
#  EVENT 5 — DOCTOR CREATES CARE PLAN
#  Notifies: Patient
# ══════════════════════════════════════════════════════════

def notify_patient_care_plan_created(patient_id, doctor_full_name, note_id):
    """
    Called from notes route after doctor creates a shared care plan.

    Args:
        patient_id       (str): patient's user_id — receives notification
        doctor_full_name (str): doctor's full name
        note_id          (str): care plan UUID for reference
    """
    _create_notification(
        user_id      = patient_id,
        notif_type   = NotificationType.doctor_created_care_plan,
        title        = "New Care Plan",
        body         = f"Dr. {doctor_full_name} has created a care plan for you.",
        reference_id = note_id,
    )