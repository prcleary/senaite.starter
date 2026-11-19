# -*- coding: utf-8 -*-

from archetypes.schemaextender.field import ExtensionField
from Products.Archetypes.public import StringField
from senaite.patient import api as patient_api

from senaite.starter.api import to_cnic


class CNICField(ExtensionField, StringField):
    """String field that stores the CNIC as entered, without surrounding
    whitespace
    """

    def set(self, instance, value, **kwargs):
        super(CNICField, self).set(instance, to_cnic(value), **kwargs)

    def get_linked_patient(self, instance):
        """Returns the patient the sample is assigned to by its Medical
        Record Number, like senaite.patient's TemporaryIdentifierField
        """
        if instance.isMedicalRecordTemporary():
            return None
        mrn = instance.getMedicalRecordNumberValue()
        if not mrn:
            return None
        try:
            return patient_api.get_patient_by_mrn(mrn, include_inactive=True)
        except ValueError:
            # more than one patient with this MRN
            return None
