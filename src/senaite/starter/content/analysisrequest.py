# -*- coding: utf-8 -*-
"""Patient fields for Samples (AnalysisRequest)

Same approach senaite.patient uses in its content/analysisrequest.py for the
patient fields of the sample (MRN, name, address, sex, ...): an AT schema
extender, active only when the add-on's browser layer is registered.

The schema modifier also turns senaite.core's Sample Point field into the
mandatory "District of Residence" of the patient.
"""

from archetypes.schemaextender.interfaces import IBrowserLayerAwareExtender
from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims.interfaces import IAnalysisRequest
from Products.Archetypes.atapi import StringWidget
from Products.CMFCore.permissions import View
from senaite.patient.catalog import PATIENT_CATALOG
from senaite.starter import messageFactory as _
from senaite.starter.api import SAMPLE_CNIC_FIELD
from senaite.starter.browser.widgets import CNICWidget
from senaite.starter.content import ExtStringField
from senaite.starter.content.fields import CNICField
from senaite.starter.interfaces import ISenaiteStarter
from senaite.starter.permissions import FieldEditCNIC
from senaite.starter.permissions import FieldEditPatientEmail
from senaite.starter.permissions import FieldEditPatientPhone
from senaite.starter.sync import ADDRESS_FIELD
from senaite.starter.sync import EMAIL_FIELD
from senaite.starter.sync import PHONE_FIELD
from senaite.starter.validators import CNICValidator
from senaite.starter.validators import PatientEmailValidator
from zope.component import adapts
from zope.interface import implementer

# senaite.patient's Medical Record Number field. CNIC is placed right after it
MRN_FIELD = "MedicalRecordNumber"
CNIC_AFTER_FIELD = MRN_FIELD

# senaite.core's Sample Point field, used as the district of residence
SAMPLE_POINT_FIELD = "SamplePoint"

# Copies of the Sample Point field used as district: {id(original): copy}
DISTRICT_FIELDS = {}

# Configured like senaite.patient's MedicalRecordNumberField, but optional,
# without temporary values and searching patients by their CNIC only
PatientCNICField = CNICField(
    SAMPLE_CNIC_FIELD,
    required=False,
    validators=(CNICValidator(), ),
    read_permission=View,
    write_permission=FieldEditCNIC,
    widget=CNICWidget(
        label=_(u"label_sample_cnic", default=u"CNIC"),
        description=_(
            u"description_sample_cnic",
            default=u"Computerized National Identity Card number of the "
                    u"patient"),
        render_own_label=True,
        visible={
            "add": "edit",
            "secondary": "disabled",
            "header_table": "prominent",
        },
        # Queryselect widget
        catalog=PATIENT_CATALOG,
        query={
            "portal_type": "Patient",
            "is_active": True,
            "sort_on": "title",
            "sort_order": "ascending",
        },
        search_index="patient_searchable_cnic",
        value_key="cnic",
        value_query_index="patient_cnic",
        search_wildcard=True,
        multi_valued=False,
        allow_user_value=True,
        columns=[
            {
                "name": "cnic",
                "width": "20",
                "align": "left",
                "label": _(u"CNIC"),
            }, {
                "name": "mrn",
                "width": "20",
                "align": "left",
                "label": _(u"MRN"),
            }, {
                "name": "firstname",
                "width": "20",
                "align": "left",
                "label": _(u"Firstname"),
            }, {
                "name": "lastname",
                "width": "20",
                "align": "left",
                "label": _(u"Lastname"),
            }, {
                "name": "getLocalizedBirthdate",
                "width": "20",
                "align": "left",
                "label": _(u"Birthdate"),
            },
        ],
        limit=3,
    ),
)

# Contact details of the patient, configured like senaite.patient's
# "Place of residence" (PatientAddress) field
PatientEmailField = ExtStringField(
    EMAIL_FIELD,
    required=False,
    validators=(PatientEmailValidator(), ),
    read_permission=View,
    write_permission=FieldEditPatientEmail,
    widget=StringWidget(
        label=_(u"label_sample_patient_email", default=u"Patient email"),
        description=_(u"description_sample_patient_email",
                      default=u"Primary email address of the patient"),
        render_own_label=True,
        visible={
            "add": "edit",
        },
    ),
)

PatientPhoneField = ExtStringField(
    PHONE_FIELD,
    required=False,
    read_permission=View,
    write_permission=FieldEditPatientPhone,
    widget=StringWidget(
        label=_(u"label_sample_patient_phone", default=u"Patient phone"),
        description=_(u"description_sample_patient_phone",
                      default=u"Primary phone number of the patient"),
        render_own_label=True,
        visible={
            "add": "edit",
        },
    ),
)


def get_district_field(field):
    """Returns the Sample Point field as the mandatory "District of
    Residence" of the patient

    The field of senaite.core is shared by all samples and the whole process,
    so a modified copy is returned. The copy is created once per field.
    """
    if getattr(field, "district_of_residence", False):
        return field
    district = DISTRICT_FIELDS.get(id(field))
    if district is None:
        district = field.copy()
        district.district_of_residence = True
        district.required = True
        district.widget.label = _(
            u"label_sample_district", default=u"District of Residence")
        district.widget.description = _(
            u"description_sample_district",
            default=u"District where the patient lives")
        DISTRICT_FIELDS[id(field)] = district
    return district


@implementer(IOrderableSchemaExtender, IBrowserLayerAwareExtender)
class AnalysisRequestSchemaExtender(object):
    """Extends the AnalysisRequest with the CNIC and the patient's contact
    details
    """
    adapts(IAnalysisRequest)
    layer = ISenaiteStarter

    def __init__(self, context):
        self.context = context

    def getOrder(self, schematas):
        return schematas

    def getFields(self):
        return [
            PatientCNICField,
            PatientEmailField,
            PatientPhoneField,
        ]


@implementer(ISchemaModifier, IBrowserLayerAwareExtender)
class AnalysisRequestSchemaModifier(object):
    """Places the patient fields next to senaite.patient's, displays the
    Medical Record Number as entered and turns the Sample Point into the
    District of Residence
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

        # Email and phone after the "Place of residence"
        after = ADDRESS_FIELD
        for name in (EMAIL_FIELD, PHONE_FIELD):
            if name in names and after in names:
                schema.moveField(name, after=after)
                after = name

        # Without display template, the MRN widget shows the MRN as entered
        # instead of rendering new MRNs (no matching patient yet) in red as
        # "broken reference", like the CNIC widget. senaite.patient modifies
        # its shared field objects the same way in its schema modifier
        mrn = schema.get(MRN_FIELD)
        if mrn is not None:
            if getattr(mrn.widget, "display_template", None) != "":
                mrn.widget.display_template = ""

        sample_point = schema.get(SAMPLE_POINT_FIELD)
        if sample_point is not None:
            schema.replaceField(
                SAMPLE_POINT_FIELD, get_district_field(sample_point))

        return schema
