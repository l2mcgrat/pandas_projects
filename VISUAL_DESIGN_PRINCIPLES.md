# Visual & Interactive Analytics Design Principles (`liammspandasprojects.org`)

This document codifies the visual, biomechanical, and interactive business-intelligence (PowerBI-style) standards applied across all dashboards, empirical studies, and notebook reflections on `liammspandasprojects.org`.

---

## 1. Universal Unit & Axis Labeling
1. **Explicit Units Everywhere**: Every chart title, axis tick, bar data label, KPI card, and tooltip must state its physical, financial, or statistical unit explicitly:
   - **Weightlifting**: `lb` (load / mechanical volume), `reps` (repetitions), `kcal` (biomechanical energy expended), `m` (range of motion).
   - **Running**: `min/km` (pace), `m/s` (velocity), `km` or `m` (distance), `s` (interval time / spread), `kcal` (running energy expenditure).
   - **Swimming**: `m` (metres), `yd` (yards, converted at $1\text{ yd} = 0.9144\text{ m}$), `s` (50 m split time), `kcal` (swimming energy expenditure).
   - **Sleep & Dreams**: `h` (hours slept), `dreams` (logged dream count), VADER sentiment polarity `[-1.0, +1.0]`.
   - **Diet & Calorie Tracking**: `kcal` / `kcal/day` (expenditure, consumption, net deficit), `g` (protein / fat / carbohydrate macros), `lb` (estimated tissue mass delta at $3{,}500\text{ kcal/lb}$).
   - **Empirical Studies**:
     - `ST-01` (AI Iceberg): `% of wage bill`, `$B` (billions USD), $\Lambda\times$ (submerged-to-surface multiplier).
     - `ST-02` (Alberta Referendum): `% ballot share`, `pp` (percentage-point margin).
     - `ST-05` (Sodium Battery): `Wh/kg` (gravimetric density), `Wh/L` (volumetric density), `$/kWh` (pack/cell cost floor), `% capacity at −20 °C`, `cycles`.
     - `ST-06` (Gas Price Collusion): `$/L` and `c/L` (pump price, wholesale TGP, tax, ex-tax markup), $\delta$ and $\delta^*$ (discount factors), `%` (CR4 concentration & Lerner index).
     - `ST-08` (AI Cost & Compute Economics): `$/1M tokens` (blended inference price), `FLOPs` / `$M` (training compute & capex), `Wh/query` (inference energy), `%` (annualized price deflation rate).
   - **Map & Site % (`Completion/index.html`)**: `%` (completion share), `leaves` (out of 216), `words` (prose volume), `formulae` (LaTeX equation count).

---

## 2. Visual Hierarchy: Charts ON TOP of Cards on Study Pages
- On every Study page (`ST-01`, `ST-02`, `ST-05`, `ST-06`, `ST-08`, and dynamically executed Workbench studies), the **primary empirical SVG visual chart is rendered ON TOP of (above) the KPI & Parameter Inspector cards**.
- Every Study KPI card and Parameter Inspector box includes a compact hover-on-web / tap-on-mobile definition popup (`data-kpi-card`) with a direct link to its corresponding **Mental Map** section (`🧠 Mental Map: § ... ↗`).
- Standalone owner reflection pages (`Completion/index.html`, `Traffic/index.html`, `Updates/index.html`) use plain, self-explanatory KPI cards without tooltip popups.

---

## 3. Dynamic Card Scaling & Zero Text Clipping (Web & Mobile)
- **Container-Query Typography (`cqi`)**: Metric cards (`.sports-metric`, `.metric-card`, `.study-reg-kpis > div`) use `container-type: inline-size` with `min-width: 0` and `font-size: clamp(1.2rem, min(9.2cqi, 2.25rem), 2.4rem)` on primary values (`strong`) so multi-part values like `84 / 216 (38.9%)` or `$0.14 / 1M tokens` never overflow card boundaries at any zoom level or viewport width.
- **Generous SVG Right-Hand Margins**: Horizontal bar charts reserve at least `210–240 px` on the right of the `900 px` SVG `viewBox` (`left + width <= 685`) so value + unit annotations never clip at 100% zoom.

---

## 4. PowerBI-Style Interactive Controls (`visuals-bi.js`)
Every visual dashboard supports 5 core interactive capabilities:

### 4.1 Sliders (Time Window & Threshold Filtering)
- **Time Range Slider**: Dual range controls (`Start Date` → `End Date`) to zoom into any historical sub-window as logs grow.
- **Repetition / Value Threshold Slider**: In Weightlifting, filters sets and exercises by minimum repetitions (`1` to `30` reps). At the lowest drilldown level (Workout & Set Clustered Column), sets below the rep threshold are dynamically filtered out.

### 4.2 Multi-Select Slicers & Visual Bucketing
- **Weightlifting Muscle Group Slicer**: Multi-select pills for **`Chest`**, **`Back`**, **`Shoulders`**, **`Triceps`**, **`Biceps`**, **`Abs`**, and **`Legs`**.
- When multiple muscle groups are selected, both the main chart and the exercise progression multiples filter to those groups, and the small multiples are **visually bucketed under color-coded muscle group headers** so each anatomical group is immediately distinguishable.

### 4.3 Hierarchy Drilldown (`Year → Fiscal Qtr → Month → Week → Day → Granular Set/Item`)
- Users can step up (`↑ Drill Up`) or down (`↓ Drill Down`) or click any bar to traverse:
  1. **Year** (`2026`)
  2. **Fiscal Quarter** (`Q1 (Jan–Mar)`, `Q2 (Apr–Jun)`, `Q3 (Jul–Sep)`, `Q4 (Oct–Dec)`)
  3. **Month** (`Sep 2026`, `Oct 2026`, ...)
  4. **Week** (`ISO Week / Monday start`)
  5. **Day / Session** (`2026-10-25`)
  6. **Granular Workout & Set Clustered Column** (each exercise in that workout plotted as a cluster of individual set bars showing weight in `lb` or energy in `kcal`, filtered by the Min Reps slider).

### 4.4 Drillout (Period Expansion & Biomechanical Energy Conversion)
- Clicking **Drillout** expands grouped periods (e.g., expanding `Q4` into `Oct / Nov / Dec` or `Q2` into `Apr / May / Jun`) and switches the primary y-axis from raw mechanical volume (`lb`) to **Average / Total Energy Expended (`kcal`)**.
- **190 cm Wingspan Biomechanical Energy Model**:
  - Given wingspan $W = 1.90\text{ m}$, single-arm length is $L_{\text{arm}} \approx 0.38\,W = 0.722\text{ m}$.
  - Vertical displacement per repetition ($d_{\text{ROM}}$) by movement class:
    - Compound Presses, Rows, Pulldowns & Pullups: $d_{\text{ROM}} = 0.32\,W \approx 0.608\text{ m}$
    - Lower-Body Squats, Deadlifts & Leg Presses: $d_{\text{ROM}} = 0.34\,W \approx 0.646\text{ m}$
    - Isolation Curls, Tricep Extensions & Deltoid Raises: $d_{\text{ROM}} = 0.24\,W \approx 0.456\text{ m}$
    - Core Crunches, Situps, Leg Raises & Back Extensions: $d_{\text{ROM}} = 0.18\,W \approx 0.342\text{ m}$
  - Effective load mass $m_{\text{eff}}$ (in $\text{kg}$, where $1\text{ lb} = 0.453592\text{ kg}$):
    - Loaded lifts: $m_{\text{eff}} = 0.453592 \times w_{\text{lbs}} + m_{\text{limb}}$ ($m_{\text{limb}} \approx 8\text{ kg}$)
    - Assisted lifts (Pullups / Dips, assuming $m_{\text{body}} \approx 88\text{ kg}$): $m_{\text{eff}} = \max(18.0,\; 88.0 - 0.453592 \times w_{\text{assist, lbs}})$
    - Bodyweight lifts: $m_{\text{eff}} \approx 45.0\text{ kg}$ (pushups/dips/extensions) or $28.0\text{ kg}$ (core/leg raises)
  - Mechanical work (concentric + eccentric control factor $\gamma = 1.35$, $g = 9.80665\text{ m/s}^2$) converted at human anaerobic muscular efficiency $\eta_{\text{met}} = 0.18$ ($4{,}184\text{ J/kcal}$) plus active inter-set stabilization/postural cost ($2.2\text{ kcal/set}$):
    $$E_{\text{set, kcal}} = \frac{\text{reps} \times m_{\text{eff}} \times g \times d_{\text{ROM}} \times 1.35}{4184 \times 0.18} + 2.2$$

### 4.5 Dynamic Report-Table Tooltips & Drillthrough
- **Report-Table Tooltip**: Hovering (web) or tapping (mobile) any bar/point renders a structured mini-table for the exact time range encapsulated by that column (listing the constituent dates, splits/categories, exercises, sets, volume `lb`, and energy `kcal`).
- **Drillthrough**: Clicking **↗ Drillthrough to Table** filters the page's underlying HTML table to the exact records belonging to that bar and scrolls smoothly to inspect them.
