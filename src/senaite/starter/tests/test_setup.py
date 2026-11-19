# -*- coding: utf-8 -*-

from bika.lims import api
from bika.lims.content.analysisrequest import schema as AnalysisRequestSchema
from plone.behavior.interfaces import IBehavior
from Products.CMFPlone.utils import get_installer
from senaite.impress.interfaces import ITemplateFinder
from senaite.patient.content.patient import IPatientSchema
from zope.component import getUtility
from zope.component import queryUtility

from senaite.starter.adapters.addsample import PatientRecordsValidator
from senaite.starter.api import get_patient_cnic
from senaite.starter.api import is_cnic_unique
from senaite.starter.api import set_patient_cnic
from senaite.starter.content.analysisrequest import get_district_field
from senaite.starter.content.patient import ICNICField
from senaite.starter.content.sampletype import ISampleTypeSchemaExtender
from senaite.starter.setuphandlers import PATIENT_FIELD_PERMISSIONS
from senaite.starter.sync import EDIT
from senaite.starter.sync import FILL
from senaite.starter.sync import get_updates
from senaite.starter.sync import REGISTER
from senaite.starter.tests.base import SimpleTestCase
from senaite.starter.interfaces import ISenaiteStarter
from senaite.starter.validators import get_cnic_error
from senaite.starter.validators import PatientEmailValidator

BEHAVIOR_ID = ISampleTypeSchemaExtender.__identifier__
PATIENT_BEHAVIOR_ID = ICNICField.__identifier__


class TestSetup(SimpleTestCase):
    """Test Setup
    """

    def test_is_addon_installed(self):
        qi = get_installer(self.portal)
        self.assertTrue(qi.is_product_installed("senaite.starter"))

    def test_browser_layer_active(self):
        self.assertTrue(ISenaiteStarter.providedBy(self.request))

    def test_custom_report_templates(self):
        finder = getUtility(ITemplateFinder)
        record = {}
        for resource in finder.resources:
            if resource.get("name") == "senaite.starter":
                record = resource
        self.assertTrue(len(record.get("contents", [])) > 0)

    def test_sampletype_behavior_registered(self):
        behavior = queryUtility(IBehavior, name=BEHAVIOR_ID)
        self.assertIsNotNone(behavior)

    def test_sampletype_behavior_assigned(self):
        fti = api.get_tool("portal_types").get("SampleType")
        self.assertIn(BEHAVIOR_ID, fti.behaviors)

    def test_patient_cnic_behavior_assigned(self):
        fti = api.get_tool("portal_types").get("Patient")
        self.assertIn(PATIENT_BEHAVIOR_ID, fti.behaviors)

    def test_cnic_catalogs(self):
        patient_catalog = api.get_tool("senaite_catalog_patient")
        self.assertIn("patient_cnic", patient_catalog.indexes())
        self.assertIn("patient_searchable_cnic", patient_catalog.indexes())
        sample_catalog = api.get_tool("senaite_catalog_sample")
        self.assertIn("cnic", sample_catalog.indexes())
        self.assertIn("getCNIC", sample_catalog.schema())

    def test_cnic_unique_per_patient(self):
        patients = self.portal.patients
        patient = api.create(patients, "Patient", mrn="CNIC-1")
        set_patient_cnic(patient, " 3520212345671 ")
        patient.reindexObject()
        # stored as entered, without surrounding whitespace
        self.assertEqual(get_patient_cnic(patient), u"3520212345671")

        # like the MRN, CNICs are compared as entered
        self.assertFalse(is_cnic_unique("3520212345671"))
        self.assertTrue(is_cnic_unique("35202-1234567-1"))

        # another patient can not get the same CNIC
        other = api.create(patients, "Patient", mrn="CNIC-2")
        with self.assertRaises(ValueError):
            set_patient_cnic(other, "3520212345671")

        # samples with this CNIC must be for that patient
        self.assertIsNone(get_cnic_error("3520212345671", "CNIC-1"))
        self.assertIsNotNone(get_cnic_error("3520212345671", "CNIC-2"))
        self.assertIsNotNone(get_cnic_error("3520212345671", "CNIC-1",
                                            temporary=True))
        self.assertIsNone(get_cnic_error("3520212345672", "CNIC-2"))

    def test_patient_records_validator(self):
        validator = PatientRecordsValidator(self.request)
        mrn = {"value": "REC-1", "temporary": False}
        # the patient values of samples are copied to their patient, so
        # samples of the same patient must not contradict each other
        records = [
            {"MedicalRecordNumber": mrn, "CNIC": "111",
             "PatientPhone": "0300"},
            {"MedicalRecordNumber": mrn, "CNIC": "222",
             "PatientPhone": ""},
        ]
        self.assertIsNotNone(validator.validate(records))
        # empty values are ignored
        records[1]["CNIC"] = "111"
        self.assertIsNone(validator.validate(records))
        # no patient for temporary MRNs
        records[1]["CNIC"] = "222"
        for record in records:
            record["MedicalRecordNumber"] = {"value": "T", "temporary": True}
        self.assertIsNone(validator.validate(records))

    def test_patient_sync_updates(self):
        values = {"email": u"new@x.org", "phone": u"", "cnic": u"111"}
        patient = {"email": u"old@x.org", "phone": u"0300", "cnic": u""}
        snapshot = {"email": u"new@x.org", "phone": u"0300", "cnic": u""}
        names = ["email", "phone", "cnic"]
        # registration: sample values replace the patient's, empty ones not
        self.assertEqual(
            get_updates(REGISTER, names, values, patient), ["email", "cnic"])
        # copies: only empty patient values are filled
        self.assertEqual(
            get_updates(FILL, names, values, patient), ["cnic"])
        # edit: only values changed since the last sync
        self.assertEqual(
            get_updates(EDIT, names, values, patient, snapshot), ["cnic"])
        # equivalent patient values
        patient["email"] = [u"x@x.org", u"new@x.org"]
        self.assertEqual(
            get_updates(REGISTER, names, values, patient), ["cnic"])

    def test_district_field(self):
        field = AnalysisRequestSchema["SamplePoint"]
        district = get_district_field(field)
        self.assertTrue(district.required)
        self.assertEqual(district.widget.label.default,
                         u"District of Residence")
        # senaite.core's field is shared by all samples and stays unchanged
        self.assertFalse(field.required)
        self.assertIs(get_district_field(field), district)
        self.assertIs(get_district_field(district), district)

    def test_patient_single_address(self):
        field = IPatientSchema["address"]
        self.assertEqual(field.get_address_types(), ("physical", ))

    def test_patient_email_validator(self):
        validator = PatientEmailValidator()
        self.assertTrue(validator(""))
        self.assertTrue(validator(" patient@example.org "))
        self.assertNotEqual(validator("patient@"), True)

    def test_cnic_workflow_permissions(self):
        wf_tool = api.get_tool("portal_workflow")
        workflow = wf_tool.getWorkflowById("senaite_sample_workflow")
        verified = workflow.states.get("verified")
        patient_workflow = wf_tool.getWorkflowById("senaite_patient_workflow")
        inactive = patient_workflow.states.get("inactive")
        for permission in PATIENT_FIELD_PERMISSIONS:
            # read-only in verified samples, like senaite.patient's fields
            self.assertIn(permission, workflow.permissions)
            self.assertEqual(verified.permission_roles[permission], ())
            # read-only in inactive patients
            self.assertEqual(inactive.permission_roles[permission], ())

    def test_jsonapi_registered(self):
        endpoint = "senaite.starter/version"
        response = self.get_json(endpoint)
        self.assertEquals(response.get("version"), "1.0.0")


def test_suite():
    from unittest import TestSuite
    from unittest import makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestSetup))
    return suite
