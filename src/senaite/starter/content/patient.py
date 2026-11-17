# -*- coding: utf-8 -*-
"""
Patient CNIC field extension
Field is added directly to Patient schema in setuphandler
"""

from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope.interface import provider
from zope import schema

from senaite.starter import messageFactory as _


@provider(IFormFieldProvider)
class ICNICField(model.Schema):
    """Add CNIC field to Patient
    
    Note: This interface is defined here for reference but is NOT used.
    The CNIC field is added directly to IPatientSchema in setuphandler.extend_patient_schema()
    to ensure it's properly integrated into the Patient form at startup time.
    """
    
    cnic = schema.TextLine(
        __name__='cnic',
        title=_(u"label_patient_cnic", default=u"CNIC"),
        description=_(
            u"description_patient_cnic",
            default=u"Computerized National Identity Card number"
        ),
        required=False,
    )

