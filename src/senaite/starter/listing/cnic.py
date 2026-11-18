# -*- coding: utf-8 -*-

from bika.lims import api
from senaite.app.listing.interfaces import IListingView
from senaite.app.listing.interfaces import IListingViewAdapter
from senaite.app.listing.utils import add_column
from senaite.starter import check_installed
from senaite.starter import messageFactory as _
from senaite.starter.api import get_patient_cnic
from zope.component import adapter
from zope.interface import implementer


def add_cnic_column(listing, column_id, column_values, after=None):
    """Adds the column to all review states, after the first column of the
    `after` list that exists in the listing (or at the end)
    """
    columns = listing.columns.keys()
    after = filter(lambda column: column in columns, after or [])
    review_states = map(lambda rs: rs["id"], listing.review_states)
    add_column(
        listing=listing,
        column_id=column_id,
        column_values=column_values,
        after=after[0] if after else None,
        review_states=review_states)


@implementer(IListingViewAdapter)
@adapter(IListingView)
class SamplesListingAdapter(object):
    """Adds the CNIC column to sample listings
    """
    # run after senaite.patient's adapter (99999), which adds the MRN column
    priority_order = 100000

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    @check_installed(None)
    def before_render(self):
        add_cnic_column(
            self.listing, "CNIC", {
                "title": _(u"CNIC"),
                "sortable": False,
            }, after=["MRN", "getId"])

    @check_installed(None)
    def folder_item(self, obj, item, index):
        # obj is a catalog brain: the value comes from the "getCNIC" metadata
        # column (added by the setup handler) instead of waking up the sample
        value = api.safe_getattr(obj, "getCNIC", default="")
        item["CNIC"] = api.to_utf8(value, default="")
        return item


@implementer(IListingViewAdapter)
@adapter(IListingView)
class PatientsListingAdapter(object):
    """Adds the CNIC column to patient listings
    """

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context

    @check_installed(None)
    def before_render(self):
        add_cnic_column(
            self.listing, "cnic", {
                "title": _(u"CNIC"),
                "index": "patient_cnic",
            }, after=["mrn"])

    @check_installed(None)
    def folder_item(self, obj, item, index):
        item["cnic"] = get_patient_cnic(obj).encode("utf-8")
        return item
