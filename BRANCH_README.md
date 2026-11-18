# Branch `add-cnic-field`: CNIC for patients and samples

Adds a **CNIC** (Computerized National Identity Card number) field to SENAITE
2.6.0 / senaite.patient 1.5.0 as a pure add-on (no fork of senaite.patient).

This file is the single source of documentation for the branch.

## Status

Implemented, byte-compiled and pyflakes-checked with Python 2.7.18, and every
dotted name/import cross-checked against the pinned sources (senaite.core
2.6.0, senaite.patient 1.5.0, senaite.app.listing 2.6.0,
archetypes.schemaextender 3.0.2, collective.monkeypatcher 1.2.1).
**Not yet run on a SENAITE instance**: see [Install](#install) and
[Testing checklist](#testing-checklist).

## Design: do what senaite.patient does for its own fields

senaite.patient does **not** show Patient fields on samples. It stores its
patient fields (MRN, name, place of residence, date of birth, sex, gender)
**on the sample** (AT schema extender), and **creates the Patient** from those
values when a sample with a new MRN is registered. Each sample keeps the values
recorded at registration; existing patients are never updated from samples.

CNIC follows the same model:

- Sample field `CNIC` (AT extension field) placed after "Medical Record #".
- Patient field `cnic` (Dexterity behavior). Values entered on patients in
  earlier attempts on this branch are kept, since the behavior is the same.

The list of files to replicate came from grepping senaite.patient 1.5.0 for
every file that touches its closest equivalent field, `PatientAddress` (a plain
text field stored on both sample and patient). That gives your original list
plus the MRN auto-fill JavaScript.

| senaite.patient 1.5.0 file | What it does for its patient fields | Equivalent here |
|---|---|---|
| `content/analysisrequest.py`, `content/__init__.py` | AT schema extender with the sample fields; `ExtStringField` | [content/analysisrequest.py](src/senaite/starter/content/analysisrequest.py), [content/\_\_init\_\_.py](src/senaite/starter/content/__init__.py), [content/configure.zcml](src/senaite/starter/content/configure.zcml) |
| `content/patient.py` | Patient schema field + `getX`/`setX` accessors | Behavior [content/patient.py](src/senaite/starter/content/patient.py) + `Patient.getCNIC`/`setCNIC` in [monkeys/](src/senaite/starter/monkeys/) |
| `monkeys/configure.zcml`, `monkeys/content/analysisrequest.py` | `getX`/`setX` on `AnalysisRequest` (needed for catalog metadata columns) | [monkeys/configure.zcml](src/senaite/starter/monkeys/configure.zcml), [monkeys/content/](src/senaite/starter/monkeys/content/) |
| `permissions.py`, `permissions.zcml` | One "Field: Edit ..." permission per field | `senaite.starter: Field: Edit CNIC` in [permissions/](src/senaite/starter/permissions/) |
| `profiles/default/rolemap.xml` | Default roles: Owner, LabClerk, LabManager, Manager | [profiles/default/rolemap.xml](src/senaite/starter/profiles/default/rolemap.xml) |
| `setuphandlers.py` (`WORKFLOW_TO_UPDATE`, `INDEXES`, `COLUMNS`) | Field permissions read-only in verified/published/dispatched/rejected/invalid/cancelled samples; sample catalog indexes/columns | [setuphandlers.py](src/senaite/starter/setuphandlers.py) (same states; `getCNIC` column) |
| `profiles/default/workflows/senaite_patient_workflow/definition.xml` | Field permissions: acquired when active, none when inactive | [setuphandlers.py](src/senaite/starter/setuphandlers.py) updates that workflow (overriding the XML would replace senaite.patient's workflow) |
| `catalog/patient_catalog.py`, `catalog/indexer/patient.py` | Patient indexes, `patient_searchable_text` (patients search box), `patient_searchable_mrn` (MRN lookup in the sample add form) | `patient_cnic` index; both text indexers extended in [catalog/indexer/patient.py](src/senaite/starter/catalog/indexer/patient.py) |
| `catalog/indexer/sample.py` | `IListingSearchableTextProvider` adds patient values to the samples search | Named provider in [catalog/indexer/sample.py](src/senaite/starter/catalog/indexer/sample.py) |
| `adapters/listing.py` | MRN/Patient columns in sample listings (samples folder, client, batch) | CNIC column in [listing/cnic.py](src/senaite/starter/listing/cnic.py) |
| `browser/patientfolder.py` | Columns of the patients listing | CNIC column (global and client patients) in [listing/cnic.py](src/senaite/starter/listing/cnic.py) |
| `subscribers/analysisrequest.py`, `api.py` (`update_patient`) | Patient created from the sample values | [subscribers/analysisrequest.py](src/senaite/starter/subscribers/analysisrequest.py) copies the CNIC to that patient; helpers in [api.py](src/senaite/starter/api.py) |
| `browser/patient/add2.py` | "Add sample" from inside a patient pre-fills the patient fields | `CNIC_default_value_hook` (senaite.core's hook for add-on fields) in [adapters/addsample.py](src/senaite/starter/adapters/addsample.py) |
| `webpack/.../temporaryidentifierwidget.coffee` (bundled JS) | Selecting an existing MRN fills the patient fields; deselecting clears them | [browser/static/js/senaite.starter.cnic.js](src/senaite/starter/browser/static/js/senaite.starter.cnic.js), loaded by a head viewlet |

Nothing here is assumed to happen "automatically". Each item above was checked
against the senaite.core / senaite.app.listing source it relies on.

## Behaviour

- **Sample add form**: CNIC input after "Medical Record #". Selecting an
  existing patient's MRN fills it with that patient's CNIC. Clearing the MRN
  clears it.
- **Add sample from a patient**: CNIC pre-filled from the patient.
- **New patient from a sample**: the patient senaite.patient creates gets the
  sample's CNIC.
- **Existing patient without CNIC**: filled from the next sample registered or
  edited with a CNIC, if the user may modify the patient. An existing patient
  CNIC is **never overwritten** from a sample, as senaite.patient does for its
  own fields. Change it on the patient record instead.
- **Sample view**: CNIC in the header table. It is editable with the "Edit
  CNIC" permission and read-only once the sample is verified (or published,
  dispatched, rejected, invalid or cancelled).
- **Listings**: CNIC column in the samples listings (samples, client, batch)
  and the patients listings (global and client). It is not shown in a
  patient's own samples listing, like MRN.
- **Search**: the CNIC is searchable from the samples and patients search
  boxes, and from the "Medical Record #" lookup in the sample add form. It
  matches with or without dashes (both forms are indexed).
- **API / reports**: `sample.getCNIC()` and `patient.getCNIC()`. In
  senaite.impress templates, use `model.CNIC` or `model.getCNIC()`.

## Install

1. `git pull` on branch `add-cnic-field`.
2. Re-run buildout. `setup.py` now declares `senaite.patient`,
   `archetypes.schemaextender` and `collective.monkeypatcher`. All three are
   already in the working set and pinned.
3. Restart the instance.
4. Reinstall senaite.starter. In Site Setup → Add-ons, uninstall then install.
   Alternatively, in the ZMI use `portal_setup` → Import → "SENAITE.STARTER" →
   "Import all steps". The profile now depends on `senaite.patient:default`.

The installer is idempotent and:

- enables the CNIC behavior on the Patient type
- adds the `patient_cnic` index (patient catalog) and the `getCNIC` metadata
  column (sample catalog)
- reindexes patients that already have a CNIC
- sets the CNIC permission in the sample and patient workflows
- applies that permission to existing samples in the read-only states and to
  inactive patients

The last step loads every such sample once, so it can take a while on a large
production database.

Quick ZMI checks afterwards:

- `portal_types/Patient` → behaviors include
  `senaite.starter.content.patient.ICNICField`.
- `senaite_catalog_patient` → Indexes has `patient_cnic`.
- `senaite_catalog_sample` → Metadata has `getCNIC`.
- `portal_workflow/senaite_sample_workflow/states/verified` → Permissions:
  "senaite.starter: Field: Edit CNIC" has no roles and is not acquired.

## Testing checklist

- [ ] Instance starts and the install reports no errors in the event log.
- [ ] Sample add form shows CNIC after "Medical Record #".
- [ ] Register a sample with a **new** MRN and a CNIC. The created patient has
      that CNIC.
- [ ] New sample, **select** that MRN: the CNIC is filled in. Clear the MRN:
      the CNIC is cleared.
- [ ] Patient → Samples → Add: the CNIC is pre-filled.
- [ ] Samples listing: CNIC column. Searching the CNIC with and without
      dashes finds the sample.
- [ ] Patients listing: CNIC column, sortable. Searching the CNIC finds the
      patient.
- [ ] Sample add form: typing a CNIC in "Medical Record #" finds the patient.
- [ ] Verify a sample: CNIC is no longer editable in its header table.
- [ ] Log in as a client contact: registering a sample with a CNIC works.
- [ ] Automated tests: `bin/test -s senaite.starter`. They include new checks
      for the behavior, catalogs and workflow permissions.

## Notes and limitations

- **Field order in the add form**: if "Manage form fields" in the Sample Add
  form was ever saved, fields missing from that saved order (CNIC) go last.
  Move CNIC there.
- **Reinstalling or upgrading senaite.patient** can re-import the Patient type
  and drop the CNIC behavior. The data is kept. Reinstall senaite.starter to
  enable it again.
- **Not included**: CNIC uniqueness or format validation, a CNIC column in the
  MRN lookup dropdown, and CNIC on the result report templates (use
  `model.CNIC`).
- The `getCNIC`/`setCNIC` monkey patches are registered without docstrings, so
  Zope does not publish them as URL-callable methods. Otherwise
  `setCNIC` could be called by URL, bypassing the field permission.
- The template's unregistered `content/sample.py` example
  (`ProductionBatchNumber`) is intentionally left unregistered.

## Why the earlier attempts on this branch did not work

- Adding only a Dexterity behavior to Patient: Patient fields are never shown
  on samples. senaite.patient copies values in the other direction, from
  sample to patient.
- Modifying the AnalysisRequest schema in the install handler: this changes
  the class schema in memory only, in that one process, and is lost on
  restart.
- "Register `SampleSchemaExtender`" (previous README): would fail at startup,
  because `ExtStringField` did not exist in `content/__init__.py`. It would
  also add the template's `ProductionBatchNumber` field to every sample.
- "Catalogs index new fields automatically": they do not. The samples search
  uses fixed fields plus provider adapters, the patients search uses
  `patient_searchable_text`, and listings read catalog metadata columns.
- The `IOError ... schemaextender/meta.zcml`: archetypes.schemaextender has
  no `meta.zcml`. Its `configure.zcml` is included instead.
