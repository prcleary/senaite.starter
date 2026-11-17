# -*- coding: utf-8 -*-
"""
Patient CNIC field extension using Dexterity behavior and form provider
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


