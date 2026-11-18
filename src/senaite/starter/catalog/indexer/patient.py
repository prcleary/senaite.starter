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
    """Index the CNIC of the patient
    """
    return get_patient_cnic(instance).encode("utf-8")


# The two indexers below are registered for the patient catalog interface,
# which is more specific than the IZCatalog default senaite.patient uses, so
# they take precedence while still delegating to senaite.patient's indexers.

@indexer(IPatient, IPatientCatalog)
def patient_searchable_text(instance):
    """Index used by the search box of the patient listings, extended with
    the CNIC
    """
    text = patient_indexers.patient_searchable_text.callable(instance)
    tokens = get_cnic_search_tokens(get_patient_cnic(instance))
    return extend_searchable_text(text, tokens)


@indexer(IPatient, IPatientCatalog)
def patient_searchable_mrn(instance):
    """Index used to search patients from the Medical Record # field of the
    sample add form, extended with the CNIC
    """
    text = patient_indexers.patient_searchable_mrn.callable(instance)
    tokens = get_cnic_search_tokens(get_patient_cnic(instance))
    return extend_searchable_text(text, tokens)
