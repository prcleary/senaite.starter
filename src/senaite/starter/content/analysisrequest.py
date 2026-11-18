# -*- coding: utf-8 -*-
"""CNIC field for Samples (AnalysisRequest)

Same approach senaite.patient uses in its content/analysisrequest.py for the
patient fields of the sample (MRN, name, address, sex, ...): an AT schema
extender, active only when the add-on's browser layer is registered.
"""

from archetypes.schemaextender.interfaces import IBrowserLayerAwareExtender
from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims.interfaces import IAnalysisRequest
from Products.CMFCore.permissions import View
from senaite.patient.catalog import PATIENT_CATALOG
from senaite.starter import messageFactory as _
from senaite.starter.api import SAMPLE_CNIC_FIELD
from senaite.starter.browser.widgets import CNICWidget
from senaite.starter.content.fields import CNICField
from senaite.starter.interfaces import ISenaiteStarter
from senaite.starter.permissions import FieldEditCNIC
from senaite.starter.validators import CNICValidator
from zope.component import adapts
from zope.interface import implementer

# The CNIC field is placed right after this senaite.patient field
CNIC_AFTER_FIELD = "MedicalRecordNumber"

# Configured like senaite.patient's MedicalRecordNumberField, but optional,
# without temporary values and searching patients by their CNIC only
PatientCNICField = CNICField(
    SAMPLE_CNIC_FIELD,
    required=False,
    validators=(CNICValidator(), ),
    read_permission=View,
    write_permission=FieldEditCNIC,
    widget=CNICWidget(
        label=_(u"label_sample_cnic", default=u"CNIC"),
        description=_(
            u"description_sample_cnic",
            default=u"Computerized National Identity Card number of the "
                    u"patient"),
        render_own_label=True,
        visible={
            "add": "edit",
            "secondary": "disabled",
            "header_table": "prominent",
        },
        # Queryselect widget
        catalog=PATIENT_CATALOG,
        query={
            "portal_type": "Patient",
            "is_active": True,
            "sort_on": "title",
            "sort_order": "ascending",
        },
        search_index="patient_searchable_cnic",
        value_key="cnic",
        value_query_index="patient_cnic",
        search_wildcard=True,
        multi_valued=False,
        allow_user_value=True,
        columns=[
            {
                "name": "cnic",
                "width": "20",
                "align": "left",
                "label": _(u"CNIC"),
            }, {
                "name": "mrn",
                "width": "20",
                "align": "left",
                "label": _(u"MRN"),
            }, {
                "name": "firstname",
                "width": "20",
                "align": "left",
                "label": _(u"Firstname"),
            }, {
                "name": "lastname",
                "width": "20",
                "align": "left",
                "label": _(u"Lastname"),
            }, {
                "name": "getLocalizedBirthdate",
                "width": "20",
                "align": "left",
                "label": _(u"Birthdate"),
            },
        ],
        limit=3,
    ),
)


@implementer(IOrderableSchemaExtender, IBrowserLayerAwareExtender)
class AnalysisRequestSchemaExtender(object):
    """Extends the AnalysisRequest with the CNIC field
    """
    adapts(IAnalysisRequest)
    layer = ISenaiteStarter

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        return schematas

    def getFields(self):
        return [PatientCNICField]


@implementer(ISchemaModifier, IBrowserLayerAwareExtender)
class AnalysisRequestSchemaModifier(object):
    """Moves the CNIC field next to the Medical Record Number
    """
    adapts(IAnalysisRequest)
    layer = ISenaiteStarter

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        # Schema modifiers run after all schema extenders, so the fields of
        # senaite.patient are present regardless of the extenders order
        names = schema.keys()
        if SAMPLE_CNIC_FIELD in names and CNIC_AFTER_FIELD in names:
            schema.moveField(SAMPLE_CNIC_FIELD, after=CNIC_AFTER_FIELD)
        return schema
