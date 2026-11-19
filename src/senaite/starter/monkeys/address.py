# -*- coding: utf-8 -*-

from senaite.core.schema.addressfield import PHYSICAL_ADDRESS
from senaite.patient.content.patient import IPatientSchema

# Address types of patients: only the physical address, which senaite.patient
# shows as "Place of residence" of samples (instead of physical, postal and
# other address)
PATIENT_ADDRESS_TYPES = (PHYSICAL_ADDRESS, )


def patch_patient_address_types():
    """Restricts the address field of patients to the physical address

    The field of senaite.patient's patient schema is used by the patient form
    and by the field's getter and setter, which ignore other address types
    """
    field = IPatientSchema.get("address")
    if field is not None:
        field.address_types = PATIENT_ADDRESS_TYPES
