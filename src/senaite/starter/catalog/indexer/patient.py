# -*- coding: utf-8 -*-

from bika.lims import api
from plone.indexer import indexer
from senaite.patient.catalog.indexer import patient as patient_indexers
from senaite.patient.interfaces import IPatient
from senaite.patient.interfaces import IPatientCatalog
from senaite.starter.api import get_patient_cnic


def extend_searchable_text(text, values):
    """Appends the non-empty values to the searchable text (utf-8 encoded)
    """
    values = filter(None, values)
    if not values:
        return text
    parts = [api.safe_unicode(text or "")] + map(api.safe_unicode, values)
    return u" ".join(filter(None, parts)).encode("utf-8")


@indexer(IPatient, IPatientCatalog)
def patient_cnic(instance):
    """Index the CNIC of the patient, like patient_mrn
    """
    return get_patient_cnic(instance).encode("utf-8")


@indexer(IPatient, IPatientCatalog)
def patient_searchable_cnic(instance):
    """Index used to search patients from the CNIC field of the sample add
    form, like patient_searchable_mrn is for the Medical Record # field.
    Contains the CNIC only
    """
    return get_patient_cnic(instance).encode("utf-8")


# Registered for the patient catalog interface, which is more specific than
# the IZCatalog default senaite.patient uses, so it takes precedence while
# still delegating to senaite.patient's indexer.
#
# NOTE: patient_searchable_mrn (the "Medical Record #" lookup of the sample
#       add form) is deliberately not extended: a CNIC typed in the MRN field
#       would match unrelated patients or end up as the MRN of a new patient.

@indexer(IPatient, IPatientCatalog)
def patient_searchable_text(instance):
    """Index used by the search box of the patient listings, extended with
    the CNIC
    """
    text = patient_indexers.patient_searchable_text.callable(instance)
    return extend_searchable_text(text, [get_patient_cnic(instance)])
