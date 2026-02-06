# Phase 3 QA Checklist — April 10 Intelligence Surface

Manual QA runbook for Phase 3 features: meta comparison, format forecast, tech card insights, and confidence badges.

## Prerequisites

- [ ] Local development environment running (frontend + backend)
- [ ] Docker containers healthy (`docker ps` shows postgres, redis, tcgdex)
- [ ] Sample tournament data loaded (JP + International placements)
- [ ] Navigate to `http://localhost:3000` in browser
- [ ] Open browser DevTools console (check for errors throughout testing)
- [ ] Backend accessible at `http://localhost:8000` (verify `/health` endpoint)

## 1. Japan Page (`/meta/japan`)

### Page Load & Layout

- [ ] Navigate to `/meta/japan` from homepage or direct URL
- [ ] Page loads without errors (check console)
- [ ] BO1 context banner visible at top of page
- [ ] Banner explains Japanese BO1 tournament format (tie = double loss)
- [ ] Banner uses appropriate warning/info styling
- [ ] Page title displays "Japan Meta Analysis" or similar

### MetaDivergenceComparison Table

- [ ] Table renders with JP and International columns
- [ ] Table header shows "Archetype", "JP Share", "Global Share", "Divergence"
- [ ] At least 3-5 archetypes displayed (if sample data loaded)
- [ ] Archetype sprites render correctly (images load, no broken icons)
- [ ] Sprite images have alt text with archetype name
- [ ] JP Share column displays percentages (e.g., "15.2%")
- [ ] Global Share column displays percentages
- [ ] Divergence badges visible in dedicated column
- [ ] Divergence badges show positive/negative indicators (e.g., "+8.3%", "-4.1%")
- [ ] Divergence badges color-coded (green for positive JP divergence, red for negative)
- [ ] Tier badges present for each archetype (S/A/B/C tiers)
- [ ] Tier badges color-coded (S=purple/gold, A=blue, B=green, C=gray)
- [ ] Confidence badges visible for each row
- [ ] Confidence badges display icon + label (High/Medium/Low)

### Table Interactivity

- [ ] Click on archetype row → detail panel opens
- [ ] Detail panel shows archetype name and sprite
- [ ] Detail panel displays tech card insights section
- [ ] Click outside detail panel or close button → panel closes
- [ ] Hover over divergence badge → tooltip shows calculation details (if implemented)
- [ ] Table data sorted by JP share descending (top archetypes first)

### Confidence Badges (Table Context)

- [ ] High confidence badge: emerald background, CheckCircle icon
- [ ] Medium confidence badge: amber background, Info icon
- [ ] Low confidence badge: slate/gray background, AlertTriangle icon
- [ ] Hover over confidence badge → tooltip appears
- [ ] Tooltip shows sample size (e.g., "N=47 placements")
- [ ] Tooltip shows data freshness (e.g., "Updated 2d ago")
- [ ] Badge has `data-testid="confidence-badge"` attribute (inspect in DevTools)
- [ ] Tooltip disappears on mouse out

### Mobile/Responsive Behavior

- [ ] Resize browser to mobile width (375px, 414px)
- [ ] Table is horizontally scrollable (not cut off)
- [ ] Badges remain readable on small screens
- [ ] Sprites scale appropriately (not distorted)
- [ ] BO1 banner text wraps gracefully
- [ ] Detail panel fills screen on mobile (modal-style)
- [ ] Confidence badge tooltips appear correctly on tap (mobile)

### No Data State

- [ ] If no JP data available, table shows "No data available" message
- [ ] Message is centered and styled appropriately
- [ ] No broken table layout when empty
- [ ] BO1 banner still visible even with no data

## 2. Homepage FormatForecast

### Section Visibility

- [ ] Navigate to homepage (`/`)
- [ ] "Format Forecast" section visible below hero section
- [ ] Section uses SectionLabel component with "FORMAT FORECAST" text
- [ ] Section heading styled consistently with other homepage sections
- [ ] Section positioned between meta insights and recent tournaments (verify layout)

### Content Display

- [ ] Shows 3-5 JP archetypes (top divergent archetypes)
- [ ] Each archetype displays sprite image
- [ ] Sprites load correctly (no broken images)
- [ ] Archetype names displayed clearly
- [ ] Share bars visible for each archetype (dual-color bars)
- [ ] Rose/pink bar represents JP share
- [ ] Teal/cyan bar represents Global share
- [ ] Share bars proportional to percentage values
- [ ] Divergence badges visible next to each archetype
- [ ] Divergence badges show percentage difference (e.g., "+12.4%")
- [ ] Positive divergence badges styled green/emerald
- [ ] Negative divergence badges styled red/rose (if any)

### Navigation

- [ ] "Deep Dive: Full JP Analysis" link visible at bottom of section
- [ ] Link text clearly indicates navigation to Japan page
- [ ] Click link → navigates to `/meta/japan`
- [ ] Link styled as button or prominent CTA
- [ ] Link hover state visible (color change, underline, etc.)

### Loading State

- [ ] Refresh page and observe loading behavior
- [ ] ComparisonRowSkeleton components visible during load
- [ ] Skeleton shows 3-5 placeholder rows
- [ ] Skeleton animates (shimmer/pulse effect)
- [ ] Skeleton replaced by actual data when loaded
- [ ] No layout shift when transitioning from skeleton to data

### Empty State

- [ ] If no JP comparison data available, section hidden gracefully
- [ ] Section returns null (does not render at all)
- [ ] No broken layout or empty box on homepage
- [ ] Other homepage sections unaffected by missing forecast data

### Responsive Behavior

- [ ] Resize to tablet width (768px) → layout adapts
- [ ] Resize to mobile width (375px) → layout stacks or scrolls
- [ ] Share bars remain readable on small screens
- [ ] Sprites scale down appropriately
- [ ] "Deep Dive" link remains accessible on mobile

## 3. Tech Card Insights (Japan Page)

### Archetype Selector

- [ ] Archetype dropdown/selector visible on Japan page
- [ ] Dropdown populated with all JP archetypes from table
- [ ] Dropdown displays archetype names (not IDs)
- [ ] Default state: either first archetype selected or placeholder text
- [ ] Click dropdown → menu opens with full list
- [ ] Select archetype → dropdown updates to show selection
- [ ] Selection persists when closing/reopening dropdown

### Key Cards Display

- [ ] After selecting archetype, tech cards section renders
- [ ] Section title indicates selected archetype (e.g., "Tech Cards: Charizard ex")
- [ ] Key cards displayed as list or grid
- [ ] Each card shows card name
- [ ] Each card shows inclusion rate (e.g., "85% of decks")
- [ ] Each card shows average copies (e.g., "Avg: 2.3 copies")
- [ ] Card images or icons displayed (if available)
- [ ] Cards sorted by inclusion rate descending (most common first)

### Data Accuracy

- [ ] Inclusion rates are percentages between 0-100%
- [ ] Average copies are reasonable (typically 1-4 for most cards)
- [ ] Cards displayed match expected tech choices for archetype
- [ ] No duplicate cards in list
- [ ] If archetype has no tech data, shows "No tech card data available" message

### Interactivity

- [ ] Switch to different archetype → tech cards update immediately
- [ ] No stale data from previous archetype
- [ ] Loading state shows skeleton or spinner during data fetch
- [ ] Error fetching tech cards → graceful error message (not crash)

## 4. Confidence Badges (Global Verification)

### Badge Display

- [ ] High confidence: emerald/green background
- [ ] High confidence: CheckCircle icon visible
- [ ] High confidence: "High" text label or equivalent
- [ ] Medium confidence: amber/yellow background
- [ ] Medium confidence: Info icon visible
- [ ] Medium confidence: "Medium" text label
- [ ] Low confidence: slate/gray background
- [ ] Low confidence: AlertTriangle icon visible
- [ ] Low confidence: "Low" text label
- [ ] Icons render correctly (not broken or missing)
- [ ] Badge sizing consistent across all locations

### Tooltip Behavior

- [ ] Hover over High confidence badge → tooltip appears
- [ ] Tooltip shows sample size (e.g., "47 placements")
- [ ] Tooltip shows freshness (e.g., "Updated 2 days ago")
- [ ] Tooltip positioned near cursor (not off-screen)
- [ ] Tooltip remains visible while hovering
- [ ] Move mouse away → tooltip disappears
- [ ] Repeat for Medium confidence badge
- [ ] Repeat for Low confidence badge
- [ ] Tooltip styling readable (contrast, font size)

### Accessibility

- [ ] Badge has `data-testid="confidence-badge"` (inspect in DevTools)
- [ ] Badge has aria-label or title for screen readers
- [ ] Keyboard focus: Tab to badge → Enter/Space shows tooltip (if supported)
- [ ] Tooltip has proper ARIA role (tooltip, dialog, or popover)

### Context Verification

- [ ] MetaDivergenceComparison: each row has confidence badge
- [ ] FormatForecast: each archetype has confidence badge (if implemented)
- [ ] Archetype detail panels: confidence badge visible
- [ ] Badges appear in all relevant contexts (not missing anywhere)

## 5. Error States

### API Down / Network Errors

- [ ] Stop backend server (`docker-compose down` or `Ctrl+C`)
- [ ] Refresh Japan page → graceful error message
- [ ] Error message explains data unavailable (not technical stack trace)
- [ ] Page does not crash or show white screen
- [ ] Navigate to homepage → FormatForecast section hidden or shows error
- [ ] Restart backend → data loads correctly after recovery

### No JP Data Available

- [ ] Clear JP tournament data from database (or use empty dataset)
- [ ] Navigate to `/meta/japan`
- [ ] MetaDivergenceComparison shows "No data available" message
- [ ] Message styled consistently (centered, appropriate typography)
- [ ] No broken table headers or layout
- [ ] BO1 banner still visible
- [ ] No console errors related to missing data

### FormatForecast Empty State

- [ ] With no JP comparison data, navigate to homepage
- [ ] FormatForecast section returns null (completely hidden)
- [ ] No empty box or placeholder section visible
- [ ] Homepage layout flows naturally (no gaps)
- [ ] Other sections (hero, meta insights) unaffected
- [ ] No console errors about missing forecast data

### Malformed Data

- [ ] If API returns unexpected data shape (test in DevTools Network tab)
- [ ] Tables/components handle gracefully (no crash)
- [ ] Invalid percentage values → show "N/A" or default
- [ ] Missing sprites → show placeholder icon
- [ ] Missing confidence data → default badge or hide badge

## 6. Cross-Browser Spot Check

### Chrome (Desktop)

- [ ] Navigate to `/meta/japan` → all features work
- [ ] Navigate to `/` → FormatForecast renders
- [ ] Confidence badge tooltips appear on hover
- [ ] Sprites and images load
- [ ] No console errors
- [ ] Layout matches design specs

### Safari (Desktop)

- [ ] Repeat all Japan page checks
- [ ] Repeat all homepage checks
- [ ] Verify badge styling (Safari CSS differences)
- [ ] Verify tooltip positioning
- [ ] Check for any Safari-specific rendering issues

### Chrome Mobile (DevTools Device Emulation)

- [ ] Open DevTools → Toggle device toolbar
- [ ] Select iPhone 12 Pro or similar
- [ ] Navigate to `/meta/japan`
- [ ] Table scrolls horizontally
- [ ] Badges readable on small screen
- [ ] Tap archetype row → detail panel opens
- [ ] Tap confidence badge → tooltip appears (or tap-and-hold)
- [ ] Navigate to `/` → FormatForecast stacks correctly

### Safari Mobile (iOS Simulator or Real Device)

- [ ] Open Safari on iOS device or simulator
- [ ] Navigate to homepage → FormatForecast renders
- [ ] Navigate to Japan page → table interactive
- [ ] Tap interactions work (no double-tap required)
- [ ] Tooltips appear on tap (iOS touch behavior)
- [ ] No layout overflow or horizontal scroll issues

## 7. Performance & Optimization

### Initial Load Time

- [ ] Homepage loads in under 3 seconds (normal network)
- [ ] Japan page loads in under 3 seconds
- [ ] FormatForecast data fetches quickly (no long spinner)
- [ ] Images/sprites lazy-load or load efficiently

### Data Fetching

- [ ] Navigate to Japan page → check Network tab
- [ ] Verify API call to `/api/meta/japan/comparison` or similar
- [ ] Response time under 1 second (typical)
- [ ] No redundant API calls (same data fetched multiple times)
- [ ] Cached data used on revisit (if applicable)

### Rendering Performance

- [ ] Scroll MetaDivergenceComparison table → smooth scrolling
- [ ] Open/close archetype detail panels → no lag
- [ ] Hover over multiple badges rapidly → tooltips responsive
- [ ] No janky animations or layout thrashing

## 8. Data Integrity

### Meta Comparison Calculations

- [ ] Verify divergence math: JP Share - Global Share = Divergence
- [ ] Check a few rows manually against raw data
- [ ] Negative divergence displays with minus sign (e.g., "-3.2%")
- [ ] Positive divergence displays with plus sign (e.g., "+8.7%")
- [ ] Percentages sum to ~100% within JP and Global columns (allow rounding)

### Tech Card Data

- [ ] Inclusion rates between 0-100%
- [ ] Average copies reasonable (0.1 to 4.0 typical range)
- [ ] Cards match archetype (e.g., Charizard ex deck has Fire Energy)
- [ ] No nonsensical values (e.g., 500% inclusion, -2 average copies)

### Confidence Badge Logic

- [ ] High confidence: sample size >= 30 placements, data < 7 days old (verify logic)
- [ ] Medium confidence: sample size 10-29 or data 7-14 days old
- [ ] Low confidence: sample size < 10 or data > 14 days old
- [ ] Tooltip sample sizes match database counts (spot check)

## 9. Accessibility

### Keyboard Navigation

- [ ] Tab through Japan page → all interactive elements focusable
- [ ] Tab to archetype row → Enter opens detail panel
- [ ] Tab to confidence badge → tooltip accessible via keyboard (if supported)
- [ ] Tab to "Deep Dive" link → Enter navigates to Japan page
- [ ] Esc key closes open detail panels or tooltips

### Screen Reader

- [ ] Use screen reader (VoiceOver, NVDA) on Japan page
- [ ] Table structure announced correctly (headers, rows, cells)
- [ ] Confidence badges have accessible labels (not just icons)
- [ ] Sprites have alt text (archetype names)
- [ ] Divergence badges have descriptive text (not just "+8%")

### Color Contrast

- [ ] Tier badges meet WCAG AA contrast ratio (use DevTools Accessibility panel)
- [ ] Confidence badges meet contrast requirements
- [ ] Divergence badge text readable on colored backgrounds
- [ ] Text on share bars (if any) readable

## 10. Final Smoke Test

- [ ] Full user journey: Homepage → FormatForecast → Japan page → Archetype detail → Tech cards
- [ ] No console errors during entire flow
- [ ] No 404s or failed network requests
- [ ] All images loaded correctly
- [ ] Layout consistent across all pages
- [ ] Browser back button works correctly (no broken state)
- [ ] Refresh Japan page → state preserved (or reloads cleanly)
- [ ] Test with sample data + empty data scenarios
- [ ] Verify Phase 3 features integrate seamlessly with existing Phase 1-2 features

## Sign-Off

- [ ] All critical items checked and passing
- [ ] Known issues documented (create GitHub issues if needed)
- [ ] Screenshots captured for major features (optional)
- [ ] QA completed by: **\*\*\*\***\_**\*\*\*\*** Date: \***\*\_\*\***
- [ ] Ready for production deployment

---

## Notes & Issues Found

(Document any bugs, edge cases, or improvements discovered during testing)

-
-
- ***

  **Phase 3 Components Tested:**

- MetaDivergenceComparison (Japan page table)
- FormatForecast (homepage section)
- Tech card insights (archetype detail)
- Confidence badges (global system)
- BO1 context banner (Japan page)
