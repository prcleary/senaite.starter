# -*- coding: utf-8 -*-
"""CNIC field for Patients

Patient is a Dexterity type, so the field is added through a behavior that is
enabled on the Patient FTI by the setup handler. Values are stored as the
`cnic` attribute of the patient.
"""

from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import provider

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
