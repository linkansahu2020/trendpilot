# Design System: TrendPilot (Luminous Precision)
**Project ID:** 9239474572071020366

## 1. Visual Theme & Atmosphere
High-velocity clarity and product-led simplicity. An airy, light SaaS canvas:
generous whitespace, soft slate tints, and electric violet reserved for
conversion moments. Refined modern minimalism with delicate micro-glassmorphism—
hairline borders, whisper-soft ambient shadows, and frosted floating surfaces.
Chromatic weight is reserved for CTAs, success states, and live product demos;
UI chrome stays quiet so previews and value props breathe.

## 2. Color Palette & Roles
- **Electric Violet Primary (`#7C3AED` / `#630ed4`):** Primary CTAs, focus rings, metric callouts.
- **Indigo Companion (`#6366F1` / `#4648d4`):** Gradient partner to violet; secondary actions and hover depth.
- **Deep Obsidian Slate (`#020617` / on-surface `#151b2d`):** Headlines and high-contrast labels (never harsh pure black for body).
- **Muted Slate (`#64748B`):** Supporting body copy and telemetry text.
- **Ghost Border (`#E2E8F0`):** Cards, inputs, badges—tactile definition without weight.
- **Base Canvas (`#FFFFFF` / background `#faf8ff`):** Primary sections and max brightness.
- **Subtle Surface (`#F8FAFC`):** Alternate bands and secondary fills.
- **Elevated Surface (`#F1F5F9`):** Nested panels and subdued chrome.
- **Error Coral (`#ba1a1a`):** Destructive and validation errors.

## 3. Typography Rules
- **Display & headlines — Plus Jakarta Sans:** Weights 700–800, tight tracking
  (`-0.02em` to `-0.03em`) for striking authority against whitespace.
  Scale spans hero display (~64px desktop / ~38px mobile) down through
  headline-lg/md/sm.
- **Body, labels, captions — Inter:** Weights 400–600 for clinical screen
  legibility. Body copy prefers muted slate over pure black. Labels use
  slightly open tracking for scannability; captions are compact and medium weight.

## 4. Component Stylings
* **Buttons:** Pill-shaped. Primary = violet→indigo gradient, white label, soft
  violet ambient glow; hover scales slightly (~1.02). Secondary/ghost = white
  fill, hairline `#E2E8F0` border, slate label. Badge CTAs = micro-pills with
  violet-tint fill and violet text.
* **Cards/Containers:** White fill, 1px ghost border, generously rounded
  corners (~24–32px), soft ambient shadow. Featured cards may use a violet–indigo
  hairline gradient edge or faint glow plus a “Most Popular” chip.
* **Inputs/Forms:** White or near-white fields with `#E2E8F0` stroke; focus
  shifts border to `#7C3AED` with a soft violet outer ring. Hero conversion hub
  is a continuous pill bar with an embedded primary CTA. Checkboxes use soft
  6px corners and violet fill when selected; toggles are pill tracks that fill
  violet when active.
* **Badges:** Fully pill-shaped announcement chips with violet-tint border and
  muted slate copy; optional status dot.
* **Video preview frames:** Large rounded (~24px) frosted shells with ultra-soft
  elevation over the canvas.

## 5. Layout Principles
Centered content capped at **1200px**. Fluid grid: 12 columns desktop
(2rem gutters, 4rem outer margin), 8 on tablet, 4 on mobile (1.25rem margin).
Vertical section rhythm uses large breathing gaps (64–96px); within cards and
control clusters, use compact spacing (4–16px). Hierarchy comes from surface
tiers and whisper-soft shadows—not heavy drop shadows or dense chrome.
