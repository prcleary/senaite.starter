# CNIC Field Implementation - Session 2 Complete

## Status Overview

**Branch**: `add-cnic-field`  
**Session**: 2 (Analysis & Planning)  
**Completion**: 100% (Analysis & Documentation)  
**Code Implementation**: 0% (Ready to begin)  
**Next Phase**: Implementation using documented approach  

## What This Session Accomplished

✓ **Reviewed** all previous work and documentation  
✓ **Analyzed** senaite.patient source code to understand patterns  
✓ **Identified** why previous approach failed (incomplete)  
✓ **Documented** proper complete implementation approach  
✓ **Created** prioritized action plan with time estimates  
✓ **Planned** all required file changes  
✓ **Established** success criteria for each phase  

## Key Discovery

**Previous approach was incomplete:**
- Only extended Patient (Dexterity) with behavior ✓
- Didn't extend AnalysisRequest (Archetypes) ✗
- Didn't add monkey-patched methods ✗
- Didn't define permissions ✗
- Didn't add catalog indexing ✗
- Didn't configure workflow ✗

**Result**: CNIC only appeared in Patient individual record, not in Sample form where it's needed.

**Solution**: Follow senaite.patient's complete pattern with 6 coordinated phases.

## Documentation Created (This Session)

| Document | Purpose | Location |
|----------|---------|----------|
| NEW_APPROACH_INFORMED_BY_SENAITE_PATIENT.md | Complete implementation plan | Branch root |
| NEXT_ACTIONS.md | Sequential action steps (1-6) | Branch root |
| SESSION_2_ANALYSIS_SUMMARY.md | This session's findings | Branch root |
| PROGRESS_SESSION_2026_11_17.md | Previous session summary | Branch root |

## Implementation Phases (Ready to Start)

### Phase 1: Verify archetypes.schemaextender ✓ Planned
- Action: Import test in Python shell
- Time: 2 minutes
- Outcome: Know if we can use senaite.patient pattern

### Phase 2: Extend AnalysisRequest ✓ Planned
- Action: Rewrite `content/analysisrequest.py` using schema extender pattern
- Files: 2 (analysisrequest.py, configure.zcml)
- Time: 30 minutes
- Outcome: CNIC appears on Sample form

### Phase 3: Add Monkey-Patched Methods ✓ Planned
- Action: Create monkeys module with getCNIC/setCNIC
- Files: 4 (init files, analysisrequest.py, configure.zcml)
- Time: 20 minutes
- Outcome: API methods available

### Phase 4: Define Permissions ✓ Planned
- Action: Create permissions.py and permissions.zcml
- Files: 2 (permissions.py, permissions.zcml)
- Time: 15 minutes
- Outcome: Permission controls enforced

### Phase 5: Add Catalog Indexing ✓ Planned
- Action: Update setuphandler to index CNIC
- Files: 1 (setuphandlers.py)
- Time: 20 minutes
- Outcome: CNIC searchable in listings

### Phase 6: Verify Workflow Config ✓ Planned
- Action: Check/update workflow definition
- Files: 1 (workflow definition.xml)
- Time: 10 minutes
- Outcome: Workflow state permissions correct

**Total Implementation Time**: 1.5-3 hours (Phase 1-6)

## Code Patterns to Follow

All patterns documented with references to senaite.patient source:

- **AnalysisRequest Schema Extender**: senaite.patient lines 51-158
- **Monkey Patches**: senaite.patient monkeys/content/analysisrequest.py
- **ZCML Registration**: senaite.patient content/configure.zcml
- **Permissions**: senaite.patient permissions.py

## Current Branch State

```
add-cnic-field (20 commits)
├── Implementation Phase: 1/6 (Patient DX behavior only)
├── Patient CNIC: ✓ Working (form only)
├── AnalysisRequest CNIC: ✗ Not started
├── Monkey patches: ✗ Not started
├── Permissions: ✗ Not started
├── Catalog indexing: ✗ Not started
├── Workflow config: ✗ Not started
└── All phases planned with clear actions
```

## How to Use This Documentation

### For Implementation:
1. Start with `NEXT_ACTIONS.md` - follow steps 1-6 in order
2. For each step, reference `NEW_APPROACH_INFORMED_BY_SENAITE_PATIENT.md`
3. Use senaite.patient code as pattern for exact syntax
4. Test after each step using provided success criteria

### For Understanding:
1. Read `SESSION_2_ANALYSIS_SUMMARY.md` for overview
2. Read `NEW_APPROACH_INFORMED_BY_SENAITE_PATIENT.md` for details
3. Read `PROGRESS_SESSION_2026_11_17.md` for previous context

### For Reference:
- Commit history shows all attempted approaches
- Comments in git log explain what was tried and why
- Code changes are minimal pending completion

## Success Criteria for Next Session

After implementing all 6 phases, CNIC should:

**In Patient**:
- ✓ Appear in individual Patient record (already working)
- ✓ Appear in Patient listing (after indexing)
- ✓ Be searchable by CNIC value (after indexing)

**In Sample/AnalysisRequest**:
- ✓ Appear in registration form
- ✓ Be editable during data entry
- ✓ Appear in sample view/listing
- ✓ Be searchable
- ✓ Accessible via API: `sample.getCNIC()`

**System-wide**:
- ✓ No errors in event log
- ✓ Permissions enforced correctly
- ✓ Workflow state permissions respected

## Files Changed History

**Session 1** (Incomplete approach):
- Created: patient.py, analysisrequest.py
- Modified: configure.zcml, setuphandlers.py, setup.py
- Result: CNIC in Patient form only

**Session 2** (This session - Planning):
- Analyzed: senaite.patient codebase
- Documented: Proper approach with 6 phases
- Planned: All required file changes
- Result: Clear implementation path ready

**Session 3** (Next - Implementation):
- Will create: monkeys modules, permissions files
- Will modify: analysisrequest.py, setuphandlers.py, ZCML files
- Will achieve: CNIC visible and functional everywhere

## Git Commands for Reference

```bash
# View all documentation
git show add-cnic-field:NEW_APPROACH_INFORMED_BY_SENAITE_PATIENT.md
git show add-cnic-field:NEXT_ACTIONS.md
git show add-cnic-field:SESSION_2_ANALYSIS_SUMMARY.md

# View commit history
git log --oneline add-cnic-field | head -10

# See what's on branch vs master
git diff master..add-cnic-field --stat
```

## Notes for Next Session

1. **Start with Step 1 of NEXT_ACTIONS.md** - verify archetypes.schemaextender
2. **Keep senaite.patient code nearby** - use it as reference for syntax
3. **Test after each phase** - don't do all 6 at once
4. **Follow documented patterns exactly** - they're based on working code
5. **Update NEXT_ACTIONS.md as you progress** - check off completed steps

## Questions for Clarification (Optional)

If blocked on Phase 1 (archetypes.schemaextender), consider:
- Is there an older/different schema extension mechanism in SENAITE 2.6.0?
- What import error occurs if archetypes.schemaextender unavailable?
- Are there example schema extenders in senaite.core or senaite.lims?

These should be answered in Python shell before proceeding, but may reveal alternate approaches if needed.

---

## Summary

**This session completed comprehensive analysis and planning.**

The approach is now **fully informed by actual senaite.patient implementation**, not assumptions.

All required changes are **documented with specific files, patterns, and success criteria**.

**Next step**: Follow NEXT_ACTIONS.md steps 1-6 to implement the complete solution.

**Branch is clean, documented, and ready for implementation.**
