---
name: TaskBridge AI
description: A bright, inspectable operations workshop for mapping work and keeping human authority visible.
colors:
  workshop-ink: "#10233f"
  workshop-ink-soft: "#526176"
  cool-paper: "#f9fbff"
  process-paper: "#edf3ff"
  workshop-table: "#dfe7f2"
  binder-cobalt: "#2856d7"
  binder-cobalt-deep: "#17388e"
  review-lime: "#d8ff5f"
  focus-orange: "#ff6b42"
  assist-aqua: "#73ddd0"
  exception-red: "#c83c36"
  rule-line: "#b8c5d6"
  field-white: "#ffffff"
typography:
  display:
    fontFamily: "Archivo, ui-sans-serif, sans-serif"
    fontSize: "clamp(1.9rem, 3vw, 3.7rem)"
    fontWeight: 760
    lineHeight: 0.98
    letterSpacing: "-0.035em"
  title:
    fontFamily: "Archivo, ui-sans-serif, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-0.02em"
  body:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "0.68rem"
    fontWeight: 850
    lineHeight: 1.2
    letterSpacing: "0.1em"
rounded:
  banner: "4px"
  button: "5px"
  field: "6px"
  lane: "10px"
  folder: "12px"
  shell: "14px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  control: "12px"
  md: "14px"
  lg: "18px"
  xl: "24px"
  section: "28px"
  canvas: "40px"
components:
  button-primary:
    backgroundColor: "{colors.binder-cobalt}"
    textColor: "{colors.field-white}"
    typography: "{typography.body}"
    rounded: "{rounded.button}"
    padding: "14px 18px"
  button-primary-hover:
    backgroundColor: "#1f49bd"
    textColor: "{colors.field-white}"
    rounded: "{rounded.button}"
    padding: "14px 18px"
  stage-active:
    backgroundColor: "{colors.review-lime}"
    textColor: "{colors.workshop-ink}"
    typography: "{typography.body}"
    padding: "13px 18px"
  scenario-active:
    backgroundColor: "{colors.binder-cobalt}"
    textColor: "{colors.field-white}"
    rounded: "{rounded.folder}"
    padding: "12px 18px 15px"
  field:
    backgroundColor: "{colors.field-white}"
    textColor: "{colors.workshop-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.field}"
    padding: "12px"
  workbench:
    backgroundColor: "{colors.cool-paper}"
    textColor: "{colors.workshop-ink}"
    rounded: "{rounded.shell}"
    padding: "clamp(20px, 3vw, 40px)"
---

# Design System: TaskBridge AI

## Overview

**Creative North Star: "The Operations Workshop Table"**

TaskBridge AI presents process improvement as a facilitated, physical workshop rather than a conventional AI dashboard. Cobalt binder tabs, numbered steps, cool paper, ruled lanes, stamps, notes, and review marks make the workflow feel movable and inspectable. The visual world is bright, pragmatic, and slightly tactile without becoming decorative stationery.

The work itself carries the hierarchy. Current and proposed process lanes dominate the primary view; the recommendation bridges them; evidence, exceptions, and human checkpoints remain attached to the decisions they qualify. AI assistance uses a supporting color and never visually outranks the human decision state.

The interface is dense enough for serious operational review but uses large headings, explicit labels, and strong color blocks to keep the path legible. Its tone is plain and procedural: every surface should quickly establish what work is under review, why an intervention was selected, and where people retain authority.

**Key Characteristics:**

- Bright workshop table with a subtle technical-dot ground.
- Deep cobalt binder navigation and folder-like scenario tabs.
- Cool, lightly ruled paper surfaces with restrained ambient depth.
- High-visibility lime reserved for active stages, human checkpoints, and operating constraints.
- Compact evidence labels paired with oversized, plain-language conclusions.
- Code-native geometry and typography rather than illustrative or generated decoration.

### Provenance and finish record

The visual system is implemented directly in `web/app/page.tsx` and `web/app/style.css`; the display face is the locally bundled Archivo variable font. There are no generated imagery, customer photographs, or outcome-proof assets in the interface. The desktop and mobile PNGs under `.impeccable/review/` are review evidence, not product-content assets.

The final finish-review disposition is **SHIP**. All findings are clear in the reviewed desktop and mobile surfaces. Preserve that statement as a dated implementation status, not as permission to bypass future review after visual or behavioral changes.

**The Inspectable Work Rule.** The process, evidence, and human authority must remain more visually prominent than technology branding or decoration.

## Colors

The palette combines institutional navy and cobalt with cool paper neutrals, then uses lime, aqua, and warm exception tones as precise operational annotations.

### Primary

- **Binder Cobalt:** The principal action and selection color for the active scenario folder, recommendation label, primary buttons, rule-mode markers, and measured pilot bars.
- **Binder Cobalt Deep:** The persistent navigation field and dark interactive foundation; it establishes the workshop's ordered structure without reading as a generic black sidebar.

### Secondary

- **Review Lime:** Marks the active workshop stage, human decision points, synthetic-demonstration banner, and stop-or-continue rules. Its brightness makes retained human authority unmistakable.
- **Assist Aqua:** Identifies AI suggestion steps. It is intentionally quieter than lime so assistance cannot be mistaken for final authority.

### Tertiary

- **Focus Orange:** Reserved for keyboard focus outlines and other urgent interaction visibility.
- **Exception Red:** Supports exception and blocked-state communication; use tinted red surfaces with dark red text for legibility rather than filling large regions with saturated red.

### Neutral

- **Workshop Ink:** Primary text, dark lane headers, authority strips, and evidence panels.
- **Workshop Ink Soft:** Supporting copy, metadata, descriptions, and low-emphasis navigation text.
- **Cool Paper:** The main workbench surface.
- **Process Paper:** A lightly blue-tinted surface for workflow lanes and evidence rails.
- **Workshop Table:** The page ground behind the binder-and-paper composition.
- **Rule Line:** Structural borders, dividers, and lane outlines.
- **Field White:** Inputs, teaching sheets, document cards, and inverse text against dark or cobalt surfaces.

**The Lime Means Control Rule.** Keep review lime rare and operational. Use it for the selected path, human authority, and explicit constraints—not as general decoration.

**The Same Facts Rule.** Semantic color may change how a fact is categorized, never the fact itself. Rules are cobalt, AI suggestions are aqua, human decisions are lime, and exceptions use warm warning tints.

## Typography

**Display Font:** Archivo Variable, locally bundled, with a sans-serif fallback.

**Body Font:** The native UI sans-serif stack: system UI, Apple system, BlinkMacSystemFont, Segoe UI, then sans-serif.

**Character:** Archivo gives the workshop titles compressed, decisive mass while the native body face keeps evidence and operational copy neutral and highly readable. The hierarchy is built through width, weight, and scale rather than multiple decorative families.

### Hierarchy

- **Display:** Heavy, tightly tracked Archivo with a compact line box. Use for one plain-language page conclusion, constrained to roughly 11–19 characters per line depending on the view.
- **Title:** Compact Archivo for the TaskBridge wordmark and other rare identity-level labels.
- **Body:** Native UI sans at a comfortable reading rhythm for explanations, scenario descriptions, and operational notes. Keep long explanatory measures near 56–62 characters.
- **Label:** Small, very bold, and often letter-spaced for workshop coordinates, table headings, banners, and evidence identifiers. Uppercase is reserved for system-status and wayfinding labels.
- **Data:** Use tabular numerals for stage counts, scores, timings, and measures so comparisons remain stable while values change.

**The One Conclusion Rule.** Give each workshop stage one dominant display heading. Supporting cards and notes use compact titles rather than competing display type.

**The Labels Are Coordinates Rule.** Small uppercase text is navigational metadata, not body copy; never set explanations or instructions in the compressed label style.

## Layout

The desktop composition is a capped workshop canvas with three layers: a full-width utility header, horizontally arranged scenario folders, and a two-part workbench. The main shell is limited to 1500px, with a 184px vertical stage rail beside a flexible paper surface. Workbench padding scales from 20px to 40px, and major content areas use purpose-built grids rather than interchangeable dashboard cards.

Spacing follows a compact 4px/8px base with recurring 12px, 14px, 18px, 24px, 28px, and 40px intervals. Use tighter values inside controls and evidence rows, medium values between related blocks, and the largest values to separate stage-level ideas. Process tiles remain visually connected by arrows and shared lanes.

At widths below 1050px, the stage rail moves above the workbench as a horizontally scrollable strip. Three-column decision, measure, and handoff layouts collapse to two columns, and supporting evidence can span the full width. At widths below 760px, the interface becomes one column: the header becomes two rows, stage controls form a visible four-column wrap, scenario folders remain horizontally scrollable, and process lanes stack vertically with downward arrows. Dense record tables may scroll within their own container, but the page itself must not overflow horizontally.

On mobile, preserve the sequence: scenario selection, complete stage navigation, workshop coordinate, stage conclusion, then the operational artifact. The stage controls must remain discoverable without opening a menu, and the initial workflow map must read as a vertical process rather than a squeezed desktop diagram.

Print removes application chrome, scenario folders, stage controls, navigation, and footer; the workbench becomes a shadowless document surface.

**The Lane Owns Its Overflow Rule.** When content cannot collapse safely, confine horizontal scrolling to the scenario strip or record table. Never create page-level horizontal overflow.

**The Path Stays Visible Rule.** Responsive changes may reflow or wrap the seven stages, but must not hide them behind an undisclosed control.

## Elevation & Depth

The system uses a hybrid of tonal layering and restrained ambient shadows. The dotted table sits behind a cool paper workbench; darker rails, colored folders, ruled lane surfaces, and narrow top bars provide most of the depth. Shadows are reserved for the large workbench, lifted teaching sheets, workshop notes, decision stamps, and the stacked handoff documents.

The main workbench uses a broad, cool ambient shadow. Notes and stamps use smaller, slightly firmer shadows plus sub-two-degree rotation to feel placed by hand. Cards that function as records use a very light shadow or no shadow, relying on borders and overlap instead. Hover elevation is limited to the primary run action; most controls communicate state through color and a one-pixel active press.

**The Paper Before Shadow Rule.** Establish hierarchy with surface tone, borders, tabs, and overlap first. Add a shadow only when an object is meant to feel placed above the workshop surface.

**The Controlled Imperfection Rule.** Slight rotation belongs only to note-, stamp-, or stacked-document metaphors. Remove rotation on narrow screens and never rotate primary reading surfaces.

## Shapes

The form language mixes practical rounded containers with crisp internal records. The overall shell has generous 14px outer corners; scenario folders use 12px top corners and a small raised tab; process lanes use 10px corners; fields use 6px corners; primary actions use 5px corners; the synthetic banner uses 4px corners. Evidence rows, tab controls, score tracks, and document records stay comparatively square.

Circular markers are reserved for ordered steps, legends, and scrollbar thumbs. The active desktop stage terminates in a triangular paper pointer, and folder tabs use a stepped silhouette. Borders use the cool structural line rather than decorative outlines.

**The Bounded Geometry Rule.** Rounded corners identify containing surfaces and controls; square edges identify records, evidence, and measurements.

## Components

### Buttons

- **Shape:** Compact, practical corners; primary actions use the 5px button radius, while rail and audience controls remain square within their containing system.
- **Primary:** Binder cobalt with white text, bold labeling, and 14px by 18px padding. Hover deepens the cobalt and may lift by one pixel; active state drops by one pixel.
- **Focus:** Every interactive control uses the global 3px focus-orange outline with a 3px offset. Focus must remain visible independently of hover or color fill.
- **Disabled:** Use a cool gray fill, darker gray text, and an appropriate non-action cursor. Disabled state must not be communicated through opacity alone.
- **Secondary:** Workshop navigation buttons are transparent with a cobalt-gray border; hover inverts to cobalt and white. Preserve clear disabled previous/next states at path boundaries.

### Scenario Folders

- **Style:** A horizontally scrollable row of file-tab buttons with department metadata above the scenario name. The raised tab is part of the folder silhouette, not a separate decoration.
- **State:** The selected scenario is cobalt with white text; unselected folders use muted blue paper. Selection is expressed with `aria-pressed`, and changing scenarios returns the workshop to the map stage.

### Stage Rail

- **Style:** Seven numbered steps on a deep cobalt field. The active step reverses to review lime with workshop-ink text and, on desktop, points into the workbench.
- **State:** Use `aria-current="step"` for the active stage. Hover adds a restrained light veil to inactive items; active hover remains lime. On mobile, all seven stages wrap visibly across two rows and secondary labels disappear to protect scanability.

### Cards / Containers

- **Corner Style:** Use the radius hierarchy described in Shapes; do not apply one universal radius to every surface.
- **Background:** Workbench and workflow surfaces use cool paper tones; evidence and authority panels may invert to workshop ink; lime surfaces communicate checkpoints and operating rules.
- **Shadow Strategy:** Follow the Paper Before Shadow Rule. Most process and evidence containers use borders, not shadows.
- **Internal Padding:** Compact rows use 10–16px; notes and supporting panels use 23–28px; major reading surfaces use fluid 26–56px padding.

### Inputs / Fields

- **Style:** White fill, workshop-ink text, a single cool blue-gray border, and gently rounded 6px corners. Text inputs are 46px high; text areas begin at 100px and may resize vertically.
- **Focus:** Use the shared focus-orange outline. Do not remove the native interaction affordance without replacing it with an equally visible state.
- **Read-only:** Read-only workshop answers should still look legible and selectable, not disabled; the presentation communicates captured evidence rather than unavailable controls.

### Process Lanes

- **Style:** Pair a dark or lime lane label with a lightly tinted ruled process surface. Use numbered circular markers, compact actor/time metadata, and directional arrows to preserve sequence.
- **Modes:** Rule markers use cobalt, AI suggestions use aqua, and human decisions use lime with a darker edge. Friction and authority annotations use warm tinted tags.
- **Responsive Behavior:** Horizontal four-step lanes become vertical sequences below 760px, and arrows rotate downward. The content must remain fully readable without page zoom.

### Evidence, Results, and Status

- **Style:** Evidence identifiers and table headers use the label hierarchy; values use stronger weight and tabular numerals. Results appear in ledgers and bars, not ornamental KPI cards.
- **Truthfulness:** Always label fixtures, synthetic outcomes, disabled external actions, and unsupported claims explicitly. Status colors supplement the words; they never replace them.

### Interaction and Accessibility

- Use native buttons and links for actions and navigation. Preserve the skip link to the workshop and the global `:focus-visible` treatment.
- Audience selection follows the tab pattern with `tablist`, `tab`, and `tabpanel` roles, roving tab stops, Left/Right arrow navigation, and Home/End support.
- Synthetic-pilot progress uses `aria-busy` and a polite live region. The visible waiting treatment combines copy with opacity and subtle blur.
- SVG marks and arrows are decorative and remain hidden from assistive technology; meaningful states are expressed in adjacent text.
- Honor reduced-motion preferences by effectively removing animation and transition duration. Motion is supportive feedback only and never required to understand state.
- Maintain WCAG AA contrast, keyboard access, visible focus, and touch targets that remain practical in the compact mobile rail.

## Do's and Don'ts

### Do:

- **Do** let the process map, evidence, and decision authority carry each stage's visual hierarchy.
- **Do** reserve review lime for selected path, human checkpoints, and explicit operating constraints.
- **Do** state synthetic data, unsupported claims, and disabled external actions in visible text.
- **Do** keep desktop and mobile stage navigation continuously visible and keyboard operable.
- **Do** use semantic HTML and ARIA state that matches the visible selected, busy, disabled, and tab states.
- **Do** contain necessary overflow inside the scenario strip or data table and verify the page itself remains within the viewport.
- **Do** rerun desktop and mobile finish review after meaningful visual or behavioral changes; the current recorded result is **SHIP — all findings clear**.

### Don't:

- **Don't** turn TaskBridge into a generic dark AI dashboard, card mosaic, chat interface, or model-centric control panel.
- **Don't** let the AI-suggestion treatment become brighter or more prominent than the human-decision treatment.
- **Don't** use generated imagery, customer-like proof, or unlabeled outcome figures to imply real deployment evidence.
- **Don't** spread lime, orange, or exception colors across decorative backgrounds; each has a narrow semantic job.
- **Don't** hide the stage path on mobile or compress desktop process lanes until labels become illegible.
- **Don't** apply shadows, rounded corners, rotations, or uppercase microtype indiscriminately; each encodes a specific material or informational role.
- **Don't** rely on color, motion, hover, or visual position alone to communicate state or sequence.
