# -*- coding: utf-8 -*-
"""CNIC field for Patients

Patient is a Dexterity type, so the field is added through a behavior that is
enabled on the Patient FTI by the setup handler. Values are stored as the
`cnic` attribute of the patient.
"""

from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from senaite.patient.interfaces import IPatient
from zope import schema
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Invalid
from zope.interface import invariant
from zope.interface import provider

from senaite.starter import messageFactory as _
from senaite.starter.api import get_patient_cnic
from senaite.starter.api import is_cnic_unique
from senaite.starter.api import set_patient_cnic
from senaite.starter.api import to_cnic


@provider(IFormFieldProvider)
class ICNICField(model.Schema):
    """CNIC field for Patient
    """

    # next to the Medical Record #, like in the sample
    directives.order_after(cnic="mrn")
    cnic = schema.TextLine(
        title=_(u"label_patient_cnic", default=u"CNIC"),
        description=_(
            u"description_patient_cnic",
            default=u"Computerized National Identity Card number"
        ),
        required=False,
    )

    @invariant
    def validate_cnic(data):
        """Checks if the patient CNIC is unique, like senaite.patient does
        for the Medical Record Number
        """
        cnic = to_cnic(data.cnic)
        if not cnic:
            return

        context = getattr(data, "__context__", None)
        if isinstance(context, CNICFieldAdapter):
            context = context.context
        if IPatient.providedBy(context) and get_patient_cnic(context) == cnic:
            # nothing changed
            return

        if not is_cnic_unique(cnic):
            raise Invalid(
                _(u"invalid_patient_cnic_must_be_unique",
                  default=u"Patient CNIC must be unique"))


@implementer(ICNICField)
@adapter(IPatient)
class CNICFieldAdapter(object):
    """Stores the CNIC as `cnic` attribute of the patient
    """

    def __init__(self, context):
        self.context = context

    @property
    def cnic(self):
        return get_patient_cnic(self.context) or None

    @cnic.setter
    def cnic(self, value):
        set_patient_cnic(self.context, value)
