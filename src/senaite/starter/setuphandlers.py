# -*- coding: utf-8 -*-

from bika.lims import api

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

    logger.info("Install handler [DONE]")


def setup_behaviors(portal):
    """Assigns additional behaviors to existing content types
    """
    logger.info("*** Setup Behaviors ***")
    print("\n=== SETUP_BEHAVIORS DEBUG ===")
    pt = api.get_tool("portal_types")
    for portal_type, behavior_ids in BEHAVIORS:
        print(f"\nProcessing: {portal_type}")
        fti = pt.get(portal_type)
        print(f"  FTI found: {fti is not None}")
        if fti is None:
            print(f"  ERROR: FTI not found for {portal_type}")
            continue
        print(f"  FTI type: {type(fti)}")
        print(f"  Has 'behaviors' attr: {hasattr(fti, 'behaviors')}")
        if not hasattr(fti, "behaviors"):
            # Skip, type is not registered yet probably (AT2DX migration)
            logger.warn("Behaviors is missing: {} [SKIP]".format(portal_type))
            print(f"  SKIP: No behaviors attribute")
            continue
        fti_behaviors = fti.behaviors
        print(f"  Current behaviors: {fti_behaviors}")
        additional = list(filter(lambda b: b not in fti_behaviors, behavior_ids))
        print(f"  Behaviors to add: {additional}")
        if additional:
            fti_behaviors = list(fti_behaviors)
            fti_behaviors.extend(additional)
            fti.behaviors = tuple(fti_behaviors)
            print(f"  Updated behaviors: {fti.behaviors}")
            logger.info("Added behaviors to {}: {}".format(portal_type, additional))
        else:
            print(f"  No new behaviors to add")
    print("=== SETUP_BEHAVIORS DONE ===\n")
