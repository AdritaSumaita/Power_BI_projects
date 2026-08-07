# KPI catalogue — Donor Retention & Fundraising Performance

Every measure in the model: what it means in business terms, how it is calculated, and **the decision it supports**. A measure that supports no decision should not be in the model.

This is the analytics equivalent of a data dictionary, and it is the artefact that separates a business analyst from a chart-maker.

---

## Conventions

- All measures live in the `_Measures` table.
- Division always uses `DIVIDE()`, never `/`, so a zero denominator returns blank rather than erroring the visual.
- Currency is EUR. Formatting is set on the measure, not the visual, so every visual inherits it.

---

## Business rules

These affect every number in the report. Each was a decision, not an accident.

| Rule | Decision | Rationale |
|---|---|---|
| **Refunds** — 30 rows with a negative `Gift Amount` | Kept, and netted off income | A refund is real money going back out, not a data error. Excluding them would overstate what the organisation kept. |
| **Missing donor country** — ~360 donors | Relabelled `Unknown`, not deleted | The donor exists; only the attribute is missing. Deleting the rows would understate donor counts and silently change every total. |
| **Duplicate donor records** — 40 | Removed on `Donor Name` + `Acquisition Date` | Name alone is unsafe — two people can share one. |

---

## 01 Core

| Measure | Business definition | DAX | Supports |
|---|---|---|---|
| **Total Income** | All money received, net of refunds | `SUM(FactDonation[Gift Amount])` | Every view |
| **Gift Count** | Number of individual gifts | `COUNTROWS(FactDonation)` | Volume versus value |
| **Donor Count** | Distinct people who gave in the period | `DISTINCTCOUNT(FactDonation[DonorKey])` | Reach |
| **Average Gift** | Typical gift size | `DIVIDE([Total Income], [Gift Count])` | Setting the ask level |
| **New Donors** | Donors giving for the first time | `CALCULATE(DISTINCTCOUNT(FactDonation[DonorKey]), FactDonation[Is First Gift] = TRUE())` | Acquisition performance |

---

## 02 Value & ROI

This group is the point of the project.

| Measure | Business definition | DAX | Supports |
|---|---|---|---|
| **Campaign Cost** | Spend on acquisition and appeals | `SUM(FactCampaignCost[Cost Amount])` | Any ROI view |
| **Cost per Acquired Donor** | Spend per new donor (CAC) | `DIVIDE([Campaign Cost], [New Donors])` | Channel budget allocation |
| **Return on Investment %** | Net return on spend | `DIVIDE([Total Income] - [Campaign Cost], [Campaign Cost])` | Budget defence |

> **Gross income flatters whichever channel recruits the most people.** Cost per donor and ROI are the honest measures, and they change the ranking. That reversal is the finding the report exists to surface.

---

## The finding

Face-to-Face recruits **4,768 donors** — more than any other channel — and raises **€1,141,305**, the largest gross income of any mass channel. On that number alone it looks like the strongest performer.

It costs **€178.49 per donor acquired** against Direct Mail's **€119.75**, and returns **34.1%** against Direct Mail's **120.4%**. It is last of all seven channels on return.

**Decision this supports:** where next year's acquisition budget should go. On gross income the answer is "more Face-to-Face". On cost per donor and ROI it is not — and only the second view reflects what the money actually bought.

### Two exclusions, and why

Neither is hidden — both appear in the channel table. They are excluded from the *comparison charts* because ranking them against mass acquisition is a category error, not because the numbers are inconvenient.

| Channel | Why excluded from the ROI comparison |
|---|---|
| **Major Gifts** | 123 donors giving an average of **€30,569** each, recruited at **€1,976** per donor. A high-touch relationship programme, not a mass channel. On a scatter the cost figure is an outlier that compresses every other point into an unreadable cluster. |
| **Digital Organic** | €12 per donor, because it carries almost no acquisition spend. Dividing by a near-zero cost produces a near-infinite return; it is earned traffic rather than a budget line. |

The comparison that answers the question is between the channels that **compete for acquisition budget**: Face-to-Face, Digital Paid, Direct Mail, Telemarketing and Events.
