# Build guide — Consultancy Utilisation & Bench Cost

**What you will build:** a two-page report on a star schema, answering *which practice is leaking capacity, and what is it costing us?*

**Time:** about 2–3 hours. Stop after any step.

---

## Progress tracker

- [ ] **Step 1** — Setup
- [ ] **Step 2** — Load the data
- [ ] **Step 3** — Check types
- [ ] **Step 4** — Relationships
- [ ] **Step 5** — Date table
- [ ] **Step 6** — Measures
- [ ] **Step 7** — Page 1: Overview
- [ ] **Step 8** — Page 2: Practice Detail
- [ ] **Step 9** — Screenshots and publish

Each step ends with a ✅ **Check**. Do not move past a failing one.

---

## Step 1 — Setup

1. **File → New** in Power BI Desktop. Save immediately as `Utilisation.pbix` in this project folder.
2. **File → Options and settings → Options**
3. **GLOBAL → Data Load** → untick **Auto date/time for new files**
4. **CURRENT FILE → Data Load** → untick **Auto date/time**

> The Current File setting resets for every new `.pbix`. It is not inherited from the global one.

✅ Both boxes unticked.

---

## Step 2 — Load the data

**Home → Get data → Text/CSV**, once per file, clicking **Load**:

```
FactTimesheet.csv    FactCapacity.csv
DimEmployee.csv      DimProject.csv     DimWorkLocation.csv
```

✅ **Check:**

| Table | Rows |
|---|---|
| `FactTimesheet` | **14,799** |
| `FactCapacity` | **6,300** |
| `DimEmployee` | **60** |
| `DimProject` | **32** |
| `DimWorkLocation` | **3** |

> If a table shows `Column1`, `Column2`… → **Home → Transform data** → select it → **Use First Row as Headers** → Close & Apply.

---

## Step 3 — Check types

**Home → Transform data.** Check the icon on every column header.

| Column | Type |
|---|---|
| `…Key` | `123` Whole Number |
| `Week Start Date` | 📅 **Date** |
| `Hours`, `Capacity Hours`, `Target Hours`, `Revenue`, `Cost`, `Billing Rate` | `1.2` Decimal |
| `Role Target %` | `1.2` Decimal |
| `Is Billable`, `Is Onsite` | **True/False** |
| everything else | Text |

**Nothing needs cleaning.** The data is clean by design.

### 📸 Capture before leaving

With `FactTimesheet` selected so the **Applied Steps** panel shows → `screenshots/02-power-query-steps.png`

**Home → Close & Apply.**

---

## Step 4 — Relationships

**Home → Manage relationships** → select all → **Delete** → then **New relationship** ×4:

| # | Top (many) | Column | Bottom (one) | Column |
|---|---|---|---|---|
| 1 | `FactTimesheet` | `EmployeeKey` | `DimEmployee` | `EmployeeKey` |
| 2 | `FactTimesheet` | `ProjectKey` | `DimProject` | `ProjectKey` |
| 3 | `FactTimesheet` | `WorkLocationKey` | `DimWorkLocation` | `WorkLocationKey` |
| 4 | `FactCapacity` | `EmployeeKey` | `DimEmployee` | `EmployeeKey` |

All: **Many to one (\*:1)** · **Single** · **Active**

`DimEmployee` feeds **both** facts. That conformed dimension is what lets one practice slicer filter timesheets and capacity together — and without it, utilisation could not be calculated at all, because its numerator and denominator live in different tables.

✅ **4 relationships**, all `*—◄—1`, all Active.

---

## Step 5 — Date table

### 5a. Create it

**Home → New table**:

```dax
DimDate =
ADDCOLUMNS(
    CALENDAR(DATE(2024,1,1), DATE(2025,12,31)),
    "Year",         YEAR([Date]),
    "Month Number", MONTH([Date]),
    "Month",        FORMAT([Date], "mmm"),
    "Year Month",   FORMAT([Date], "yyyy-mm"),
    "Quarter",      YEAR([Date]) & " Q" & QUARTER([Date])
)
```

### 5b. Sort the months ⚠️

`Month` → **Column tools → Sort by column → `Month Number`**

### 5c. Mark it

Right-click `DimDate` → **Mark as date table** → `Date`

### 5d. Join it

| Top (many) | Column | Bottom (one) | Column |
|---|---|---|---|
| `FactTimesheet` | `Week Start Date` | `DimDate` | `Date` |
| `FactCapacity` | `Week Start Date` | `DimDate` | `Date` |

Both Active — different fact tables, no ambiguity.

✅ `DimDate` = **731 rows** · **6 relationships** total, all Active

### 5e. 📸 Screenshot the model

Facts centre, dimensions around → `screenshots/01-data-model.png`

---

## Step 6 — Measures

**Home → Enter data** → `_Measures` → **Load** → right-click `Column1` → **Hide**.

> Hide the **column**, not the table.

Select `_Measures` → **New measure** → paste the whole line including the name.

### Hours

```dax
Billable Hours = CALCULATE(SUM(FactTimesheet[Hours]), FactTimesheet[Is Billable] = TRUE())
```
```dax
Total Hours = SUM(FactTimesheet[Hours])
```
```dax
Capacity Hours = SUM(FactCapacity[Capacity Hours])
```
```dax
Target Hours = SUM(FactCapacity[Target Hours])
```

### Utilisation — the heart of the report

```dax
Utilisation % = DIVIDE([Billable Hours], [Capacity Hours])
```
```dax
Target Utilisation % = DIVIDE([Target Hours], [Capacity Hours])
```
```dax
Utilisation Gap pp = [Utilisation %] - [Target Utilisation %]
```
```dax
Billable Share % = DIVIDE([Billable Hours], [Total Hours])
```

> ### `Billable Share %` exists for one reason: work location
>
> `FactCapacity` has **no work location** — capacity is not worked anywhere, it just exists. So slicing `Utilisation %` by `Work Location` filters the numerator and leaves the denominator at the firm total. The three bars then sum to 62.7% and Home comes out highest simply because most hours happen there. Plausible-looking and completely wrong.
>
> `Billable Share %` takes both halves from `FactTimesheet`, which *does* carry a location.
>
> **A measure is only valid on dimensions that can reach every table it touches.** Worth checking whenever a slice produces a surprising ranking.

> `Target Utilisation %` divides two pre-computed sums rather than averaging a target column. That matters: averaging targets across a group with a different role mix gives the wrong benchmark, and the whole point of this report is that the benchmark differs per person.

### Money

```dax
Revenue = SUM(FactTimesheet[Revenue])
```
```dax
Delivery Cost = SUM(FactTimesheet[Cost])
```
```dax
Gross Margin % = DIVIDE([Revenue] - [Delivery Cost], [Revenue])
```
```dax
Effective Hourly Rate = DIVIDE([Revenue], [Billable Hours])
```

### The measure that changes the conversation

```dax
Hours Below Target = MAX([Target Hours] - [Billable Hours], 0)
```
```dax
Revenue at Risk = [Hours Below Target] * [Effective Hourly Rate]
```

A director hears "we are 8.8 points below target" and nods. They hear **"that is €2.3 million"** and act. Same fact, different unit.

`MAX(…, 0)` stops a practice that is *over* target contributing a negative and quietly offsetting one that is under.

### Formatting

| Measures | Format |
|---|---|
| `Utilisation %`, `Target Utilisation %`, `Utilisation Gap pp`, `Gross Margin %` | Percentage, 1 dp |
| `Revenue`, `Delivery Cost`, `Revenue at Risk`, `Effective Hourly Rate` | Currency €, 0 dp |
| Hours measures | Whole number, comma separator |

✅ **Ground truth from the source data:**

| Measure | Expected |
|---|---|
| `Utilisation %` | **62.7%** |
| `Target Utilisation %` | **71.5%** |
| `Utilisation Gap pp` | **−8.8%** |
| `Capacity Hours` | **217,890** |
| `Target Hours` | **155,790** |
| `Billable Hours` | **136,636** |
| `Revenue` | **€16,267,495** |
| `Gross Margin %` | **27.8%** |
| `Hours Below Target` | **19,155** |
| `Revenue at Risk` | **€2,280,493** |

> **Text measures:** if you ever add one, create the **Card first**, then tick the field. Ticking a text field with nothing selected lets Power BI pick the visual, and its choice will not render the string.

---

## Step 7 — Page 1: Overview

Rename the page **Overview**. Title:

> **Are we running at the utilisation we planned?**

| Visual | Type | Fields |
|---|---|---|
| KPI row | 5 × **Card** | `Utilisation %` · `Target Utilisation %` · `Revenue` · `Gross Margin %` · `Revenue at Risk` |
| Trend | **Line chart** | X: `DimDate[Year Month]` · Y: `Utilisation %` |
| By practice | **Clustered bar** | Y: `DimEmployee[Practice]` · X: `Utilisation %` |
| By industry | **Clustered bar** | Y: `DimProject[Industry]` · X: `Revenue` |

**Sorting:** line chart → `⋯` → **Sort axis → Year Month** → `⋯` → **Sort ascending**. Bars → by their measure, descending.

✅ **Checks**

- `Utilisation %` **62.7%** against `Target Utilisation %` **71.5%**
- The trend runs **64.1% at the start to 61.2% at the end**, roughly flat through 2024 and sliding through 2025. That decline is Design deteriorating and pulling the firm average down — page 2 isolates it.
- By practice: **Design lowest** at ~48%, Advisory highest at ~72%

> ### There is no July dip, and that is the point
>
> July capacity falls to about 5,560 hours against a 9,400 average — Finnish summer holidays. But billable hours fall by the same proportion, so the **ratio is unchanged**: 63.6% and 62.5% in the two Julys, in line with every other month.
>
> **That immunity is why utilisation is the right metric.** Plot absolute billable hours instead and you get a cliff every summer that says nothing about performance. A ratio with the seasonality in both numerator and denominator cancels it out and leaves only the signal.

📸 → `screenshots/03-page-overview.png`

---

## Step 8 — Page 2: Practice Detail

New page, **Practice Detail**. Title:

> **Where is capacity leaking, and what is it costing?**

| Visual | Type | Fields |
|---|---|---|
| **The gap** | **Clustered bar** | Y: `Practice` · X: `Utilisation Gap pp` |
| **The money** | **Clustered bar** | Y: `Practice` · X: `Revenue at Risk` |
| Design vs Delivery | **Line chart** | X: `DimDate[Year Month]` · Y: `Utilisation %` · Legend: `Practice` — filter to **Design** and **Delivery** only |
| Role detail | **Matrix** | Rows: `DimEmployee[Role Level]` · Values: **`Utilisation %` *and* `Utilisation Gap pp`** ⚠️ both |
| Hybrid work | **Clustered bar** | Y: `DimWorkLocation[Work Location]` · X: **`Billable Share %`** ⚠️ not `Utilisation %` |

✅ **Checks**

- **Gap chart:** Design ≈ **−24 pp**, everything else within 5 pp of target
- **Money chart:** Design ≈ **€1.85M**, the other three under €0.3M each — a quarter of the firm, three quarters of the problem

> ⚠️ **The four bars will not add up to the €2,280,493 card on page 1.** They come to €2,382,972. Nothing is broken: `Effective Hourly Rate` re-evaluates per practice, so each bar uses that practice's own rate while the card uses the firm blend. The *hours* are additive, the money is not. Explained in full in [`kpi-catalogue.md`](kpi-catalogue.md) §04 — and it is worth being able to explain in an interview, because it is the first thing a numerate reader will test.
- **Line chart:** Delivery flat near 69–70%; Design slides from ~52% to ~42%
- **Role matrix:** Consultant −6.2 · Junior −10.6 · Manager −4.1 · Principal −1.1 · **Senior −12.5** · Total −8.8
- **Hybrid:** Client site **77.2%**, Office 63.6%, Home 62.3%

> ⚠️ **The role matrix needs both columns, and this is the point of the whole report.**
> On `Utilisation %` alone, Manager is the worst in the firm at 25.9% and Senior looks fine at 59.5%. Against their own targets — 30% and 72% — Manager is the *second best* at −4.1 and **Senior is the worst at −12.5**, in the biggest role group there is. The ranking inverts.
>
> A manager billing 25.9% is doing the job as designed. Ship the matrix with utilisation alone and you have rebuilt the blanket-target error inside the report written to correct it.

### Write the findings on the page

> *Design is 28% of the firm and 77% of the shortfall — 14,763 of 19,155 unbilled hours, worth €1.85M at its own €125.40 rate. It has been below target since 2024 and is still falling while Delivery holds steady. This is a demand problem, not an effort problem.*

The share is stated **in hours** on purpose. Dividing Design's €1.85M by the €2.28M card gives 81%, but that divides a practice-rated numerator by a blend-rated denominator — two different bases. Hours are additive, so they compare cleanly.

> *Client-facing hours bill at 77% against 62% worked from home, while office and home are near-identical. The split that matters is client-facing versus not — though people are likely at a client site because billable work is there, so this is association rather than proven cause.*

That second caveat matters. **Stating the limit of what your data can show is what separates analysis from assertion**, and it is the kind of thing an interviewer probes.

### Link the thesis

**Insert → Text box** in the footer:

> *Extends the Master's thesis "Optimizing Resource Planning in Hybrid Knowledge Work" — https://trepo.tuni.fi/handle/10024/232515*

📸 → `screenshots/04-page-practice-detail.png`

---

## Step 9 — Screenshots and publish

| File | Shows |
|---|---|
| `01-data-model.png` | Star schema |
| `02-power-query-steps.png` | Applied Steps |
| `03-page-overview.png` | Overview |
| `04-page-practice-detail.png` | Practice Detail — the findings |

Collapse the right-hand panes, **View → Page view → Fit to page**, same window size and theme for all four.

**File → Save as** → `Utilisation.pbix` in this folder.

### Publish *(optional)*

**File → Sign in** → **Home → Publish** → *My workspace* → then <https://app.powerbi.com> → **File → Embed report → Publish to web (public)**.

> ⚠️ Publish to web makes the report **fully public**. Fine here — the data is entirely synthetic. Never with real timesheet data, which identifies individuals.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `Utilisation %` blank or 100% | `FactCapacity` not related to `DimEmployee`, so numerator and denominator do not share a filter |
| Time series scrambled | Chart sorted by measure, not date — `⋯` → Sort axis |
| Months read Apr, Aug, Dec… | `Month` not sorted by `Month Number` (Step 5b) |
| Every bar the same height | A relationship is missing or reversed |
| Measures missing from the Data pane | The `_Measures` **table** is hidden — hide the column instead |
| A text measure shows a blank card | Create the **Card first**, then tick the field |
| Several measures in one chart | A visual was selected when you ticked — click empty canvas first |
| Expected a July dip and there isn't one | Correct — utilisation is a ratio, and summer cuts capacity and billable hours proportionally. Only *absolute* hours dip in July. |
| Work-location bars sum to 62.7% and Home is highest | `Utilisation %` used instead of `Billable Share %`. `FactCapacity` has no location, so the denominator never filters. |
