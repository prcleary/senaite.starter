# -*- coding: utf-8 -*-

from bika.lims import api
from bika.lims.api.security import check_permission
from bika.lims.interfaces import IAnalysisRequestSecondary
from Products.Archetypes.interfaces import IObjectInitializedEvent
from Products.CMFCore.permissions import ModifyPortalContent
from senaite.patient import api as patient_api
from senaite.starter import check_installed
from senaite.starter import logger
from senaite.starter.api import get_patient_cnic
from senaite.starter.api import get_sample_cnic
from senaite.starter.api import is_cnic_unique
from senaite.starter.api import pop_sample_cnic_changed
from senaite.starter.api import set_patient_cnic


@check_installed(None)
def on_object_created(instance, event):
    """Event handler when a sample was created

    The CNIC entered at registration replaces the CNIC of the patient.
    Partitions and secondary samples copy the CNIC of their primary sample,
    which therefore only fills an empty CNIC of the patient
    """
    update_patient_cnic(instance, replace=not is_copy(instance))


@check_installed(None)
def on_object_edited(instance, event):
    """Event handler when a sample was modified

    A CNIC changed on the sample replaces the CNIC of the patient. Otherwise
    the CNIC of the sample only fills an empty CNIC of the patient, e.g. of
    the patient created when a temporary MRN is replaced by a new one
    """
    if IObjectInitializedEvent.providedBy(event):
        # sample created, see on_object_created
        return
    changed = pop_sample_cnic_changed(instance)
    update_patient_cnic(instance, replace=changed)


def is_copy(sample):
    """Returns whether the sample got its values from another sample when it
    was created (partitions and secondary samples)
    """
    if IAnalysisRequestSecondary.providedBy(sample):
        return True
    return sample.isPartition()


def update_patient_cnic(sample, replace=False):
    """Sets the CNIC of the sample to the patient with the same MRN

    senaite.patient creates the patient from the sample fields when a sample
    with a new MRN is registered, but never updates existing patients from
    samples (see its subscribers/analysisrequest.py). The CNIC is entered and
    corrected in the samples instead, so that the patient record does not
    need to be opened:

    - a patient without CNIC gets the CNIC of the sample
    - a different CNIC of the patient is replaced if `replace` is set

    An empty CNIC never removes the CNIC of the patient. The patient is only
    updated if the current user is allowed to modify it and never gets a CNIC
    that another patient has already (CNIC is unique per patient).

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

    patient_cnic = get_patient_cnic(patient)
    if patient_cnic == cnic:
        return None

    if patient_cnic and not replace:
        return None

    if not check_permission(ModifyPortalContent, patient):
        return None

    if not is_cnic_unique(cnic):
        logger.warn("CNIC of sample '{}' belongs to another patient. "
                    "Not set for Patient with MRN '{}'"
                    .format(sample.getId(), mrn))
        return None

    logger.info("Setting CNIC of Patient with MRN '{}' from sample '{}' "
                "(was: '{}')".format(mrn, sample.getId(),
                                     api.to_utf8(patient_cnic)))
    set_patient_cnic(patient, cnic)
    patient.reindexObject()
    return patient
