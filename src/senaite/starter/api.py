# -*- coding: utf-8 -*-
"""CNIC helpers

The CNIC is handled like senaite.patient handles the Medical Record Number
(MRN), but as a separate, optional identifier:

- it is stored on the Sample (AnalysisRequest) as the AT extension field
  "CNIC", the value recorded at sample registration
- it is stored on the Patient as the Dexterity behavior field "cnic"
- it is unique per patient

CNICs are stored and compared in the standard format #####-#######-#, so that
the same CNIC entered with or without dashes is the same identifier.

These helpers access the stored values directly and do not depend on the
browser layer of the current request, so they also work in scripts.
"""

import re

from Acquisition import aq_base
from bika.lims import api
from senaite.patient.catalog import PATIENT_CATALOG
from six import string_types

# Name of the AT extension field on the Sample (AnalysisRequest)
SAMPLE_CNIC_FIELD = "CNIC"

# Name of the Dexterity behavior field on the Patient
PATIENT_CNIC_FIELD = "cnic"

# A CNIC consists of 13 digits, written as #####-#######-#
CNIC_DIGITS = re.compile(r"^\d{13}$")

# Characters ignored when comparing CNICs
CNIC_SEPARATORS = re.compile(r"[\s\-]")


def to_cnic(value):
    """Returns the value as a stripped unicode string or u"" if not a string
    """
    if not isinstance(value, string_types):
        return u""
    return api.safe_unicode(value).strip()


def format_cnic(value):
    """Returns the CNIC in the standard format #####-#######-# if it consists
    of 13 digits (dashes and spaces are ignored), otherwise as entered

    :returns: unicode CNIC or u"" if empty
    """
    cnic = to_cnic(value)
    digits = CNIC_SEPARATORS.sub(u"", cnic)
    if CNIC_DIGITS.match(digits):
        return u"{}-{}-{}".format(digits[:5], digits[5:12], digits[12:])
    return cnic


def get_cnic_search_tokens(value):
    """Returns the CNIC in standard format plus without separators, so that a
    CNIC can be searched for with or without dashes (text indexes split
    words on dashes)
    """
    cnic = format_cnic(value)
    if not cnic:
        return []
    tokens = [cnic]
    compact = CNIC_SEPARATORS.sub(u"", cnic)
    if compact and compact != cnic:
        tokens.append(compact)
    return tokens


def get_sample_cnic(sample):
    """Returns the CNIC recorded in the sample

    :param sample: Sample object or catalog brain
    :returns: unicode CNIC in standard format, u"" if not set or the field is
        not available
    """
    sample = api.get_object(sample)
    field = sample.getField(SAMPLE_CNIC_FIELD)
    if field is None:
        # the schema extender is only active when senaite.starter is installed
        return u""
    return format_cnic(field.get(sample))


def get_patient_cnic(patient):
    """Returns the CNIC of the patient

    :param patient: Patient object or catalog brain
    :returns: unicode CNIC in standard format, u"" if not set or the behavior
        is not enabled
    """
    patient = api.get_object(patient)
    return format_cnic(getattr(aq_base(patient), PATIENT_CNIC_FIELD, None))


def set_patient_cnic(patient, value):
    """Sets the CNIC of the patient in standard format. An empty value
    removes the CNIC. Like senaite.patient's `setMRN`, a CNIC that another
    patient has already is rejected

    NOTE: The patient is not reindexed

    :raises ValueError: if another patient has the CNIC already
    """
    patient = api.get_object(patient)
    cnic = format_cnic(value)
    if cnic == get_patient_cnic(patient):
        # nothing changed
        return
    if cnic and not is_cnic_unique(cnic):
        raise ValueError("Patient CNIC must be unique")
    setattr(patient, PATIENT_CNIC_FIELD, cnic or None)


def search_patients_by_cnic(cnic, include_inactive=True, unrestricted=False):
    """Search the patient catalog for patients with the given CNIC

    :param cnic: CNIC in any format
    :param include_inactive: Also find inactive patients
    :param unrestricted: Search regardless of the permissions of the user
    :returns: list of catalog brains
    """
    cnic = format_cnic(cnic)
    if not cnic:
        return []
    query = {
        "portal_type": "Patient",
        "patient_cnic": api.to_utf8(cnic),
    }
    if not include_inactive:
        query["is_active"] = True
    catalog = api.get_tool(PATIENT_CATALOG)
    if unrestricted:
        return catalog.unrestrictedSearchResults(query)
    return catalog(query)


def get_patient_by_cnic(cnic, full_object=True, include_inactive=False):
    """Get a patient by CNIC, like senaite.patient's `get_patient_by_mrn`

    :param cnic: CNIC in any format
    :param full_object: If true, return objects instead of catalog brains
    :param include_inactive: Also find inactive patients
    :returns: Patient or None
    """
    brains = search_patients_by_cnic(cnic, include_inactive=include_inactive)
    count = len(brains)
    if count == 0:
        return None
    elif count > 1:
        raise ValueError("Found {} Patients for CNIC {}".format(
            count, api.to_utf8(format_cnic(cnic))))
    if full_object is False:
        return brains[0]
    return api.get_object(brains[0])


def is_cnic_unique(cnic):
    """Checks whether no patient has the CNIC, regardless of the status of
    the patients and of the permissions of the current user

    :param cnic: CNIC in any format
    :returns: True if no patient with this CNIC exists
    """
    return len(search_patients_by_cnic(cnic, unrestricted=True)) == 0


def get_patient_mrn(brain):
    """Returns the MRN of a patient catalog brain as stripped unicode
    """
    mrn = getattr(brain, "mrn", None)
    if not isinstance(mrn, string_types):
        # no catalog metadata
        mrn = brain._unrestrictedGetObject().getMRN()
    return api.safe_unicode(mrn or u"").strip()
