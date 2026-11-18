# CNIC Field Implementation - Analysis Summary

## Executive Summary

**Status**: Root cause identified, complete implementation approach documented and ready to execute

**Problem**: CNIC field was added to Patient (Dexterity) but doesn't appear on Sample registration form or listings, defeating the primary use case.

**Root Cause**: The senaite.starter template has a base template bug - `SampleSchemaExtender` exists in `sample.py` but is **NOT registered in ZCML**. This prevents the existing ProductionBatchNumber field (and any new fields like CNIC) from appearing on AnalysisRequest/Sample forms.

**Solution**: Two-step fix:
1. Register `SampleSchemaExtender` in `configure.zcml` (fixes base template bug that affects all AT-based content extensions)
2. Add CNIC field to `SampleSchemaExtender.fields` list in `sample.py` (extends AnalysisRequest with CNIC)

---

## Why Previous Attempts Failed

### Attempt 1: Pure Add-On with Patient Behavior Only
- Added Dexterity behavior to Patient ✓
- Assumed CNIC would automatically appear on Sample forms ✗
- **Why it failed**: AnalysisRequest is Archetypes-based, not Dexterity - requires separate schema extender

### Attempt 2: Try to Extend AnalysisRequest via New File
- Created `analysisrequest.py` with schema extender class ✗
- Added ZCML adapter registration (attempted) ✓  
- **Why it failed**: Didn't realize existing `sample.py` already has correct extender class - should have reused it

### Attempt 3: Direct Schema Modification in Setuphandler
- Tried to modify AnalysisRequest schema at runtime ✗
- Had syntax errors and import issues ✗
- **Why it failed**: Tried to reinvent the wheel instead of using Plone's standard pattern (already proven to work in senaite.starter)

---

## Critical Discovery

The senaite.starter template itself has an **unfinished implementation**:

**File**: `src/senaite/starter/content/sample.py`
- Contains: `SampleSchemaExtender` class (fully implemented)
- Status: NOT registered in ZCML - **completely invisible to Plone**
- Result: ProductionBatchNumber field also doesn't appear on samples

**Evidence**:
```bash
# sample.py exists and has the class:
$ ls -la src/senaite/starter/content/sample.py
$ grep -n "class SampleSchemaExtender" src/senaite/starter/content/sample.py
# Line 15: class SampleSchemaExtender(object):

# But configure.zcml has NO adapter registration for it:
$ grep -i "SampleSchemaExtender\|adapter.*sample" src/senaite/starter/content/configure.zcml
# (no results)

# Master branch has same issue:
$ git show master:src/senaite/starter/content/configure.zcml | grep -i adapter
# (no adapter registrations for AT-based extenders)
```

---

## The Correct Architecture (as Proven in senaite.starter)

### Pattern 1: Dexterity Content Types (Patient, SampleType)

**Technology**: Plone Dexterity behaviors

**How it works**:
1. Define schema fields as interface with `@provider(IFormFieldProvider)` decorator
2. Register with `<plone:behavior>` directive in ZCML
3. Add behavior to FTI via setuphandler (for SampleType) or programmatically (for Patient)
4. Plone handles everything: forms, storage, indexing, rendering

**Files involved**:
- `src/senaite/starter/content/sampletype.py` - Schema definition
- `src/senaite/starter/content/configure.zcml` - Behavior registration
- `src/senaite/starter/setuphandlers.py` - FTI behavior setup

### Pattern 2: Archetypes Content Types (AnalysisRequest/Sample)

**Technology**: Archetypes schema extender (`archetypes.schemaextender` package)

**How it works**:
1. Create class implementing `ISchemaExtender` and related interfaces
2. Add field instances to `fields` list
3. Register with `<adapter>` directive in ZCML
4. Archetypes handles everything: forms, storage, indexing, rendering

**Files involved**:
- `src/senaite/starter/content/sample.py` - Schema extender class (EXISTS but unused!)
- `src/senaite/starter/content/configure.zcml` - Adapter registration (MISSING for sample.py)

---

## Implementation Strategy

### Phase 1: Fix Base Template Bug (5 minutes)

**File**: `src/senaite/starter/content/configure.zcml`

**Current**:
```xml
<?xml version="1.0" encoding="utf-8"?>
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:plone="http://namespaces.plone.org/plone"
    xmlns:browser="http://namespaces.zope.org/browser"
    i18n_domain="senaite.starter">

  <include package="plone.behavior" file="meta.zcml"/>

  <!-- Patient CNIC Field Behavior -->
  <plone:behavior
      for="senaite.patient.interfaces.IPatient"
      provides=".patient.ICNICField"
      title="CNIC Field"
      description="Add CNIC field to Patient"
      />

  <!-- Sample Type Schema Extender (DX) -->
  <plone:behavior
      for="senaite.core.interfaces.ISampleType"
      name="sampletype-extender"
      title="Custom Sample Type Fields"
      description="Add custom fields to the Sample Type Schema"
      provides=".sampletype.ISampleTypeSchemaExtender"
      factory=".sampletype.SampleTypeSchemaExtender"
      />

</configure>
```

**Add this adapter registration** (between first include and behaviors):
```xml
  <!-- Sample Schema Extender (Archetypes) - FIX FOR MISSING REGISTRATION -->
  <adapter
      factory=".sample.SampleSchemaExtender"
      provides="archetypes.schemaextender.interfaces.ISchemaExtender"/>
```

**Result**: ProductionBatchNumber field will now appear on Sample forms (even though it already has the code)

### Phase 2: Add CNIC Field to SampleSchemaExtender (10 minutes)

**File**: `src/senaite/starter/content/sample.py`

**Current** (fields list):
```python
fields = [
    ExtStringField(
        "ProductionBatchNumber",
        mode="rw",
        read_permission=View,
        write_permission=EditExtendedField,
        widget=StringWidget(
            label=_("Production batch number"),
            visible={
                "add": "edit",
            },
            description=_("The production batch number of this sample"),
            render_own_label=True,
            i18n_domain="senaite.starter",
        )),
]
```

**Add to fields list**:
```python
        ExtStringField(
            "cnic",
            mode="rw",
            read_permission=View,
            write_permission=EditExtendedField,
            widget=StringWidget(
                label=_("label_cnic", default=u"CNIC"),
                visible={
                    "add": "edit",
                    "view": "visible",
                },
                description=_("description_cnic", default=u"Computerized National Identity Card"),
                render_own_label=True,
                i18n_domain="senaite.starter",
            )),
```

**Result**: CNIC field will appear on Sample registration forms and listings

---

## Why This Solution Is Sound

✅ **Reuses existing code**: `SampleSchemaExtender` already exists and is proven to work (ProductionBatchNumber just needs to be enabled)

✅ **Fixes base template bug**: Makes ProductionBatchNumber work too (bonus fix)

✅ **Minimal changes**: 2 files, ~15 lines of code total

✅ **Follows SENAITE patterns**: Identical to how existing fields are extended

✅ **No new dependencies**: Both files and patterns already exist in senaite.starter

✅ **Leverages proven architecture**: Both Dexterity (Patient) and Archetypes (AnalysisRequest) patterns work correctly

✅ **No forking needed**: Works with vanilla senaite.patient v1.5.0

---

## Expected Behavior After Implementation

### CNIC Appears On:
- ✅ Patient add/edit form (Dexterity behavior)
- ✅ Patient list views (auto-indexed)
- ✅ Sample registration form (Archetypes extender)
- ✅ Sample list views (auto-indexed)
- ✅ Both patient_catalog and sample_catalog (searchable)
- ✅ senaite.jsonapi JSON exports
- ✅ SENAITE LIMS API responses

### CNIC Workflow:
1. User creates sample and enters MedicalRecordNumber
2. User enters CNIC value on same form
3. CNIC stored on AnalysisRequest
4. When viewing patient who owns that sample, CNIC visible
5. Can search by CNIC in both Patient and Sample listings

---

## Files Changed

### New Files
- None

### Modified Files
1. `src/senaite/starter/content/configure.zcml` - Add adapter registration (1 block, ~3 lines)
2. `src/senaite/starter/content/sample.py` - Add CNIC field to fields list (~12 lines)

### No Changes Needed
- `src/senaite/starter/content/patient.py` - Patient behavior already correct
- `src/senaite/starter/setuphandlers.py` - Already handles Patient behaviors
- `docs/CHANGES.md` - Can be updated after verification

---

## Testing Plan

### Pre-Implementation
1. Pull and verify current state
2. Confirm ProductionBatchNumber does NOT appear on Sample forms (proves registration bug)
3. Confirm CNIC appears on Patient form (proves Patient behavior works)

### Post-Implementation  
1. Buildout without errors
2. Instance starts without errors
3. Event log shows no ZCML errors
4. Create Patient with CNIC
5. Register Sample with same Patient
6. **Verify CNIC appears on Sample registration form** (key test!)
7. **Verify CNIC appears in Sample listing** (key test!)
8. Verify CNIC searchable in both catalogs
9. Verify CNIC in JSON export

### If Tests Fail
- Check event log for ZCML parsing errors
- Verify adapter registration syntax
- Verify field names match (cnic vs CNIC vs cnic)
- Restart instance to reload changes

---

## Commit Strategy

1. Apply changes to configure.zcml and sample.py
2. Commit with message:
   ```
   Fix: Register SampleSchemaExtender and add CNIC field to AnalysisRequest
   
   - Add adapter registration for SampleSchemaExtender in configure.zcml
     (fixes base template bug - ProductionBatchNumber also now works)
   - Add CNIC field to SampleSchemaExtender in sample.py
   - CNIC now appears in both Patient and Sample forms, listings, and search
   
   Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
   ```

---

## Success Criteria

✅ CNIC field appears and is editable on Sample registration form  
✅ CNIC field appears in Sample list views  
✅ CNIC is searchable by catalog queries  
✅ No errors in event log  
✅ Both Patient and Sample CNIC values persist and sync  
✅ senaite.jsonapi includes CNIC in Sample JSON export

---

## Next Steps

1. Review this analysis and approach
2. Apply the two code changes (configure.zcml + sample.py)
3. Run buildout to test for errors
4. Start instance and test manually
5. If successful, commit changes
6. If issues arise, check event log and debugging guide in README_CNIC_IMPLEMENTATION.md

---

## References

**Key Files**:
- `README_CNIC_IMPLEMENTATION.md` - Detailed implementation guide with troubleshooting
- `src/senaite/starter/content/sample.py` - Existing SampleSchemaExtender class
- `src/senaite/starter/content/configure.zcml` - Where to add adapter registration
- `src/senaite/starter/content/README.md` - senaite.starter extension patterns documentation

**External References**:
- Archetypes schemaextender: https://github.com/plone/archetypes.schemaextender
- senaite.patient v1.5.0: Demonstrates both Dexterity and Archetypes patterns
- Plone Dexterity behaviors: https://docs.plone.org/5/en/adapt-and-extend/extending-plone.html
