# -*- coding: utf-8 -*-

from senaite.starter.monkeys.address import patch_patient_address_types

# Applied when the package's ZCML is loaded (configure.zcml includes it)
patch_patient_address_types()
