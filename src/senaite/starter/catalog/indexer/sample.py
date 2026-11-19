# -*- coding: utf-8 -*-

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.interfaces import IListingSearchableTextProvider
from plone.indexer import indexer
from senaite.core.interfaces import ISampleCatalog
from senaite.starter.api import get_sample_cnic
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@indexer(IAnalysisRequest, ISampleCatalog)
def cnic(instance):
    """Returns the CNIC assigned to the sample, like senaite.patient's
    medical_record_number index
    """
    value = get_sample_cnic(instance)
    return [api.to_utf8(value)] if value else []


@adapter(IAnalysisRequest, Interface, ISampleCatalog)
@implementer(IListingSearchableTextProvider)
class ListingSearchableTextProvider(object):
    """Adds the CNIC to the listing_searchable_text index of samples, so that
    samples can be found by CNIC from the search box of sample listings
    """
    def __init__(self, context, request, catalog):
        self.context = context
        self.request = request
        self.catalog = catalog

    def __call__(self):
        value = get_sample_cnic(self.context)
        return [value] if value else []
