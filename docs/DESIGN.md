# Product and Notification Design

This utility provides both scheduled 24/7 autonomous monitoring and a modern web dashboard.

## Notification Content
- Identify the PNR only as needed; logs should mask it to the final four digits.
- Include train number/name, journey date, passenger index, old status, and new status when available.
- Avoid passenger names unless a provider and user requirement explicitly need them.
- State that railway status is provider-reported and can change; final chart status is authoritative.

## Operational Behavior
- Missing configuration fails with a clear message.
- Fetch failure is visible and must not be interpreted as a status transition.
- Notification failure preserves the old baseline for retry.
- Dry-run mode must not call external notification services.

## Travel and Transit UI/UX Specification

The web dashboard implements the UI/UX Pro Max Travel and Transit design specification.

### Style Direction
- Primary Architecture: Bento Box Grid and Swiss Modernism 2.0 with subtle glassmorphic depth.
- Visual Language: Modular card-based hierarchy, rounded corners (16-24px), clean asymmetric balance, zero visual clutter, generous whitespace.
- Layout: Asymmetric responsive grid (12-column desktop, single-column mobile) with ticket-stub inspired cards displaying Origin to Destination, Train Number, Journey Date, and Coach/Berth info.

### Color Palette System (WCAG 4.5:1 Compliant)
- Primary Brand: Deep Rail / Transit Navy (#1E3A8A) and Sky Blue (#0EA5E9)
- Secondary Accent: Transit Amber (#EA580C / #F97316) for primary actions and active states
- Surface / Cards: Pure White (#FFFFFF) in Light Mode / Deep Slate (#0F172A) in Dark Mode
- Background: Soft Ice Blue (#EFF6FF) in Light Mode / Midnight (#020617) in Dark Mode
- Status Badges:
  - Confirmed (CNF): Emerald Green (#16A34A, background: #DCFCE7)
  - RAC / Partial: Amber Warning (#D97706, background: #FEF3C7)
  - Waiting List (WL / RLWL): Indigo / Blue (#2563EB, background: #DBEAFE)

### Typography
- Headings: Inter or Space Grotesk (700 bold, tracking-tight)
- Body and Labels: Inter (400/500, line-height: 1.5)
- Numerical and PNR Data: JetBrains Mono or SF Mono (tabular figures for alignment)

### Micro-Interactions and Motion
- Transitions: 150-200ms ease-out for hover scale (1.01x) and tab switches.
- Feedback: Clear loading skeletons, instant feedback spinners on refresh, visible focus rings.
- Anti-patterns Avoided: No raw unformatted text, no low-contrast gray-on-gray, no cluttered multi-level tables without badges, no hover-only interactions (minimum 44x44px touch targets).
