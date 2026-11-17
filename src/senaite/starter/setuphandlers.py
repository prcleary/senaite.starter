# -*- coding: utf-8 -*-

from bika.lims import api

from senaite.starter import logger


BEHAVIORS = [
    ("Patient", [
        "senaite.starter.content.patient.ICNICField",
    ]),
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

    logger.info("Install handler [DONE]")


def setup_behaviors(portal):
    """Assigns additional behaviors to existing content types
    """
    logger.info("*** Setup Behaviors ***")
    pt = api.get_tool("portal_types")
    for portal_type, behavior_ids in BEHAVIORS:
        logger.info("Setting up behaviors for: {}".format(portal_type))
        fti = pt.get(portal_type)
        if fti is None:
            logger.warn("FTI not found: {}".format(portal_type))
            continue
        if not hasattr(fti, "behaviors"):
            logger.warn("FTI has no behaviors attribute: {}".format(portal_type))
            continue
        
        fti_behaviors = fti.behaviors
        logger.info("Current behaviors: {}".format(fti_behaviors))
        
        additional = [b for b in behavior_ids if b not in fti_behaviors]
        
        if additional:
            fti_behaviors = list(fti_behaviors)
            fti_behaviors.extend(additional)
            fti.behaviors = tuple(fti_behaviors)
            logger.info("Added behaviors to {}: {}".format(portal_type, additional))
            logger.info("New behaviors: {}".format(fti.behaviors))
        else:
            logger.info("No new behaviors to add for {}".format(portal_type))



