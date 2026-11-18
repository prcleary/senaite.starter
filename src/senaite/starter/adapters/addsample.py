# -*- coding: utf-8 -*-

from bika.lims.interfaces import IGetDefaultFieldValueARAddHook
from senaite.patient.interfaces import IPatient
from senaite.starter.api import get_patient_cnic
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
