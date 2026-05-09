import numpy as np
from datetime import datetime
from flask_jwt_extended import get_jwt_identity

from app import db
from models.user    import User, UserRole
from models.patient import Patient
from models.staging import Staging


# ══════════════════════════════════════════════════════════
#  EXACT ALGORITHM FROM DL TEAM — DO NOT MODIFY
# ══════════════════════════════════════════════════════════

def _size_to_t_code(size_cm):
    if size_cm <= 2.0: return 1
    if size_cm <= 5.0: return 2
    return 3


def assign_cT(tumor_size=None, skin_nip=0, pec_ch=0, no_primary=False):
    if no_primary:
        return 'T0'
    if tumor_size is None and not no_primary:
        raise ValueError('tumor_size is mandatory unless no_primary_tumour=True')
    skin_nip = skin_nip or 0
    pec_ch   = pec_ch   or 0
    if skin_nip == 1 or pec_ch == 1:
        return 'T4'
    return {1: 'T1', 2: 'T2', 3: 'T3', 4: 'T4'}.get(_size_to_t_code(tumor_size), 'Unknown')


def assign_cN(v=None):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 'N0'
    v = float(v)
    if v == 0.5: return 'N1mi'
    return {0: 'N0', 1: 'N1', 2: 'N2', 3: 'N3'}.get(int(v), 'N0')


def assign_cM(v=None):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 'M0'
    return 'M1' if int(v) == 1 else 'M0'


def derive_ajcc_stage(cT, cN, cM):
    if 'Unknown' in (cT, cN, cM): return 'Unknown'
    if cM == 'M1':   return 'IV'
    if cN == 'N1mi' and cT in ('T0', 'T1'): return 'IB'
    if cN == 'N1mi' and cT in ('T2', 'T3'): return 'IIB'
    if cN == 'N3':   return 'IIIC'
    if cT == 'T4':   return 'IIIB'
    if cN == 'N2':   return 'IIIA'
    if cT == 'T3':   return 'IIIA' if cN == 'N1' else 'IIB'
    if cT == 'T2':   return 'IIB'  if cN == 'N1' else 'IIA'
    if cT == 'T1':   return 'IIA'  if cN == 'N1' else 'IA'
    if cT == 'T0' and cN in ('N1', 'N2'): return 'IIA'
    return 'Unknown'


def get_subtype(er, pr, her2):
    try:
        er   = int(float(er))
        pr   = int(float(pr))
        her2 = int(float(her2))
    except (ValueError, TypeError):
        return 'Unknown'
    hr_pos   = (er == 1 or pr == 1)
    her2_pos = (her2 == 1)
    if hr_pos and not her2_pos:  return 'HR+/HER2-'
    if hr_pos and her2_pos:      return 'HR+/HER2+'
    if not hr_pos and her2_pos:  return 'HR-/HER2+'
    return 'Triple_Negative'


STAGE_SEQ = ['IA', 'IB', 'IIA', 'IIB', 'IIIA', 'IIIB', 'IIIC', 'IV']


def shift_stage(anatomic, delta):
    s = 'IA' if anatomic in ('I', 'IA') else anatomic
    if s not in STAGE_SEQ or s in ('IV', 'IIIC'):
        return anatomic
    idx = STAGE_SEQ.index(s)
    return STAGE_SEQ[max(0, min(len(STAGE_SEQ) - 1, idx + delta))]


_EXACT_OVERRIDES = {
    ('IIB',  'HR+/HER2+',      1): 'IB',
    ('IIB',  'HR+/HER2+',      2): 'IB',
    ('IIB',  'HR+/HER2+',      3): 'IB',
    ('IA',   'Triple_Negative', 1): 'IIA',
    ('IA',   'Triple_Negative', 2): 'IIA',
    ('IA',   'Triple_Negative', 3): 'IIA',
    ('IIIA', 'Triple_Negative', 1): 'IIIC',
    ('IIIA', 'Triple_Negative', 2): 'IIIC',
    ('IIIA', 'Triple_Negative', 3): 'IIIC',
}
_UNASSIGNABLE = {
    ('IIB', 'HR+/HER2-', 2),
    ('IIB', 'HR+/HER2-', 3),
}


def derive_prognostic_stage(anatomic_stage, er, pr, her2, grade):
    if anatomic_stage == 'IV':      return 'IV'
    if anatomic_stage == 'Unknown': return 'Unknown'
    anatomic_stage = 'IA' if anatomic_stage == 'I' else anatomic_stage

    if any(x is None or (isinstance(x, float) and np.isnan(x))
           for x in [er, pr, her2, grade]):
        return f'{anatomic_stage}*'

    subtype = get_subtype(er, pr, her2)
    g       = int(float(grade))

    if (anatomic_stage, subtype, g) in _UNASSIGNABLE:
        return f'{anatomic_stage}?'
    if (anatomic_stage, subtype, g) in _EXACT_OVERRIDES:
        return _EXACT_OVERRIDES[(anatomic_stage, subtype, g)]

    if subtype == 'Triple_Negative':  delta = +1
    elif subtype == 'HR-/HER2+':      delta = +1 if g == 3 else 0
    elif subtype == 'HR+/HER2+':      delta = -1 if g == 1 else 0
    else:                              delta = -1 if g <= 2 else 0

    result = shift_stage(anatomic_stage, delta)
    if subtype == 'Triple_Negative' and result == 'IA':
        result = 'IB'
    return result


# ══════════════════════════════════════════════════════════
#  SERVICE LAYER  — auth + assignment + DB
# ══════════════════════════════════════════════════════════

def _run_staging(no_primary, tumor_size, skin_nipple, pec_chest,
                 lymphadenopathy, metastatic, er, pr, her2, histologic_grade):
    """Pure staging calculation. Returns dict of all staging results."""
    cT = assign_cT(
        tumor_size = tumor_size,
        skin_nip   = skin_nipple,
        pec_ch     = pec_chest,
        no_primary = no_primary,
    )
    cN = assign_cN(lymphadenopathy)
    cM = assign_cM(metastatic)

    anatomic   = derive_ajcc_stage(cT, cN, cM)
    prognostic = derive_prognostic_stage(anatomic, er, pr, her2, histologic_grade)

    if prognostic.endswith('*'):
        missing = [
            n for n, v in [("ER", er), ("PR", pr), ("HER2", her2), ("grade", histologic_grade)]
            if v is None
        ]
        result_label = (
            f'Anatomic: {anatomic}  '
            f'(prognostic stage incomplete — missing: {", ".join(missing)})'
        )
    elif prognostic.endswith('?'):
        result_label = (
            f'Anatomic: {anatomic}  '
            f'(prognostic stage unassignable — gap in AJCC 8th ed. table)'
        )
    else:
        result_label = f'Prognostic: {prognostic}'

    molecular_subtype = None
    if all(x is not None for x in [er, pr, her2]):
        s = get_subtype(er, pr, her2)
        molecular_subtype = s if s != 'Unknown' else None

    return {
        "cT_stage":          cT,
        "cN_stage":          cN,
        "cM_stage":          cM,
        "anatomic_stage":    anatomic,
        "prognostic_stage":  prognostic,
        "result_label":      result_label,
        "molecular_subtype": molecular_subtype,
    }


def _auth_and_patient(patient_id):
    """
    Shared guard used by every service function.
    Returns (user_id, error_tuple) where error_tuple is (dict, status) or None.
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return user_id, ({"success": False, "message": "Access denied. Doctors only."}, 403)

    patient = Patient.query.get(str(patient_id))
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return user_id, ({"success": False, "message": "This patient is not assigned to you."}, 403)

    return user_id, None


def _validate_tumor(data):
    """
    Validates tumor_size / no_primary_tumour.
    Returns (no_primary, tumor_size, error_tuple).
    error_tuple is None when valid.
    """
    no_primary = bool(data.get("no_primary_tumour", False))
    tumor_size = data.get("tumor_size")

    if no_primary:
        return True, None, None

    if tumor_size is None:
        return False, None, (
            {"success": False, "message": "tumor_size is required when no_primary_tumour is false."},
            400,
        )
    try:
        tumor_size = float(tumor_size)
    except (TypeError, ValueError):
        return False, None, (
            {"success": False, "message": "tumor_size must be a numeric value in cm."},
            400,
        )
    if tumor_size <= 0:
        return False, None, (
            {"success": False, "message": "tumor_size must be greater than 0."},
            400,
        )

    return False, tumor_size, None


# ─────────────────────────────────────────────────────────
#  CREATE
# ─────────────────────────────────────────────────────────

def create_staging_service(patient_id, data):
    """
    Create a staging record for the given patient.

    Checks (in order):
      1. Caller is a doctor
      2. Patient is assigned to this doctor
      3. tumor_size present OR no_primary_tumour=True
      4. Run AJCC staging algorithm
      5. Persist to DB
    """
    user_id, err = _auth_and_patient(patient_id)
    if err:
        return err

    no_primary, tumor_size, err = _validate_tumor(data)
    if err:
        return err

    def _float(key): v = data.get(key); return float(v) if v is not None else None
    def _int(key):   v = data.get(key); return int(v)   if v is not None else None

    lymphadenopathy   = _float("lymphadenopathy")
    metastatic        = _int("metastatic")
    skin_nipple       = _int("skin_nipple")
    pec_chest         = _int("pec_chest")
    er                = _int("er")
    pr                = _int("pr")
    her2              = _int("her2")
    histologic_grade  = _int("histologic_grade")
    detection_scan_id = data.get("detection_scan_id")
    mri_scan_id       = data.get("mri_scan_id")

    try:
        result = _run_staging(
            no_primary, tumor_size, skin_nipple, pec_chest,
            lymphadenopathy, metastatic, er, pr, her2, histologic_grade,
        )
    except ValueError as e:
        return {"success": False, "message": str(e)}, 400

    staging = Staging(
        patient_id         = str(patient_id),
        doctor_id          = user_id,
        tumor_size         = tumor_size,
        no_primary_tumour  = no_primary,
        lymphadenopathy    = lymphadenopathy,
        metastatic         = metastatic,
        skin_nipple        = skin_nipple,
        pec_chest          = pec_chest,
        er                 = er,
        pr                 = pr,
        her2               = her2,
        histologic_grade   = histologic_grade,
        cT_stage           = result["cT_stage"],
        cN_stage           = result["cN_stage"],
        cM_stage           = result["cM_stage"],
        anatomic_stage     = result["anatomic_stage"],
        prognostic_stage   = result["prognostic_stage"],
        result_label       = result["result_label"],
        molecular_subtype  = result["molecular_subtype"],
        detection_scan_id  = str(detection_scan_id) if detection_scan_id else None,
        mri_scan_id        = str(mri_scan_id)       if mri_scan_id       else None,
    )

    db.session.add(staging)
    db.session.commit()

    return {
        "success": True,
        "message": "Staging record created successfully.",
        "data":    staging.to_dict_doctor(),
    }, 201


# ─────────────────────────────────────────────────────────
#  GET ONE
# ─────────────────────────────────────────────────────────

def get_staging_service(staging_id):
    """Get a single staging record — doctor must own the patient."""
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    staging = Staging.query.get(str(staging_id))
    if not staging:
        return {"success": False, "message": "Staging record not found."}, 404

    patient = Patient.query.get(str(staging.patient_id))
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "This patient is not assigned to you."}, 403

    return {"success": True, "data": staging.to_dict_doctor()}, 200


# ─────────────────────────────────────────────────────────
#  LIST ALL FOR PATIENT
# ─────────────────────────────────────────────────────────

def list_patient_stagings_service(patient_id):
    """List all staging records for a patient — doctor must own the patient."""
    user_id, err = _auth_and_patient(patient_id)
    if err:
        return err

    stagings = (
        Staging.query
        .filter_by(patient_id=str(patient_id))
        .order_by(Staging.created_at.desc())
        .all()
    )

    return {
        "success": True,
        "count":   len(stagings),
        "data":    [s.to_dict_doctor() for s in stagings],
    }, 200


# ─────────────────────────────────────────────────────────
#  UPDATE
# ─────────────────────────────────────────────────────────

def update_staging_service(staging_id, data):
    """
    Update inputs on an existing staging record and re-run the algorithm.
    Only the doctor who created the record can update it.
    Supports partial updates — only send the fields you want to change.
    """
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    staging = Staging.query.get(str(staging_id))
    if not staging:
        return {"success": False, "message": "Staging record not found."}, 404

    if str(staging.doctor_id) != user_id:
        return {"success": False, "message": "You can only update staging records you created."}, 403

    patient = Patient.query.get(str(staging.patient_id))
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "This patient is not assigned to you."}, 403

    # merge incoming with existing for partial update support
    merged = {
        "no_primary_tumour": data.get("no_primary_tumour", staging.no_primary_tumour),
        "tumor_size":        data.get("tumor_size",        staging.tumor_size),
    }
    no_primary, tumor_size, err = _validate_tumor(merged)
    if err:
        return err

    def _pick_float(key, current): return float(data[key]) if key in data else current
    def _pick_int(key, current):   return int(data[key])   if key in data else current

    lymphadenopathy  = _pick_float("lymphadenopathy",  staging.lymphadenopathy)
    metastatic       = _pick_int("metastatic",          staging.metastatic)
    skin_nipple      = _pick_int("skin_nipple",         staging.skin_nipple)
    pec_chest        = _pick_int("pec_chest",           staging.pec_chest)
    er               = _pick_int("er",                  staging.er)
    pr               = _pick_int("pr",                  staging.pr)
    her2             = _pick_int("her2",                staging.her2)
    histologic_grade = _pick_int("histologic_grade",    staging.histologic_grade)

    try:
        result = _run_staging(
            no_primary, tumor_size, skin_nipple, pec_chest,
            lymphadenopathy, metastatic, er, pr, her2, histologic_grade,
        )
    except ValueError as e:
        return {"success": False, "message": str(e)}, 400

    staging.no_primary_tumour  = no_primary
    staging.tumor_size         = tumor_size
    staging.lymphadenopathy    = lymphadenopathy
    staging.metastatic         = metastatic
    staging.skin_nipple        = skin_nipple
    staging.pec_chest          = pec_chest
    staging.er                 = er
    staging.pr                 = pr
    staging.her2               = her2
    staging.histologic_grade   = histologic_grade
    staging.cT_stage           = result["cT_stage"]
    staging.cN_stage           = result["cN_stage"]
    staging.cM_stage           = result["cM_stage"]
    staging.anatomic_stage     = result["anatomic_stage"]
    staging.prognostic_stage   = result["prognostic_stage"]
    staging.result_label       = result["result_label"]
    staging.molecular_subtype  = result["molecular_subtype"]
    staging.updated_at         = datetime.utcnow()

    if "detection_scan_id" in data:
        staging.detection_scan_id = str(data["detection_scan_id"]) if data["detection_scan_id"] else None
    if "mri_scan_id" in data:
        staging.mri_scan_id = str(data["mri_scan_id"]) if data["mri_scan_id"] else None

    db.session.commit()

    return {
        "success": True,
        "message": "Staging record updated and re-run successfully.",
        "data":    staging.to_dict_doctor(),
    }, 200


# ─────────────────────────────────────────────────────────
#  DELETE
# ─────────────────────────────────────────────────────────

def delete_staging_service(staging_id):
    """Delete a staging record — only the creating doctor can do this."""
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)

    if user.role != UserRole.doctor:
        return {"success": False, "message": "Access denied. Doctors only."}, 403

    staging = Staging.query.get(str(staging_id))
    if not staging:
        return {"success": False, "message": "Staging record not found."}, 404

    if str(staging.doctor_id) != user_id:
        return {"success": False, "message": "You can only delete staging records you created."}, 403

    patient = Patient.query.get(str(staging.patient_id))
    if not patient or str(patient.current_assigned_doctor_id) != user_id:
        return {"success": False, "message": "This patient is not assigned to you."}, 403

    db.session.delete(staging)
    db.session.commit()

    return {"success": True, "message": "Staging record deleted."}, 200