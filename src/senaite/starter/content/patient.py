# -*- coding: utf-8 -*-
"""
Direct Patient schema extension using plone.schemaextender
This extends the Patient schema directly at import time.
"""

from plone.schemaextender.field import SchemaExtender
from plone.schemaextender.interfaces import ISchemaModifier
from zope.component import adapter
from zope.interface import implementer
from zope import schema

from senaite.starter import messageFactory as _
from senaite.patient.interfaces import IPatient


@implementer(ISchemaModifier)
@adapter(IPatient)
class PatientSchemaExtender(SchemaExtender):
    """Extends Patient schema with CNIC field
    """
    
    fields = [
        schema.TextLine(
            __name__='cnic',
            title=_(u"label_patient_cnic", default=u"CNIC"),
            description=_(
                u"description_patient_cnic",
                default=u"Computerized National Identity Card number"
            ),
            required=False,
        ),
    ]

