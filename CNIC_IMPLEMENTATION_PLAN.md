# CNIC Field Implementation Plan - Single Field on Patient

## Overview
Add **CNIC (Computerized National Identity Card)** field to Patient only, but make it:
- **Editable on Sample form** (sample-centric data entry)
- **Visible in sample listings** (searchable/indexed)
- **Never duplicated** (single source of truth on Patient)

This supports the workflow where patients are only entered/updated through sample registration forms.

---

## Architecture: Single Field on Patient

### Data Model
```
Patient Record:
├── MRN (Medical Record Number)
├── Name (firstname, middlename, lastname)
├── Birthdate
├── Sex
├── Gender
├── CNIC ← NEW: Single field, stored only here
└── Other demographics

Sample/AnalysisRequest:
├── MedicalRecordNumber ← Links to Patient
├── PatientFullName ← Displays Patient name
├── PatientAddress ← Displays Patient address
├── DateOfBirth ← Displays Patient DOB
├── Sex ← Displays Patient sex
├── Gender ← Displays Patient gender
├── CNIC ← NEW: Displays/edits Patient.CNIC
│        (Not stored on Sample, proxy to Patient)
└── Sample-specific fields

Workflow:
1. User creates sample, enters/selects MedicalRecordNumber
2. Sample form loads Patient record via MRN link
3. Sample form displays all Patient demographics (including CNIC)
4. User can edit CNIC on sample form
5. Save sample → updates Patient.CNIC
6. CNIC stored only on Patient, never duplicated on Sample
7. Sample listings show CNIC from linked Patient
```

### Why This Architecture
✅ **Single source of truth** - CNIC stored only on Patient  
✅ **Consistent across system** - same CNIC visible in patient lookups and sample listings  
✅ **Audit trail** - Patient.CNIC history preserved  
✅ **Sample-centric workflow** - patients only edited through sample forms  
✅ **Less data duplication** - no sync/conflict issues  
✅ **Cleaner code** - no need for custom subscribers/syncing logic  

---

## Validation Requirements: CNIC Uniqueness

This is critical for implementation. Please clarify:

### **Question 1: CNIC Requirement**
Is CNIC **required** (every patient must have one) or **optional** (can skip)?

### **Question 2: Duplicate CNIC Handling**
When user enters a CNIC during sample registration that already exists on a different patient, what should happen?

**Option A: Reject**
```
User enters CNIC "42101-123456-7" (already exists on Patient P-999)
→ Validation error: "CNIC already exists for another patient"
→ User must fix or delete existing patient first
→ Prevents accidental duplicates
```

**Option B: Warn + Allow**
```
User enters CNIC "42101-123456-7" (already exists on Patient P-999)
→ Warning message: "This CNIC exists elsewhere"
→ User can proceed anyway
→ Assumes data entry error or same person with alternate ID
```

**Option C: Auto-Link**
```
User enters CNIC "42101-123456-7" (already exists on Patient P-999)
→ System finds existing Patient P-999
→ Automatically uses that Patient instead
→ Assumes re-entry of same patient ID
```

Which is correct for your workflow?

### **1. Patient CNIC Field (Dexterity Behavior with Uniqueness Validation)**
**File**: `src/senaite/starter/content/patient.py` (NEW)

Create CNIC as TextLine field on Patient via Dexterity behavior with:
- Uniqueness validation (no duplicate CNICs across patients)
- Support for patient creation during sample registration
- Invariant validator checking uniqueness at Patient save time

```python
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import Invalid, invariant
from senaite.starter import messageFactory as _
from senaite.patient.api import is_patient_required

@provider(IFormFieldProvider)
class IPatientSchemaExtender(model.Schema):
    """Extended schema fields for Patient"""
    cnic = schema.TextLine(
        title=_(u"CNIC"),
        description=_(u"Computerized National Identity Card number"),
        required=False  # Optional during patient creation
    )
    
    @invariant
    def validate_cnic_unique(data):
        """Validate CNIC uniqueness across patients"""
        # Context will be patient being edited/created
        # Check if CNIC already exists on different patient
        # Raise Invalid() if duplicate found
        # Allow empty/null values
        # Allow re-saving same value (e.g., edit without changing CNIC)
```

✅ CNIC stored on Patient  
✅ CNIC unique across all patients (validation enforced)  
✅ Patient edit form shows CNIC  
✅ Patient listings show CNIC  
✅ CNIC searchable in patient catalog  
✅ Works with patient creation during sample registration  

**Key Points:**
- Uniqueness validated at Patient save time (not Sample time)
- Sample creation can create new Patient with CNIC
- If CNIC already exists: **[SEE BELOW - NEEDS CLARIFICATION]**

### **2. Register Patient Behavior (ZCML)**
**File**: `src/senaite/starter/content/configure.zcml` (MODIFY)

Register the behavior:
```xml
<plone:behavior
    for="senaite.patient.interfaces.IPatient"
    name="patient-cnic-extender"
    title="Custom Patient Fields"
    provides=".patient.IPatientSchemaExtender"
    factory=".patient.PatientSchemaExtender"
    />
```

### **3. Register with Patient FTI (Setup Handler)**
**File**: `src/senaite/starter/setuphandlers.py` (MODIFY)

Add Patient to behavior registration:
```python
BEHAVIORS = [
    ("SampleType", [...]),
    ("Patient", [
        "senaite.starter.content.patient.IPatientSchemaExtender",
    ]),
]
```

✅ Behavior attached to Patient FTI on add-on install  
✅ CNIC field available on Patient  

### **4. Sample CNIC Display (Existing Architecture)**
**File**: No new code needed!

senaite.patient already has the architecture for displaying Patient fields on Sample forms:
- MedicalRecordNumber links to Patient
- PatientFullName, PatientAddress, Sex, Gender are displayed/editable
- These are **handled automatically** because:
  - Sample form loads Patient record via MRN
  - Patient fields are rendered in the form
  - Save updates the linked Patient record

✅ CNIC will automatically appear alongside other Patient fields  
✅ CNIC will be editable on Sample form  
✅ CNIC updates on Patient when Sample saved  

### **5. Update Documentation**
**File**: `docs/CHANGES.md` (MODIFY)

Document the new feature.

---

## Why Only 3 Code Files Needed?

The elegant part: **senaite.patient already has the infrastructure** to handle Patient fields on Sample forms!

Looking at existing code, senaite.patient extends AnalysisRequest with patient demographics via:
- **AT Schema Extender** (in senaite.patient itself)
- Fields like `MedicalRecordNumber`, `PatientFullName`, `Sex`, `Gender` are stored **on AnalysisRequest**

But your requirement is different - CNIC should live **only on Patient**, not duplicated on Sample.

This is actually **simpler** because:
1. ✅ CNIC lives on Patient (Dexterity behavior) - stored once
2. ✅ Sample form accesses Patient record via MRN link - reads CNIC from there
3. ✅ User can edit CNIC on Sample form - updates Patient.CNIC
4. ✅ No duplication - no sync needed - no indexer on Sample needed

This is different from MedicalRecordNumber/PatientFullName which are **duplicated on both Patient and Sample**.

---

## How It Works in Practice

### Sample Form Rendering
```
Sample Registration Form:
┌─────────────────────────────────────────┐
│ Medical Record Number: [MRN dropdown]   │ ← Links to Patient
│                                          │
│ ─── Patient Demographics (linked) ─── │
│ Patient Full Name: [John Smith]       │ ← From Patient.firstname + lastname
│ Place of Residence: [123 Main St]     │ ← From Patient.address
│ Date of Birth: [1990-01-15]           │ ← From Patient.birthdate
│ Sex: [Male]                            │ ← From Patient.sex
│ Gender: [Male]                         │ ← From Patient.gender
│ CNIC: [42101-1234567-8]               │ ← NEW: From Patient.cnic
│                                          │
│ ─── Sample Details ─────────────────── │
│ Sample Type: [Blood]                   │
│ Requested Analyses: [...]              │
│                                          │
│ [Save Sample]                           │
└─────────────────────────────────────────┘

When user saves:
- Sample created with linked MRN
- Patient.cnic updated if user changed it
- CNIC stored only on Patient
```

### Sample Listing Display
```
Sample Listing:
┌──────────────────────────────────────────────────┐
│ ID    │ Patient Name │ CNIC      │ Status │ Date │
├──────────────────────────────────────────────────┤
│ S-001 │ John Smith   │ 42101-... │ Pending│ ...  │
│ S-002 │ Jane Doe     │ 42101-... │ Done   │ ...  │
└──────────────────────────────────────────────────┘

CNIC displayed from linked Patient.cnic
Searchable by CNIC value
```

---

## Files to Create/Modify - Final

| File | Action | Purpose | Complexity |
|------|--------|---------|-----------|
| `src/senaite/starter/content/patient.py` | CREATE | CNIC field on Patient (Dexterity behavior) | Simple |
| `src/senaite/starter/content/configure.zcml` | MODIFY | Register behavior | Simple |
| `src/senaite/starter/setuphandlers.py` | MODIFY | Add Patient to FTI setup | Simple |
| `docs/CHANGES.md` | MODIFY | Document feature | Simple |

**Total: 4 files, ~40-50 lines of code, NO indexers, NO subscribers, NO sample modifications**

---

## Why This is Cleaner Than Original Plan

| Aspect | Original (Two Fields) | Revised (One Field) |
|--------|---|---|
| **Files modified** | 6 | 4 |
| **CNIC storage** | Duplicated on Patient + Sample | Only on Patient |
| **Indexing needed** | Yes (sample.py indexer) | No (linked access) |
| **Sync complexity** | Yes (keep in sync) | No (single source) |
| **Data duplication** | Yes (redundant) | No (clean) |
| **Code lines** | ~130 | ~50 |
| **Maintenance** | Higher (two fields) | Lower (one field) |

---

## Testing Checklist

- [ ] CNIC field appears in Patient add/edit form
- [ ] CNIC field saves/loads on Patient
- [ ] CNIC field appears in Patient listings
- [ ] CNIC field searchable in patient catalog
- [ ] CNIC field appears on Sample registration form
- [ ] CNIC editable on Sample form
- [ ] Saving Sample with CNIC updates Patient.cnic
- [ ] CNIC appears in Sample listings (from linked Patient)
- [ ] CNIC searchable across samples
- [ ] No data duplication (CNIC only on Patient)
- [ ] No permissions errors
- [ ] Existing tests pass

---

## Implementation Order

1. Create `src/senaite/starter/content/patient.py` (CNIC behavior)
2. Register behavior in `configure.zcml`
3. Add Patient to `setuphandlers.py`
4. Update `docs/CHANGES.md`
5. Test all functionality
6. Commit to `add-cnic-field` branch

---

## Branch Status

✅ **Branch**: `add-cnic-field`  
✅ **Strategy**: Single CNIC field on Patient, visible everywhere  
✅ **Files**: 4 (create 1, modify 3)  
✅ **Complexity**: Low (no custom indexers, no subscribers)  

Ready to implement?
