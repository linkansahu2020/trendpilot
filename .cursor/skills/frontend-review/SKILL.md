---
name: frontend-review
description: Reviews TrendPilot web code against architecture checkpoints—hybrid folders, reuse-or-variant gate, atom/molecule variants, type-component-export order, and design tokens. Use when reviewing web/ PRs, frontend diffs, or when the user asks for a frontend architecture or UI code review.
disable-model-invocation: true
---

# Frontend review checkpoints

## When to use

Reviewing `web/` changes (PR, branch diff, or pasted files). Not a substitute for Bugbot or security review.

## How to review

1. Read [STANDARDS.md](STANDARDS.md); skim [`web/DESIGN.md`](../../../web/DESIGN.md) for visual PRs.
2. Inspect the diff (or named files).
3. Run every checkpoint below.
4. Report with severity only for real issues.

## Checkpoints

### Architecture
- [ ] New code lives in `ui/` / `features/<name>/` / `lib/` / `api/` correctly
- [ ] `ui` does not import `features`
- [ ] No business/domain logic inside `src/ui` atoms or molecules

### Reuse gate (required)
- [ ] If a reusable component already exists, the change **uses that**
- [ ] If the style is different, the change **plans for / adds a variant** (not a near-duplicate component)
- [ ] New `ui` pieces are truly generic; feature-only UI stayed in `features/`

### Component shape
- [ ] Files follow **type → component → export**
- [ ] Variants cover look differences (Tailwind + theme classes when tokens exist)
- [ ] Oversized files are split (subcomponent / hook) or flagged

### Design & a11y
- [ ] Visual work aligns with Luminous Precision / DESIGN.md
- [ ] Real interactive elements (`button`, `input`, …); focus styles not removed

### Performance (light)
- [ ] No unnecessary `useMemo` / `useCallback`
- [ ] Stable list keys; prefer structure over memo churn

## Output format

```markdown
# Frontend review

## Summary
[1–2 sentences]

## Critical
- [must fix] …

## Suggestion
- [should improve] …

## Nice to have
- [optional] …

## Checkpoints passed
- … (list greens briefly)
```

If nothing fails: say so, list any Suggestions, stop.

## More detail

See [STANDARDS.md](STANDARDS.md).
