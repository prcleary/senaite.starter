# -*- coding: utf-8 -*-

from AccessControl import ClassSecurityInfo
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from Products.CMFCore import permissions
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider
from zope import schema

from senaite.starter import messageFactory as _
from senaite.patient.interfaces import IPatient


@provider(IFormFieldProvider)
class IPatientSchemaExtender(model.Schema):
    """Extended schema fields for Patient
    """
    cnic = schema.TextLine(
        title=_(u"label_patient_cnic", default=u"CNIC"),
        description=_(
            u"description_patient_cnic",
            default=u"Computerized National Identity Card number"
        ),
        required=False,
    )


@implementer(IPatientSchemaExtender)
@adapter(IPatient)
class PatientSchemaExtender(object):
    """Extends Patient with additional fields
    """
    security = ClassSecurityInfo()

    def __init__(self, context):
        self.context = context
