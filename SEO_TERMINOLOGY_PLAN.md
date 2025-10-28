### SEO & Terminology Plan (MEP Score)

This file tracks the plan and progress for standardizing branding to "MEP Score" and improving SEO metadata. Update checkboxes as tasks are completed.

#### Glossary
- Product name: "MEP Score" (plural: "MEP scores")
- Use "Score Breakdown" (not "Ranking Score Breakdown")
- Methodology name: "MEP Score Methodology"
- First occurrence on a page: "Member of the European Parliament (MEP)"

#### Critical Issues Found - MUST FIX
- [ ] **Backend class names** - `MEPRankingScorer` class could cause import/calculation issues
- [ ] **JavaScript function names** - `loadMEPRankingScores`, `recalculateMEPRankingScores` functions
- [ ] **File names** - `mep_ranking_scorer.py` file name
- [ ] **Import statements** - All imports referencing old naming
- [ ] **Database references** - Any database field names or table references

#### Tasks

- [x] Update page metadata (titles/descriptions/OG/Twitter)
  - [x] `public/index.html`
    - Title → "MEP Score"
    - Description → keyword-rich summary
    - OG/Twitter titles/descriptions updated
  - [x] `public/profile.html`
    - Title → "MEP Score Profile"
    - Description → keyword-rich summary
    - OG/Twitter titles/descriptions updated
  - [x] `public/methodology.html`
    - Title → "MEP Score Methodology"
    - Description → keyword-rich summary
    - OG/Twitter titles/descriptions updated

- [x] Update navigation and UI labels
  - [x] "MEP Rankings" labels/links → "MEP Score"
  - [x] "Rankings" nav links → "MEP Score"
  - [x] Footer links updated

- [x] Update JavaScript content and comments
  - [x] "MEP Ranking Score Breakdown ..." → "MEP Score Breakdown ..."
  - [x] "Final MEP Ranking Score:" → "Final MEP Score:"
  - [x] "MEP Ranking Methodology" → "MEP Score Methodology"
  - [x] Error messages updated

- [x] Update server strings
  - [x] `serve.py` server title and description

- [ ] **CRITICAL: Fix backend naming to prevent calculation issues**
  - [ ] Rename `backend/mep_ranking_scorer.py` → `backend/mep_score_scorer.py`
  - [ ] Update class name `MEPRankingScorer` → `MEPScoreScorer`
  - [ ] Update all import statements across backend files
  - [ ] Update all class instantiations
  - [ ] Update file references in documentation

- [ ] **CRITICAL: Fix JavaScript function names**
  - [ ] `loadMEPRankingScores` → `loadMEPScores`
  - [ ] `recalculateMEPRankingScores` → `recalculateMEPScores`
  - [ ] Update all function calls and references

- [ ] **CRITICAL: Update documentation files**
  - [ ] `README.md` - Update all references
  - [ ] `METHODOLOGY.md` - Update methodology references
  - [ ] `CLAUDE.md` - Update system references
  - [ ] All agent files - Update system references
  - [ ] All markdown documentation - Update terminology

#### Acceptance Criteria
- [ ] All page titles use "MEP Score" consistently
- [ ] All navigation labels use "MEP Score"
- [ ] All JavaScript functions use "MEP Score" naming
- [ ] All backend classes use "MEP Score" naming
- [ ] All documentation uses "MEP Score" terminology
- [ ] No "MEP Ranking" terminology remains in user-facing content
- [ ] Calculations and updates work without naming conflicts

#### Files to Update
- [x] `public/index.html`
- [x] `public/profile.html`
- [x] `public/methodology.html`
- [x] `public/js/profile.js`
- [x] `public/js/utilities.js`
- [x] `serve.py`
- [ ] `README.md`
- [ ] `METHODOLOGY.md`
- [ ] `CLAUDE.md`
- [ ] `backend/mep_ranking_scorer.py` → rename to `mep_score_scorer.py`
- [ ] All agent files in `agents/` directory
- [ ] All documentation markdown files


