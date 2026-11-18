# TrendPilot web standards

Stack: React 19, Vite, Tailwind v4, Luminous Precision ([`web/DESIGN.md`](../../../web/DESIGN.md)).

## Folders (hybrid)

```text
web/src/
  ui/                 # atoms + molecules (flat — design system only)
  features/<name>/    # pages, feature UI, feature hooks
  lib/                # tiny helpers
  api/                # backend clients + wire types
  index.css           # @theme tokens
```

- `ui` never imports `features`
- Features compose `ui` / `lib` / `api`

## Atoms & molecules (flat `src/ui/`)

- **Atom:** one control (Button, Input, Badge, Text, Checkbox, Toggle)
- **Molecule:** atoms composed, still domain-agnostic (e.g. `SearchField`)
- Keep atoms and molecules side by side in `src/ui/` (no `atoms/` / `molecules/` subfolders)
- Feature-specific UI stays under `features/<name>/`, not `ui/`

## File order

1. **type** — props / variant types  
2. **component** — function body  
3. **export** — named export (`export { X, type XProps }`)  
   Route pages may `export default`

Example:

```tsx
type ButtonProps = {
  variant?: 'primary' | 'secondary' | 'ghost'
  children: React.ReactNode
}

function Button({ variant = 'primary', children, ...props }: ButtonProps) {
  return (
    <button className={buttonVariants[variant]} {...props}>
      {children}
    </button>
  )
}

export { Button, type ButtonProps }
```

## Styling

- Tailwind for layout and spacing
- Theme classes when the token exists (`bg-primary`, `text-muted` from `@theme` / DESIGN.md)
- Visual differences = **variants** on the same component (variant map), not copy-paste siblings
- Prefer no per-component CSS files; tokens live in `index.css`

## Reuse gate

1. Reusable atom/molecule exists? **Use it**
2. Same role, different look? **Add / plan a variant**
3. Truly new and generic? **New file in `ui/`**
4. Feature-only? **New file under `features/<name>/`**

## When a file gets big

1. Extract feature subcomponent (presentational, props-in)
2. Extract feature hook (state / effects / handlers)
3. Promote to `ui/` only if design-system-generic (no feature knowledge)

## Performance

- No default `useMemo` / `useCallback`
- Use React 19 tools (`useEffectEvent`, `startTransition`) only when needed
- Prefer splitting over memoizing
