# -*- coding: utf-8 -*-

from bika.lims import api
from plone.behavior.interfaces import IBehavior
from Products.CMFPlone.utils import get_installer
from senaite.impress.interfaces import ITemplateFinder
from zope.component import getUtility
from zope.component import queryUtility

from senaite.starter.api import format_cnic
from senaite.starter.api import get_patient_cnic
from senaite.starter.api import is_cnic_unique
from senaite.starter.api import set_patient_cnic
from senaite.starter.content.patient import ICNICField
from senaite.starter.content.sampletype import ISampleTypeSchemaExtender
from senaite.starter.permissions import FieldEditCNIC
from senaite.starter.tests.base import SimpleTestCase
from senaite.starter.interfaces import ISenaiteStarter
from senaite.starter.validators import get_cnic_error

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

    def test_cnic_standard_format(self):
        self.assertEqual(format_cnic("3520212345671"), u"35202-1234567-1")
        self.assertEqual(format_cnic(" 35202 1234567 1 "), u"35202-1234567-1")
        # other values are kept as entered
        self.assertEqual(format_cnic(" AB-123 "), u"AB-123")
        self.assertEqual(format_cnic(None), u"")

    def test_cnic_unique_per_patient(self):
        patients = self.portal.patients
        patient = api.create(patients, "Patient", mrn="CNIC-1")
        set_patient_cnic(patient, "3520212345671")
        patient.reindexObject()
        self.assertEqual(get_patient_cnic(patient), u"35202-1234567-1")

        # the CNIC is taken, whatever its format
        self.assertFalse(is_cnic_unique("35202-1234567-1"))
        self.assertFalse(is_cnic_unique("3520212345671"))
        self.assertTrue(is_cnic_unique("35202-1234567-2"))

        # another patient can not get the same CNIC
        other = api.create(patients, "Patient", mrn="CNIC-2")
        with self.assertRaises(ValueError):
            set_patient_cnic(other, "35202 1234567 1")

        # samples with this CNIC must be for that patient
        self.assertIsNone(get_cnic_error("3520212345671", "CNIC-1"))
        self.assertIsNotNone(get_cnic_error("3520212345671", "CNIC-2"))
        self.assertIsNotNone(get_cnic_error("3520212345671", "CNIC-1",
                                            temporary=True))
        self.assertIsNone(get_cnic_error("35202-1234567-2", "CNIC-2"))

    def test_cnic_workflow_permissions(self):
        wf_tool = api.get_tool("portal_workflow")
        # read-only in verified samples, like senaite.patient's fields
        workflow = wf_tool.getWorkflowById("senaite_sample_workflow")
        self.assertIn(FieldEditCNIC, workflow.permissions)
        verified = workflow.states.get("verified")
        self.assertEqual(verified.permission_roles[FieldEditCNIC], ())
        # read-only in inactive patients
        workflow = wf_tool.getWorkflowById("senaite_patient_workflow")
        inactive = workflow.states.get("inactive")
        self.assertEqual(inactive.permission_roles[FieldEditCNIC], ())

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
