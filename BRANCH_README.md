# Branch `add-cnic-field`: patient data entry at sample registration

A pure add-on (no fork) for SENAITE 2.6.0 with senaite.patient 1.5.0. Reception
enters and corrects all patient data in the sample registration form and the
sample view; the patient listing and form are only needed for reference. This
file is the only documentation of the branch.

- **CNIC** (Computerized National Identity Card number) for patients and
  samples, handled like the Medical Record Number (MRN)
- **Patient email and phone** on samples
- **Patient data copied from samples to patients**, including for existing
  patients (senaite.patient only creates patients from samples)
- **Autocomplete** of all patient fields when an MRN or CNIC is picked
- **District of Residence**: senaite.core's Sample Point, relabelled and
  mandatory
- **One patient address** instead of three

**Status**: the CNIC was installed and checked on a test instance (forms,
listings, copy button). Everything else is not yet tested on an instance.
Checked here: Python 2.7.18 byte-compile and pyflakes, the JavaScript in a
jsdom harness, and the sync rules in a Python 2.7 harness with fake samples
and patients that mimic senaite.patient's getters and setters.

## Patient fields of samples

| Sample field | Patient field | From |
|---|---|---|
| Medical Record # | MRN, links the sample to its patient | senaite.patient |
| CNIC | CNIC | this add-on |
| Patient name (first, middle, last) | Firstname, Middlename, Lastname | senaite.patient |
| Place of residence | Address (the only one, see below) | senaite.patient |
| Patient email | Primary email address | this add-on |
| Patient phone | Primary phone number | this add-on |
| Age / Date of birth | Birthdate, "Birthdate is estimated" | senaite.patient |
| Sex, Gender Identity | Sex, Gender | senaite.patient |
| District of Residence | None, sample only | senaite.core's Sample Point |

### Autocomplete from the patient record

- **Picking an MRN** fills all patient fields. senaite.patient fills first and
  last name, place of residence, date of birth, sex and gender; this add-on
  fills CNIC, middle name, email and phone. Removing the MRN clears them.
- **Picking a CNIC** sets that patient's MRN, which fills the rest.
- **A new MRN or CNIC** keeps what was typed for the new patient.
- **Add sample from a patient** (Patient → Samples → Add) pre-fills them.
- **Copy to new** picks the copied MRNs again, so the copied patient values
  are replaced by the current ones of the patient record.

### Copy to the patient record

| When | Effect on the patient with the sample's MRN |
|---|---|
| Sample registered | Its values replace the patient's |
| Partition or retest created | Only empty patient values are filled |
| Sample edited in the sample view | Only the values changed on that sample replace the patient's. If the MRN was changed as well, the others fill empty patient values |

- Empty sample values never clear patient values.
- Only users who may edit the patient update it: lab clerks and managers, and
  client contacts for patients stored in their own client. Inactive patients
  and samples in read-only states (verified, published, ...) are never used.
- A CNIC of another patient and invalid emails are not copied (and rejected by
  the forms).
- Samples registered together with the same MRN must not contradict each
  other (different values for the same field are rejected; empty ones are
  ignored).
- If the patient has "Add the patient email as CC recipient" set, a new
  sample that changes the email gets the new email as CC, not the old one.
- With the patient name entry mode "Fullname" (senaite.patient settings),
  names are not copied: senaite.patient's autocomplete only fills in the
  first name there.

Each sample records the values of its last copy to the patient (an
annotation). That is how an edit tells values changed on the sample from
outdated ones, e.g. an old sample saved after the patient got a new phone
number from a newer sample: the outdated phone is not copied back.

### CNIC

Handled like senaite.patient's MRN, but as a separate identifier: CNIC and
MRN never share a field, an index or a lookup.

| | MRN | CNIC |
|---|---|---|
| Format | None, stored as entered | None, stored as entered |
| Required | If "Require MRN" is set | Never |
| Unique per patient | Yes | Yes |
| Temporary values | Yes | No |
| Links a sample to its patient | Yes | No. Picking a patient by CNIC sets their MRN |

- **Lookup** after "Medical Record #", searching active patients by CNIC
  only.
- **Uniqueness**: a patient's CNIC can only be used with that patient's MRN,
  checked in the add form, the sample view and the patient form. The same new
  CNIC cannot be used for samples with different MRNs.
- **Sample view**: prominent next to the MRN; read-only once verified (or
  published, dispatched, rejected, invalid, cancelled), then linked to the
  patient.
- **Patient form**: right after the MRN.
- **Listings**: CNIC column in the sample listings (samples, client, batch),
  with an info icon if it differs from the patient's CNIC, and in the patient
  listings (global, client), sortable. The search boxes find it.
- **API and reports**: `sample.getCNIC()`, `patient.getCNIC()`,
  `senaite.starter.api.get_patient_by_cnic(cnic)`. In senaite.impress
  templates, use `model.CNIC` (and `model.PatientEmail`,
  `model.PatientPhone`).

### District of Residence

senaite.core's Sample Point field is labelled "District of Residence" and is
mandatory in the sample add form and the sample view. The districts are
managed in Site Setup → Sample Points; do not assign sample types to them
(that would limit the districts offered per sample type). It stays a sample
field. The samples listing column and the setup listing are still called
"Sample Point".

### One patient address

senaite.patient's patient form has a physical, a postal and an "other"
address. The sample's "Place of residence" is the **physical** address:
senaite.patient creates it from the sample and fills the sample from it
(street, postal code, city and country joined in one line). This add-on
reduces the patient address to that one. Postal and other addresses already
entered are no longer shown and are dropped when the patient is saved.

## How a field was added

senaite.patient keeps each patient field in two places: on the **sample**, as
an Archetypes schema extension field, and on the **patient**, as a Dexterity
field. It wires each field explicitly into catalogs, listings, searches,
permissions and the add form. **Nothing picks up a new field
automatically.** The tables below come from grepping senaite.patient for every
file that handles the MRN or `PatientAddress`; each mechanism is reproduced
here. Paths are relative to [src/senaite/starter/](src/senaite/starter) and
senaite.patient's `src/senaite/patient/`.

### Needed for every patient field

| Purpose | senaite.starter | senaite.patient |
|---|---|---|
| Sample field: schema extender for the add-on's browser layer, plus a schema modifier that positions it | [content/analysisrequest.py](src/senaite/starter/content/analysisrequest.py), [content/configure.zcml](src/senaite/starter/content/configure.zcml) | `content/analysisrequest.py` |
| Patient field: a behavior enabled on install (unless senaite.patient has the field, like email and phone) | [content/patient.py](src/senaite/starter/content/patient.py), [content/configure.zcml](src/senaite/starter/content/configure.zcml), `BEHAVIORS` in [setuphandlers.py](src/senaite/starter/setuphandlers.py) | `content/patient.py` |
| Copy from sample to patient: a `SyncItem` in `SYNC_ITEMS`, called by subscribers that run after senaite.patient's ([configure.zcml](src/senaite/starter/configure.zcml) includes senaite.patient first) | [sync.py](src/senaite/starter/sync.py), [subscribers/](src/senaite/starter/subscribers) | `subscribers/analysisrequest.py` |
| Autocomplete: an entry in `PATIENT_FIELDS` of the script (loaded by a viewlet), and a default value hook for "Add sample from a patient" | [senaite.starter.patient.js](src/senaite/starter/browser/static/js/senaite.starter.patient.js), [browser/viewlets/](src/senaite/starter/browser/viewlets), [adapters/](src/senaite/starter/adapters) | `webpack/app/components/temporaryidentifierwidget.coffee`, `browser/patient/add2.py` |
| Field permission, removed in read-only samples and inactive patients | [permissions/](src/senaite/starter/permissions), [rolemap.xml](src/senaite/starter/profiles/default/rolemap.xml), `PATIENT_FIELD_PERMISSIONS` in [setuphandlers.py](src/senaite/starter/setuphandlers.py) | `permissions.py`, `permissions.zcml`, `profiles/default/rolemap.xml`, `setuphandlers.py`, `profiles/default/workflows/senaite_patient_workflow/definition.xml` |

### Only if the field is searched, listed or used in code

| Purpose | senaite.starter | senaite.patient |
|---|---|---|
| Getter/setter on sample and patient, for catalog metadata, API and reports | [monkeys/](src/senaite/starter/monkeys) | `monkeys/content/analysisrequest.py`, `content/patient.py` |
| Catalog indexes and sample metadata column, created on install | [catalog/](src/senaite/starter/catalog), `INDEXES` and `COLUMNS` in [setuphandlers.py](src/senaite/starter/setuphandlers.py) | `catalog/patient_catalog.py`, `catalog/indexer/`, `setuphandlers.py` |
| Search boxes of the sample and patient listings | [catalog/indexer/sample.py](src/senaite/starter/catalog/indexer/sample.py), [catalog/indexer/patient.py](src/senaite/starter/catalog/indexer/patient.py) | `catalog/indexer/` |
| Listing columns, with an info icon if the sample's value differs from the patient's | [listing/cnic.py](src/senaite/starter/listing/cnic.py), [listing/configure.zcml](src/senaite/starter/listing/configure.zcml) | `adapters/listing.py`, `browser/patientfolder.py` |

### Only for an identifier like the MRN (CNIC)

| Purpose | senaite.starter | senaite.patient |
|---|---|---|
| Patient lookup widget, linked to the patient in view mode | [content/fields.py](src/senaite/starter/content/fields.py), [browser/widgets/](src/senaite/starter/browser/widgets) | `content/fields.py`, `browser/widgets/temporaryidentifier.py` |
| Lookup index, searching the CNIC only | `patient_searchable_cnic` in [catalog/indexer/patient.py](src/senaite/starter/catalog/indexer/patient.py) | `patient_searchable_mrn` |
| Unique per patient: patient form (invariant, setter), sample view (field validator), add form (records validator) | [api.py](src/senaite/starter/api.py), [content/patient.py](src/senaite/starter/content/patient.py), [validators.py](src/senaite/starter/validators.py), [adapters/addsample.py](src/senaite/starter/adapters/addsample.py) | `api.py`, `content/patient.py`, `validators.py` |
| Picking a patient by CNIC sets the MRN | [senaite.starter.patient.js](src/senaite/starter/browser/static/js/senaite.starter.patient.js) | None |

Also: [setup.py](setup.py) (dependencies),
[metadata.xml](src/senaite/starter/profiles/default/metadata.xml) (depends on
`senaite.patient:default`), [configure.zcml](src/senaite/starter/configure.zcml)
(includes), [tests/](src/senaite/starter/tests). The District of Residence is
`get_district_field` in
[content/analysisrequest.py](src/senaite/starter/content/analysisrequest.py),
the single address [monkeys/address.py](src/senaite/starter/monkeys/address.py).

Not reproduced, because they handle what only the MRN has ("Require MRN",
temporary MRNs, linking samples to their patient): `browser/controlpanel.py`,
`browser/patient/views.py`, `adapters/guards.py`, `browser/viewlets/`,
`adapters/impress.py`, `browser/patient/samples.py`.

### Adding another field

For a plain field like the patient email:

1. Sample field: an `ExtStringField` (from
   [content/\_\_init\_\_.py](src/senaite/starter/content/__init__.py)) in
   [content/analysisrequest.py](src/senaite/starter/content/analysisrequest.py)
   like `PatientEmailField`, with `read_permission=View`, a new field
   permission as `write_permission` and `visible={"add": "edit"}`. Add it to
   `AnalysisRequestSchemaExtender.getFields` and position it in
   `AnalysisRequestSchemaModifier`.
2. Patient field: if the patient has none, a behavior in
   [content/patient.py](src/senaite/starter/content/patient.py) registered and
   enabled like `ICNICField`.
3. Copy to the patient: a `SyncItem` in `SYNC_ITEMS` of
   [sync.py](src/senaite/starter/sync.py), with how to read and set the
   patient value.
4. Autocomplete: an entry in `PATIENT_FIELDS` of
   [senaite.starter.patient.js](src/senaite/starter/browser/static/js/senaite.starter.patient.js),
   and a `<field>_default_value_hook` in
   [adapters/](src/senaite/starter/adapters) like the email's.
5. Permission: in [permissions/](src/senaite/starter/permissions),
   [rolemap.xml](src/senaite/starter/profiles/default/rolemap.xml) and
   `PATIENT_FIELD_PERMISSIONS`.
6. If it must be searched or listed: the second table.
7. Bump `?v=` in
   [resources.pt](src/senaite/starter/browser/viewlets/templates/resources.pt)
   if the script changed, and reinstall senaite.starter: behaviors, indexes,
   columns and permissions are only set up by the install step.

## Install and update

- **Code changes only** (Python, JavaScript, templates): `git pull` and
  restart the instance.
- **First install, or changes to behaviors, indexes, columns or permissions**
  (as in this update): `git pull`, re-run buildout, restart, then reinstall
  senaite.starter: uninstall and install it in Site Setup → Add-ons, or
  `portal_setup` → Import → "SENAITE.STARTER" → "Import all steps".

The install step:

- enables the CNIC behavior on the Patient type
- adds the indexes `patient_cnic` and `patient_searchable_cnic` (patient
  catalog) and `cnic` with the `getCNIC` column (sample catalog), and
  reindexes the patients that have a CNIC
- sets the field permissions of CNIC, patient email and phone in the sample
  and patient workflows, and on existing samples in read-only states and
  inactive patients
- records the patient values of the open samples as copied, so that their
  next edit only copies what is changed then

The first install takes a while on a large database: the new sample index is
built for all samples, and every sample is loaded once.

ZMI checks:

- `portal_types/Patient`: behaviors include
  `senaite.starter.content.patient.ICNICField`
- `senaite_catalog_patient`: indexes `patient_cnic` and
  `patient_searchable_cnic`
- `senaite_catalog_sample`: index `cnic`, metadata column `getCNIC`
- `portal_workflow/senaite_sample_workflow/states/verified` → Permissions:
  "senaite.starter: Field: Edit CNIC", "... Edit Patient Email" and "... Edit
  Patient Phone" have no roles and are not acquired

## Testing checklist

Setup: create a few districts in Site Setup → Sample Points, without sample
types.

Sample add form:

- [ ] "District of Residence" is mandatory and offers the districts.
- [ ] Patient email and phone follow "Place of residence". An invalid email
      is rejected.
- [ ] Pick a patient by MRN: all patient fields filled, including CNIC,
      middle name, email and phone. Remove the MRN: they are cleared.
- [ ] Pick a patient by CNIC: MRN and all patient fields filled. With
      "Temporary" MRN ticked first, it gets unticked.
- [ ] New MRN and all fields typed: the created patient has all of them
      (including CNIC, middle name, email, phone).
- [ ] Pick an existing patient, change the phone (or any other value) and
      save: the patient record has the new value. Clear a value and save: the
      patient keeps it.
- [ ] Rejected: an existing patient's CNIC with another MRN, the same new
      CNIC for two different MRNs, and two samples with the same MRN and
      different values (e.g. phone).
- [ ] "Temporary" MRN and a new CNIC: no patient created. Replacing the
      temporary MRN by a new one in the sample view creates the patient with
      all values.
- [ ] Several columns: the copy buttons copy the new fields too.
- [ ] Patient → Samples → Add: all patient fields pre-filled, saving does not
      change the patient.
- [ ] "Copy to new" from an old sample of a patient whose phone changed
      since: the form shows the current phone.
- [ ] Secondary sample: registers like a normal sample.
- [ ] As a client contact: registering works; for patients shared by the lab
      the patient record is not changed.

Samples and patients:

- [ ] Sample view of an open sample: "District of Residence" mandatory; email,
      phone and CNIC editable; a change is copied to the patient.
- [ ] An older open sample saved without changes leaves the patient alone,
      even if the patient's values differ.
- [ ] Creating a partition or a retest does not change the patient.
- [ ] Inactive patients are never changed from samples.
- [ ] Patient with "Add the patient email as CC recipient": a new sample with
      a new email has the new email in CC.
- [ ] Patient form: one address only; CNIC after MRN, another patient's CNIC
      rejected.
- [ ] After verification the patient fields are read-only.

Listings and regressions:

- [ ] Sample and patient listings: CNIC column and search as before.
- [ ] A patient's own Samples tab loads.
- [ ] Existing listing columns and filters are unchanged. The Sample Type form
      still shows "Process Time". A results report publishes.
- [ ] No errors in the event log or in the browser console. Errors of the
      script start with `[senaite.starter.patient]`; sync messages in the
      event log mention "Patient '...' updated from sample".
- [ ] Automated tests: `bin/test -s senaite.starter`.

## Notes and limitations

- **CNICs are compared as entered**, like MRNs: `35202-1234567-1` and
  `3520212345671` are different CNICs. Enter CNICs consistently.
- **A CNIC belongs to one patient**, so children cannot be registered under a
  parent's CNIC. Leave their CNIC empty.
- **Old samples need a district**: open samples registered before this
  version can only be saved in the sample view once a district is set.
- **Removing or replacing the MRN empties the patient fields** of the form,
  as senaite.patient does. Picking an existing patient fills them in again.
- **Date of birth**: only a changed date is copied, together with "estimated"
  (the form does not show it for a picked date). senaite.patient fills the
  date in the browser's time zone; browsers in a time zone behind the
  server's can get the previous day, which would then be copied.
- **Secondary samples** are not read-only for patient fields: the
  "secondary: disabled" setting of senaite.patient's MRN (copied for the CNIC)
  has no effect in SENAITE 2.6.
- **Saved field order**: if "Manage form fields" of the add form (or "Manage
  sample fields" of the sample view) was ever saved, new fields go last.
  Move them there.
- **Reinstalling or upgrading senaite.patient** can drop the CNIC behavior
  from the Patient type. The data is kept. Reinstall senaite.starter.
- **MRN and CNIC are shown as entered** in the add form and sample view.
  Otherwise senaite.core shows new values in red as "broken reference". As a
  result, picking a patient in the MRN field shows the MRN, not the name.
- The `getCNIC`/`setCNIC` monkey patches have no docstrings, so Zope does not
  publish them as URL-callable methods (bypassing the field permission).
- Not on the results report templates: CNIC, email, phone.
- The template's example `content/sample.py` (`ProductionBatchNumber`) stays
  unregistered.

## Dead ends

- A behavior on Patient alone does not show the CNIC on samples:
  senaite.patient copies data from sample to patient, not the other way.
- Changing the AnalysisRequest schema in the install step only changes it in
  memory, in one process, until restart.
- The template's `SampleSchemaExtender` failed at startup (`ExtStringField`
  was missing) and added `ProductionBatchNumber` to every sample.
- archetypes.schemaextender has no `meta.zcml`
  (`IOError ... schemaextender/meta.zcml`). Include its `configure.zcml`.
- Searching CNICs in the MRN lookup, and formatting 13-digit CNICs as
  `#####-#######-#`, were removed: the CNIC is a separate identifier without a
  prescribed format.
- Detecting a changed CNIC with a flag set by its field did not extend to
  senaite.patient's fields, and missed retests (which keep their creation
  flag). The per-sample record of copied values replaced it.
