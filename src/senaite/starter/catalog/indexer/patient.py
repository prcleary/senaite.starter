# -*- coding: utf-8 -*-

from bika.lims import api
from plone.indexer import indexer
from senaite.patient.catalog.indexer import patient as patient_indexers
from senaite.patient.interfaces import IPatient
from senaite.patient.interfaces import IPatientCatalog
from senaite.starter.api import get_cnic_search_tokens
from senaite.starter.api import get_patient_cnic


def extend_searchable_text(text, tokens):
    """Appends the tokens to the searchable text (utf-8 encoded)
    """
    if not tokens:
        return text
    parts = [api.safe_unicode(text or "")] + list(tokens)
    return u" ".join(filter(None, parts)).encode("utf-8")


@indexer(IPatient, IPatientCatalog)
def patient_cnic(instance):
    """Index the CNIC of the patient (standard format)
    """
    return get_patient_cnic(instance).encode("utf-8")


@indexer(IPatient, IPatientCatalog)
def patient_searchable_cnic(instance):
    """Index used to search patients from the CNIC field of the sample add
    form, like patient_searchable_mrn is for the Medical Record # field.
    Contains the CNIC only
    """
    tokens = get_cnic_search_tokens(get_patient_cnic(instance))
    return u" ".join(tokens).encode("utf-8")


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
    tokens = get_cnic_search_tokens(get_patient_cnic(instance))
    return extend_searchable_text(text, tokens)
