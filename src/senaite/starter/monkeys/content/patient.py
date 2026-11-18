# -*- coding: utf-8 -*-
#
# CNIC accessors for Patients, like the getters/setters senaite.patient
# defines on its Patient class (e.g. getMRN/setMRN)
#
# NOTE: The functions deliberately have no docstring, so that Zope does not
#       publish them as URL-callable methods.

from senaite.starter.api import get_patient_cnic
from senaite.starter.api import set_patient_cnic


def getCNIC(self):  # noqa camelcase
    # utf-8 encoded, like the other getters of the Patient class
    return get_patient_cnic(self).encode("utf-8")


def setCNIC(self, value):  # noqa camelcase
    set_patient_cnic(self, value)
