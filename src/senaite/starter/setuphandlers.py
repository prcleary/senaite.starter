# -*- coding: utf-8 -*-

import transaction
from bika.lims import api
from Products.DCWorkflow.utils import modifyRolesForPermission
from senaite.core.catalog import SAMPLE_CATALOG
from senaite.core.setuphandlers import setup_other_catalogs
from senaite.core.workflow import SAMPLE_WORKFLOW
from senaite.patient.catalog import PATIENT_CATALOG

from senaite.starter import logger
from senaite.starter.config import SAMPLE_READ_ONLY_STATES
from senaite.starter.permissions import FieldEditCNIC
from senaite.starter.permissions import FieldEditPatientEmail
from senaite.starter.permissions import FieldEditPatientPhone
from senaite.starter.sync import init_snapshot

PATIENT_WORKFLOW = "senaite_patient_workflow"

BEHAVIORS = [
    ("Patient", [
        "senaite.starter.content.patient.ICNICField",
    ]),
    ("SampleType", [
        "senaite.starter.content.sampletype.ISampleTypeSchemaExtender",
    ]),
]

# Tuples of (catalog, index_name, index_attribute, index_type)
INDEXES = [
    (PATIENT_CATALOG, "patient_cnic", "", "FieldIndex"),
    # CNIC lookup of the sample add form (like patient_searchable_mrn)
    (PATIENT_CATALOG, "patient_searchable_cnic", "", "ZCTextIndex"),
    # like senaite.patient's medical_record_number index
    (SAMPLE_CATALOG, "cnic", "", "KeywordIndex"),
]

# Tuples of (catalog, column_name)
COLUMNS = [
    # used by the CNIC column of the sample listings
    (SAMPLE_CATALOG, "getCNIC"),
]

# Patient indexes that contain the CNIC
PATIENT_CNIC_INDEXES = [
    "patient_cnic",
    "patient_searchable_cnic",
    "patient_searchable_text",
]

# Field permissions of the patient fields of samples
PATIENT_FIELD_PERMISSIONS = [
    FieldEditCNIC,
    FieldEditPatientEmail,
    FieldEditPatientPhone,
]

# Field permissions per workflow state: {permission: (acquire, roles)}
WORKFLOW_PERMISSIONS = {
    # Same as senaite.patient sets for its sample field permissions
    # (WORKFLOW_TO_UPDATE of its setuphandlers.py)
    SAMPLE_WORKFLOW: {
        state: dict.fromkeys(PATIENT_FIELD_PERMISSIONS, (False, ()))
        for state in SAMPLE_READ_ONLY_STATES
    },
    # Same as senaite_patient_workflow/definition.xml sets for its field
    # permissions
    PATIENT_WORKFLOW: {
        "active": dict.fromkeys(PATIENT_FIELD_PERMISSIONS, (True, ())),
        "inactive": dict.fromkeys(PATIENT_FIELD_PERMISSIONS, (False, ())),
    },
}

# Catalog and portal type of the objects governed by each workflow
WORKFLOW_OBJECTS = {
    SAMPLE_WORKFLOW: (SAMPLE_CATALOG, "AnalysisRequest"),
    PATIENT_WORKFLOW: (PATIENT_CATALOG, "Patient"),
}

# Number of objects after which a savepoint is done
SAVEPOINT_THRESHOLD = 500


def install(context):
    """Install handler
    """
    if context.readDataFile("senaite.starter.txt") is None:
        return
    logger.info("Install handler [BEGIN]")
    portal = context.getSite()  # noqa

    # Run Installers
    setup_behaviors(portal)
    setup_catalogs(portal)
    setup_workflows(portal)
    setup_patient_sync(portal)

    logger.info("Install handler [DONE]")


def setup_behaviors(portal):
    """Assigns additional behaviors to existing content types
    """
    logger.info("*** Setup Behaviors ***")
    pt = api.get_tool("portal_types")
    for portal_type, behavior_ids in BEHAVIORS:
        fti = pt.get(portal_type)
        if not hasattr(fti, "behaviors"):
            # Skip, type is not registered yet probably (AT2DX migration)
            logger.warn("Behaviors is missing: {} [SKIP]".format(portal_type))
            continue
        for behavior_id in behavior_ids:
            # this also invalidates the schema cache of the type
            api.enable_behavior(portal_type, behavior_id)
        logger.info("Behaviors of {}: {}".format(portal_type, fti.behaviors))


def setup_catalogs(portal):
    """Adds the CNIC indexes and metadata columns
    """
    logger.info("*** Setup Catalogs ***")

    # adds the missing indexes (and indexes them) and columns
    setup_other_catalogs(portal, indexes=INDEXES, columns=COLUMNS)

    # patient_searchable_text already exists and is only reindexed here
    reindex_patients_with_cnic(portal)


def reindex_patients_with_cnic(portal):
    """Reindexes the CNIC indexes of the patients that have a CNIC
    """
    catalog = api.get_tool(PATIENT_CATALOG)
    values = filter(None, catalog.uniqueValuesFor("patient_cnic"))
    if not values:
        return
    query = {"portal_type": "Patient", "patient_cnic": list(values)}
    brains = catalog.unrestrictedSearchResults(query)
    logger.info("Reindexing {} patients with CNIC ...".format(len(brains)))
    for brain in brains:
        obj = brain._unrestrictedGetObject()
        catalog.catalog_object(obj, idxs=PATIENT_CNIC_INDEXES,
                               update_metadata=0)


def setup_workflows(portal):
    """Sets the CNIC field permission in the workflow states and applies it to
    the existing samples and patients
    """
    logger.info("*** Setup Workflows ***")
    wf_tool = api.get_tool("portal_workflow")
    for wf_id, states in WORKFLOW_PERMISSIONS.items():
        workflow = wf_tool.getWorkflowById(wf_id)
        if workflow is None:
            logger.warn("Workflow '{}' not found [SKIP]".format(wf_id))
            continue
        for state_id, permissions in states.items():
            state = workflow.states.get(state_id)
            if state is None:
                logger.warn("State '{}' of workflow '{}' not found [SKIP]"
                            .format(state_id, wf_id))
                continue
            not_acquired = {}
            for permission, (acquire, roles) in permissions.items():
                # make the permission managed by the workflow
                if permission not in workflow.permissions:
                    workflow.permissions += (permission, )
                state.setPermission(permission, acquire, roles)
                if not acquire:
                    # objects acquire the permission unless set otherwise
                    not_acquired[permission] = roles
            if not_acquired:
                update_permissions_for(wf_id, state_id, not_acquired)


def update_permissions_for(wf_id, state_id, permissions):
    """Sets the (not acquired) roles of the permissions to the existing
    objects that are in the given workflow state

    :param permissions: dict of permission -> roles
    """
    catalog_id, portal_type = WORKFLOW_OBJECTS[wf_id]
    catalog = api.get_tool(catalog_id)
    query = {"portal_type": portal_type, "review_state": state_id}
    brains = catalog.unrestrictedSearchResults(query)
    total = len(brains)
    logger.info("Setting {} for {} {} objects in '{}' ..."
                .format(", ".join(permissions.keys()), total, portal_type,
                        state_id))
    for num, brain in enumerate(brains, start=1):
        obj = brain._unrestrictedGetObject()
        for permission, roles in permissions.items():
            modifyRolesForPermission(obj, permission, tuple(roles))
        if num % SAVEPOINT_THRESHOLD == 0:
            logger.info("Processed {}/{}".format(num, total))
            transaction.savepoint(optimistic=True)


def setup_patient_sync(portal):
    """Records the patient values of the open samples as synchronised, so
    that their next edit only copies the values changed on them to the
    patients (see senaite.starter.sync)
    """
    logger.info("*** Setup Patient Sync ***")
    catalog = api.get_tool(SAMPLE_CATALOG)
    brains = catalog.unrestrictedSearchResults(portal_type="AnalysisRequest")
    brains = filter(lambda b: b.review_state not in SAMPLE_READ_ONLY_STATES,
                    brains)
    total = len(brains)
    recorded = 0
    for num, brain in enumerate(brains, start=1):
        obj = brain._unrestrictedGetObject()
        if init_snapshot(obj):
            recorded += 1
        if num % SAVEPOINT_THRESHOLD == 0:
            logger.info("Processed {}/{}".format(num, total))
            transaction.savepoint(optimistic=True)
    logger.info("Recorded the patient values of {} of {} open samples"
                .format(recorded, total))
