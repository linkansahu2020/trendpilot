---
name: frontend-architecture
description: Reviews and guides TrendPilot web architecture—hybrid folders, flat ui atoms/molecules with Tailwind theme variants, type-component-export order, and reuse-or-variant gate. Use when reviewing web/ PRs, frontend diffs, design-system drift, or when the user asks for a frontend architecture review.
disable-model-invocation: true
---

# Frontend architecture review

## When to use

Reviewing or enforcing structure for `web/` (PRs, branch diffs, UI/design-system changes). Not a substitute for Bugbot or security review.

## How to review

1. Read [STANDARDS.md](STANDARDS.md); skim [`web/DESIGN.md`](../../../web/DESIGN.md) for visual PRs.
2. Inspect the diff (or named files).
3. Run every checkpoint below.
4. Report with severity only for real issues.

## Checkpoints

### Architecture
- [ ] Code lives in `ui/` / `features/<name>/` / `lib/` / `api/` correctly
- [ ] `ui` is flat (atoms + molecules together; no business logic)
- [ ] `ui` does not import `features`

### Reuse gate (required)
- [ ] If a reusable component exists, the change **uses that**
- [ ] If the style is different, the change **plans for / adds a variant** (not a near-duplicate)
- [ ] New `ui` pieces are generic; feature-only UI stayed in `features/`

### Component shape
- [ ] Files follow **type → component → export**
- [ ] Variants cover look differences (Tailwind + theme classes when tokens exist)
- [ ] Oversized files are split (subcomponent / hook) or flagged

### Design & a11y
- [ ] Visual work aligns with Luminous Precision / DESIGN.md
- [ ] Real interactive elements; focus styles not removed

### Performance (light)
- [ ] No unnecessary `useMemo` / `useCallback`
- [ ] Stable list keys; prefer structure over memo churn

## Output format

```markdown
# Frontend architecture review

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
