# -*- coding: utf-8 -*-

from bika.lims import api
from Products.validation import validation
from Products.validation.interfaces.IValidator import IValidator
from senaite.core.i18n import translate
from six import string_types
from zope.interface import implementer

from senaite.starter import messageFactory as _
from senaite.starter.api import format_cnic
from senaite.starter.api import get_patient_mrn
from senaite.starter.api import search_patients_by_cnic

MRN_FIELD = "MedicalRecordNumber"


def get_cnic_error(cnic, mrn, temporary=False):
    """Checks whether the CNIC can be recorded for a sample with this MRN

    A CNIC is unique per patient. If a patient has the CNIC already, the
    sample must be for that patient, i.e. have its (non temporary) MRN.

    :returns: error message or None
    """
    cnic = format_cnic(cnic)
    if not cnic:
        return None
    brains = search_patients_by_cnic(cnic, unrestricted=True)
    if not brains:
        return None
    mrn = api.safe_unicode(mrn or u"").strip()
    if mrn and not temporary:
        if any(map(lambda brain: get_patient_mrn(brain) == mrn, brains)):
            return None
    return _(u"error_cnic_assigned_to_other_patient",
             default=u"CNIC ${cnic} is already assigned to another patient. "
                     u"Select the patient through the CNIC or the Medical "
                     u"Record # instead",
             mapping={"cnic": cnic})


def get_submitted_mrn(sample):
    """Returns the MRN of the sample and whether it is temporary

    Values submitted with the request (e.g. when both fields are edited in
    the sample header) have priority over the stored ones.

    :returns: tuple of (mrn, temporary)
    """
    request = api.get_request()
    form = getattr(request, "form", {})
    if MRN_FIELD not in form:
        mrn = sample.getMedicalRecordNumberValue()
        return mrn, sample.isMedicalRecordTemporary()
    value = form.get(MRN_FIELD)
    if isinstance(value, (list, tuple)):
        value = value and value[0] or ""
    if not isinstance(value, string_types):
        value = ""
    # the textarea of the widget contains one value per line
    values = filter(None, map(lambda v: v.strip(), value.splitlines()))
    temporary = bool(form.get("{}_temporary".format(MRN_FIELD)))
    return values and values[0] or "", temporary


@implementer(IValidator)
class CNICValidator(object):
    """Verifies that the CNIC of a sample does not belong to a patient other
    than the one of the sample
    """
    name = "senaite_starter_cnic_validator"

    def __call__(self, value, instance=None, *args, **kwargs):
        if instance is None or api.is_temporary(instance):
            # samples of the sample add form are validated together with the
            # other values of the record, see adapters.addsample
            return True
        mrn, temporary = get_submitted_mrn(instance)
        error = get_cnic_error(value, mrn, temporary)
        if error:
            return translate(error)
        return True


# Register validators
validation.register(CNICValidator())
