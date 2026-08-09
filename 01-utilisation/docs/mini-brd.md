# Mini-BRD — Consultancy Utilisation & Bench Cost

**Client:** Nordwave Consulting (fictional)
**Author:** Sumaita Faria Karim Adrita
**Version:** 1.0
**Status:** Complete
**Date:** 25 July 2026

---

## 1. Problem statement

Nordwave Consulting is a 60-person Nordic software consultancy across four practices and three offices. Utilisation is reported monthly as one company-wide percentage.

Two failures follow from that.

**A single average hides the practice that is idle.** The firm currently reports 62.7%. That number looks like uniform mediocrity. It is not — three practices sit within five points of their targets and one sits twenty-four points below.

**One target for everyone is the wrong test.** Every person is measured against the same figure, when the roles are not comparable. A principal carrying 55% billable is performing exactly as intended; their week is meant to include selling, mentoring and account management. A junior at 55% is a serious problem. Against a blanket target, the principal is flagged and the junior is not — both conclusions are wrong, and the practice leads have stopped trusting the number as a result.

A third gap follows from both: **nobody has priced the shortfall.** Under-utilisation is discussed as a percentage, which nobody acts on, rather than as money, which they do.

## 2. Objective

Give practice leadership a single view that answers:

> *Which practice is leaking capacity, and what is it costing us?*

A secondary question, carried over from the underlying research: **does where people work relate to how much of their time is billable?**

## 3. Stakeholders

| Stakeholder | Interest | Primary question |
|---|---|---|
| Practice Director | Firm performance | Are we hitting utilisation, and where is margin leaking? |
| Practice Lead | Own team | Is my practice above or below *its* target, and by how much? |
| Finance | Forecasting | What is unbilled capacity worth? |
| HR / People Ops | Hybrid working policy | Does working location relate to utilisation? |

## 4. As-Is

- Utilisation reported monthly as one firm-wide percentage.
- A single target applied to every role, so the number is disputed and largely ignored.
- Capacity held in a spreadsheet, timesheets in a separate system; joining them is manual.
- Under-utilisation expressed only as a percentage — never valued.
- Hybrid working debated from opinion; no measurement exists.
- Producing a practice comparison takes an analyst most of a day and is not reproducible.

## 5. To-Be

- One refreshable model joining timesheets and capacity through a shared employee dimension.
- Utilisation measured against **each role's own target**, so the comparison is fair and the number is trusted again.
- The gap to target valued in euros, at each practice's realised rate.
- Practice trends over time, so a persistent gap is distinguishable from a bad quarter.
- Utilisation split by work location, giving the hybrid debate a measured basis.

## 6. Scope

**In scope**

- Weekly timesheets and capacity for 60 employees, four practices, three offices
- Period January 2024 – December 2025
- Utilisation against role-specific targets; gap valued in euros
- Revenue, delivery cost and gross margin
- Utilisation by work location

**Out of scope**

- Forward pipeline and demand forecasting
- What-if scenario modelling — hiring, attrition, pipeline conversion
- Individual performance management; the report stops at practice and role level
- Headcount and attrition analysis
- Project profitability and fixed-price margin tracking
- Row-level security

## 7. Success criteria

| # | Criterion | Measure of success |
|---|---|---|
| 1 | The utilisation number is trusted again | Every person measured against their own role's target, and the method documented |
| 2 | The idle practice is visible | Gap to target shown per practice, not as a firm average |
| 3 | The shortfall prompts a decision | Gap valued in euros at each practice's realised rate |
| 4 | Persistent problems distinguished from bad quarters | Practice utilisation trended over eight quarters |
| 5 | The hybrid question has evidence | Utilisation split by work location, with the limits of the finding stated |

## 8. Assumptions

- Standard working week is 37.5 hours, the Finnish norm.
- Capacity is reduced for holiday seasonality rather than utilisation being marked down.
- Delivery cost is 45% of billing rate.
- A week is attributed to a single work location.
- Time logged is complete and accurate — no allowance for under-reporting.

## 9. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| One target applied to all roles | The number is disputed and ignored, as today | Target held per person in the data, never averaged in DAX |
| Targets averaged across a mixed role group | Wrong benchmark exactly when practices differ most | `Target Utilisation %` divides two capacity-weighted sums |
| Over-target practices offsetting under-target ones | Firm-wide risk understated to zero | `MAX(…, 0)` in `Hours Below Target` |
| July read as underperformance | Wrong conclusion every summer | Holiday modelled as reduced capacity, and called out in the report |
| Location finding read as causal | A return-to-office policy built on a correlation | The limit is stated on the page and in the KPI catalogue |
| Report used for individual performance | Trust lost, timesheets gamed | Reporting stops at practice and role level; no individual view |

## 10. Deliverables

| # | Deliverable |
|---|---|
| 1 | Power BI model — star schema, two facts, conformed employee and date dimensions |
| 2 | Overview page — utilisation against target, trend, practice and industry breakdown |
| 3 | Practice Detail page — gap to target, gap valued, practice trends, role matrix, work location |
| 4 | KPI catalogue documenting every measure, business rule and assumption |
| 5 | Report published with a shareable link |
