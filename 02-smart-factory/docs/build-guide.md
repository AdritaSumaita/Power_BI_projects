# Build guide — Smart Textile Factory: OEE & Downtime

A complete Power BI project. Assumes you have built one before — if not, everything here is explained, just more briefly than a first-time guide.

**What you will build:** a two-page report on a star schema, answering *which machine and shift should the next improvement week target, and is the problem the equipment or the way it is being run?*

**Time:** about 2–3 hours. Stop after any step.

---

## Progress tracker

- [ ] **Step 1** — Setup
- [ ] **Step 2** — Load the data
- [ ] **Step 3** — Check types
- [ ] **Step 4** — Build the relationships
- [ ] **Step 5** — Build the date table
- [ ] **Step 6** — Write the measures
- [ ] **Step 7** — Page 1: Plant Overview
- [ ] **Step 8** — Page 2: Loss Analysis
- [ ] **Step 9** — Screenshots and publish

Every step ends with a ✅ **Check**. Do not move past a failing one — a mistake caught where it happens takes a minute; found three steps later it can take an hour.

---

## Step 1 — Setup

1. Open **Power BI Desktop** (Desktop, not the browser version)
2. **File → Options and settings → Options**
3. **GLOBAL → Data Load** → untick **Auto date/time for new files**
4. **CURRENT FILE → Data Load** → untick **Auto date/time**
5. Close and reopen

Both settings exist and beginners usually find only the first. Left on, Power BI builds a hidden date table behind every date column — here that would be several invisible tables and date logic scattered where you cannot see it.

✅ **Check:** reopen Options — both boxes unticked.

---

## Step 2 — Load the data

**Home → Get data → Text/CSV**, once per file, clicking **Load** each time:

```
FactProduction.csv    FactDowntime.csv
DimMachine.csv        DimShift.csv        DimReason.csv
```

Five files, five tables. Everything in `data/` is used.

✅ **Check:**

| Table | Rows |
|---|---|
| `FactProduction` | **19,152** |
| `FactDowntime` | **53,634** |
| `DimMachine` | **12** |

> If a table shows `Column1`, `Column2`… → **Home → Transform data** → select it → **Home → Use First Row as Headers** → Close & Apply.

---

## Step 3 — Check types

**Home → Transform data.** Click each query and check the icon in every column header.

| Column | Type |
|---|---|
| `…Key` | `123` Whole Number |
| `Date` | 📅 Date |
| `Planned Minutes`, `Run Minutes`, `Ideal Minutes`, `Downtime Minutes` | `1.2` Decimal |
| `Units Produced`, `Units Good`, `Stop Count`, `Install Year`, `Shift Start Hour` | `123` Whole Number |
| `Is Planned` | True/False |
| everything else | Text |

**There is no cleaning to do.** The data is clean by design.

### 📸 Capture before leaving

With `FactProduction` selected, capture the window so the **Applied Steps** panel on the right is visible → `screenshots/02-power-query-steps.png`

**Home → Close & Apply.**

✅ **Check:** row counts unchanged from Step 2.

---

## Step 4 — Build the relationships

**Home → Manage relationships**

1. Select every existing row → **Delete**. Power BI's guesses are a starting point, not an answer.
2. **New relationship** ×6. **Fact table always on top:**

| # | Top (many) | Column | Bottom (one) | Column |
|---|---|---|---|---|
| 1 | `FactProduction` | `MachineKey` | `DimMachine` | `MachineKey` |
| 2 | `FactProduction` | `ShiftKey` | `DimShift` | `ShiftKey` |
| 3 | `FactDowntime` | `MachineKey` | `DimMachine` | `MachineKey` |
| 4 | `FactDowntime` | `ShiftKey` | `DimShift` | `ShiftKey` |
| 5 | `FactDowntime` | `ReasonKey` | `DimReason` | `ReasonKey` |

Every one: **Many to one (\*:1)** · **Single** · **Active**.

`DimMachine` and `DimShift` each feed **both** fact tables. That is the *conformed dimension* pattern, and it is what lets one machine slicer filter production and downtime together.

✅ **Check:** 5 relationships, all `*—◄—1`, all Active.

---

## Step 5 — Build the date table

### 5a. Create it

**Home → New table**, paste, Enter:

```dax
DimDate =
ADDCOLUMNS(
    CALENDAR(DATE(2025,1,1), DATE(2026,6,30)),
    "Year",         YEAR([Date]),
    "Month Number", MONTH([Date]),
    "Month",        FORMAT([Date], "mmm"),
    "Year Month",   FORMAT([Date], "yyyy-mm"),
    "Quarter",      YEAR([Date]) & " Q" & QUARTER([Date])
)
```

### 5b. Sort the months ⚠️

Click **`Month`** → **Column tools → Sort by column → `Month Number`**

Skip this and every chart reads Apr, Aug, Dec… alphabetically.

### 5c. Mark it

Right-click **`DimDate`** → **Mark as date table** → column `Date`

### 5d. Join it

**Manage relationships → New relationship**, twice, `DimDate` on the **bottom**:

| Top (many) | Column | Bottom (one) | Column |
|---|---|---|---|
| `FactProduction` | `Date` | `DimDate` | `Date` |
| `FactDowntime` | `Date` | `DimDate` | `Date` |

Both stay **Active** — they point at two different fact tables, so there is no ambiguity.

✅ **Check:** `DimDate` = **546 rows**. Relationships total **7**, all Active.

### 5e. 📸 Screenshot the model

**Model view** → arrange with the two facts in the centre, dimensions around them, no crossing lines → `screenshots/01-data-model.png`

---

## Step 6 — Write the measures

**Home → Enter data** → name it `_Measures` → **Load** → right-click `Column1` → **Hide**.

> Hide the **column**, not the table. Hiding the table removes every measure from the Data pane and makes your DAX invisible.

For each: click `_Measures` → **Home → New measure** → `Ctrl+A` → paste **the whole line including the name** → Enter.

### The five raw sums

```dax
Planned Minutes = SUM(FactProduction[Planned Minutes])
```
```dax
Run Minutes = SUM(FactProduction[Run Minutes])
```
```dax
Ideal Minutes = SUM(FactProduction[Ideal Minutes])
```
```dax
Units Produced = SUM(FactProduction[Units Produced])
```
```dax
Units Good = SUM(FactProduction[Units Good])
```

### The three OEE components

Each answers a different question and belongs to a different person.

```dax
Availability % = DIVIDE([Run Minutes], [Planned Minutes])
```
*Of the time we planned to run, how much did we actually run?* — **Maintenance**

```dax
Performance % = DIVIDE([Ideal Minutes], [Run Minutes])
```
*While running, how close to design speed were we?* — **Production**

```dax
Quality % = DIVIDE([Units Good], [Units Produced])
```
*Of what we made, how much was sellable?* — **QA**

### OEE itself

```dax
OEE % = [Availability %] * [Performance %] * [Quality %]
```

That multiplication is why OEE is unforgiving. Three components at 90% give 72.9%, not 90% — losses compound.

```dax
OEE Gap to World Class = [OEE %] - 0.85
```

### Downtime

```dax
Downtime Minutes = SUM(FactDowntime[Downtime Minutes])
```
```dax
Stop Count = SUM(FactDowntime[Stop Count])
```
```dax
Unplanned Downtime Minutes =
CALCULATE([Downtime Minutes], DimReason[Is Planned] = FALSE())
```
```dax
Downtime Cost = DIVIDE([Unplanned Downtime Minutes], 60) * 180
```
```dax
Avg Changeover Minutes =
CALCULATE(
    AVERAGE(FactDowntime[Downtime Minutes]),
    DimReason[Reason] = "Changeover"
)
```

> ### Why an average and not a sum
>
> The claim on page 2 is that changeovers **take longer** on night shift. Total changeover minutes cannot show that, because night shift has more stoppages everywhere — the total mixes *how often* with *how long* and blurs the comparison.
>
> Averaging the minutes per stoppage isolates duration. It is the difference between a clean 2.2× on Finishing against 1.0× everywhere else, and a muddy 2.5× against 1.1–1.2×.
>
> **A finding is only as good as the measure that carries it.**

`Downtime Cost` assumes **€180 per hour** of lost contribution. That is an assumption, not a fact — it is recorded as one in the KPI catalogue. Being able to say which of your numbers are assumptions is worth more than the number.

### The measure that does the most work

```dax
Biggest Loss =
VAR A = [Availability %]
VAR P = [Performance %]
VAR Q = [Quality %]
VAR Lowest = MIN(A, MIN(P, Q))
RETURN
IF(
    Lowest = A, "Availability - stoppages",
    IF(Lowest = P, "Performance - speed loss", "Quality - defects")
)
```

One card, and a supervisor knows which of three problems they have. Work out which of the three components is smallest, then name it.

> ### ⚠️ Text measures: create the visual **first**
>
> For every numeric measure the usual order works — click empty canvas, tick the field, then choose the visual type. **For a measure that returns text it does not.** Power BI picks the visual for you when you tick a field with nothing selected, and its choice will not render the string.
>
> Do it the other way round:
>
> 1. Click **empty canvas**
> 2. Click the **Card** icon in Visualizations — you get an empty card
> 3. **Then** tick `Biggest Loss`
>
> A blank card where a text measure should be is almost always this, not the DAX.

### Formatting

Select each → **Measure tools** ribbon:

| Measures | Format |
|---|---|
| `Availability %`, `Performance %`, `Quality %`, `OEE %`, `OEE Gap to World Class` | Percentage, 1 decimal |
| `Downtime Cost` | Currency €, 0 decimals |
| everything else numeric | Whole number, comma separator |

✅ **Check — ground truth from the source data:**

| Measure | Expected |
|---|---|
| `Availability %` | **84.2%** |
| `Performance %` | **85.7%** |
| `Quality %` | **98.4%** |
| `OEE %` | **71.0%** |
| `Planned Minutes` | **9,149,164** |
| `Run Minutes` | **7,704,010** |
| `Units Produced` | **25,746,216** |
| `Downtime Minutes` | **1,489,086** |

`Availability % × Performance % × Quality %` must reconcile exactly to `OEE %`. If it does not, one of the three is pointing at the wrong column.

> **To make separate cards:** click **empty canvas** to deselect → tick **one** field → click the **Card** icon. Ticking while a visual is selected adds the field *into* that visual.

---

## Step 7 — Page 1: Plant Overview

Rename the page **Plant Overview**. Title text box:

> **Is the plant running at the standard it should?**

| Visual | Type | Fields |
|---|---|---|
| KPI row | 5 × **Card** | `OEE %` · `Availability %` · `Performance %` · `Quality %` · `Biggest Loss` |
| OEE over time | **Line chart** | X: `DimDate[Year Month]` · Y: `OEE %` |
| By line | **Bar chart** | Y: `DimMachine[Production Line]` · X: `OEE %` |
| Downtime reasons | **Bar chart** | Y: `DimReason[Reason]` · X: `Downtime Minutes` |

**Sorting matters on two of these:**

- Line chart → `⋯` → **Sort axis → Year Month** → then `⋯` → **Sort ascending**. Power BI defaults to sorting by the measure, which scrambles a time series.
- Both bar charts → sort by the **measure**, descending.

**Add an 85% reference line** to the OEE chart: select it → **Format visual → Analytics → Y-axis constant line** → Value `0.85` → name it *World class*.

✅ **Check:**

- `OEE %` reads **71.0%**, `Biggest Loss` says **Availability — stoppages**
- Weaving is the lowest line
- The downtime bar chart is dominated by **Changeover**, then Mechanical Failure, then Yarn Break — the top three are about two thirds of all stop time. **That is your Pareto**: aim the improvement week at the top of this chart, not at the bottom.

📸 **View → Page view → Fit to page**, collapse the right-hand panes → `screenshots/03-page-overview.png`

---

## Step 8 — Page 2: Loss Analysis

New page, rename **Loss Analysis**. Title:

> **Which machine and shift — and is it equipment or process?**

| Visual | Type | Fields |
|---|---|---|
| **The heatmap** | **Matrix** | Rows: `DimMachine[Machine ID]` · Columns: `DimShift[Shift Name]` · Values: `OEE %` |
| **Changeover duration** | **Clustered bar** | Y: `DimMachine[Production Line]` · X: **`Avg Changeover Minutes`** · Legend: `DimShift[Shift Name]` |
| Failing asset | **Line chart** | X: `DimDate[Year Month]` · Y: `OEE %` · Legend: `DimMachine[Machine ID]` — filter to `WEV-03` and `WEV-05` |
| Stoppage frequency | **Bar chart** | Y: `Machine ID` · X: `Stop Count` |

### The changeover chart carries finding 2 — use the right measure

Use **`Avg Changeover Minutes`**, not `Downtime Minutes`. No visual filter is needed; the measure carries the `Changeover` filter itself, which is one fewer thing to forget.

Rename the title to state the claim: **Format → General → Title → Text** → `Average changeover duration by line and shift`

✅ **Expected:**

| Line | Morning | Evening | Night | Ratio |
|---|---:|---:|---:|---:|
| **Finishing** | **38.3** | 38.5 | **83.3** | **2.2×** |
| Spinning | 35.9 | 38.4 | 37.8 | 1.05× |
| Weaving | 43.0 | 42.5 | 44.4 | 1.03× |

**The control lines are the proof.** Finishing more than doubles at night while Spinning and Weaving stay flat. Same machines, same products, same shift pattern — so the difference is how the shift is run, not what it is running.

> **Do not use `Downtime Minutes` here.** The total would show Weaving at 1.14× and Spinning at 1.20% higher at night purely because night shift has *more* stoppages. That blunts the contrast and invites the obvious objection — "everything is worse at night." The average isolates duration, which is what the claim actually asserts.

**Conditional-format the matrix** — this is what makes it readable at a glance:
select it → **Format visual → Cells → Background colour** → *fx* → Format style **Gradient**, based on `OEE %`.

**Filter the line chart to two machines** so the comparison is legible: in the Filters pane, filter `Machine ID` to **`WEV-03`** and one healthy machine such as **`WEV-05`**.

✅ **Check — the two findings:**

**1. `WEV-03` is failing.** On the line chart it starts near 62% and ends near 42%, while `WEV-05` stays flat around 80%. It is also the tallest bar on stop count. **A declining trend, not a low average, is what distinguishes a failing asset from a merely old one.**

**2. Night shift on Finishing.** In the matrix, `FIN-01`, `FIN-02` and `FIN-03` drop noticeably in the Night column while the Spinning and Weaving rows stay roughly level across all three shifts. Same machines, same products — so it is **not** the equipment.

### Write the findings on the page

Two text boxes:

> *WEV-03 has declined from 62% to 42% OEE across the period and has the highest stop count in the plant. This is a failing asset, not an underperforming one — plan the intervention before it becomes an unplanned stoppage.*

> *Finishing changeovers take 83 minutes on night shift against 38 on mornings. Other lines show no shift difference, so this is a process and training gap, not equipment.*

**A dashboard that names its own findings is worth far more than one that leaves the reader to spot them** — and those two sentences are what you will be asked about.

📸 → `screenshots/04-page-loss-analysis.png`

---

## Step 9 — Screenshots and publish

### The four images

| File | Shows |
|---|---|
| `01-data-model.png` | Star schema — data modelling |
| `02-power-query-steps.png` | Applied Steps — data preparation |
| `03-page-overview.png` | Plant Overview |
| `04-page-loss-analysis.png` | Loss Analysis — the findings |

**How:** `Win + Shift + S` → drag → `Ctrl+S`. Collapse the right-hand panes first. Same window size and theme across all four.

### Save

**File → Save as** → `SmartFactory.pbix`, in this project folder.

### Publish *(optional)*

1. **File → Sign in** (free account)
2. **Home → Publish** → *My workspace*
3. <https://app.powerbi.com> → **File → Embed report → Publish to web (public)**
4. Put the link in the README

> ⚠️ Publish to web makes the report **fully public**. Fine here because the data is entirely synthetic. Never with real production or commercial data.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `OEE %` does not equal A × P × Q | One component points at the wrong column — check `Ideal Minutes` vs `Run Minutes` in `Performance %` |
| Time series scrambled | Chart sorted by the measure, not the date — `⋯` → Sort axis |
| Every bar the same height | A relationship is missing or reversed |
| Months read Apr, Aug, Dec… | `Month` not sorted by `Month Number` (Step 5b) |
| Measures missing from the Data pane | The `_Measures` **table** is hidden — hide the column instead |
| Several measures in one chart | A visual was selected when you ticked — click empty canvas first |
| A text measure shows a blank card | The visual was auto-picked. Create the **Card first**, then tick the field (Step 6) |
| A measure is called `Measure` | Only the right-hand side was pasted; the name goes before the `=` |
| Matrix shows blanks for some machine/shift pairs | Expected during the July 2025 shutdown — the plant was stopped |
