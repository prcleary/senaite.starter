# -*- coding: utf-8 -*-
"""
AnalysisRequest (Sample) CNIC field extender
Displays Patient CNIC on Sample forms and listings
"""

from Products.Archetypes import atapi
from Products.Archetypes.atapi import StringField


def get_cnic_field():
    """Return CNIC field for AnalysisRequest schema
    """
    from senaite.starter import messageFactory as _
    
    return StringField(
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
    )

