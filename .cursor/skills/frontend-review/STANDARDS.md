# TrendPilot web standards

Stack: React 19, Vite, Tailwind v4, Luminous Precision ([`web/DESIGN.md`](../../../web/DESIGN.md)).

## Folders (hybrid)

```text
web/src/
  ui/                 # atoms + molecules (design system only)
  features/<name>/    # pages, feature UI, feature hooks
  lib/                # tiny helpers
  api/                # backend clients + wire types
  index.css           # @theme tokens
```

- `ui` never imports `features`
- Features compose `ui` / `lib` / `api`

## Atoms & molecules

- **Atom:** one control (Button, Input, Badge, Text, Checkbox, Toggle)
- **Molecule:** atoms composed, still domain-agnostic
- Feature-specific UI stays under `features/<name>/`

Flat layout: atoms and molecules together in `src/ui/`.

## File order

1. **type**
2. **component**
3. **export**

## Styling

- Tailwind + theme tokens when present
- Differences = **variants**, not duplicate components
- Avoid per-component CSS files

## Reuse gate

1. Reusable present? **Use it**
2. Style different? **Plan for variant**
3. Else new atom/molecule or feature component

## Split when big

Subcomponent → hook → `ui` only if generic.

## Performance

No default `useMemo` / `useCallback`; split before memoize.
