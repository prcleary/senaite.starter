# CNIC Field Implementation - New Approach Based on senaite.patient Analysis

## Critical Discovery
The previous approach was **fundamentally incomplete** - it only extended Patient (Dexterity) but ignored AnalysisRequest (Sample/Archetypes). senaite.patient shows that BOTH content types must be extended AND several supporting files are required.

## What senaite.patient Actually Does

### 1. **Patient Schema Extension (Dexterity)**
- Defines CNIC field in `content/patient.py` as part of IPatientSchema
- Field is part of the main Patient schema (not via behavior extension)
- Already working in our implementation ✓

### 2. **AnalysisRequest Schema Extension (Archetypes)** 
- Uses `archetypes.schemaextender` with TWO classes:
  - `AnalysisRequestSchemaExtender` - provides the field definitions
  - `AnalysisRequestSchemaModifier` - adjusts field properties after addition
- Implements `IOrderableSchemaExtender` and `ISchemaExtender` interfaces
- Registered as ZCML adapters with `archetypes.schemaextender`
- **Currently missing from our implementation** ✗

### 3. **Monkey Patches for AnalysisRequest Methods**
- Adds getter/setter methods to AnalysisRequest class: `getCNIC()`, `setCNIC()`
- Defined in `monkeys/content/analysisrequest.py`
- Registered in `monkeys/configure.zcml` using `monkey:patch` directive
- Allows code to call `sample.getCNIC()` instead of field access
- **Currently missing from our implementation** ✗

### 4. **Permissions**
- senaite.patient defines permissions for each field: `FieldEditMRN`, `FieldEditFullName`, etc.
- Each field specifies `read_permission` and `write_permission`
- Permissions file: `permissions.py` and `permissions.zcml`
- **Currently missing from our implementation** ✗

### 5. **Catalog Indexing**
- Fields are indexed in catalogs for search
- Setuphandler adds indexes to patient_catalog and sample_catalog
- Needed for CNIC to appear in listings
- **Currently missing from our implementation** ✗

### 6. **Workflow Permissions**
- Workflow definition specifies which fields are editable in each state
- Prevents editing of fields in certain workflow states
- File: `profiles/default/workflows/senaite_patient_workflow/definition.xml`
- **Currently missing from our implementation** ✗

## Why Our Current Approach Failed

1. ✗ AnalysisRequest field not being added (archetypes.schemaextender not available? import path wrong?)
2. ✗ No monkey-patched getter/setter methods on AnalysisRequest
3. ✗ No permissions defined for CNIC field
4. ✗ No catalog indexing configured
5. ✗ No workflow field permissions set

**Result**: Field added to Patient form only, never reaches Sample or listings.

## Proposed New Complete Approach

### Phase 1: Verify archetypes.schemaextender Availability

**Action**: Check if `archetypes.schemaextender` is available in SENAITE 2.6.0 environment
- Try importing it in Python shell
- If available: use it like senaite.patient does
- If NOT available: use direct schema modification before runtime

### Phase 2: Extend AnalysisRequest Schema (Archetypes Pattern)

**Files to create/modify:**

1. **src/senaite/starter/content/analysisrequest.py** (REWRITE)
   ```
   - Define CNIC field as AT StringField
   - Implement AnalysisRequestSchemaExtender class
     - Extend IOrderableSchemaExtender, ISchemaExtender
     - Return CNIC field in getFields()
   - Implement AnalysisRequestSchemaModifier class (if needed)
     - Implement ISchemaModifier
     - Adjust field properties in fiddle()
   ```

2. **src/senaite/starter/content/configure.zcml** (UPDATE)
   ```
   - Add: <include package="archetypes.schemaextender" />
   - Register AnalysisRequestSchemaExtender as adapter
   - Register AnalysisRequestSchemaModifier as adapter
   ```

### Phase 3: Add Monkey-Patched Methods

**Files to create:**

1. **src/senaite/starter/monkeys/__init__.py** (NEW)
   - Empty init file

2. **src/senaite/starter/monkeys/content/__init__.py** (NEW)
   - Empty init file

3. **src/senaite/starter/monkeys/content/analysisrequest.py** (NEW)
   ```
   - Define getCNIC(self) function
   - Define setCNIC(self, value) function
   - Use @check_installed decorator (or implement wrapper)
   - Follow senaite.patient pattern exactly
   ```

4. **src/senaite/starter/monkeys/configure.zcml** (NEW)
   ```
   - Register monkey patches for getCNIC and setCNIC
   - Use monkey:patch directive for each function
   - Point to AnalysisRequest class
   ```

5. **src/senaite/starter/configure.zcml** (UPDATE)
   ```
   - Add: <include package="senaite.starter.monkeys" />
   - Or register monkeys manually
   ```

### Phase 4: Define Permissions

**Files to create/modify:**

1. **src/senaite/starter/permissions.py** (NEW or UPDATE)
   ```
   - Define: FieldEditCNIC = "senaite.starter: Edit CNIC"
   - Define: FieldViewCNIC = "senaite.starter: View CNIC"
   ```

2. **src/senaite/starter/permissions.zcml** (NEW)
   ```
   - Register permissions:
     - senaite.starter:FieldEditCNIC
     - senaite.starter:FieldViewCNIC
   ```

3. **src/senaite/starter/content/analysisrequest.py** (UPDATE)
   ```
   - Add read_permission and write_permission to CNIC field
   ```

### Phase 5: Configure Catalog Indexing

**Files to modify:**

1. **src/senaite/starter/setuphandlers.py** (UPDATE - extend_analysisrequest_schema function)
   ```
   - Add CNIC index to patient_catalog
   - Add CNIC index to sample_catalog
   - Add CNIC as column in catalogs
   - Reindex affected objects
   ```

### Phase 6: Workflow Configuration

**Files to create:**

1. **profiles/default/workflows/senaite_patient_workflow/definition.xml** (UPDATE if exists, or CREATE)
   ```
   - Add CNIC field to workflow state permissions
   - Define which roles can edit CNIC in which states
   - Or verify existing workflow handles it
   ```

## Implementation Plan (Prioritized)

### Must Have (Phase 1-2):
1. Rewrite `analysisrequest.py` using archetypes.schemaextender properly
2. Register schema extenders in configure.zcml
3. Test: Does CNIC appear on Sample form?

### Should Have (Phase 3):
4. Add monkey-patched getCNIC/setCNIC methods
5. Register in monkeys/configure.zcml
6. Test: Can code call `sample.getCNIC()`?

### Nice to Have (Phase 4-6):
7. Define permissions (if not covered by field-level perms)
8. Add catalog indexing (for search/listing)
9. Update workflow configuration

## Testing Strategy

After each phase:
1. Rebuild and reinstall senaite.starter
2. Create a Patient with CNIC
3. Check if CNIC appears in:
   - [ ] Patient individual record (should already work)
   - [ ] Sample registration form
   - [ ] Sample view
   - [ ] Patient listing
   - [ ] Sample listing
4. Try searching by CNIC
5. Verify no errors in event log

## Critical Questions to Answer First

1. **Is `archetypes.schemaextender` available in Plone 5.2.15?**
   - YES → Use it like senaite.patient
   - NO → Use alternate pattern (direct schema modification or custom adapter)

2. **What is correct import path for AnalysisRequest schema?**
   - Current assumption: `bika.lims.content.analysisrequest.AnalysisRequest`
   - Verify by inspection in Python shell

3. **Are there any existing CNIC-related permissions or workflow steps?**
   - Check SENAITE 2.6.0 codebase

## Files That MUST Be Modified/Created

Based on senaite.patient pattern:

**MUST CREATE:**
- monkeys/__init__.py
- monkeys/content/__init__.py
- monkeys/content/analysisrequest.py
- monkeys/configure.zcml
- permissions.py (or update if exists)
- permissions.zcml (or update if exists)

**MUST MODIFY:**
- content/analysisrequest.py (complete rewrite)
- content/configure.zcml (add schema extenders + monkeys include)
- setuphandlers.py (add catalog indexing)

**MIGHT MODIFY:**
- profiles/default/workflows/... (if needed)
- profiles/default/rolemap.xml (if needed)

## Key Difference from Previous Approach

**Previous**: "Add behavior to Patient, hope it works for Sample"
**New**: "Extend BOTH Patient AND AnalysisRequest properly, with permissions, monkey patches, and catalog setup"

This is NOT an add-on feature - it's a **schema extension** that affects multiple content types and requires coordinated changes across multiple files.
