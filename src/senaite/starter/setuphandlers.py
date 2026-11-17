# -*- coding: utf-8 -*-

from bika.lims import api
from zope import schema

from senaite.starter import messageFactory as _
from senaite.starter import logger


BEHAVIORS = [
    ("SampleType", [
        "senaite.starter.content.sampletype.ISampleTypeSchemaExtender",
    ]),
]


def install(context):
    """Install handler
    """
    if context.readDataFile("senaite.starter.txt") is None:
        return
    logger.info("Install handler [BEGIN]")
    portal = context.getSite()  # noqa

    # Run Installers
    setup_behaviors(portal)
    extend_patient_schema(portal)

    logger.info("Install handler [DONE]")


def setup_behaviors(portal):
    """Assigns additional behaviors to existing content types
    """
    logger.info("*** Setup Behaviors ***")
    pt = api.get_tool("portal_types")
    for portal_type, behavior_ids in BEHAVIORS:
        fti = pt.get(portal_type)
        if not hasattr(fti, "behaviors"):
            logger.warn("Behaviors is missing: {} [SKIP]".format(portal_type))
            continue
        fti_behaviors = fti.behaviors
        additional = list(filter(lambda b: b not in fti_behaviors, behavior_ids))
        if additional:
            fti_behaviors = list(fti_behaviors)
            fti_behaviors.extend(additional)
            fti.behaviors = tuple(fti_behaviors)
            logger.info("Added behaviors to {}: {}".format(portal_type, additional))


def extend_patient_schema(portal):
    """Add CNIC field directly to Patient schema
    """
    logger.info("*** Extending Patient Schema ***")
    try:
        from senaite.patient.content.patient import IPatientSchema
        
        # Check if CNIC field already exists
        if hasattr(IPatientSchema, 'cnic'):
            logger.info("CNIC field already exists in Patient schema")
            return
        
        # Add CNIC field to the schema
        cnic_field = schema.TextLine(
            __name__='cnic',
            title=_(u"label_patient_cnic", default=u"CNIC"),
            description=_(
                u"description_patient_cnic",
                default=u"Computerized National Identity Card number"
            ),
            required=False,
        )
        
        IPatientSchema['cnic'] = cnic_field
        logger.info("Successfully added CNIC field to Patient schema")
        
    except Exception as e:
        logger.error("Error extending Patient schema: {}".format(str(e)))
        import traceback
        logger.error(traceback.format_exc())

