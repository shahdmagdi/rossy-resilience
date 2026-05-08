"""
notes_service.py
----------------
Handles doctor notes (private) and care plans (shared with patient).

Rules:
  - Only the assigned doctor of a patient can create/edit/delete notes for them.
  - Patients can only READ their own shared (care plan) notes.
  - Private notes are never exposed to patients.
  - A care-plan notification is fired when a shared note is created.
"""

from datetime import datetime
from app import db
from models import User, Doctor, Patient, UserRole
from models.doctor_notes import DoctorNote, NoteVisibility
from models.detection_scan import DetectionScan
from services.notification_service import notify_patient_care_plan_created
from flask_jwt_extended import get_jwt_identity


# ──────────────────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────────────────

def _get_doctor_or_error():
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)
    if user.role != UserRole.doctor:
        return None, None, ({"success": False, "message": "Access denied. Doctors only."}, 403)
    return user_id, user, None


def _get_patient_or_error():
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)
    if user.role != UserRole.patient:
        return None, None, ({"success": False, "message": "Access denied. Patients only."}, 403)
    return user_id, user, None


def _assert_doctor_owns_patient(doctor_id, patient_id):
    """Returns error tuple if doctor is not the assigned doctor of this patient, else None."""
    patient = Patient.query.get(patient_id)
    if not patient or str(patient.current_assigned_doctor_id) != doctor_id:
        return {"success": False, "message": "This patient is not assigned to you."}, 403
    return None


# ══════════════════════════════════════════════════════════
#  CREATE NOTE / CARE PLAN
# ══════════════════════════════════════════════════════════

def create_note(patient_id, data, visibility="private"):
    """
    Doctor creates a note or care plan for their assigned patient.

    Query Param:
        ?visibility=private|shared

    Body:
        title
        content
        scan_id (optional)
    """

    doctor_id, doctor_user, error = _get_doctor_or_error()
    if error:
        return error

    guard = _assert_doctor_owns_patient(doctor_id, patient_id)
    if guard:
        return guard

    title   = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    scan_id = data.get("scan_id")

    if not title:
        return {"success": False, "message": "Title is required."}, 400

    if not content:
        return {"success": False, "message": "Content is required."}, 400

    if visibility not in [v.value for v in NoteVisibility]:
        return {
            "success": False,
            "message": "visibility must be 'private' or 'shared'."
        }, 400

    # Validate scan_id
    if scan_id:
        scan = DetectionScan.query.filter_by(
            scan_id=scan_id,
            patient_id=patient_id,
        ).first()

        if not scan:
            return {
                "success": False,
                "message": "Scan not found or does not belong to this patient."
            }, 404

    try:
        note = DoctorNote(
            doctor_id=doctor_id,
            patient_id=patient_id,
            scan_id=scan_id or None,
            title=title,
            content=content,
            visibility=NoteVisibility(visibility),
        )

        db.session.add(note)
        db.session.commit()

        if note.visibility == NoteVisibility.shared:
            notify_patient_care_plan_created(
                patient_id=patient_id,
                doctor_full_name=doctor_user.full_name,
                note_id=note.id,
            )

        label = "Care plan" if note.visibility == NoteVisibility.shared else "Note"

        return {
            "success": True,
            "message": f"{label} created successfully.",
            "note": note.to_dict_doctor(),
        }, 201

    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": "Something went wrong.",
            "error": str(e)
        }, 500


# ══════════════════════════════════════════════════════════
#  GET ALL NOTES FOR A PATIENT — DOCTOR VIEW
# ══════════════════════════════════════════════════════════

def get_patient_notes(patient_id, visibility=None):
    """
    Doctor retrieves all notes (private + shared) for their assigned patient.
    Optional query param: ?visibility=private | shared
    """
    doctor_id, _, error = _get_doctor_or_error()
    if error:
        return error

    guard = _assert_doctor_owns_patient(doctor_id, patient_id)
    if guard:
        return guard

    try:
        query = DoctorNote.query.filter_by(
            doctor_id  = doctor_id,
            patient_id = patient_id,
        )

        if visibility:
            if visibility not in [v.value for v in NoteVisibility]:
                return {"success": False, "message": "visibility must be 'private' or 'shared'."}, 400
            query = query.filter_by(visibility=NoteVisibility(visibility))

        notes = query.order_by(DoctorNote.created_at.desc()).all()

        return {
            "success": True,
            "total":   len(notes),
            "notes":   [n.to_dict_doctor() for n in notes],
        }, 200

    except Exception as e:
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


# ══════════════════════════════════════════════════════════
#  GET SINGLE NOTE — DOCTOR
# ══════════════════════════════════════════════════════════

def get_note_by_id_doctor(note_id):
    """Doctor retrieves a single note they created."""
    doctor_id, _, error = _get_doctor_or_error()
    if error:
        return error

    note = DoctorNote.query.filter_by(id=note_id, doctor_id=doctor_id).first()
    if not note:
        return {"success": False, "message": "Note not found."}, 404

    return {"success": True, "note": note.to_dict_doctor()}, 200


# ══════════════════════════════════════════════════════════
#  UPDATE NOTE — DOCTOR
# ══════════════════════════════════════════════════════════

def update_note(note_id, data):
    """
    Doctor updates an existing note.
    Updatable fields: title, content, visibility, scan_id.
    If visibility is changed to 'shared', a new notification is sent.
    """
    doctor_id, doctor_user, error = _get_doctor_or_error()
    if error:
        return error

    note = DoctorNote.query.filter_by(id=note_id, doctor_id=doctor_id).first()
    if not note:
        return {"success": False, "message": "Note not found."}, 404

    # Guard — still assigned to this patient?
    guard = _assert_doctor_owns_patient(doctor_id, str(note.patient_id))
    if guard:
        return guard

    was_private = note.visibility == NoteVisibility.private

    try:
        if "title" in data and data["title"].strip():
            note.title = data["title"].strip()
        if "content" in data and data["content"].strip():
            note.content = data["content"].strip()
        if "visibility" in data:
            if data["visibility"] not in [v.value for v in NoteVisibility]:
                return {"success": False, "message": "visibility must be 'private' or 'shared'."}, 400
            note.visibility = NoteVisibility(data["visibility"])
        if "scan_id" in data:
            if data["scan_id"]:
                scan = DetectionScan.query.filter_by(
                    scan_id    = data["scan_id"],
                    patient_id = str(note.patient_id),
                ).first()
                if not scan:
                    return {"success": False, "message": "Scan not found or does not belong to this patient."}, 404
                note.scan_id = data["scan_id"]
            else:
                note.scan_id = None

        note.updated_at = datetime.utcnow()
        db.session.commit()

        # Notify patient if note was just made shared (promoted to care plan)
        if was_private and note.visibility == NoteVisibility.shared:
            notify_patient_care_plan_created(
                patient_id       = str(note.patient_id),
                doctor_full_name = doctor_user.full_name,
                note_id          = note.id,
            )

        return {
            "success": True,
            "message": "Note updated successfully.",
            "note":    note.to_dict_doctor(),
        }, 200

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


# ══════════════════════════════════════════════════════════
#  DELETE NOTE — DOCTOR
# ══════════════════════════════════════════════════════════

def delete_note(note_id):
    """Doctor deletes a note they created."""
    doctor_id, _, error = _get_doctor_or_error()
    if error:
        return error

    note = DoctorNote.query.filter_by(id=note_id, doctor_id=doctor_id).first()
    if not note:
        return {"success": False, "message": "Note not found."}, 404

    try:
        db.session.delete(note)
        db.session.commit()
        return {"success": True, "message": "Note deleted successfully."}, 200

    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


# ══════════════════════════════════════════════════════════
#  GET CARE PLANS — PATIENT VIEW
#  Only shared notes are returned.
# ══════════════════════════════════════════════════════════

def get_my_care_plans():
    """
    Patient retrieves all care plans (shared notes) written by their assigned doctor.
    Private notes are never exposed here.
    """
    patient_id, _, error = _get_patient_or_error()
    if error:
        return error

    try:
        patient = Patient.query.get(patient_id)

        query = DoctorNote.query.filter_by(
            patient_id = patient_id,
            visibility = NoteVisibility.shared,
        )

        # Only show care plans from the currently assigned doctor (if any)
        if patient.current_assigned_doctor_id:
            query = query.filter_by(doctor_id=str(patient.current_assigned_doctor_id))

        notes = query.order_by(DoctorNote.created_at.desc()).all()

        return {
            "success":    True,
            "total":      len(notes),
            "care_plans": [n.to_dict_patient() for n in notes],
        }, 200

    except Exception as e:
        return {"success": False, "message": "Something went wrong.", "error": str(e)}, 500


# ══════════════════════════════════════════════════════════
#  GET SINGLE CARE PLAN — PATIENT VIEW
# ══════════════════════════════════════════════════════════

def get_care_plan_by_id(note_id):
    """Patient views a single shared care plan addressed to them."""
    patient_id, _, error = _get_patient_or_error()
    if error:
        return error

    note = DoctorNote.query.filter_by(
        id         = note_id,
        patient_id = patient_id,
        visibility = NoteVisibility.shared,
    ).first()

    if not note:
        return {"success": False, "message": "Care plan not found."}, 404

    return {"success": True, "care_plan": note.to_dict_patient()}, 200