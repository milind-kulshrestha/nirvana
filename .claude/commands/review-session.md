# UI Review Session

Generate a structured review document for the latest development work. This helps the user visually inspect and provide focused feedback on Claude's implementation.

## Instructions

1. **Read the latest changelog entry** from `docs/project/changelog.md` (the first `##` entry after `[Unreleased]`)

2. **Read the git log** for commits since the previous changelog date to capture any unlisted changes:
   ```
   git log --oneline --since="<previous_changelog_date>"
   ```

3. **Identify all UI-facing changes** — anything that affects what the user sees or interacts with:
   - New pages/routes
   - New components or widgets
   - Modified layouts, styling, or theming
   - New interactive elements (buttons, forms, modals)
   - Data display changes (charts, tables, badges)
   - Navigation changes

4. **Create a review file** at `docs/project/reviews/YYYY-MM-DD-<feature-slug>.md` using this structure:

```markdown
# Review: [Feature Name]
**Date:** YYYY-MM-DD
**Changelog Entry:** [date] - [title]
**Commits:** [first_sha..last_sha]
**Status:** 🔴 Not Started | 🟡 In Progress | 🟢 Complete

---

## UI Changes to Review

### 1. [Component/Page Name]
- **What changed:** Brief description
- **Where to look:** Route or location in app (e.g., `/discover`, expanded stock row)
- **Files:** List of relevant frontend files
- **Screenshot:** <!-- paste or describe -->
- [ ] **Looks correct**
- [ ] **Styling matches design system**
- [ ] **Responsive/resize behavior OK**
- **Feedback:** _your notes here_

### 2. [Next Component/Page]
...

---

## Functional Checks

- [ ] App starts without errors
- [ ] Navigation between pages works
- [ ] Data loads correctly (no stale/missing data)
- [ ] Error states handled gracefully
- [ ] Loading states present and smooth

---

## Overall Feedback

### What works well
-

### Issues found
| # | Severity | Component | Description | Action |
|---|----------|-----------|-------------|--------|
| 1 | 🔴 Bug / 🟡 UX / 🟢 Nit | | | |

### Design/UX suggestions
-

### Questions for next session
-
```

5. **Print a summary** of what to review and suggest the user run the app to inspect each item.

6. **After the user provides feedback**, update the review file with their notes and create follow-up tasks if needed.
