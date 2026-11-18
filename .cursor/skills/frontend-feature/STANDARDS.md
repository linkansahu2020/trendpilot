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
- **Molecule:** atoms composed, still domain-agnostic (e.g. search field + button)
- Feature-specific UI stays under `features/<name>/`, not `ui/`

Flat layout: keep atoms and molecules together in `src/ui/`.

## File order

1. **type** — props / variant types  
2. **component** — function  
3. **export** — named export (`export { X, type XProps }`)  
   Route pages may `export default`

## Styling

- Tailwind for layout and spacing
- Theme classes when the token exists (`bg-primary`, `text-muted`, …)
- Visual differences = **variants** on the same component (variant map), not a near-duplicate file
- Prefer no per-component CSS files; tokens live in `index.css`

## Reuse gate (before adding UI)

1. Reusable atom/molecule exists? **Use it**
2. Same role, different look? **Add a variant**
3. Truly new and generic? **New atom/molecule in `ui/`**
4. Feature-only? **New file under `features/<name>/`**

## When a file gets big

1. Extract feature subcomponent (presentational, props-in)
2. Extract feature hook (state / effects / handlers)
3. Promote to `ui/` only if design-system-generic (no feature knowledge)

## Performance

- No default `useMemo` / `useCallback`
- Use React 19 tools (`useEffectEvent`, `startTransition`) only when needed
- Prefer splitting over memoizing
