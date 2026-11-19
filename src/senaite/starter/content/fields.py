# -*- coding: utf-8 -*-

from archetypes.schemaextender.field import ExtensionField
from Products.Archetypes.public import StringField
from senaite.patient import api as patient_api

from senaite.starter.api import mark_sample_cnic_changed
from senaite.starter.api import to_cnic


class CNICField(ExtensionField, StringField):
    """String field that stores the CNIC as entered, without surrounding
    whitespace
    """

    def set(self, instance, value, **kwargs):
        cnic = to_cnic(value)
        # A CNIC changed on an existing sample replaces the CNIC of the
        # patient, see subscribers/analysisrequest.py. Not flagged while a
        # sample is created (creation flag set), e.g. when partitions and
        # retests copy the CNIC of another sample
        if not instance.checkCreationFlag():
            if cnic != to_cnic(self.get(instance)):
                mark_sample_cnic_changed(instance)
        super(CNICField, self).set(instance, cnic, **kwargs)

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
