# Mini-BRD — Donor Retention & Fundraising Performance

**Client:** Nordic Relief Foundation (fictional)
**Author:** _[add your name]_
**Version:** 0.1 — draft
**Date:** _[add date]_

---

## 1. Problem statement

The Foundation raises approximately €1.6M a year across four Nordic markets through seven channels. It reports thoroughly on **funds raised** and almost not at all on **funds retained**.

The consequence is a structural blind spot. A channel that recruits a high volume of donors at low apparent cost looks like the organisation's best performer in the annual report, even when most of those donors have lapsed within twelve months and the acquisition spend never paid back. Budget is then allocated to that channel again the following year, on the strength of a number that measures the wrong thing.

Two specific gaps:

1. **Acquisition cost is never joined to income.** Cost sits in finance spreadsheets, income sits in the CRM, and no report brings them together.
2. **Channels are ranked on gross income.** That measure rewards whichever channel recruits the most people, regardless of what each of those people cost to recruit.

## 2. Objective

Give the fundraising leadership a single view that answers:

> *Where should next year's acquisition budget go?*

## 3. Stakeholders

| Stakeholder | Interest | Primary question |
|---|---|---|
| Fundraising Director | Sustainable growth | Are we growing, or renting income? |
| Channel / Campaign Manager | Budget allocation | Which channels actually pay back? |
| Finance / Board | Value for money | What did each euro of acquisition spend return? |

## 4. As-Is

- Monthly income reported from the CRM as a single total, split by channel.
- Acquisition cost held in finance spreadsheets, never joined to income.
- Channels ranked on gross income alone, so the highest-volume channel always appears to be the best performer.
- Producing a channel comparison takes an analyst roughly two days of manual work, and the result is not reproducible.

## 5. To-Be

- One refreshable model joining donations and campaign cost through a shared channel dimension.
- Cost per acquired donor and return on investment calculated per channel, from the same source as income.
- Income, donor volume and growth visible by channel, country and month.
- Every measure defined once, in writing, so the numbers are not re-argued each time they are quoted.

## 6. Scope

**In scope**

- Donations, campaign cost, donors, campaigns and channels
- Period 2022–2025, four Nordic markets
- Income and donor volume by channel, country and time
- Acquisition cost per donor and return on investment by channel

**Out of scope**

- Live CRM connection — this build uses a generated dataset
- Individual donor contact details or any personal data
- Recurring pledge health and cancellation analysis
- Cohort retention and RFM donor segmentation
- Gift Aid, tax reclaim, and country-specific tax treatment
- Legacy / bequest pipeline forecasting
- Predictive churn scoring

## 7. Success criteria

| # | Criterion | Measure of success |
|---|---|---|
| 1 | Channel decisions use cost and return, not gross income | Cost per acquired donor and ROI visible per channel on one page |
| 2 | The comparison is fair | Campaign cost joined to income at channel level; no channel judged on volume alone |
| 3 | Report is trusted | Totals reconcile to source; every business rule documented |
| 4 | The report states its own finding | Each page titled with the question it answers, and the conclusion written on the page |

## 8. Assumptions

- One CRM donor record equals one person, after deduplication.
- Campaign cost is attributable to a single channel and month.
- A donor is "acquired" by the channel that generated their first gift.
- Refunds are netted off income rather than excluded.
- All figures in EUR; no currency conversion is modelled.

## 9. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Cost data attributed to the wrong channel | ROI misstated, budget moved on a false signal | Cost held at campaign × month × channel grain; assumption documented |
| Donors with a missing country dropped during cleaning | Donor counts understated, every total shifts | Missing values relabelled `Unknown`, never deleted; dimension row count verified after cleaning |
| Duplicate donor records inflate counts | Reach overstated | Deduplicated on name plus acquisition date, not name alone |
| Channels still compared on gross income | No behaviour change, wrong budget decision | Cost per donor and ROI placed on the same page as income, and the conclusion written on the page |
| Report becomes a description, not a decision tool | Nobody acts on it | Every page titled with the question it answers |

## 10. Deliverables

| # | Deliverable |
|---|---|
| 1 | Power BI model — star schema, cleaned data, dedicated date table |
| 2 | Overview page — income, donors and growth over time |
| 3 | Channel ROI page — cost per acquired donor and return by channel |
| 4 | KPI catalogue documenting every measure and business rule |
| 5 | Report published with a shareable link |
