# Build guide — Donor Retention & Fundraising Performance

A complete Power BI project, written for someone who has never opened Power BI.

**What you will build:** a two-page report on a proper star schema, answering a real business question — *which fundraising channels actually pay back?*

**Time:** about 3 hours, and you can stop after any step.

---

## Progress tracker

- [ ] **Step 1** — Install and configure Power BI Desktop
- [ ] **Step 2** — Load the data
- [ ] **Step 3** — Clean the donor table
- [ ] **Step 4** — Build the relationships
- [ ] **Step 5** — Build the date table
- [ ] **Step 6** — Write the measures
- [ ] **Step 7** — Page 1: Overview
- [ ] **Step 8** — Page 2: Channel ROI
- [ ] **Step 9** — Screenshots and publish

Every step ends with a ✅ **Check**. Do not move on until it passes — a mistake caught in the step where it happens takes a minute; the same mistake found three steps later can take an hour.

---

## Step 1 — Install and configure

1. Install **Power BI Desktop** — Microsoft Store, search "Power BI Desktop". Free, Windows only.

   > Use **Desktop**, not the browser version. The web editor is missing several things this guide needs.

2. **File → Options and settings → Options**
3. **GLOBAL → Data Load** → untick **Auto date/time for new files**
4. **CURRENT FILE → Data Load** → untick **Auto date/time**
5. Close and reopen Power BI Desktop.

**Why:** Power BI otherwise builds a hidden date table behind every date column — several invisible tables, a bloated file, and date logic scattered where you cannot see it. You will build one visible date table instead.

✅ **Check:** reopen Options — both boxes unticked.

---

## Step 2 — Load the data

The CSVs are in the `data` folder next to this guide.

**Home → Get data → Text/CSV**, once per file. Click **Load** each time.

| File | What it is |
|---|---|
| `FactDonation.csv` | Every gift — 124,742 rows |
| `FactCampaignCost.csv` | What each campaign cost to run |
| `DimDonor.csv` | The donor list |
| `DimChannel.csv` | The seven fundraising channels |
| `DimCampaign.csv` | Campaigns and appeals |

Five files, five tables. Everything in the `data` folder is used.

✅ **Check:**

| Table | Rows |
|---|---|
| `FactDonation` | 124,742 |
| `DimDonor` | 12,040 |
| `DimChannel` | 7 |

> If a table shows `Column1`, `Column2`… → **Home → Transform data** → select it → **Home → Use First Row as Headers** → Close & Apply.

---

## Step 3 — Clean the donor table

Only `DimDonor` needs cleaning. **Home → Transform data**, select `DimDonor` on the left.

### 3a. Replace missing countries

About 360 donors have no country recorded.

1. Click the **`Country` column header** to select the whole column
2. **Transform → Replace Values**
3. Value To Find: `null` · Replace With: `Unknown` → **OK**

> **If blanks survive, they are empty strings rather than nulls.** Power BI may read an empty CSV field either way, and `Replace Values` with `null` only matches true nulls.
>
> The reliable version handles both. Click the step in **Applied Steps**, select everything in the formula bar and paste:
>
> ```m
> = Table.TransformColumns(#"Cleaned Text", {{"Country", each if _ = null or _ = "" then "Unknown" else _, type text}})
> ```
>
> Keep the `#"..."` step name matching whatever precedes it in your own query, or the chain breaks.

> ### ⚠️ Do not use the dropdown arrow on the column header
>
> Ticking `(null)` in that filter list **deletes every other row** — it leaves about 360 donors out of 12,000 and the mistake is nearly invisible afterwards, because the column still looks populated.
>
> **Replace Values** never deletes rows. Use it.

**Why replace rather than delete?** A missing country is a data-entry gap, not a missing donor. Removing those rows would understate donor counts and quietly change every total in the report.

### 3b. Remove duplicate donors

40 donors were entered twice, with a double space in the name.

1. `Donor Name` column → **Transform → Replace Values** → find **two spaces**, replace with **one space**
2. Click `Donor Name`, then **Ctrl+click** `Acquisition Date`
3. **Home → Remove Rows → Remove Duplicates**

**Why both columns?** Two different people can share a name. Name *plus* acquisition date is a far safer key.

> ### ⚠️ Check the formula this produced
>
> Click the step and read the formula bar. It must say **`Replacer.ReplaceText`**:
>
> ```m
> = Table.ReplaceValue(#"Replaced Value", "  ", " ", Replacer.ReplaceText, {"Donor Name"})
> ```
>
> If it says **`Replacer.ReplaceValue`**, the step does nothing. `ReplaceValue` swaps a cell only when the *entire* cell equals the search text — `"Sharon  Martin"` never equals `"  "`. `ReplaceText` replaces *within* the text, which is what is needed.
>
> Also confirm the search value is **two spaces**, not one. `" "` → `" "` is a no-op and easy to type by accident.
>
> Either fault leaves the duplicate names still different, so the dedupe removes nothing and the row count stays at 12,040. Paste the line above over the formula to fix both at once.

### 3c. Leave the refunds alone

30 rows in `FactDonation` have a negative `Gift Amount`. **Do nothing.**

A refund is real money going back out, not a data error — netting it off is correct. This is a business rule, and being able to state it is the point.

### 3d. Screenshot, then apply

📸 With `DimDonor` selected, capture the **Applied Steps** panel on the right → save as `02-power-query-steps.png`

This is the screenshot that proves you cleaned the data rather than receiving it clean. Almost no portfolio includes one.

Then **Home → Close & Apply**.

✅ **Check — the important one:**

| Check | Expected |
|---|---|
| `DimDonor` rows | **~12,000** |
| `Country` distinct values | **5** — FI, SE, NO, DK, Unknown |
| Applied Steps | contains **no** `Filtered Rows` step |

> A measure cannot detect a broken dimension. `Donor Count` counts rows in `FactDonation`, so it reports a healthy 12,000 even if `DimDonor` has been emptied. **Always check a dimension on its own row count.**

---

## Step 4 — Build the relationships

**Home → Manage relationships**

1. Select every existing row (click the first, Shift+click the last) → **Delete**

   Power BI guesses relationships on load. Guesses are a starting point, not an answer — you want to be able to explain every one.

2. Click **New relationship** and build these four. **The fact table always goes on top:**

| # | Top (many) | Column | Bottom (one) | Column |
|---|---|---|---|---|
| 1 | `FactDonation` | `DonorKey` | `DimDonor` | `DonorKey` |
| 2 | `FactDonation` | `CampaignKey` | `DimCampaign` | `CampaignKey` |
| 3 | `FactDonation` | `ChannelKey` | `DimChannel` | `ChannelKey` |
| 4 | `FactCampaignCost` | `ChannelKey` | `DimChannel` | `ChannelKey` |

Every one: **Cardinality = Many to one (\*:1)** · **Cross filter direction = Single** · **Active** ticked.

**Why "many to one"?** One donor makes many gifts. Read it aloud — *many donations, to one donor* — and the direction is obvious.

**Why single direction?** Filters flow from dimensions down to facts, never back up. Bidirectional filtering looks helpful and then produces wrong numbers in ways that are very hard to trace.

✅ **Check:** Manage relationships lists **4 rows**, all showing `*—◄—1`, all Active.

---

## Step 5 — Build the date table

Every model needs one dedicated date table. It gives Power BI a single authority on dates instead of a hidden one behind every date column, and it is what any time-intelligence calculation would later depend on.

### 5a. Create it

**Home → New table**, paste this, press Enter:

```dax
DimDate =
ADDCOLUMNS(
    CALENDAR(DATE(2022,1,1), DATE(2025,12,31)),
    "Year",         YEAR([Date]),
    "Month Number", MONTH([Date]),
    "Month",        FORMAT([Date], "mmm"),
    "Year Month",   FORMAT([Date], "yyyy-mm")
)
```

### 5b. Sort the months ⚠️

Click the **`Month`** column → **Column tools → Sort by column → `Month Number`**

Skip this and every chart reads Apr, Aug, Dec, Feb… alphabetically. It is the most common beginner tell in a portfolio, and invisible until someone looks at a chart closely.

### 5c. Mark it as a date table

Right-click **`DimDate`** in the Data pane → **Mark as date table** → choose the **`Date`** column → OK.

This tells Power BI's time-intelligence functions which table is authoritative.

### 5d. Join it

**Manage relationships → New relationship**, twice. `DimDate` goes on the **bottom**:

| Top (many) | Column | Bottom (one) | Column |
|---|---|---|---|
| `FactDonation` | `Donation Date` | `DimDate` | `Date` |
| `FactCampaignCost` | `Month Start Date` | `DimDate` | `Date` |

Both **Many to one**, **Single**, **Active**.

✅ **Check:** `DimDate` = **1,461 rows**. Relationships total **6**, all Active.

### 5e. Screenshot the model

**Model view** (the diagram icon on the left edge). Drag the boxes so the **fact tables sit in the centre with dimensions around them, no crossing lines.**

📸 Save as `01-data-model.png`

This goes at the top of the project README. It answers a technical reviewer's first question: *does this person understand data modelling?*

---

## Step 6 — Write the measures

A **measure** is a saved calculation — not stored data. It recalculates for whatever the visual is showing, which is why measures live in their own table rather than inside any one fact table.

### 6a. Make a home for them

**Home → Enter data** → name it **`_Measures`** → **Load**

Right-click the `Column1` it creates → **Hide**.

*(The underscore makes it sort to the top of the field list.)*

### 6b. Add the measures

For each one: click **`_Measures`** in the Data pane → **Home → New measure** → `Ctrl+A` → paste **the whole line including the name** → Enter.

> The text before the `=` becomes the measure's name. Pasting only the right-hand side leaves it called `Measure`.

```dax
Total Income = SUM(FactDonation[Gift Amount])
```
```dax
Gift Count = COUNTROWS(FactDonation)
```
```dax
Donor Count = DISTINCTCOUNT(FactDonation[DonorKey])
```
```dax
Average Gift = DIVIDE([Total Income], [Gift Count])
```
```dax
New Donors = CALCULATE(DISTINCTCOUNT(FactDonation[DonorKey]), FactDonation[Is First Gift] = TRUE())
```
```dax
Campaign Cost = SUM(FactCampaignCost[Cost Amount])
```
```dax
Cost per Acquired Donor = DIVIDE([Campaign Cost], [New Donors])
```
```dax
Return on Investment % = DIVIDE([Total Income] - [Campaign Cost], [Campaign Cost])
```
> **Always `DIVIDE`, never `/`.** A zero denominator returns blank instead of erroring the whole visual.
>
> `[Square brackets]` means a measure. `Table[Column]` means a column. Measures can call other measures — `Average Gift` uses two.

### 6c. Format them

Select each measure → **Measure tools** ribbon:

| Measures | Format |
|---|---|
| `Total Income`, `Average Gift`, `Campaign Cost`, `Cost per Acquired Donor` | Currency, €, 0 decimals |
| `Return on Investment %` | Percentage, 1 decimal |
| `Gift Count`, `Donor Count`, `New Donors` | Whole number, comma separator |

Format at the measure level, not inside each visual — every visual then inherits it.

✅ **Check — these come straight from the source data:**

| Measure | Expected | Card shows |
|---|---|---|
| `Total Income` | **€6,463,722** | `6.46M` |
| `Gift Count` | **124,742** | `125K` |
| `Donor Count` | **12,000** | `12K` |
| `New Donors` | **12,000** | `12K` |

Cards abbreviate large numbers by default, so `6.46M` is correct rather than a rounding problem. To see full figures, select the card → **Format → Callout value → Display units → None**.

That total is the sum of **all** rows including the 30 refunds, which come to −€543.49. Positive gifts alone total €6,464,266 — if you see that instead, the refunds have been filtered out somewhere and should not have been.

> **To make four separate cards:** click **empty canvas** to deselect → tick **one** field → click the **Card** icon (`123`) in Visualizations. Repeat.
>
> Ticking a field while a visual is selected adds it *into* that visual — that is how several measures end up crammed in one chart.

---

## Step 7 — Page 1: Overview

Right-click the page tab at the bottom → **Rename** → **Overview**.

Add a text box at the top with the question the page answers:

> *Are we growing sustainably, or renting income?*

A page title should state a question, not a label. A page without a question is a pile of charts.

| Visual | Type | Fields |
|---|---|---|
| KPI row | 4 × **Card** | `Total Income` · `Donor Count` · `New Donors` · `Return on Investment %` |
| Income over time | **Line chart** | X: `DimDate[Year Month]` · Y: `Total Income` |
| Income by channel | **Bar chart** | Y: `DimChannel[Channel Name]` · X: `Total Income` |
| Income by country | **Bar chart** | Y: `DimDonor[Country]` · X: `Total Income` |

> ### ⚠️ Sort the line chart by date, not by value
>
> Power BI sorts a chart by its **measure** by default, largest first. A time series then comes out in income order rather than date order — a smooth decline with the months scrambled, which looks like real data and is not.
>
> Click the chart → **`⋯`** in its top-right corner → **Sort axis → `Year Month`**. Open the same menu again → **Sort ascending**. Both clicks are needed: one sets the field, the other the direction.

✅ **Check:** the line chart shows a **large December spike every year** — that is the Christmas appeal, roughly a quarter of annual income.

A flat or smoothly declining line means one of two things: the axis is sorted by value (see above), or the `DimDate` relationship is wrong. Check the sort first — it is far more common.

The country chart should show four real bars with **FI tallest**, plus a small `Unknown`. If it shows only `Unknown`, go back to Step 3a.

📸 **View → Page view → Fit to page**, collapse the Filters / Visualizations / Data panes on the right, then capture → `03-page-overview.png`

---

## Step 8 — Page 2: Channel ROI

New page, rename it **Channel ROI**. Title text box:

> *Which channels actually pay back?*

| Visual | Type | Fields |
|---|---|---|
| **The finding** | **Scatter chart** | X: `Cost per Acquired Donor` · Y: `Return on Investment %` · Size: `New Donors` · Legend: `DimChannel[Channel Name]` |
| ROI ranking | **Bar chart** | Y: `Channel Name` · X: `Return on Investment %` |
| Channel detail | **Table** | `Channel Name`, `New Donors`, `Total Income`, `Campaign Cost`, `Cost per Acquired Donor`, `Return on Investment %` |

### Filter the comparison charts to the channels that compete for budget

Two channels break the comparison and should be filtered **out of the scatter and the bar chart** — but left **in the table**, so nothing is hidden:

| Channel | Why |
|---|---|
| **Major Gifts** | Costs €1,976 per donor against everything else under €180, so on a scatter it sits far off to the right and compresses every other point into an unreadable cluster. Those 123 donors give an average of €30,569 each — a high-touch relationship programme, not a mass acquisition channel. |
| **Digital Organic** | €12 per donor, because it carries almost no spend. Dividing by a near-zero cost gives a near-infinite return — it is earned traffic, not a budget line. |

Select each chart → **Filters** pane → drag `DimChannel[Channel Name]` into *Filters on this visual* → untick both.

Then add a text box saying so:

> *Major Gifts and Digital Organic excluded — a high-touch programme and an unpaid channel are not comparable to paid mass acquisition.*

**An analyst who excludes an outlier and states the reason is doing the job; one who silently drops it is not.** Expect to be asked about this.

✅ **Check — this is the payoff of the whole project:**

| Channel | New donors | Income | Cost per donor | ROI |
|---|---:|---:|---:|---:|
| Telemarketing | 935 | €217,624 | €69.88 | 233.1% |
| Events | 622 | €101,944 | €61.41 | 166.9% |
| Digital Paid | 2,889 | €612,974 | €87.00 | 143.9% |
| Direct Mail | 1,451 | €382,890 | €119.75 | 120.4% |
| **Face-to-Face** | **4,768** | **€1,141,305** | **€178.49** | **34.1%** |

Face-to-Face has the **largest bubble** (most donors), sits **furthest right** (most expensive per donor) and **lowest on the Y axis** (worst return) — last of all seven channels.

That is the finding: **the channel that looks strongest on gross income is the one that pays back worst.** Gross income flatters whichever channel recruits the most people; only cost per donor and ROI show what the money bought.

Add a text box stating it in one sentence. **A dashboard that names its own finding is worth far more than one that leaves the reader to spot it** — and that sentence is what you will be asked about in an interview.

📸 Capture → `04-page-channel-roi.png`

---

## Step 9 — Screenshots and publish

### Why this matters

**Nobody will download your `.pbix`.** A recruiter has your link open for about ninety seconds, on a laptop that probably does not have Power BI installed. If the project is only a file in a repository, the work is invisible.

Most Power BI portfolios show only the finished dashboard, which proves you can arrange charts. The **model diagram and the Power Query steps prove you built the thing underneath** — the part that cannot be inferred from a course certificate.

### The four images

| File | Shows |
|---|---|
| `01-data-model.png` | Star schema — data modelling |
| `02-power-query-steps.png` | Applied Steps — data cleaning |
| `03-page-overview.png` | Overview page |
| `04-page-channel-roi.png` | Channel ROI — the finding |

Save them all to the `screenshots/` folder at the project root.

**How to take them well:**

- `Win + Shift + S` → drag a rectangle → `Ctrl+S` to save as PNG
- **Collapse the right-hand panes** before capturing a page — editor chrome makes a finished report look unfinished
- **View → Page view → Fit to page** so nothing is cropped
- Keep the **same window size and theme** for all four
- Check the frame for anything personal — file paths, other tabs, notifications

### Save the file

**File → Save as** → `DonorRetention.pbix`, in this project folder.

### Publish a live link

A recruiter who can *click* your dashboard is worth ten who look at a picture of it.

1. **File → Sign in** (free account is enough)
2. **Home → Publish** → *My workspace*
3. Open <https://app.powerbi.com>, find the report
4. **File → Embed report → Publish to web (public)**
5. Put the link in the project README

> ### ⚠️ Publish to web makes the report fully public on the internet
>
> Anyone with the link can see every row. That is acceptable here **only because this dataset is entirely synthetic**.
>
> Never do this with real donor, patient, employee or customer data. For anything real, share it inside the organisation's own tenant instead.
>
> Being able to say exactly that in an interview is itself a strong signal — most candidates have never thought about it.

**Done.** This is a complete, publishable portfolio project.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| A dimension column shows only one value | A `Filtered Rows` step is deleting rows — check Applied Steps (Step 3a) |
| Totals look fine but slicers return almost nothing | A dimension lost rows. Check its own row count, not a measure |
| Every bar the same height | A relationship is missing or reversed |
| Months read Apr, Aug, Dec… | `Month` not sorted by `Month Number` (Step 5b) |
| Time series scrambled or smoothly declining | Chart sorted by the measure, not the date — `⋯` → Sort axis (Step 7) |
| A measure shows `2.95` instead of `295.0%` | Format not set on the measure — select it → **Measure tools → Format → Percentage** |
| Blank chart | No relationship between the measure's table and the axis field's table |
| Several measures crammed in one chart | A visual was selected when you ticked the field — click empty canvas first |
| A measure is called `Measure` | Only the right-hand side was pasted; the name goes before the `=` |
| Time intelligence returns blank | `DimDate` not marked as a date table (Step 5c) |
| "Cannot determine relationship" | Two fact tables with no shared dimension on the axis |
