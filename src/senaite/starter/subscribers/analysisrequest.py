# -*- coding: utf-8 -*-

from bika.lims.api.security import check_permission
from Products.CMFCore.permissions import ModifyPortalContent
from senaite.patient import api as patient_api
from senaite.starter import check_installed
from senaite.starter import logger
from senaite.starter.api import get_patient_cnic
from senaite.starter.api import get_sample_cnic
from senaite.starter.api import is_cnic_unique
from senaite.starter.api import set_patient_cnic


@check_installed(None)
def on_object_created(instance, event):
    """Event handler when a sample was created
    """
    update_patient_cnic(instance)


@check_installed(None)
def on_object_edited(instance, event):
    """Event handler when a sample was edited
    """
    update_patient_cnic(instance)


def update_patient_cnic(sample):
    """Sets the CNIC of the sample to the patient with the same MRN

    senaite.patient creates the patient from the sample fields when a sample
    with a new MRN is registered (see its subscribers/analysisrequest.py).
    This copies the CNIC to that patient as well.

    Like senaite.patient, an existing value of the patient is never
    overwritten from a sample: the CNIC is only set if the patient has none
    yet and the current user is allowed to modify the patient. A CNIC that
    another patient has already is never set (CNIC is unique per patient).

    :returns: the updated patient or None
    """
    cnic = get_sample_cnic(sample)
    if not cnic:
        return None

    # no patient is created for temporary MRNs
    if sample.isMedicalRecordTemporary():
        return None

    mrn = sample.getMedicalRecordNumberValue()
    if not mrn:
        return None

    patient = patient_api.get_patient_by_mrn(mrn, include_inactive=True)
    if patient is None:
        return None

    if get_patient_cnic(patient):
        return None

    if not check_permission(ModifyPortalContent, patient):
        return None

    if not is_cnic_unique(cnic):
        logger.warn("CNIC of sample '{}' belongs to another patient. "
                    "Not set for Patient with MRN '{}'"
                    .format(sample.getId(), mrn))
        return None

    logger.info("Setting CNIC of Patient with MRN '{}' from sample '{}'"
                .format(mrn, sample.getId()))
    set_patient_cnic(patient, cnic)
    patient.reindexObject()
    return patient
