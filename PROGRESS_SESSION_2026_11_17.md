# CNIC Field Implementation - Session Progress 2026-11-17

## Status Summary
**Current**: CNIC field partially working - appears in Patient individual record only, NOT in Sample registration form (where it's needed)

**Branch**: `add-cnic-field` - ready for continued development

## What Works ✅
- CNIC field successfully added to Patient content type (Dexterity behavior)
- Field appears in Patient individual record (view/edit form)
- Field is optional (required=False)
- Behavior registration in ZCML working correctly
- Setuphandler correctly attaching behavior to Patient FTI

## What Doesn't Work ❌
1. CNIC not appearing in Patient listing/search
2. CNIC not appearing in AnalysisRequest/Sample registration form
3. CNIC not appearing in AnalysisRequest/Sample listing
4. AnalysisRequest schema extension not working (unclear why)

## Implementation Details

### Files Created/Modified:
1. **src/senaite/starter/content/patient.py**
   - Dexterity behavior with IFormFieldProvider interface
   - Defines ICNICField schema with CNIC field
   - Works correctly for Patient type

2. **src/senaite/starter/content/analysisrequest.py**
   - Helper function `get_cnic_field()` to create CNIC field
   - Intended for AnalysisRequest schema extension
   - Currently not working (import or schema modification issue)

3. **src/senaite/starter/content/configure.zcml**
   - Registers Patient CNIC behavior with plone:behavior directive
   - Specifies `for="senaite.patient.interfaces.IPatient"`
   - SampleType behavior also defined here

4. **src/senaite/starter/setuphandlers.py**
   - `setup_behaviors()` - attaches behaviors to content type FTI
   - `extend_analysisrequest_schema()` - attempts to add CNIC to AnalysisRequest schema
   - Includes detailed logging to diagnose issues

5. **setup.py**
   - No external dependencies needed (plone.behavior already included)

## Approaches Tried

### 1. Dexterity Behavior Registration ✓ (PARTIAL SUCCESS)
- **Status**: Works for Patient form, not for Sample
- **Issue**: Behavior applied to Patient FTI, but not propagating to Sample form
- **Why**: Patient and Sample are different types (Dexterity vs Archetypes)

### 2. plone.schemaextender (FAILED)
- **Error**: Not available in Plone 5.2.15
- **Abandoned**: Dependency not in buildout index

### 3. Direct Schema Modification at Installation (CURRENT ATTEMPT)
- **Status**: Code runs without errors, but field not appearing
- **Issue**: Unclear - either schema modification not persisting or field not rendering
- **Needs**: Investigate if `bika.lims.content.analysisrequest.schema` is the correct import path

## Key Findings

### Architecture Understanding:
- **Patient**: Dexterity-based content type
  - Extended via `plone.behavior` with IFormFieldProvider interface
  - Behaviors are registered in ZCML and attached to FTI at installation
  - Works well for adding fields

- **AnalysisRequest (Sample)**: Archetypes-based content type
  - Extended via AT schema extenders (older pattern)
  - senaite.patient uses AT schema extenders to add fields like MRN, name, address
  - Standard Dexterity behavior registration doesn't apply

### Why CNIC Only Shows in Patient Record:
- Patient form: ✓ Renders all fields from DX behavior
- Sample registration: ✗ Doesn't know about Patient's CNIC field
- Sample listing: ✗ Not indexed or displayed

### Why AnalysisRequest Extension Isn't Working:
Possible reasons (not yet confirmed):
1. Import path incorrect - `bika.lims.content.analysisrequest` may not be the right module
2. Schema object may not support direct field addition at runtime
3. Field needs to be added before schema is used by form builder
4. SENAITE 2.6.0 may use a different mechanism than expected

## Recommended Next Steps (Priority Order)

### Immediate (Phase 1):
1. **Verify AnalysisRequest schema import path**
   - Check actual location in senaite.core or bika.lims
   - Look for existing AT schema extenders in senaite.patient code
   - Use Python shell to inspect AnalysisRequest class

2. **Look at how senaite.patient extends AnalysisRequest**
   - Review senaite.patient setuphandlers.py for AnalysisRequest modifications
   - Check if they use AT schema extenders or monkey-patching
   - Copy their pattern for consistency

3. **Consider monkey-patching approach**
   - If schema is locked, may need to add field via monkey-patch at module load time
   - Create a module that modifies AnalysisRequest schema before it's used

### Medium Term (Phase 2):
4. **Add CNIC to Patient listing columns**
   - Even if not in Sample yet, make it searchable in Patient list
   - Add to catalog indexing for search functionality

5. **Link Sample CNIC to Patient CNIC**
   - Create a view adapter that displays linked Patient's CNIC on Sample
   - Or use a computed field that reads from linked Patient

### Long Term (Phase 3):
6. **Validation & Uniqueness**
   - Add validation for CNIC format (if needed)
   - Implement uniqueness checking per Patient
   - Auto-link when existing CNIC entered

## Testing Checklist for Next Session

When resuming work:
- [ ] Check server logs for AnalysisRequest schema extension messages
- [ ] Verify CNIC field in Patient form (should still be there)
- [ ] Check if "Extending AnalysisRequest Schema" message appears in logs
- [ ] Try entering CNIC on Sample registration form
- [ ] Try searching for CNIC in Patient listing

## Git Commits Made This Session

```
f457c4f - Add detailed logging to debug AnalysisRequest schema extension
d44b996 - Add CNIC to AnalysisRequest via direct schema modification
39e3534 - Add CNIC field to AnalysisRequest via AT schema extender
c62fdf8 - Back to behavior registration with simplified setuphandler
17860a4 - Direct schema modification approach for CNIC field
f7205be - Fix Python 2 compatibility - replace f-strings with .format()
0edede5 - Use IFormFieldProvider behavior for CNIC field
1cbab5a - Add plone.schemaextender dependency
3131cce - Switch to plone.schemaextender for Patient CNIC field
4fc7337 - Add debug logging to setuphandler
f42ebd8 - Add quick reference and branch readme for CNIC implementation
c7ca1cd - Add implementation and testing documentation for CNIC field
6dd343e - Add CNIC field to Patient content type
```

## Branch Status
- **Current branch**: `add-cnic-field`
- **Base**: `master` (commit 64d4935)
- **Status**: Ready for continued work
- **No conflicting changes**: Safe to continue development

## Code Quality Notes
- Python 2.7.18 compatibility maintained (no f-strings, using .format())
- Logging statements for debugging
- Comments for clarity
- Follow existing senaite.starter patterns

## Conclusion
Good progress on Patient CNIC field, but AnalysisRequest/Sample extension needs investigation. The issue is likely an import path or schema modification timing problem rather than a conceptual one. Next session should focus on understanding how senaite.patient itself extends AnalysisRequest schema.
