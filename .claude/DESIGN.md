# DESIGN — the brand contract

> The LAW for anything visual or motion on this project. One file, one fixed schema.
> Every visual artifact (a page, a component, a color, a duration) reads it; the design
> reviewer (`art-director`) grades fidelity to it. If a rule here is broken, the design
> gate FAILs, whatever the taste.
>
> **Filled once at scoping**, by distilling the client's brand (an existing site, a logo,
> a brand book, or a framing conversation) into the sections below. Keep it CONCRETE:
> hex values, pixel/rem scales, named durations and easings, not adjectives. A section
> you cannot fill yet says "TBD" explicitly, never a vague guess.
>
> The section HEADINGS are fixed (the reviewer and any tool rely on them). The CONTENT
> is per project. Delete this quote block once filled.

## 1. Brand meaning

<!-- One paragraph: what the brand stands for, the feeling a screen should leave, how it
differs from its look-alikes. The "why" every visual choice below serves. -->

TBD

## 2. Palette

Tokens (the ONLY colors allowed; anything off this table is off-brand):

| Token | Hex | Role |
|---|---|---|
| `TBD` | `#000000` | TBD |

Usage rules:
- <!-- Which color carries meaning where; accent discipline (a color that must stay rare
  or must never be a large fill); reversed/dark sections; gradients allowed or banned. -->
- **Accessibility (non-negotiable):** text/background contrast meets **WCAG AA** (4.5:1 for
  small text, 3:1 for large/UI). A token that fails AA in a context has a darker/lighter
  declension named here for that context.

## 3. Typography

- **Families** (max 2–3): `TBD` — <!-- role of each: display, body, mono/meta -->
- **Scale**: `TBD` — <!-- the type sizes and their level (h1/h2/lead/body/caption) -->
- **Register rules**: <!-- readable line length, line-height, when each family/weight is used -->

## 4. Spacing & rhythm

- **Unit / scale**: `TBD` — <!-- the spacing scale everything snaps to -->
- **Section rhythm**: <!-- vertical rhythm between sections, reading-column max width, grid -->

## 5. Motion grammar

The movement language. Motion serves meaning; restraint is the default.

- **Durations**: `TBD` — <!-- named tokens: micro (hovers), short, entrance -->
- **Easings**: `TBD` — <!-- named curves; the house feel (calm, snappy, editorial…) -->
- **Allowed**: <!-- the sanctioned motions (scroll reveals, micro-interactions, parallax %) -->
- **Banned**: <!-- overshoot, aggressive ease-in, stacked effects, wow-sequences… whatever is off-brand -->
- **Reduced motion**: `prefers-reduced-motion` freezes animation to a complete, static screen.

## 6. Voice

- **Tone**: <!-- how copy sounds; the register -->
- **Address**: <!-- how the reader is addressed; person; formality -->
- **Copy rules**: <!-- typographic conventions, banned characters, language parity if multilingual -->

## 7. Don't

<!-- The explicit anti-patterns. The fastest fidelity check: if a screen does any of these,
it FAILs regardless of how it otherwise looks. -->

- TBD
