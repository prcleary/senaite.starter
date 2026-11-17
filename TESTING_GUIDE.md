# Quick Testing Guide - CNIC Field Implementation

## 1. Pull and Install

```bash
# Navigate to your senaite.starter directory
cd /path/to/senaite.starter

# Fetch the branch
git fetch origin
git checkout add-cnic-field

# If using buildout, reinstall the package
# If using pip, reinstall: pip install -e .
```

## 2. Restart SENAITE Instance

```bash
# Stop the running instance
# Then start it again (force reload)
bin/instance fg
```

## 3. Reinstall Add-On in Web UI

1. Navigate to `http://localhost:8080/senaite`
2. Go to **Add-ons** (or Products in ZMI)
3. Find **senaite.starter**
4. Click **Reinstall** (this triggers setuphandlers.py)
5. Wait for completion message

---

## 4. Verify Patient CNIC Field

### Create a Patient
1. Navigate to **Patients** folder
2. Click **Add Patient**
3. Fill in:
   - Medical Record Number: `TEST-001`
   - Firstname: `John`
   - Lastname: `Doe`
   - CNIC: `42101-1234567-8` ← **NEW FIELD**
4. Click **Save**
5. ✅ Verify CNIC appears in form
6. ✅ Verify CNIC saved in patient record

### View Patient Listing
1. Go to **Patients** folder
2. ✅ Verify CNIC column appears in listing
3. ✅ Verify CNIC value visible

---

## 5. Verify Sample Registration

### Register Sample for New Patient
1. Navigate to **Sample Registration**
2. Fill in:
   - Medical Record Number: `TEST-002`
   - Patient Name: `Jane Smith`
   - CNIC: `42101-9876543-2` ← **NEW FIELD**
   - Sex: Select option
   - Gender: Select option
   - Other required fields...
3. Click **Save**
4. ✅ Verify Patient created with CNIC
5. ✅ Verify Sample linked to Patient

### Register Sample for Existing Patient
1. Navigate to **Sample Registration**
2. Enter Medical Record Number: `TEST-001` (existing patient)
3. ✅ Verify Patient data loads including CNIC
4. CNIC should show: `42101-1234567-8`
5. Can edit CNIC if needed
6. Click **Save**
7. ✅ Verify Patient.CNIC updated (if changed)

---

## 6. Verify Sample Listing

1. Navigate to **Samples** (or Analysis Requests)
2. View sample list
3. ✅ Verify CNIC column appears
4. ✅ Verify CNIC values displayed from linked Patient

---

## 7. Test Search

### Search in Listings
1. Sample or Patient listing page
2. Use search box
3. Enter CNIC value: `42101-1234567-8`
4. ✅ Verify results appear

### Advanced Filtering (if available)
1. Use listing filters
2. ✅ Verify CNIC searchable as field

---

## 8. Troubleshooting

### CNIC Field Not Appearing in Form

**Check:**
1. Was add-on reinstalled? (Check event log)
2. Did setuphandlers.py run? (Check logs for "Setup Behaviors")
3. Is senaite.patient installed? (Check Add-ons)

**Fix:**
```bash
# In ZMI, go to Control Panel > Event Log
# Look for "*** Setup Behaviors ***" message
# If not there, reinstall add-on manually

# Or use Zope shell:
bin/zopepy
>>> from senaite.starter import setuphandlers
>>> from senaite.lims import api
>>> portal = app['senaite']
>>> setuphandlers.setup_behaviors(portal)
>>> import transaction
>>> transaction.commit()
```

### CNIC Field Not Saving

**Check:**
1. No Python errors in event log
2. Field is marked as `required=False` (should be optional)
3. Dexterity behavior properly registered

**Fix:**
1. Check `src/senaite/starter/content/patient.py` has correct decorator
2. Check `configure.zcml` has correct behavior registration
3. Check `setuphandlers.py` added Patient to BEHAVIORS

### CNIC Not Appearing in Sample Form

**Expected Behavior:**
- CNIC should appear because senaite.patient already displays Patient fields
- When MedicalRecordNumber filled, Patient data loads
- CNIC should display alongside Sex, Gender, etc.

**If not appearing:**
1. Check Patient was created with CNIC
2. Check sample form loads Patient data
3. Check no JavaScript errors in browser console

---

## 9. Verify Implementation Files

```bash
# Check patient.py exists
ls -la src/senaite/starter/content/patient.py

# Check ZCML is registered
grep "patient-cnic-extender" src/senaite/starter/content/configure.zcml

# Check setuphandler updated
grep "Patient" src/senaite/starter/setuphandlers.py

# Check CHANGES.md updated
grep "CNIC" docs/CHANGES.md
```

---

## 10. Git Verification

```bash
# Check you're on correct branch
git branch -v
# Should show: * add-cnic-field

# Check commit is there
git log --oneline -1
# Should show: "Add CNIC field to Patient content type"

# Check which files changed
git diff master..add-cnic-field --name-only
# Should show: patient.py, configure.zcml, setuphandlers.py, CHANGES.md
```

---

## Success Criteria

✅ CNIC field appears in Patient form
✅ CNIC field appears in Sample registration form  
✅ CNIC saves and loads correctly
✅ CNIC appears in Patient listing
✅ CNIC appears in Sample listing
✅ CNIC searchable in both listings
✅ No errors in event log
✅ Existing tests still pass (if running test suite)

---

## Notes for Test Instance

- This is a minimal implementation - no uniqueness constraints yet
- CNIC is optional (can be left blank)
- Multiple patients can have same CNIC (no auto-linking yet)
- These can be added in future iterations

---

## Support

If you encounter any issues:
1. Check event log for error messages
2. Verify files are in correct locations
3. Restart Zope instance
4. Reinstall add-on via web UI
5. Check git diff to verify changes pulled correctly
