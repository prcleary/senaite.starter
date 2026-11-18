# -*- coding: utf-8 -*-
#
# CNIC accessors for Samples (AnalysisRequest), like the ones senaite.patient
# adds for its sample fields (e.g. getPatientAddress). They are also used to
# fill the "getCNIC" metadata column of the sample catalog.
#
# NOTE: The functions deliberately have no docstring, so that Zope does not
#       publish them as URL-callable methods.

from senaite.starter.api import SAMPLE_CNIC_FIELD


def getCNIC(self):  # noqa camelcase, but compliant with AT's
    field = self.getField(SAMPLE_CNIC_FIELD)
    if field is None:
        return None
    return field.get(self)


def setCNIC(self, value):  # noqa camelcase, but compliant with AT's
    field = self.getField(SAMPLE_CNIC_FIELD)
    if field is None:
        return
    field.set(self, value)
