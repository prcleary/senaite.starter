# -*- coding: utf-8 -*-
"""
Patient CNIC field stored as object attribute
"""

from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope.interface import provider, implementer
from zope import schema

from senaite.starter import messageFactory as _


@provider(IFormFieldProvider)
class ICNICField(model.Schema):
    """CNIC field for Patient
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


