# -*- coding: utf-8 -*-

from bika.lims import api
from bika.lims.interfaces import IAddSampleRecordsValidator
from bika.lims.interfaces import IGetDefaultFieldValueARAddHook
from senaite.core.i18n import translate
from senaite.patient.interfaces import IPatient
from senaite.starter import messageFactory as _
from senaite.starter.api import get_patient_cnic
from senaite.starter.api import is_cnic_unique
from senaite.starter.api import SAMPLE_CNIC_FIELD
from senaite.starter.api import to_cnic
from senaite.starter.validators import get_cnic_error
from senaite.starter.validators import MRN_FIELD
from six import string_types
from zope.interface import implementer


@implementer(IGetDefaultFieldValueARAddHook)
class CNICDefaultValueHook(object):
    """Default value of the CNIC field in the sample add form

    When samples are added from inside a patient, senaite.patient fills the
    patient fields of the form with the values of the patient (see its
    browser/patient/add2.py). This does the same for the CNIC.
    """

    def __init__(self, request):
        self.request = request

    def __call__(self, context):
        if IPatient.providedBy(context):
            return get_patient_cnic(context).encode("utf-8")
        return ""


def get_record_mrn(record):
    """Returns the MRN of a sample add form record and whether it is temporary

    :returns: tuple of (mrn, temporary)
    """
    value = record.get(MRN_FIELD)
    if isinstance(value, dict):
        # as processed by senaite.patient's TemporaryIdentifierWidget
        return value.get("value"), bool(value.get("temporary"))
    if isinstance(value, string_types):
        return value, False
    return None, False


@implementer(IAddSampleRecordsValidator)
class CNICRecordsValidator(object):
    """Validates the CNICs of the samples to be created

    A CNIC is unique per patient:

    - a CNIC that belongs to a patient can only be used with that patient's
      Medical Record Number
    - a CNIC that does not belong to any patient yet can not be used with
      different Medical Record Numbers, because each of them would create or
      refer to a different patient
    - samples with the same Medical Record Number can not have different
      CNICs, because the CNIC of a sample is set to its patient
    """

    def __init__(self, request):
        self.request = request

    def validate(self, records):
        errors = []
        new_cnics = {}
        mrn_cnics = {}
        for record in records:
            cnic = to_cnic(record.get(SAMPLE_CNIC_FIELD))
            if not cnic:
                continue
            mrn, temporary = get_record_mrn(record)
            mrn = api.safe_unicode(mrn or u"").strip()
            error = get_cnic_error(cnic, mrn, temporary)
            if error is None and mrn and not temporary:
                mrn_cnics.setdefault(mrn, set()).add(cnic)
                if len(mrn_cnics[mrn]) > 1:
                    error = _(
                        u"error_mrn_used_with_different_cnics",
                        default=u"Samples with Medical Record # ${mrn} have "
                                u"different CNICs",
                        mapping={"mrn": mrn})
            if error is None and not temporary and is_cnic_unique(cnic):
                new_cnics.setdefault(cnic, set()).add(mrn)
                if len(new_cnics[cnic]) > 1:
                    error = _(
                        u"error_cnic_used_for_different_mrns",
                        default=u"CNIC ${cnic} is used for samples with "
                                u"different Medical Record Numbers",
                        mapping={"cnic": cnic})
            if error is not None:
                error = translate(error)
                if error not in errors:
                    errors.append(error)

        if not errors:
            return None
        return {"message": " ".join(errors), "fielderrors": {}}
