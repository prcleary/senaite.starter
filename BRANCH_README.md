# Branch `add-cnic-field`: CNIC for patients and samples

Adds a **CNIC** (Computerized National Identity Card number) to patients and
samples in SENAITE 2.6.0 with senaite.patient 1.5.0, as a pure add-on (no fork
of senaite.patient). This file is the only documentation of the branch.

**Status**: installed on a test instance. The CNIC appears in the sample add
form, the patient form and the sample and patient listings, and the add
form's copy button copies it. Registering samples end to end is still to be
tested. The Python code is checked with Python 2.7.18 (byte-compile,
pyflakes) and the JavaScript in a jsdom harness.

## What the CNIC does

The CNIC is handled like senaite.patient's Medical Record Number (MRN), but as
a separate identifier: CNIC and MRN never share a field, an index or a lookup.

| | MRN | CNIC |
|---|---|---|
| Format | None, stored as entered | None, stored as entered |
| Required | If "Require MRN" is set | Never |
| Unique per patient | Yes | Yes |
| Temporary values | Yes | No |
| Links a sample to its patient | Yes | No. Picking a patient by CNIC sets their MRN |

- **Sample add form**: CNIC lookup after "Medical Record #", searching active
  patients by CNIC only. Picking a patient sets their MRN, and senaite.patient
  then fills the other patient fields. Picking a patient by MRN fills the
  CNIC, and removing the MRN clears it. A new CNIC can be typed for a new
  patient.
- **Uniqueness**: a CNIC that belongs to a patient can only be used with that
  patient's MRN. This is checked in the add form, the sample header and the
  patient form. The same new CNIC cannot be used for samples with different
  MRNs, and samples registered together with the same MRN must have the same
  CNIC.
- **Sample to patient**: the CNIC is entered and corrected in samples, so
  the patient record never needs to be opened. Registering a sample, or
  changing the CNIC of an open sample, sets its CNIC on the patient with that
  MRN, replacing a different one. Other changes to a sample only fill an
  empty patient CNIC, e.g. when a temporary MRN is replaced. An empty CNIC
  never removes the patient's CNIC, and partitions and secondary samples
  (copies of another sample) never replace it.
- **Add sample from a patient**: CNIC pre-filled. With "Copy to new", the
  copied CNICs are refreshed from the patient records, so that an outdated
  CNIC is not set back on the patient.
- **Sample view**: CNIC prominent next to the MRN. Read-only once the sample
  is verified, published, dispatched, rejected, invalid or cancelled, and
  then linked to the patient. Disabled for secondary samples.
- **Patient form**: CNIC right after the MRN.
- **Listings**: CNIC column in the sample listings (samples, client, batch),
  with an info icon if it differs from the patient's CNIC. Also in the
  patient listings (global, client), sortable. The search boxes find it.
- **API and reports**: `sample.getCNIC()`, `patient.getCNIC()`,
  `senaite.starter.api.get_patient_by_cnic(cnic)`. In senaite.impress
  templates, use `model.CNIC`.

## How the field was added

senaite.patient keeps each patient field in two places:

- on the **sample**, as an Archetypes schema extension field holding the value
  entered at registration
- on the **patient**, as a Dexterity field. senaite.patient creates the
  patient from the sample when a sample with a new MRN is registered.

It then wires each field explicitly into catalogs, listings, searches,
permissions and the add form. **Nothing picks up a new field automatically.**
The tables below come from grepping senaite.patient for every file that
handles the MRN or `PatientAddress`. Each mechanism is reproduced in this
add-on. senaite.starter paths are relative to
[src/senaite/starter/](src/senaite/starter), senaite.patient paths to its
`src/senaite/patient/`.

### Needed for every patient field

| Purpose | senaite.starter | senaite.patient |
|---|---|---|
| Sample field: schema extender for the add-on's browser layer, plus a schema modifier that places it after the MRN | [content/analysisrequest.py](src/senaite/starter/content/analysisrequest.py), [content/configure.zcml](src/senaite/starter/content/configure.zcml) | `content/analysisrequest.py` |
| Patient field: behavior, enabled on install | [content/patient.py](src/senaite/starter/content/patient.py), [content/configure.zcml](src/senaite/starter/content/configure.zcml), `BEHAVIORS` in [setuphandlers.py](src/senaite/starter/setuphandlers.py) | `content/patient.py` |
| `getCNIC`/`setCNIC` on sample and patient, for catalog metadata, API and reports | [monkeys/](src/senaite/starter/monkeys) | `monkeys/content/analysisrequest.py`, `content/patient.py` |
| Copy from sample to patient. senaite.patient only creates patients from samples, the CNIC also updates existing ones: the field flags a CNIC changed on an existing sample. Must run after senaite.patient's subscribers, so [configure.zcml](src/senaite/starter/configure.zcml) includes senaite.patient first | [subscribers/](src/senaite/starter/subscribers), [content/fields.py](src/senaite/starter/content/fields.py) | `subscribers/analysisrequest.py` |
| Fill from the patient in the add form: when an MRN is picked or samples are copied ("Copy to new"), with a script loaded by a viewlet, and when a sample is added from a patient | [senaite.starter.cnic.js](src/senaite/starter/browser/static/js/senaite.starter.cnic.js), [browser/viewlets/](src/senaite/starter/browser/viewlets), `CNICDefaultValueHook` in [adapters/](src/senaite/starter/adapters) | `webpack/app/components/temporaryidentifierwidget.coffee`, `browser/patient/add2.py` |
| Catalog indexes and sample metadata column, created on install | [catalog/](src/senaite/starter/catalog), `INDEXES` and `COLUMNS` in [setuphandlers.py](src/senaite/starter/setuphandlers.py) | `catalog/patient_catalog.py`, `catalog/indexer/`, `setuphandlers.py` |
| Search boxes of the sample and patient listings | `IListingSearchableTextProvider` in [catalog/indexer/sample.py](src/senaite/starter/catalog/indexer/sample.py), `patient_searchable_text` in [catalog/indexer/patient.py](src/senaite/starter/catalog/indexer/patient.py) | `catalog/indexer/` |
| Listing columns, linked to the patient, with an info icon in sample listings if the sample's value differs from the patient's | [listing/cnic.py](src/senaite/starter/listing/cnic.py), [listing/configure.zcml](src/senaite/starter/listing/configure.zcml) | `adapters/listing.py`, `browser/patientfolder.py` |
| Field permission, removed in closed samples and inactive patients | [permissions/](src/senaite/starter/permissions), [rolemap.xml](src/senaite/starter/profiles/default/rolemap.xml), `WORKFLOW_PERMISSIONS` in [setuphandlers.py](src/senaite/starter/setuphandlers.py) | `permissions.py`, `permissions.zcml`, `profiles/default/rolemap.xml`, `setuphandlers.py`, `profiles/default/workflows/senaite_patient_workflow/definition.xml` |

### Only for an identifier like the MRN

| Purpose | senaite.starter | senaite.patient |
|---|---|---|
| Patient lookup widget, linked to the patient in view mode | [content/fields.py](src/senaite/starter/content/fields.py), [browser/widgets/](src/senaite/starter/browser/widgets) | `content/fields.py`, `browser/widgets/temporaryidentifier.py` |
| Lookup index, searching the CNIC only | `patient_searchable_cnic` in [catalog/indexer/patient.py](src/senaite/starter/catalog/indexer/patient.py) | `patient_searchable_mrn` in `catalog/indexer/patient.py` |
| Unique per patient: patient form (invariant, setter), sample header (field validator), add form (records validator) | [api.py](src/senaite/starter/api.py), [content/patient.py](src/senaite/starter/content/patient.py), [validators.py](src/senaite/starter/validators.py), `CNICRecordsValidator` in [adapters/](src/senaite/starter/adapters) | `api.py`, `content/patient.py`, `validators.py` |
| Picking a patient by CNIC sets the MRN | [senaite.starter.cnic.js](src/senaite/starter/browser/static/js/senaite.starter.cnic.js) | None |

Done once for the package: [setup.py](setup.py) (dependencies),
[metadata.xml](src/senaite/starter/profiles/default/metadata.xml) (depends on
`senaite.patient:default`), [configure.zcml](src/senaite/starter/configure.zcml)
(includes) and [tests/](src/senaite/starter/tests).

Not reproduced, because these files handle what only the MRN has (the
"Require MRN" setting, temporary MRNs, linking samples to their patient):
`browser/controlpanel.py`, `browser/patient/views.py`, `adapters/guards.py`,
`browser/viewlets/` (temporary MRN), `adapters/impress.py` (reports grouped by
MRN), `browser/patient/samples.py` (a patient's samples, found by MRN).

### Adding another field

For a plain field like senaite.patient's `PatientAddress`, repeat the first
table:

1. Define the sample field in
   [content/analysisrequest.py](src/senaite/starter/content/analysisrequest.py)
   and add it to `AnalysisRequestSchemaExtender.getFields`. Use `ExtStringField`
   from [content/\_\_init\_\_.py](src/senaite/starter/content/__init__.py) with
   a standard widget, `read_permission=View`, a new field permission as
   `write_permission` and `visible={"add": "edit"}`. Position it in
   `AnalysisRequestSchemaModifier`.
2. Add the patient field as a behavior in
   [content/patient.py](src/senaite/starter/content/patient.py), registered
   and enabled like `ICNICField`.
3. Add code next to the CNIC's in the other files of the table: accessors,
   subscriber, JS fill, default value hook, indexers and indexes, searches,
   listing columns, permission and workflow states.
4. Reinstall senaite.starter. Behaviors, indexes, columns and workflow
   permissions are only set up by the install step.

## Install and update

- **Code changes only** (Python, JavaScript, templates): `git pull` and
  restart the instance.
- **First install, or changes to behaviors, indexes, columns or
  permissions**: `git pull`, re-run buildout, restart, then reinstall
  senaite.starter. Either uninstall and install it in Site Setup → Add-ons,
  or use `portal_setup` → Import → "SENAITE.STARTER" → "Import all steps".

The install step:

- enables the CNIC behavior on the Patient type
- adds the indexes `patient_cnic` and `patient_searchable_cnic` (patient
  catalog) and `cnic` with the `getCNIC` column (sample catalog)
- reindexes the patients that have a CNIC
- sets the CNIC permission in the sample and patient workflows, and on
  existing samples in read-only states and inactive patients

The first install takes a while on a large database: the new sample index is
built for all samples, and the permission is set on every closed sample.

ZMI checks:

- `portal_types/Patient`: behaviors include
  `senaite.starter.content.patient.ICNICField`
- `senaite_catalog_patient`: indexes `patient_cnic` and
  `patient_searchable_cnic`
- `senaite_catalog_sample`: index `cnic`, metadata column `getCNIC`
- `portal_workflow/senaite_sample_workflow/states/verified` → Permissions:
  "senaite.starter: Field: Edit CNIC" has no roles and is not acquired

## Testing checklist

Sample add form:

- [ ] New MRN and new CNIC: the created patient has the CNIC, as typed.
- [ ] Pick a patient by MRN: CNIC filled. Remove the MRN: CNIC cleared.
- [ ] Pick a patient by CNIC: MRN, name, address, date of birth, sex and
      gender filled. With "Temporary" MRN ticked first, it gets unticked.
- [ ] Pick a patient by MRN, change the CNIC to a new one and save: the
      patient record has the new CNIC.
- [ ] Rejected: an existing patient's CNIC with another MRN, the same new
      CNIC for two different MRNs, and two samples with the same MRN but
      different CNICs.
- [ ] "Temporary" MRN and a new CNIC: saved with a temporary MRN, no patient
      created. Replacing the temporary MRN by a new one in the sample view
      (CNIC entered again if emptied) creates the patient with the CNIC.
- [ ] "Temporary" ticked after a patient with a CNIC was filled in: saving
      is refused with "CNIC … belongs to a registered patient".
- [ ] A CNIC typed in "Medical Record #" finds no patient, nor does an MRN
      typed in "CNIC".
- [ ] A sample without CNIC registers as before, also with a temporary MRN.
- [ ] Several columns: picking a patient fills only that column. The copy
      button copies the CNIC, and fills the MRN for an existing patient's
      CNIC.
- [ ] Secondary sample: CNIC disabled.
- [ ] Patient → Samples → Add: CNIC pre-filled.
- [ ] "Copy to new" from a sample registered before its patient's CNIC was
      changed: the form shows the patient's current CNIC.
- [ ] As a client contact: registering a sample with a CNIC works.

Samples and patients:

- [ ] Sample header of an open sample: the CNIC can be changed, and the
      patient record gets the new CNIC. Another patient's CNIC is rejected,
      unless the MRN is changed to that patient's MRN at the same time.
- [ ] After verification the CNIC is read-only and links to the patient.
- [ ] Older samples with a previous CNIC of the patient show the info icon.
      Saving their header without changing the CNIC leaves the patient's
      CNIC alone.
- [ ] Existing patient without CNIC: gets it from the next sample.
- [ ] Creating a partition or a retest does not change the patient's CNIC.
- [ ] Inactive patients are not offered by the CNIC lookup, and their CNIC is
      not changed from samples.
- [ ] Patient form: CNIC after MRN, saved as typed, can be cleared. Another
      patient's CNIC is rejected, also when adding a patient.
- [ ] Partitions and retests carry the CNIC.

Listings and regressions:

- [ ] Sample listings: CNIC column linked to the patient. The search finds it.
- [ ] Patient listings: CNIC column, linked and sortable. The search finds it.
- [ ] A patient's own Samples tab loads (no CNIC column, like the MRN).
- [ ] Existing listing columns and filters are unchanged. The Sample Type form
      still shows "Process Time". A results report publishes.
- [ ] No errors in the event log or in the browser console. Errors of the
      CNIC script start with `[senaite.starter.cnic]`.
- [ ] Automated tests: `bin/test -s senaite.starter`.

## Notes and limitations

- **CNICs are compared as entered**, like MRNs: `35202-1234567-1` and
  `3520212345671` are different CNICs, and a search must use the same form.
  Enter CNICs consistently.
- **Only the CNIC is updated from samples.** Name, address, date of birth,
  sex and gender follow senaite.patient: a new patient is created from the
  sample, but existing patients are not updated.
- **In the sample view, only a changed CNIC replaces the patient's.** If the
  MRN is changed but the CNIC is saved as it was on the sample, an existing
  patient with a different CNIC keeps theirs, and the samples listing shows
  the info icon. Picking an MRN normally fills in that patient's CNIC
  anyway.
- **Removing or replacing the MRN empties the patient fields** of the form,
  including the CNIC, as senaite.patient does in the add form and the sample
  view. Picking an existing patient fills them in again. For a new MRN, enter
  them again.
- **A CNIC belongs to one patient**, so children cannot be registered under a
  parent's CNIC. Leave their CNIC empty.
- **Saved field order**: if "Manage form fields" of the sample add form (or
  "Manage sample fields" of the sample view) was ever saved, new fields go
  last. Move the CNIC there.
- **Reinstalling or upgrading senaite.patient** can drop the CNIC behavior
  from the Patient type. The data is kept. Reinstall senaite.starter to enable
  it again.
- **MRN and CNIC are shown as entered** in the add form and sample header.
  Otherwise senaite.core shows new values in red as "broken reference". As a
  result, picking a patient in the MRN field shows the MRN, not the name.
- The `getCNIC`/`setCNIC` monkey patches have no docstrings. Otherwise Zope
  would publish them as URL-callable methods, bypassing the field permission.
- The CNIC is not on the results report templates.
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
  `#####-#######-#`, were removed. The CNIC is a separate identifier without a
  prescribed format.
