# CNIC Field Implementation - Complete Approach

**Branch**: `add-cnic-field`  
**Status**: Implementation strategy documented and ready to implement  
**Goal**: Add CNIC (Computerized National Identity Card) field to Patient content type, with CNIC visible and editable in both Patient records and Sample registration forms

---

## Executive Summary

This document outlines the **complete, correct approach** to adding a CNIC field to SENAITE 2.6.0 via senaite.starter as a pure add-on (no forking of senaite.patient).

**Key Requirements**:
- CNIC stored once on Patient content type (Dexterity-based)
- CNIC editable on Sample registration form (links to Patient via MedicalRecordNumber)
- CNIC visible in Patient and Sample listings
- CNIC searchable in both catalogs
- Sample-centric workflow: patients created/edited during sample registration

**Current State**: 
- Patient (Dexterity) behavior: Partially implemented (needs ZCML adapter registration for AnalysisRequest) ✗
- AnalysisRequest (Archetypes) extension: Code exists but ZCML registration is MISSING ✗
- **CNIC missing from Sample form and listings because SampleSchemaExtender itself isn't registered in ZCML**

---

## Critical Discovery: Root Cause of Missing CNIC

The senaite.starter template includes `src/senaite/starter/content/sample.py` with a fully-implemented `SampleSchemaExtender` class (Archetypes schema extender), BUT **it is never registered in ZCML**.

**Evidence**:
- File exists: `src/senaite/starter/content/sample.py` (has SampleSchemaExtender class)
- ZCML missing: `src/senaite/starter/content/configure.zcml` has NO adapter registration for it
- Master branch has same issue (not specific to add-cnic-field branch)
- Documentation exists: `src/senaite/starter/content/README.md` shows how it SHOULD be registered

**Result**: The existing ProductionBatchNumber field also doesn't appear on samples - this is a base template bug, not specific to CNIC.

---

## Why The Initial CNIC Approach Failed

The first implementation added a Dexterity behavior to Patient but didn't address the broken AnalysisRequest extender registration:

1. **Patient is Dexterity** (modern) - behaviors work automatically ✓
2. **AnalysisRequest/Sample is Archetypes** (legacy) - requires explicit schema extension ✗
3. **senaite.starter's existing SampleSchemaExtender is not registered** - ZCML adapter registration is missing
4. Result: CNIC appears on Patient form only, never reaches Sample form or listings

The solution is to:
- **Fix the base template bug** - register SampleSchemaExtender in ZCML
- **Add CNIC as an Archetypes field** - extend the existing SampleSchemaExtender with CNIC field
- **Keep Patient CNIC behavior** - Dexterity behavior for Patient already works

---

## Architecture: Correct Pattern Based on senaite.starter Template

The senaite.starter template already demonstrates both patterns correctly in its code (but ZCML registration is broken):

### Pattern 1: Patient (Dexterity Content Type)

**File**: `src/senaite/starter/content/patient.py`

```python
@provider(IFormFieldProvider)
class ICNICField(model.Schema):
    """CNIC field for Patient"""
    cnic = schema.TextLine(
        title=_(u"label_patient_cnic", default=u"CNIC"),
        description=_(u"description_patient_cnic", default=u"..."),
        required=False,
    )
```

**ZCML Registration** in `src/senaite/starter/content/configure.zcml`:

```xml
<plone:behavior
    for="senaite.patient.interfaces.IPatient"
    provides=".patient.ICNICField"
    title="CNIC Field"
    description="Add CNIC field to Patient"
    />
```

**How it works**:
1. Define schema fields as interface with `@provider(IFormFieldProvider)` decorator
2. Register as behavior with `<plone:behavior>` directive
3. Plone automatically handles everything: forms, storage, indexing, rendering

**Status**: ✓ Already implemented

### Pattern 2: AnalysisRequest/Sample (Archetypes Content Type)

**File**: `src/senaite/starter/content/sample.py`

```python
class SampleSchemaExtender(object):
    """Extend Schema Fields for Samples"""
    implements(ISchemaExtender, IBrowserLayerAwareExtender, IOrderableSchemaExtender)
    adapts(IAnalysisRequest)

    fields = [
        ExtStringField("ProductionBatchNumber", ...)
    ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields
```

**ZCML Registration** in `src/senaite/starter/content/configure.zcml`:

```xml
<adapter
    factory=".sample.SampleSchemaExtender"
    provides="archetypes.schemaextender.interfaces.ISchemaExtender"/>
```

**How it works**:
1. Create class implementing `ISchemaExtender` and related interfaces
2. Add field instances to `fields` list
3. Register as adapter with `<adapter>` directive
4. Archetypes automatically handles everything: forms, storage, indexing, rendering

**Status**: ✗ **CODE EXISTS BUT ZCML REGISTRATION IS MISSING** - this is why ProductionBatchNumber doesn't appear on samples either!

---

## Complete Implementation Strategy

### Part A: Fix senaite.starter Base Template Bug

**Problem**: `SampleSchemaExtender` exists in `sample.py` but isn't registered in ZCML

**Solution**: Add missing adapter registration to `src/senaite/starter/content/configure.zcml`

### Part B: Add CNIC to AnalysisRequest via Existing SampleSchemaExtender

**Problem**: CNIC field needs to appear on Sample/AnalysisRequest forms

**Solution**: Add CNIC field to the `fields` list in `SampleSchemaExtender` in `sample.py`

**Benefits**:
- Reuses existing extender class (don't duplicate)
- Shares same ZCML registration
- Keeps related fields together
- Maintains consistency with existing ProductionBatchNumber field

---

## Detailed Implementation Plan

### Step 1: Register SampleSchemaExtender in ZCML

**File**: `src/senaite/starter/content/configure.zcml`

**Current content** (missing adapter):
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

**New content** (add adapter registration):
```xml
<?xml version="1.0" encoding="utf-8"?>
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:plone="http://namespaces.plone.org/plone"
    xmlns:browser="http://namespaces.zope.org/browser"
    i18n_domain="senaite.starter">

  <include package="plone.behavior" file="meta.zcml"/>

  <!-- Patient CNIC Field Behavior (Dexterity) -->
  <plone:behavior
      for="senaite.patient.interfaces.IPatient"
      provides=".patient.ICNICField"
      title="CNIC Field"
      description="Add CNIC field to Patient"
      />

  <!-- Sample Schema Extender (Archetypes) - FIX FOR BASE TEMPLATE BUG -->
  <adapter
      factory=".sample.SampleSchemaExtender"
      provides="archetypes.schemaextender.interfaces.ISchemaExtender"/>

  <!-- Sample Type Schema Extender (Dexterity) -->
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

**Key change**: Added adapter registration for `SampleSchemaExtender`

### Step 2: Add CNIC Field to SampleSchemaExtender

**File**: `src/senaite/starter/content/sample.py`

**Current**: Has only `ProductionBatchNumber` field

**New**: Add CNIC field to the `fields` list

```python
# -*- coding: utf-8 -*-

from archetypes.schemaextender.interfaces import IBrowserLayerAwareExtender
from archetypes.schemaextender.interfaces import IOrderableSchemaExtender
from archetypes.schemaextender.interfaces import ISchemaExtender
from archetypes.schemaextender.interfaces import ISchemaModifier
from bika.lims.interfaces import IAnalysisRequest
from Products.Archetypes.atapi import StringWidget
from Products.CMFCore.permissions import View
from zope.component import adapts
from zope.interface import implements

from senaite.starter import messageFactory as _
from senaite.starter.content import ExtStringField
from senaite.starter.interfaces import ISenaiteStarter
from senaite.starter.permissions import EditExtendedField


class SampleSchemaExtender(object):
    """Extend Schema Fields for Samples
    """
    layer = ISenaiteStarter
    implements(
        ISchemaExtender,
        IBrowserLayerAwareExtender,
        IOrderableSchemaExtender)
    adapts(IAnalysisRequest)

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
        ExtStringField(
            "cnic",  # NEW: CNIC field for Patient
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
    ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.fields

    def getOrder(self, original):
        """Change the order of the extended fields
        """
        # get the fields of the default schemata
        default = original["default"]

        # move fields to desired position
        # (optional - remove if default ordering is acceptable)
        
        return original


class SampleSchemaModifier(object):
    """Modify Sample Schema Fields
    """
    layer = ISenaiteStarter
    implements(
        ISchemaModifier,
        IBrowserLayerAwareExtender)
    adapts(IAnalysisRequest)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        return schema
```

**Key changes**:
- Added CNIC field to `fields` list as ExtStringField
- Used same mode, permissions, and visibility as ProductionBatchNumber
- Added i18n labels (will appear in English by default)

---

## Expected Behavior After Implementation

### For Patients
1. ✅ CNIC field appears in Patient add/edit form (Dexterity behavior)
2. ✅ CNIC appears in Patient list views (auto-indexed)
3. ✅ CNIC is searchable in patient_catalog (auto-indexed)
4. ✅ CNIC persists on Patient content object

### For Samples/AnalysisRequest  
1. ✅ CNIC field appears in Sample registration form (Archetypes extender - once ZCML is fixed)
2. ✅ CNIC appears in Sample list views (auto-indexed)
3. ✅ CNIC is searchable in sample_catalog (auto-indexed)
4. ✅ CNIC can be edited when editing sample
5. ✅ CNIC persists on AnalysisRequest content object

### For Search/Integration
1. ✅ CNIC indexed in both catalogs
2. ✅ CNIC included in senaite.jsonapi JSON exports
3. ✅ CNIC appears in senaite.lims API responses

---

## Why This Approach Is Sound

✅ **Replicates senaite.starter template patterns** - Uses same code pattern that already exists (SampleSchemaExtender in sample.py)

✅ **Fixes base template bug** - Registers SampleSchemaExtender that was implemented but never registered

✅ **No forking required** - Works with vanilla senaite.patient v1.5.0+

✅ **Leverages existing infrastructure** - Plone and Archetypes handle schema integration automatically

✅ **Minimal code changes** - Only 2 files need modification (configure.zcml + sample.py)

✅ **Maintainable** - Clean separation of Patient (Dexterity) and AnalysisRequest (Archetypes) extensions

✅ **Reuses extender class** - Doesn't duplicate SampleSchemaExtender logic

---

## Implementation Steps

### 1. Update configure.zcml with Adapter Registration

```bash
cd C:\Users\Paul.Cleary\senaite.starter
# Edit src/senaite/starter/content/configure.zcml
# Add: <adapter factory=".sample.SampleSchemaExtender" provides="archetypes.schemaextender.interfaces.ISchemaExtender"/>
```

### 2. Add CNIC Field to SampleSchemaExtender  

```bash
# Edit src/senaite/starter/content/sample.py
# Add CNIC field to the 'fields' list in SampleSchemaExtender class
```

### 3. Run Buildout and Test

```bash
./bin/buildout -c develop.cfg
./bin/instance fg
# 1. Create Patient with CNIC
# 2. Register Sample with same Patient
# 3. Verify CNIC appears on both forms and listings
# 4. Check event log for errors
```

### 4. Commit Changes

```bash
git add -A
git commit -m "Fix: Register SampleSchemaExtender in ZCML and add CNIC field to AnalysisRequest

- Add adapter registration for SampleSchemaExtender in configure.zcml (fixes base template bug)
- Add CNIC field to SampleSchemaExtender in sample.py (extends AnalysisRequest)
- CNIC now appears in both Patient and Sample forms, listings, and search catalogs

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

## Files to Modify

### 1. `src/senaite/starter/content/configure.zcml`
- Add adapter registration for SampleSchemaExtender

### 2. `src/senaite/starter/content/sample.py`
- Add CNIC field to `fields` list in SampleSchemaExtender

### Already Done (Don't Change)
- `src/senaite/starter/content/patient.py` - Patient CNIC behavior ✓
- `src/senaite/starter/setuphandlers.py` - Patient FTI setup ✓

---

## Troubleshooting Guide

### If CNIC appears on Patient but NOT Sample

1. **Check ZCML registration**: Verify adapter line was added to configure.zcml
2. **Check event log**: Look for ZCML parsing errors
3. **Restart instance**: Make sure changes are loaded
4. **Reinstall add-on**: Trigger installation step again via quickinstaller

### If CNIC doesn't appear anywhere

1. **Check event log**: Look for behavior/adapter registration errors
2. **Verify ZCML syntax**: Check for typos in configure.zcml
3. **Verify interfaces**: Ensure senaite.patient.interfaces.IPatient exists
4. **Check Python syntax**: Run Python syntax checker on sample.py

### If CNIC appears but isn't searchable

1. **Reindex catalogs**: Run maintenance > Reindex in SENAITE
2. **Check field indexing**: Verify ExtStringField is searchable by default
3. **Check catalog columns**: May need to add CNIC as column to sample_catalog

---

## References

- **senaite.starter template**: Existing SampleSchemaExtender in sample.py
- **Template documentation**: `src/senaite/starter/content/README.md`
- **Archetypes schemaextender**: https://github.com/plone/archetypes.schemaextender
- **Plone Dexterity behaviors**: https://github.com/plone/plone.behavior

---

## Next Steps

1. Apply changes to configure.zcml and sample.py
2. Run buildout to verify no errors
3. Start instance and test on SENAITE 2.6.0
4. Verify CNIC appears in both Patient and Sample contexts
5. Commit to add-cnic-field branch

