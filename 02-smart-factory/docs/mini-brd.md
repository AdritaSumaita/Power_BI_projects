# Mini-BRD — Smart Textile Factory: OEE & Downtime

**Client:** Aurora Textiles Oy (fictional)
**Author:** Sumaita Faria Karim Adrita
**Version:** 1.0
**Status:** Complete
**Date:** 4 August 2026

---

## 1. Problem statement

Aurora Textiles runs 12 machines across three lines on a three-shift pattern. Production reports OEE monthly as a single plant figure.

That figure is the problem. OEE is the product of three independent losses — availability, performance and quality — and each belongs to a different department. Reported fused together, the number says something is wrong without saying what, so it generates concern rather than action. In practice every dip is answered with maintenance spend, because maintenance is the department that gets asked.

Three specific gaps:

1. **OEE is never decomposed.** Nobody can say whether the loss is stoppages, speed or scrap, so nobody can be accountable for it.
2. **Downtime is reported in total hours, not by reason.** Improvement effort is spread evenly instead of aimed at the few causes that dominate.
3. **Equipment problems and process problems look identical in the reporting.** A machine that stops because it is worn and a machine that stops because a shift handles it differently produce the same number.

## 2. Objective

Give plant leadership a single view that answers:

> *Which machine and shift should the next improvement week target — and is the problem the equipment or the way it is being run?*

## 3. Stakeholders

| Stakeholder | Interest | Primary question |
|---|---|---|
| Plant Manager | Overall performance | Are we improving, and where is the biggest loss? |
| Production Supervisor | Shift performance | Which machine and shift is underperforming, and why? |
| Maintenance Lead | Asset condition | Which machine is degrading rather than merely old? |

## 4. As-Is

- OEE quoted monthly as one plant-wide percentage, with no breakdown.
- Downtime totalled in hours; reason codes are captured but never reported on.
- Shift comparisons done by recollection, not measurement.
- Machine condition assessed by age and by whoever complains loudest.
- Producing a machine-level comparison takes a supervisor most of a day, and the result is not reproducible.

## 5. To-Be

- One refreshable model joining production and downtime through shared machine, shift and date dimensions.
- OEE decomposed into availability, performance and quality, each attributable to a named owner.
- Downtime ranked by reason so the vital few are obvious.
- Machine × shift comparison on one visual, making a shift-specific problem distinguishable from a machine-specific one.
- Unplanned loss valued in euros, so improvement spend can be argued against the cost of not spending it.

## 6. Scope

**In scope**

- Production and downtime for 12 machines, three lines, three shifts
- Period January 2025 – June 2026
- OEE and its three components; downtime by reason and by category
- Unplanned downtime valued at an assumed hourly contribution rate

**Out of scope**

- Live machine telemetry — this build uses a generated dataset
- Order fulfilment and on-time delivery (OTIF)
- Raw event-log processing; the data arrives pre-aggregated to machine × date × shift
- Maintenance scheduling and spare-parts inventory
- Energy consumption and cost per unit
- Predictive failure modelling

## 7. Success criteria

| # | Criterion | Measure of success |
|---|---|---|
| 1 | OEE is actionable, not just reported | The three components are visible separately, and the dominant loss is named on the page |
| 2 | Improvement effort is aimed | Downtime ranked by reason; the top three causes identifiable in one glance |
| 3 | Equipment and process problems are distinguishable | Machine × shift comparison available on one visual |
| 4 | The report is trusted | `Availability × Performance × Quality` reconciles exactly to OEE; every figure traces to source |
| 5 | The report states its own findings | Each page titled with the question it answers, conclusions written on the page |

## 8. Assumptions

- Planned maintenance is deducted from planned time rather than counted as a loss — the standard OEE treatment.
- The July 2025 shutdown is excluded rather than recorded as zeros.
- Ideal cycle time per machine is the manufacturer's rated speed and does not change over the period.
- Unplanned downtime is valued at **€180 per hour** of lost contribution.
- One row per machine, date and shift is a complete record of that shift.

## 9. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Planned maintenance counted as downtime | Availability understated; the plant looks worse for maintaining its machines | Maintenance deducted from planned time; treatment documented in the KPI catalogue |
| Shutdown period recorded as zeros | Monthly averages dragged down, real trend hidden | Shutdown excluded from the dataset entirely |
| OEE read as a single number again | No change in behaviour — the original problem returns | The three components sit beside it on the same page, with the dominant loss named |
| A low-but-stable machine mistaken for a failing one | Maintenance spent where it is not needed | Trend shown over time, not just an average — a decline is the signal, not a low value |
| Cost figure treated as measured fact | Improvement business case built on a number nobody agreed | The €180/hour rate is labelled an assumption wherever it appears |

## 10. Deliverables

| # | Deliverable |
|---|---|
| 1 | Power BI model — star schema, two facts, conformed dimensions, dedicated date table |
| 2 | Plant Overview page — OEE, its three components, trend against benchmark, downtime by reason |
| 3 | Loss Analysis page — machine × shift comparison, failing-asset trend, loss by category |
| 4 | KPI catalogue documenting every measure, business rule and assumption |
| 5 | Report published with a shareable link |
