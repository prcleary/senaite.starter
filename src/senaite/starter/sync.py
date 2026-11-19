# -*- coding: utf-8 -*-
"""Synchronisation of patient data from samples to patients

Reception enters and corrects patient data in samples, so that patient
records never need to be opened. senaite.patient creates a patient from the
first sample with a new Medical Record Number (MRN), but never updates
existing patients from samples. This module does:

- Sample registered: the sample's patient values replace those of the
  patient with the sample's MRN. Partitions and retests, which copy their
  values from another sample, only fill empty patient values.
- Sample edited: the values changed on the sample since its last sync
  replace those of the patient. If the MRN was changed as well, the other
  values only fill empty patient values (e.g. of the patient senaite.patient
  creates when a temporary MRN is replaced by a new one).

Empty sample values never remove patient values. A patient is only updated
if the current user may modify it, which excludes inactive patients. Samples
in read-only states are ignored.

Each sample keeps the values of its last sync in an annotation, to tell
values changed on the sample from outdated values that must not be copied
back to the patient.
"""

from collections import OrderedDict
from datetime import date
from datetime import datetime

from bika.lims import api
from bika.lims.api.mail import is_valid_email_address
from bika.lims.api.security import check_permission
from bika.lims.interfaces import IAnalysisRequestRetest
from Products.CMFCore.permissions import ModifyPortalContent
from senaite.core.api import dtime
from senaite.core.schema.addressfield import PHYSICAL_ADDRESS
from senaite.patient import api as patient_api
from six import string_types
from ZODB.POSException import ConflictError
from zope.annotation.interfaces import IAnnotations

from senaite.starter import logger
from senaite.starter import messageFactory as _
from senaite.starter.api import get_patient_cnic
from senaite.starter.api import is_cnic_unique
from senaite.starter.api import SAMPLE_CNIC_FIELD
from senaite.starter.api import set_patient_cnic
from senaite.starter.api import to_cnic
from senaite.starter.config import SAMPLE_READ_ONLY_STATES

# Annotation key of the patient values of a sample at its last sync
SNAPSHOT_KEY = "senaite.starter.patient_sync"

# Sync modes
REGISTER = "register"    # sample values replace those of the patient
FILL = "fill"            # sample values only fill empty patient values
EDIT = "edit"            # values changed since the last sync replace them
EDIT_FILL = "edit_fill"  # like EDIT, other values fill empty patient values

# Sample fields of senaite.patient
MRN_FIELD = "MedicalRecordNumber"
FULLNAME_FIELD = "PatientFullName"
ADDRESS_FIELD = "PatientAddress"
DOB_FIELD = "DateOfBirth"
SEX_FIELD = "Sex"
GENDER_FIELD = "Gender"

# Sample fields of this add-on
EMAIL_FIELD = "PatientEmail"
PHONE_FIELD = "PatientPhone"

# Patient name entry modes with a single input for the whole name
FULLNAME_ENTRY_MODES = ("full", "fullname")

# Parts of the patient's physical address that senaite.patient puts in the
# "Place of residence" of samples, in this order
# (webpack/app/components/temporaryidentifierwidget.coffee)
ADDRESS_PARTS = ("address", "zip", "city", "country")

# Keys of an address record of senaite.core's AddressField
ADDRESS_KEYS = (
    "address", "zip", "city", "subdivision2", "subdivision1", "country")


def to_text(value):
    """Returns the value as unicode without surrounding whitespace, u"" if
    the value is not a string
    """
    if not isinstance(value, string_types):
        return u""
    return api.safe_unicode(value).strip()


def to_text_block(value):
    """Returns multi-line text with stripped lines and unified line breaks
    """
    lines = to_text(value).splitlines()
    return u"\n".join(map(lambda line: line.strip(), lines)).strip()


def to_address(value):
    """Returns an address line for comparisons: text block without empty
    comma separated parts, which senaite.patient's address format leaves
    behind for empty address parts
    """
    parts = map(lambda part: part.strip(), to_text_block(value).split(u","))
    return u", ".join(filter(None, parts))


def to_date_string(value):
    """Returns the date of a date, datetime or DateTime as YYYY-MM-DD, u""
    if the value is not a date
    """
    if value and not isinstance(value, date):
        # DateTime or string
        value = dtime.to_dt(value)
    if isinstance(value, datetime):
        value = value.date()
    if not isinstance(value, date):
        return u""
    return api.safe_unicode(value.isoformat())


def get_field_value(sample, fieldname):
    """Returns the raw value of a sample field or None
    """
    field = sample.getField(fieldname)
    if field is None:
        return None
    return field.get(sample)


def get_part(part):
    """Returns a function that returns a part of a dict value, e.g. the
    firstname of the PatientFullName field
    """
    def getter(value):
        if not isinstance(value, dict):
            return None
        return value.get(part)
    return getter


def get_dob(value):
    """Returns the date of birth of a DateOfBirth value: a tuple (dob,
    from_age, estimated) as stored, or a dict as processed by its widget
    """
    if isinstance(value, dict):
        return value.get("dob")
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    return None


def identity(value):
    return value


def patient_getter(method):
    """Returns a function that returns a patient value as text
    """
    def getter(patient):
        return to_text(getattr(patient, method)())
    return getter


def patient_setter(method):
    """Returns a function that sets a patient value with its setter
    """
    def setter(patient, sample, value):
        getattr(patient, method)(value)
    return setter


def get_patient_address(patient):
    """Returns the physical address of the patient as the address lines
    senaite.patient puts in the "Place of residence" of samples: when the
    patient is picked by MRN (parts joined by commas) and when a sample is
    added from the patient (address format of the senaite.patient settings)
    """
    lines = []
    for record in patient.getAddress() or []:
        if record.get("type") != PHYSICAL_ADDRESS:
            continue
        parts = map(lambda key: to_text(record.get(key)), ADDRESS_PARTS)
        lines.append(to_address(u", ".join(filter(None, parts))))
        break
    lines.append(to_address(patient.getFormattedAddress()))
    return lines


def set_patient_address(patient, sample, value):
    """Sets the "Place of residence" of the sample as physical address of the
    patient. Like senaite.patient does when it creates a patient from a
    sample, the whole value is stored as the address line
    """
    value = to_text_block(get_field_value(sample, ADDRESS_FIELD))
    physical = dict.fromkeys(ADDRESS_KEYS, u"")
    physical.update({"type": PHYSICAL_ADDRESS, "address": value})
    others = []
    for record in patient.getAddress() or []:
        if record.get("type") == PHYSICAL_ADDRESS:
            continue
        if any(map(lambda key: to_text(record.get(key)), ADDRESS_KEYS)):
            others.append(record)
    patient.setAddress([physical] + others)


def get_patient_birthdate(patient):
    return to_date_string(patient.getBirthdate())


def set_patient_birthdate(patient, sample, value):
    """Sets the date of birth of the sample and whether it is estimated
    """
    field = sample.getField(DOB_FIELD)
    patient.setBirthdate(field.get_date_of_birth(sample))
    patient.setEstimatedBirthdate(bool(field.get_estimated(sample)))


def set_patient_email(patient, sample, value):
    """Sets the email of the patient, if valid. The patient form rejects
    invalid emails
    """
    if not is_valid_email_address(value):
        logger.warn("Patient email of sample '{}' is invalid. Not set for "
                    "Patient '{}'".format(sample.getId(), patient.getId()))
        return False
    patient.setEmail(value)


def set_cnic_of_sample(patient, sample, value):
    """Sets the CNIC of the patient, unless another patient has it already
    (CNIC is unique per patient)
    """
    if not is_cnic_unique(value):
        logger.warn("CNIC of sample '{}' belongs to another patient. Not set "
                    "for Patient '{}'".format(sample.getId(), patient.getId()))
        return False
    set_patient_cnic(patient, value)


class SyncItem(object):
    """A patient value that is copied from samples to patients

    :param name: name of the item
    :param title: label of the item for messages
    :param fieldname: name of the sample field
    :param get_patient: returns the normalised value of a patient, or a list
        of normalised values that are all equivalent to the patient's value
    :param set_patient: sets the value to a patient. Returns False if not set
    :param get: returns the item's value from the raw sample field value
    :param normalize: returns the value in the form used for comparisons
    :param name_part: whether the item is a part of the patient's name
    """

    def __init__(self, name, title, fieldname, get_patient, set_patient,
                 get=identity, normalize=to_text, name_part=False):
        self.name = name
        self.title = title
        self.fieldname = fieldname
        self.get_patient = get_patient
        self.set_patient = set_patient
        self.get = get
        self.normalize = normalize
        self.name_part = name_part

    def get_sample_value(self, sample):
        return self.normalize(self.get(get_field_value(sample, self.fieldname)))

    def get_record_value(self, record):
        """Value of a record of the sample add form (processed by widgets)
        """
        return self.normalize(self.get(record.get(self.fieldname)))


SYNC_ITEMS = (
    SyncItem("firstname", _(u"First name"), FULLNAME_FIELD,
             patient_getter("getFirstname"), patient_setter("setFirstname"),
             get=get_part("firstname"), name_part=True),
    SyncItem("middlename", _(u"Middle name"), FULLNAME_FIELD,
             patient_getter("getMiddlename"), patient_setter("setMiddlename"),
             get=get_part("middlename"), name_part=True),
    SyncItem("lastname", _(u"Last name"), FULLNAME_FIELD,
             patient_getter("getLastname"), patient_setter("setLastname"),
             get=get_part("lastname"), name_part=True),
    SyncItem("address", _(u"Place of residence"), ADDRESS_FIELD,
             get_patient_address, set_patient_address,
             normalize=to_address),
    SyncItem("birthdate", _(u"Date of birth"), DOB_FIELD,
             get_patient_birthdate, set_patient_birthdate,
             get=get_dob, normalize=to_date_string),
    SyncItem("sex", _(u"Sex"), SEX_FIELD,
             patient_getter("getSex"), patient_setter("setSex")),
    SyncItem("gender", _(u"Gender Identity"), GENDER_FIELD,
             patient_getter("getGender"), patient_setter("setGender")),
    SyncItem("email", _(u"Patient email"), EMAIL_FIELD,
             patient_getter("getEmail"), set_patient_email),
    SyncItem("phone", _(u"Patient phone"), PHONE_FIELD,
             patient_getter("getPhone"), patient_setter("setPhone")),
    SyncItem("cnic", _(u"CNIC"), SAMPLE_CNIC_FIELD,
             get_patient_cnic, set_cnic_of_sample, normalize=to_cnic),
)


def get_sync_items():
    """Returns the items that are synchronised with the current settings
    """
    if patient_api.get_patient_name_entry_mode() in FULLNAME_ENTRY_MODES:
        # senaite.patient fills only the first name of the patient into the
        # single name input, so names entered this way are not synchronised
        return filter(lambda item: not item.name_part, SYNC_ITEMS)
    return SYNC_ITEMS


def get_item(name):
    """Returns the sync item with the given name
    """
    for item in SYNC_ITEMS:
        if item.name == name:
            return item
    raise KeyError(name)


def get_sample_values(sample):
    """Returns the normalised patient values of the sample
    """
    return dict(map(lambda item: (item.name, item.get_sample_value(sample)),
                    SYNC_ITEMS))


def get_record_values(record):
    """Returns the normalised patient values of a record of the sample add
    form that are synchronised with the current settings
    """
    return OrderedDict(map(
        lambda item: (item.name, item.get_record_value(record)),
        get_sync_items()))


def get_conflicts(values_list):
    """Returns the names of the values that differ between the given values
    of samples of the same patient. Empty values are ignored

    :param values_list: list of dicts as returned by `get_record_values`
    """
    conflicts = []
    for item in get_sync_items():
        found = map(lambda record_values: record_values.get(item.name),
                    values_list)
        if len(set(filter(None, found))) > 1:
            conflicts.append(item.name)
    return conflicts


def get_sample_mrn(sample):
    """Returns the MRN of the sample and whether it is temporary

    :returns: tuple of (unicode MRN, temporary)
    """
    value = get_field_value(sample, MRN_FIELD)
    if isinstance(value, string_types):
        value = {"value": value}
    if not isinstance(value, dict):
        return u"", False
    mrn = to_text(value.get("value"))
    return mrn, bool(value.get("temporary")) or not mrn


def is_copy(sample):
    """Returns whether the sample got its patient values from another sample
    when it was created (partitions and retests)
    """
    if IAnalysisRequestRetest.providedBy(sample):
        return True
    return sample.isPartition()


def get_snapshot(sample):
    """Returns the MRN and the patient values of the sample at its last sync
    """
    annotations = IAnnotations(sample, None)
    if annotations is None:
        return None
    return annotations.get(SNAPSHOT_KEY)


def set_snapshot(sample, mrn, temporary, values):
    """Records the MRN and the patient values of the sample as synchronised
    """
    annotations = IAnnotations(sample, None)
    if annotations is None:
        return
    snapshot = {"mrn": mrn, "temporary": temporary, "values": dict(values)}
    if annotations.get(SNAPSHOT_KEY) != snapshot:
        annotations[SNAPSHOT_KEY] = snapshot


def init_snapshot(sample):
    """Records the current patient values of a sample without snapshot as
    synchronised, so that its next edit only copies changed values

    :returns: True if a snapshot was recorded
    """
    if get_snapshot(sample) is not None:
        return False
    mrn, temporary = get_sample_mrn(sample)
    set_snapshot(sample, mrn, temporary, get_sample_values(sample))
    return True


def get_edit_mode(snapshot, mrn, temporary):
    """Returns the sync mode for a modified sample
    """
    if not snapshot:
        # values of the last sync unknown, e.g. samples registered before
        # this add-on: they might be outdated and only fill empty values
        return FILL
    if (snapshot.get("mrn"), snapshot.get("temporary")) != (mrn, temporary):
        return EDIT_FILL
    return EDIT


def get_updates(mode, names, values, patient_values, snapshot_values=None):
    """Returns the names of the patient values to replace by sample values

    :param mode: sync mode
    :param names: names of the values to consider
    :param values: normalised values of the sample
    :param patient_values: normalised values of the patient. A list of
        values means that each of them is equivalent to the patient's value
    :param snapshot_values: normalised values of the sample at its last sync
    """
    snapshot_values = snapshot_values or {}
    updates = []
    for name in names:
        value = values.get(name)
        if not value:
            # empty sample values never remove patient values
            continue
        current = patient_values.get(name)
        if not isinstance(current, (list, tuple)):
            current = [current]
        if value in current:
            continue
        empty = not any(current)
        changed = value != snapshot_values.get(name)
        if mode == REGISTER:
            replace = True
        elif mode == EDIT:
            replace = changed
        elif mode == EDIT_FILL:
            replace = changed or empty
        else:
            replace = empty
        if replace:
            updates.append(name)
    return updates


def update_patient(sample, mrn, mode, values, snapshot_values):
    """Updates the patient with the MRN with the patient values of the sample

    :returns: dict with the patient (or None), the names of the updated
        values and the previous values of the patient
    """
    result = {"patient": None, "updated": [], "previous": {}}

    # skip the patient lookup if no value can be copied
    items = filter(lambda item: values.get(item.name), get_sync_items())
    if mode == EDIT:
        items = filter(lambda item: values.get(item.name) !=
                       snapshot_values.get(item.name), items)
    if not items:
        return result

    try:
        patient = patient_api.get_patient_by_mrn(mrn, include_inactive=True)
    except ValueError as exc:
        logger.error("Patient of sample '{}' not updated: {}"
                     .format(sample.getId(), exc))
        return result
    if patient is None:
        return result
    result["patient"] = patient

    # also excludes inactive patients
    if not check_permission(ModifyPortalContent, patient):
        return result

    previous = dict(map(lambda item: (item.name, item.get_patient(patient)),
                        items))
    result["previous"] = previous
    names = map(lambda item: item.name, items)
    updates = get_updates(mode, names, values, previous, snapshot_values)

    for item in items:
        if item.name not in updates:
            continue
        try:
            if item.set_patient(patient, sample, values[item.name]) is False:
                continue
        except ConflictError:
            raise
        except Exception as exc:
            # do not prevent the registration of samples
            logger.error("Patient '{}': {} not updated from sample '{}': {}"
                         .format(patient.getId(), item.name, sample.getId(),
                                 repr(exc)))
            continue
        result["updated"].append(item.name)

    if result["updated"]:
        patient.reindexObject()
        logger.info("Patient '{}' updated from sample '{}': {}".format(
            patient.getId(), sample.getId(), ", ".join(result["updated"])))
    return result


def sync_sample(sample, mode=None):
    """Updates the patient of the sample with the sample's patient values and
    records them as synchronised

    :param sample: the sample
    :param mode: sync mode, from the last sync of the sample if None
    :returns: dict with the patient (or None), the names of the updated
        values and the previous values of the patient
    """
    result = {"patient": None, "updated": [], "previous": {}}
    if api.is_temporary(sample):
        return result
    if api.get_review_status(sample) in SAMPLE_READ_ONLY_STATES:
        return result

    values = get_sample_values(sample)
    mrn, temporary = get_sample_mrn(sample)
    snapshot = get_snapshot(sample)
    if mode is None:
        mode = get_edit_mode(snapshot, mrn, temporary)
    snapshot_values = snapshot.get("values", {}) if snapshot else {}

    # no patient is created for temporary MRNs
    if mrn and not temporary:
        try:
            result = update_patient(sample, mrn, mode, values,
                                    snapshot_values)
        except ConflictError:
            raise
        except Exception:
            # do not prevent the registration or edition of samples. The
            # values are not recorded as synchronised
            logger.exception("Patient of sample '{}' not updated"
                             .format(sample.getId()))
            return result

    set_snapshot(sample, mrn, temporary, values)
    return result


def update_cc_emails(sample, result):
    """Replaces the patient's previous email by the new one in the CC emails
    of a new sample

    senaite.patient adds the email of the patient to the CC emails of new
    samples if the patient's "email report" option is set. This happens
    before the patient gets the email of the sample.

    :param result: result of `sync_sample`
    """
    patient = result.get("patient")
    if patient is None or "email" not in result.get("updated", []):
        return
    if not patient.getEmailReport():
        return
    previous = result.get("previous", {}).get("email")
    new = to_text(patient.getEmail())
    emails = []
    for email in (sample.getCCEmails() or "").split(","):
        email = to_text(email)
        if email == previous:
            email = new
        if email and email not in emails:
            emails.append(email)
    if new not in emails:
        emails.append(new)
    sample.setCCEmails(api.to_utf8(u",".join(emails)))
