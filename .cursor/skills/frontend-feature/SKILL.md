---
name: frontend-feature
description: Guides creating or changing TrendPilot web features under hybrid folders, ui atoms/molecules with variants, and type-component-export file order. Use when adding a screen, feature, or UI change in web/, or when the user asks to build or modify frontend functionality.
disable-model-invocation: true
---

# Frontend feature (create / change)

## When to use

Creating or changing anything under `web/` (pages, feature UI, hooks, api clients, design-system pieces).

## Before coding

1. Read [STANDARDS.md](STANDARDS.md) and [`web/DESIGN.md`](../../../web/DESIGN.md) if the UI is visual.
2. Run the **reuse gate**:
   - Reusable component present? **Use that**
   - Style different but same role? **Plan for variant** on the existing atom/molecule
   - Else add a new atom/molecule (`ui/`) or feature component (`features/<name>/`)
3. Place code in the hybrid layout (`ui` / `features` / `lib` / `api`).

## Implementation steps

Copy and track:

```text
Feature progress:
- [ ] Reuse gate decided (use / variant / new)
- [ ] Files in correct folder
- [ ] type → component → export order
- [ ] Tailwind + theme tokens; variants not forks
- [ ] No business logic in src/ui
- [ ] Big JSX/logic split if needed
- [ ] Build or smoke-check
```

### Creating UI

- **Atoms / molecules** in `src/ui/`: variants via a small map; theme classes when tokens exist
- **Feature UI** in `src/features/<name>/`: compose `@/ui`; keep pages thin
- File shape:

```tsx
type Props = { variant?: 'primary' | 'secondary'; children: React.ReactNode }

function Example({ variant = 'primary', children }: Props) {
  return <div className={variants[variant]}>{children}</div>
}

export { Example, type Props }
```

### Changing existing UI

- Prefer extending **variants** or props over cloning components
- If a feature file is large, split: subcomponent → hook → promote to `ui` only if generic

### Wiring data

- Clients and wire types under `src/api/`
- Feature hooks own fetch/state; UI leaves stay presentational

## Done when

- Reuse gate respected
- Imports only `features` → `ui` / `lib` / `api`
- Matches Luminous Precision where visual
- `npm run build` in `web/` succeeds (or note why not)

## More detail

See [STANDARDS.md](STANDARDS.md).
