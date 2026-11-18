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
from Products.Archetypes.Widget import StringWidget
from Products.CMFCore.permissions import View
from senaite.starter import messageFactory as _
from senaite.starter.api import SAMPLE_CNIC_FIELD
from senaite.starter.content import ExtStringField
from senaite.starter.interfaces import ISenaiteStarter
from senaite.starter.permissions import FieldEditCNIC
from zope.component import adapts
from zope.interface import implementer

# The CNIC field is placed right after this senaite.patient field
CNIC_AFTER_FIELD = "MedicalRecordNumber"

CNICField = ExtStringField(
    SAMPLE_CNIC_FIELD,
    required=False,
    read_permission=View,
    write_permission=FieldEditCNIC,
    widget=StringWidget(
        label=_(u"label_sample_cnic", default=u"CNIC"),
        description=_(
            u"description_sample_cnic",
            default=u"Computerized National Identity Card number of the "
                    u"patient"),
        render_own_label=True,
        visible={
            "add": "edit",
        },
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
        return [CNICField]


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
