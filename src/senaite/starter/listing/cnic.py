# -*- coding: utf-8 -*-

from cgi import escape

from bika.lims import api
from bika.lims.utils import get_link
from plone.memoize.instance import memoize
from senaite.app.listing.interfaces import IListingView
from senaite.app.listing.interfaces import IListingViewAdapter
from senaite.app.listing.utils import add_column
from senaite.core.i18n import translate
from senaite.patient.api import get_patient_by_mrn
from senaite.starter import check_installed
from senaite.starter import messageFactory as _
from senaite.starter.api import get_patient_cnic
from senaite.starter.api import to_cnic
from zope.component import adapter
from zope.component import getMultiAdapter
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
    """Adds the CNIC column to sample listings, like senaite.patient's MRN
    column: linked to the patient, with an info icon if the CNIC of the
    sample is not the one of the patient
    """
    # run after senaite.patient's adapter (99999), which adds the MRN column
    priority_order = 100000

    def __init__(self, listing, context):
        self.listing = listing
        self.context = context
        self.patients = {}

    @property
    @memoize
    def senaite_theme(self):
        return getMultiAdapter(
            (self.context, self.listing.request),
            name="senaite_theme")

    def icon_tag(self, name, **kwargs):
        return self.senaite_theme.icon_tag(name, **kwargs)

    def get_patient(self, obj):
        """Returns the patient assigned to the sample by its MRN
        """
        mrn = api.safe_getattr(obj, "getMedicalRecordNumberValue", default="")
        mrn = api.to_utf8(mrn, default="")
        if not mrn:
            return None
        if mrn not in self.patients:
            try:
                self.patients[mrn] = get_patient_by_mrn(mrn)
            except ValueError:
                # more than one patient with this MRN
                self.patients[mrn] = None
        return self.patients[mrn]

    @check_installed(None)
    def before_render(self):
        add_cnic_column(
            self.listing, "CNIC", {
                "title": _(u"CNIC"),
                "sortable": False,
                "index": "cnic",
            }, after=["MRN", "getId"])

    @check_installed(None)
    def folder_item(self, obj, item, index):
        # obj is a catalog brain: the value comes from the "getCNIC" metadata
        # column (added by the setup handler) instead of waking up the sample
        cnic = to_cnic(api.safe_getattr(obj, "getCNIC", default=""))
        if not cnic:
            return item
        value = api.to_utf8(cnic)
        item["CNIC"] = value

        patient = self.get_patient(obj)
        if patient is None:
            return item

        # Link to patient object
        item["replace"]["CNIC"] = get_link(
            api.get_url(patient), value=escape(value))

        patient_cnic = get_patient_cnic(patient)
        if patient_cnic != cnic:
            msg = _(u"Patient CNIC of sample is not equal to ${cnic}",
                    mapping={"cnic": patient_cnic or u"-"})
            item["after"]["CNIC"] = self.icon_tag(
                "info", width=16, title=translate(msg))
        return item


@implementer(IListingViewAdapter)
@adapter(IListingView)
class PatientsListingAdapter(object):
    """Adds the CNIC column to patient listings, linked to the patient like
    the Medical Record # column
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
        cnic = get_patient_cnic(obj)
        if not cnic:
            return item
        value = api.to_utf8(cnic)
        item["cnic"] = value
        item["replace"]["cnic"] = get_link(api.get_url(obj), value=escape(value))
        return item
