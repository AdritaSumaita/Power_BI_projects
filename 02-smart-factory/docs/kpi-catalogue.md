# KPI catalogue — Smart Textile Factory

Every measure in the model: what it means in business terms, how it is calculated, and **the decision it supports**. A measure that supports no decision should not be in the model.

---

## Conventions

- All measures live in the `_Measures` table.
- Division always uses `DIVIDE()`, never `/`, so a zero denominator returns blank rather than erroring the visual.
- Formatting is set on the measure, not the visual, so every visual inherits it.

---

## Business rules and assumptions

| Rule | Decision | Rationale |
|---|---|---|
| **Planned maintenance** | Subtracted from `Planned Minutes`, not counted as a loss | Standard OEE treatment. Time the plant never intended to run is not availability lost — counting it would punish a plant for maintaining its machines. |
| **Plant shutdown (July 2025)** | Excluded entirely — no rows generated | Two weeks of zeros would drag every monthly average down and hide the real trend. |
| **Downtime cost rate** | **€180 per hour** of lost contribution | An **assumption**, not a measured figure. It converts minutes into money so the loss can be compared against the cost of fixing it. Change the rate, change every cost figure — which is exactly why it is written down here. |
| **Ideal Minutes** | Pre-computed in the source data | `Units Produced × ideal cycle time`. Deriving it in DAX would need `SUMX` with `RELATED`; as a column, `Performance %` is one `DIVIDE`. |

---

## 01 Raw totals

| Measure | Business definition | DAX |
|---|---|---|
| **Planned Minutes** | Time the plant intended to run, net of scheduled maintenance | `SUM(FactProduction[Planned Minutes])` |
| **Run Minutes** | Time the machine was actually producing | `SUM(FactProduction[Run Minutes])` |
| **Ideal Minutes** | Time the output *should* have taken at design speed | `SUM(FactProduction[Ideal Minutes])` |
| **Units Produced** | Everything made, good or not | `SUM(FactProduction[Units Produced])` |
| **Units Good** | Units that passed inspection | `SUM(FactProduction[Units Good])` |

---

## 02 OEE — the three losses

**This is the point of the report.** A single OEE figure tells a supervisor something is wrong but never what. Split into three, each part has a different owner and a different fix.

| Measure | Question it answers | Owner | DAX |
|---|---|---|---|
| **Availability %** | Of the time we planned to run, how much did we run? | Maintenance | `DIVIDE([Run Minutes], [Planned Minutes])` |
| **Performance %** | While running, how close to design speed? | Production | `DIVIDE([Ideal Minutes], [Run Minutes])` |
| **Quality %** | Of what we made, how much was sellable? | QA | `DIVIDE([Units Good], [Units Produced])` |
| **OEE %** | All three together | Plant Manager | `[Availability %] * [Performance %] * [Quality %]` |
| **OEE Gap to World Class** | Distance from the 85% benchmark | Plant Manager | `[OEE %] - 0.85` |

> **Why the multiplication matters.** Three components at 90% each give **72.9%**, not 90%. Losses compound. A plant can look healthy on every individual measure and still be losing a quarter of its capacity.

### Biggest Loss

```dax
Biggest Loss =
SWITCH(
    TRUE(),
    [Availability %] <= [Performance %] && [Availability %] <= [Quality %], "Availability — stoppages",
    [Performance %] <= [Quality %], "Performance — speed loss",
    "Quality — defects"
)
```

**Supports:** where to send the improvement team this week.

A one-line measure that turns a number into an instruction. It respects whatever filter is applied, so selecting a machine tells you that machine's dominant loss rather than the plant's.

---

## 03 Downtime

| Measure | Business definition | DAX | Supports |
|---|---|---|---|
| **Downtime Minutes** | All recorded stop time | `SUM(FactDowntime[Downtime Minutes])` | Loss ranking |
| **Stop Count** | Number of separate stoppages | `SUM(FactDowntime[Stop Count])` | Frequency vs duration — many short stops and one long stop need different fixes |
| **Unplanned Downtime Minutes** | Stop time excluding maintenance and cleaning | `CALCULATE([Downtime Minutes], DimReason[Is Planned] = FALSE())` | The genuinely avoidable loss |
| **Downtime Cost** | Unplanned loss valued at €180/hour | `DIVIDE([Unplanned Downtime Minutes], 60) * 180` | Justifying improvement spend |
| **Avg Changeover Minutes** | How long a changeover takes, on average | `CALCULATE(AVERAGE(FactDowntime[Downtime Minutes]), DimReason[Reason] = "Changeover")` | Separating a duration problem from a frequency one |

> ### Why `Avg Changeover Minutes` is an average and not a sum
>
> Finding 2 claims changeovers **take longer** on night shift. Total changeover minutes cannot demonstrate that, because night shift records more stoppages across every line — the total mixes *how often* with *how long*.
>
> | Line | By total minutes | By average duration |
> |---|---:|---:|
> | **Finishing** | 2.49× | **2.17×** |
> | Weaving | 1.14× | **1.03×** |
> | Spinning | 1.20× | **1.05×** |
>
> On totals, every line looks somewhat worse at night and the contrast blurs. On averages, Finishing more than doubles while the other two are flat — which is the actual finding, and the version that survives the obvious objection that everything is worse at night.
>
> **A finding is only as good as the measure that carries it.**

**`Downtime Cost` is the measure that changes the conversation.** A plant manager hears "we lost 24,000 hours" and nods. They hear "we lost €4.3 million" and act. Same number, different unit.

---

## The findings

### 1. `WEV-03` is a failing asset

Lowest OEE in the plant at **51.3%**, and declining every quarter:

| 2025 Q1 | Q2 | Q3 | Q4 | 2026 Q1 | Q2 |
|---|---|---|---|---|---|
| 61.9% | 59.9% | 52.0% | 48.3% | 44.1% | **41.7%** |

**A declining trend, not a low average, is what distinguishes a failing asset from a merely old one.** SPN-03 is a year older and stable at 63.9% — it needs no intervention. WEV-03 does, and before it stops entirely.

### 2. Finishing changeovers are a process problem, not an equipment one

Measured as `Avg Changeover Minutes` — the average duration of a changeover, not the total.

| Line | Morning | Evening | Night | Night ÷ Morning |
|---|---:|---:|---:|---:|
| **Finishing** | **38.3** | 38.5 | **83.3** | **2.17×** |
| Spinning | 35.9 | 38.4 | 37.8 | 1.05× |
| Weaving | 43.0 | 42.5 | 44.4 | 1.03× |

**The control is what makes this conclusive.** Spinning and Weaving show no shift difference at all, so it is not a general night-shift effect. Same machines, same products, twice the time — the difference is how the shift is run.

**Decision this supports:** answering it with maintenance spend would fix nothing. It is a training and handover question.
