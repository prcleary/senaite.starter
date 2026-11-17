# Architecture Comparison: Why Single Field on Patient is Better

## Your Clarification: Critical Insight

You stated clearly:
> "CNIC should only be for a patient, but should be visible in sample request form, and in all listings of samples/searches"

This reveals an elegant truth: **CNIC should not be duplicated**.

---

## Three Possible Architectures

### **❌ Architecture A: Duplicate Field (My Initial Proposal)**
```
Patient Record:
├── CNIC (Patient's own field)

Sample/AnalysisRequest:
├── MedicalRecordNumber (links to Patient)
├── PatientFullName
├── PatientAddress
├── DateOfBirth
├── Sex
├── Gender
├── CNIC (duplicated - stored on Sample too)

Problem:
❌ Two copies of same data
❌ Sync logic needed if either updates
❌ Conflict resolution needed
❌ Extra indexer required
❌ Higher complexity
❌ Not what you asked for
```

---

### **❌ Architecture B: Stored Only on Sample**
```
Sample/AnalysisRequest:
├── MedicalRecordNumber (links to Patient)
├── PatientFullName
├── CNIC (stored here, not on Patient)

Patient Record:
├── (no CNIC field)

Problem:
❌ Patients can only be entered/accessed through samples
❌ What if same patient in multiple samples?
  → Different CNIC values?
  → Inconsistent data
❌ Cannot look up patient by CNIC directly
❌ Violates your single-entry-point workflow
```

---

### **✅ Architecture C: Single Field on Patient (Your Requirement)**
```
Patient Record:
├── MRN
├── Name
├── Birthdate
├── Sex
├── Gender
├── CNIC ← Single source of truth

Sample/AnalysisRequest:
├── MedicalRecordNumber ← Links to Patient
├── PatientFullName ← Displays Patient.name
├── DateOfBirth ← Displays Patient.birthdate
├── Sex ← Displays Patient.sex
├── Gender ← Displays Patient.gender
├── CNIC ← Displays & edits Patient.cnic

Advantages:
✅ Single CNIC per patient (no duplication)
✅ Consistent across all samples linked to patient
✅ Sample-centric entry point (edit CNIC on sample form)
✅ Patient record always has authoritative CNIC
✅ Simplest implementation
✅ No sync/conflict logic needed
✅ Clean data model
```

---

## Why This Works with Existing senaite.patient Architecture

senaite.patient already has the pattern:

```python
# From senaite.patient/content/analysisrequest.py:

MedicalRecordNumberField = TemporaryIdentifierField(
    "MedicalRecordNumber",  # Field on AnalysisRequest
    # ... displays/edits patient data
)

PatientFullNameField = FullnameField(
    "PatientFullName",  # Field on AnalysisRequest
    # ... displays/edits patient data
)
```

These existing fields work by:
1. ✅ AnalysisRequest has field that links to Patient
2. ✅ Sample form loads Patient data via MRN
3. ✅ User can view/edit Patient fields on sample form
4. ✅ When saved, it updates Patient record

**CNIC will follow the same pattern** - but instead of being duplicated on both, it will live only on Patient, accessed through the link.

---

## Implementation Simplicity Comparison

### **Architecture A: Duplicate (My Initial Proposal)**
```
Files: 6
├── patient.py (behavior - CNIC)
├── configure.zcml (register behavior)
├── setuphandlers.py (FTI setup)
├── sample.py (extend with CNIC)
├── catalog/indexer/sample.py (index CNIC)
└── CHANGES.md

Code: ~130 lines
Complexity: High
- Need custom indexer
- Need AT schema extender
- Sync logic if ever needed
- Two data sources for same value
```

### **Architecture C: Single (Your Requirement) ✅**
```
Files: 4
├── patient.py (behavior - CNIC only)
├── configure.zcml (register behavior)
├── setuphandlers.py (FTI setup)
└── CHANGES.md

Code: ~50 lines
Complexity: Low
- Just add field to Patient
- Existing senaite.patient architecture displays it on samples
- No indexer needed (Patient catalog auto-indexes)
- No sync logic needed (single field)
- One authoritative source
```

---

## Data Flow: Architecture C (Correct)

### Patient Creation (via Sample Form)
```
User fills Sample Form:
  Medical Record Number: "P-12345"
  Patient Name: "John Smith"
  CNIC: "42101-1234567-8"
  Sex: "M"
  Gender: "M"
  [Other patient fields]

↓

System:
  1. Checks if Patient P-12345 exists
  2. If not: creates new Patient with CNIC
  3. If yes: updates Patient.cnic if changed
  4. Links Sample to Patient via MRN
  5. Saves Sample

↓

Result:
  Patient (single record):
    - MRN: "P-12345"
    - Name: "John Smith"
    - CNIC: "42101-1234567-8" ← Stored once
    - Sex: "M"
    - Gender: "M"

  Sample:
    - MedicalRecordNumber: "P-12345" ← Reference only
    - Linked to above Patient
    - Shows Patient's CNIC from link

  Listings:
    Sample shows: Patient Name | CNIC
    Both from linked Patient record
```

### Patient Update (via Sample Form for Same Patient)
```
User creates another Sample for same patient:
  Medical Record Number: "P-12345"
  CNIC: "42101-1234567-8" (unchanged)
  [Other fields]

↓

System:
  1. Finds existing Patient P-12345
  2. CNIC matches → no update needed
  3. If user changed CNIC: updates Patient.cnic once
  4. All samples linked to this patient see updated value

↓

Result:
  Patient (single record):
    - CNIC: updated value ← Automatically visible in all linked samples
  
  All Samples for P-12345:
    - Display updated CNIC from Patient
    - No duplication, no sync issues
```

---

## Comparison: Your Workflow with Architecture C

| Workflow Step | Implementation | Why It Works |
|---|---|---|
| User opens Sample form | Standard senaite.patient form | No changes needed |
| User enters MRN | Queryselect shows existing patients | Existing pattern |
| User enters CNIC | Displayed in form like other patient fields | CNIC is now on Patient |
| User saves sample | Updates Patient record if data changed | Existing pattern |
| CNIC appears in sample listing | Pulled from linked Patient | No indexer needed |
| User searches by CNIC | Searches Patient catalog | Auto-indexed by Dexterity |
| User searches samples by CNIC | Sample listing shows Patient.cnic | Linked field visible |

---

## Why Not the Duplicate Approach?

If we duplicated CNIC on Sample:

```
Problem 1: Inconsistent Data
  Sample 1: CNIC "42101-111111-1" (from patient entry)
  Sample 2: CNIC "42101-222222-2" (typo during entry)
  → Same patient, different CNICs → data quality issue

Problem 2: Maintenance Burden
  If patient's CNIC updated after sample created:
  → Need subscriber to sync it
  → Need indexer on sample
  → Need resolver for conflicts
  → Extra complexity for no benefit

Problem 3: Violation of Your Workflow
  You said: "patients are never entered separately - only through sample forms"
  → Single field on Patient enforces this design
  → Duplicate fields tempt separate patient entry
```

---

## Decision: Single Field on Patient

✅ **This is the correct architecture** because:

1. **Matches your workflow** - patients only entered/edited through sample forms
2. **Single source of truth** - CNIC stored once on Patient
3. **No duplication** - clean data model
4. **Simplest code** - 4 files, ~50 lines
5. **Existing pattern** - follows how senaite.patient already works
6. **Lower maintenance** - no sync logic, no conflict resolution
7. **Data consistency** - same patient always has same CNIC
8. **Audit trail** - Patient.cnic change history clear

---

## Summary

**You were right to ask "is this creating two data items?"**

The answer changed from:
- ❌ "Yes, two CNIC fields (bad architecture)" 
  
To:
- ✅ "No, one CNIC field on Patient, visible everywhere (good architecture)"

This is simpler, cleaner, and aligns perfectly with your sample-centric workflow.
