# CNIC Implementation - Next Actions Summary

## What We Learned
The previous approach was **incomplete and based on assumptions**. By analyzing senaite.patient's actual implementation, we discovered that extending SENAITE requires:

1. ✓ Patient schema extension (Dexterity behavior) - **ALREADY DONE**
2. ✗ AnalysisRequest schema extension (Archetypes) - **MISSING**
3. ✗ Monkey-patched accessor methods - **MISSING**
4. ✗ Permissions - **MISSING**
5. ✗ Catalog indexing - **MISSING**
6. ✗ Workflow field permissions - **PROBABLY MISSING**

## Immediate Next Steps (In Order)

### Step 1: Verify archetypes.schemaextender Availability
**Goal**: Can we use the same pattern as senaite.patient?

**Action**: 
- Try importing in SENAITE Python shell: `from archetypes.schemaextender.interfaces import ISchemaExtender`
- If ImportError: use different approach
- If Success: proceed with Step 2

**Expected Time**: 2 minutes

---

### Step 2: Rewrite AnalysisRequest Extension
**Goal**: Add CNIC field to Sample form properly

**Files**:
- `src/senaite/starter/content/analysisrequest.py` - **REWRITE COMPLETELY**
- `src/senaite/starter/content/configure.zcml` - **UPDATE** (add schema extender registration)

**Pattern to Follow**: 
Exactly mirror `senaite/senaite.patient/src/senaite/patient/content/analysisrequest.py` lines 51-158

**What to Do**:
1. Define CNIC field as AT StringField (copy patient field definition format)
2. Create `AnalysisRequestSchemaExtender` class implementing `IOrderableSchemaExtender`
3. Return CNIC field in `getFields()` method
4. Optionally create `AnalysisRequestSchemaModifier` for field adjustment
5. Register both as adapters in ZCML

**Expected Time**: 30 minutes

**Success Criteria**:
- CNIC field appears on Sample registration form
- Field is editable
- No errors in event log

---

### Step 3: Add Monkey-Patched Methods
**Goal**: Enable `sample.getCNIC()` and `sample.setCNIC()` calls

**Files to Create**:
- `src/senaite/starter/monkeys/__init__.py` (empty)
- `src/senaite/starter/monkeys/content/__init__.py` (empty)
- `src/senaite/starter/monkeys/content/analysisrequest.py` (NEW)
- `src/senaite/starter/monkeys/configure.zcml` (NEW)

**Files to Update**:
- `src/senaite/starter/configure.zcml` (include monkeys)

**Pattern to Follow**:
Exactly mirror `senaite/senaite.patient/src/senaite/patient/monkeys/content/analysisrequest.py` and `configure.zcml`

**What to Do**:
1. Create `getCNIC(self)` function - return field value
2. Create `setCNIC(self, value)` function - set field value
3. Register via monkey:patch directives in ZCML

**Expected Time**: 20 minutes

**Success Criteria**:
- Python code can call `sample.getCNIC()`
- Returns correct value
- No errors in event log

---

### Step 4: Define Permissions
**Goal**: Control who can view/edit CNIC

**Files**:
- `src/senaite/starter/permissions.py` (NEW or UPDATE)
- `src/senaite/starter/permissions.zcml` (NEW or UPDATE)
- Update `content/analysisrequest.py` field definition

**Pattern**:
```python
# permissions.py
FieldEditCNIC = "senaite.starter: Edit CNIC"

# analysisrequest.py
cnic_field = StringField(...,
    read_permission=View,
    write_permission=FieldEditCNIC,
)
```

**Expected Time**: 15 minutes

---

### Step 5: Add Catalog Indexing
**Goal**: Make CNIC searchable in listings

**File**: `src/senaite/starter/setuphandlers.py`

**What to Do**:
1. Add CNIC as keyword index in patient_catalog
2. Add CNIC as keyword index in sample_catalog
3. Add CNIC as column in catalogs
4. Reindex affected objects

**Pattern**: Follow senaite.patient setuphandlers INDEXES and COLUMNS definitions

**Expected Time**: 20 minutes

---

### Step 6: Verify Workflow Permissions (If Needed)
**Goal**: Ensure CNIC can be edited in correct workflow states

**File**: `profiles/default/workflows/senaite_patient_workflow/definition.xml`

**What to Check**:
- Does SENAITE 2.6.0 have a standard patient workflow?
- Does it define field permissions per state?
- Do we need to add CNIC permissions?

**Expected Time**: 10 minutes (or skip if not needed)

---

## Total Expected Time
**Without workflow step**: ~1.5-2 hours
**With workflow step**: ~2.5-3 hours

## Testing Between Steps
- After Step 2: CNIC should appear on Sample form
- After Step 3: Programmatic access should work
- After Step 4: Permissions should be enforced
- After Step 5: Search and listings should work
- After Step 6: Workflow transitions should respect permissions

## Documentation to Update
- PROGRESS_SESSION_2026_11_17.md (add to "What Works")
- Create IMPLEMENTATION_CHECKLIST.md (track completion)
- Update CHANGES.md with actual implementation details

## Branch Status
- Branch: `add-cnic-field`
- Ready to continue development
- All analysis documented for reference
