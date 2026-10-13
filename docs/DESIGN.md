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

## Anti-Vibecoding Design Architecture

To avoid generic SaaS cliches, the web dashboard strictly adheres to the 30-point anti-vibecoding standard:

1. No Harsh Gradients: Solid functional tones with 1px structural borders.
2. No Lucide Icon Clutter: Minimalist inline SVGs and functional indicators.
3. No Pure White Backgrounds: Industrial neutral tones (#F8FAFC in light, #0B1120 in dark).
4. No Rainbow Coloring: Strict transit palette (Transit Navy, Signal Green, Signal Amber, Cobalt).
5. No Drop Shadows Everywhere: Crisp 1px structural borders without floating drop shadows.
6. No Three Feature Cards in a Row: Direct operational telemetry and real dynamic ticket rosters.
7. No Emojis: Strictly 0 emojis across the entire codebase, UI, and documentation.
8. No Liquid Glass Effect: Solid, opaque, performant UI panels without backdrop-blur filters.
9. No Em Dashes: Standard hyphens and colons used consistently.
10. No Inter / Geist / Space Grotesk Overuse: High-performance native system UI and monospace stack.
11. No Colored Stripes: Clean, border-delimited section containers.
12. No Fake Testimonials: 100% utility and developer tooling focus.
13. No Gimmicky Bento Grids: Structured Railway Operations Control Station layout.
14. No Fake Terminal Windows: Real, structured operational event log table with timestamps.
15. No "It is not X, it is Y" Copy: Direct, factual engineering labels.
16. No Checkmark Bullets: Clear data tables and status cards.
17. No Pricing Tiers: 100% free, MIT licensed open-source software.
18. Real Live Functionality: Live queries against real railway endpoints, not static mockups.
19. Crisp Corner Radius: Precision 6px industrial corner radius instead of bubbly soft curves.
20. No Purple and Black Schemes: Authentic transit slate, navy, and signaling colors.
21. Skeleton Loaders Included: Clear accessible skeleton state during data fetches.
22. No Radial Orbs or Blur Blobs: Zero ambient glow spheres or blurry backdrops.
23. No Dot Grids: Clean, solid, distraction-free backgrounds.
24. No Sparkle Icons: Clean technical iconography.
25. No Animated Arrows: Static, clear directional markers.
26. Terms of Service Included: Fully documented and accessible terms in UI and documentation.
27. Privacy Policy Included: Explicit local data isolation and zero telemetry collection disclosures.
28. No Excessive Hover Animations: Immediate, tactile button states without bouncy zoom effects.
29. No Neon Colors: Industry-standard transit signal tones.
30. High Contrast Badges: WCAG AA/AAA compliant contrast ratios on all ticket badges.
