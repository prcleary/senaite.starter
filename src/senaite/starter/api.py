# -*- coding: utf-8 -*-
"""CNIC helpers shared by indexers, listings, subscribers and monkey patches

The CNIC is stored twice, following senaite.patient's design for the other
patient fields (MRN, name, address, sex, ...):

- on the Sample (AnalysisRequest) as the AT extension field "CNIC", which is
  the value recorded at sample registration
- on the Patient as the Dexterity behavior field "cnic"

These helpers access the stored values directly and do not depend on the
browser layer of the current request, so they also work in scripts.
"""

import re

from Acquisition import aq_base
from bika.lims import api
from six import string_types

# Name of the AT extension field on the Sample (AnalysisRequest)
SAMPLE_CNIC_FIELD = "CNIC"

# Name of the Dexterity behavior field on the Patient
PATIENT_CNIC_FIELD = "cnic"


def to_cnic(value):
    """Returns the value as a stripped unicode string or u"" if not a string
    """
    if not isinstance(value, string_types):
        return u""
    return api.safe_unicode(value).strip()


def get_cnic_search_tokens(value):
    """Returns the CNIC as entered plus its digits only, so that a CNIC can
    be searched for with or without dashes (text indexes split on dashes)
    """
    cnic = to_cnic(value)
    if not cnic:
        return []
    tokens = [cnic]
    digits = re.sub(r"\D", u"", cnic)
    if digits and digits != cnic:
        tokens.append(digits)
    return tokens


def get_sample_cnic(sample):
    """Returns the CNIC recorded in the sample as unicode

    :param sample: Sample object or catalog brain
    :returns: CNIC or u"" if not set or the field is not available
    """
    sample = api.get_object(sample)
    field = sample.getField(SAMPLE_CNIC_FIELD)
    if field is None:
        # the schema extender is only active when senaite.starter is installed
        return u""
    return to_cnic(field.get(sample))


def get_patient_cnic(patient):
    """Returns the CNIC of the patient as unicode

    :param patient: Patient object or catalog brain
    :returns: CNIC or u"" if not set or the behavior is not enabled
    """
    patient = api.get_object(patient)
    return to_cnic(getattr(aq_base(patient), PATIENT_CNIC_FIELD, None))


def set_patient_cnic(patient, value):
    """Sets the CNIC of the patient. An empty value removes the CNIC

    NOTE: The patient is not reindexed
    """
    patient = api.get_object(patient)
    setattr(patient, PATIENT_CNIC_FIELD, to_cnic(value) or None)
