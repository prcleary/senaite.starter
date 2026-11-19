# -*- coding: utf-8 -*-
"""Patient data of samples copied to patients, see senaite.starter.sync

senaite.patient creates the patient of a sample with a new Medical Record
Number in its handlers for the same events (subscribers/analysisrequest.py).
They are called before these ones, see subscribers/configure.zcml.
"""

from Products.Archetypes.interfaces import IObjectInitializedEvent
from senaite.starter import check_installed
from senaite.starter import sync


@check_installed(None)
def on_object_created(instance, event):
    """Event handler when a sample was created
    """
    mode = sync.FILL if sync.is_copy(instance) else sync.REGISTER
    result = sync.sync_sample(instance, mode=mode)
    sync.update_cc_emails(instance, result)


@check_installed(None)
def on_object_edited(instance, event):
    """Event handler when a sample was modified
    """
    if IObjectInitializedEvent.providedBy(event):
        # sample created, see on_object_created
        return
    sync.sync_sample(instance)


@check_installed(None)
def on_after_transition(instance, event):
    """Event handler when a sample was transitioned

    The retest senaite.core creates for an invalidated sample copies the
    values of the sample without the events of sample registration
    """
    transition = getattr(event, "transition", None)
    if getattr(transition, "id", None) != "invalidate":
        return
    retest = instance.getRetest()
    if retest is not None:
        sync.sync_sample(retest, mode=sync.FILL)
