# -*- coding: utf-8 -*-
"""
AnalysisRequest (Sample) CNIC field extender
Displays Patient CNIC on Sample forms and listings
"""

from Products.Archetypes import atapi
from Products.Archetypes.atapi import StringField
from archetypes.schemaextender.interfaces import ISchemaModifier
from zope.interface import implementer
from zope.component import adapter

from bika.lims.interfaces import IAnalysisRequest
from senaite.starter import messageFactory as _


@implementer(ISchemaModifier)
@adapter(IAnalysisRequest)
class AnalysisRequestCNICExtender(object):
    """Extend AnalysisRequest with CNIC field from linked Patient
    """
    
    def __init__(self, context):
        self.context = context
    
    def fiddle(self, schema):
        """Add CNIC field to AnalysisRequest schema
        """
        schema.addField(
            StringField(
                name='cnic',
                widget=atapi.StringWidget(
                    label=_(u"label_patient_cnic", default=u"CNIC"),
                    description=_(
                        u"description_patient_cnic",
                        default=u"Computerized National Identity Card number"
                    ),
                    visible={'edit': 'visible', 'view': 'visible'},
                ),
                searchable=True,
                required=False,
            ),
        )
        return schema
