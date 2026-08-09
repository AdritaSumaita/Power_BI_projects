# KPI catalogue — Consultancy Utilisation & Bench Cost

Every measure in the model: what it means in business terms, how it is calculated, and **the decision it supports**. A measure that supports no decision should not be in the model.

---

## Conventions

- All measures live in the `_Measures` table.
- Division always uses `DIVIDE()`, never `/`, so a zero denominator returns blank rather than erroring the visual.
- Formatting is set on the measure, not the visual.
- **No column shares a name with a measure.** `DimEmployee[Role Target %]` is the flat target held against each role in the data; `Target Utilisation %` is the measure that weights those targets by capacity for whatever group is in filter context. They were both called `Target Utilisation %` at first, which put two indistinguishable entries in the field list and disguised the fact that they answer different questions at different grains.

---

## Business rules and assumptions

| Rule | Decision | Rationale |
|---|---|---|
| **Utilisation denominator** | Capacity hours, not hours logged | Utilisation must fall when someone is idle. Dividing by hours *logged* would show 100% for a person who logged nothing but a single billable hour. |
| **Role-specific targets** | Each role has its own target: Junior 80%, Consultant 78%, Senior 72%, Principal 55%, Manager 30% | A principal's week is meant to include selling and mentoring. Measured against a blanket 75%, a well-performing principal looks like a failure and an underperforming junior looks acceptable. Both readings are wrong. |
| **`Target Hours` pre-computed** | Held per person, per week, in `FactCapacity` | Averaging targets in DAX gives the wrong benchmark whenever the role mix differs between practices — which is exactly when the comparison matters. |
| **Summer capacity** | July capacity is ~45% lower | Finnish holiday season. Modelled as reduced *capacity*, and billable hours fall proportionally — so **utilisation itself is unchanged in July** (63.6% and 62.5% in the two Julys, in line with every other month). A quiet summer does not read as underperformance, which is exactly why a ratio is the right metric here: plot absolute billable hours and you get a cliff every year that says nothing. |
| **Cost rate** | 45% of billing rate | An **assumption**. It drives `Gross Margin %` and nothing else. |
| **Client name and industry** | Held on `DimProject`, not a separate `DimClient` | The fact table has no client key, so a client dimension would hang off the project dimension — a snowflake rather than a star. |

---

## 01 Hours

| Measure | Business definition | DAX |
|---|---|---|
| **Billable Hours** | Time charged to a client | `CALCULATE(SUM(FactTimesheet[Hours]), FactTimesheet[Is Billable] = TRUE())` |
| **Total Hours** | All time logged, billable or not | `SUM(FactTimesheet[Hours])` |
| **Capacity Hours** | Time available to work, net of holiday | `SUM(FactCapacity[Capacity Hours])` |
| **Target Hours** | Capacity × each person's own target | `SUM(FactCapacity[Target Hours])` |

---

## 02 Utilisation

**This is the report.** Everything else supports it.

| Measure | Question it answers | DAX |
|---|---|---|
| **Utilisation %** | How much of our capacity did we sell? | `DIVIDE([Billable Hours], [Capacity Hours])` |
| **Target Utilisation %** | How much *should* this group have sold? | `DIVIDE([Target Hours], [Capacity Hours])` |
| **Utilisation Gap pp** | Are we ahead or behind, in points | `[Utilisation %] - [Target Utilisation %]` |
| **Billable Share %** | Of the hours actually worked, what share was billable | `DIVIDE([Billable Hours], [Total Hours])` |

> ### Why work location needs `Billable Share %`, not `Utilisation %`
>
> `FactCapacity` records hours available per employee per week. **It has no work location** — capacity is not worked anywhere, it simply exists.
>
> So slicing `Utilisation %` by `Work Location` filters the numerator and leaves the denominator at the firm total. Each bar becomes *that location's share of total capacity*, and the three bars sum to 62.7% — the firm-wide figure. Plausible-looking, entirely wrong, and Home comes out highest purely because most hours are worked there.
>
> `Billable Share %` takes both halves from `FactTimesheet`, which does carry a location. It also removes capacity from the question altogether, so holidays and part-time contracts cannot distort it: *of the time worked in this setting, how much was sold?*
>
> **A measure is only valid on dimensions that can reach every table it touches.**

> **Why `Target Utilisation %` is a division and not an average.**
> `AVERAGE(DimEmployee[Role Target %])` would weight every person equally regardless of how many hours they were available. A practice of eight managers and two juniors would get a target near 40%; the same practice weighted by capacity gets something quite different. Dividing two pre-computed sums keeps the benchmark honest whatever the role mix.

**Supports:** which practice to intervene in, and whether the intervention is warranted at all — a practice 1 point below target does not need one.

---

## 03 Money

| Measure | Business definition | DAX |
|---|---|---|
| **Revenue** | Fees earned | `SUM(FactTimesheet[Revenue])` |
| **Delivery Cost** | Salary cost of time logged | `SUM(FactTimesheet[Cost])` |
| **Gross Margin %** | Margin after delivery cost | `DIVIDE([Revenue] - [Delivery Cost], [Revenue])` |
| **Effective Hourly Rate** | Average realised rate per billable hour | `DIVIDE([Revenue], [Billable Hours])` |

---

## 04 The gap, priced

```dax
Hours Below Target = MAX([Target Hours] - [Billable Hours], 0)
```
```dax
Revenue at Risk = [Hours Below Target] * [Effective Hourly Rate]
```

**Supports:** whether the shortfall is worth acting on, and where the money is.

A director hears *"we are 8.8 points below target"* and nods. They hear ***"that is €2.28 million"*** and act. Same fact, different unit — and the second one is the version that gets a decision made.

`MAX(…, 0)` prevents a practice that is *over* target contributing a negative and quietly offsetting one that is under. Without it, a firm with one practice 10 points up and another 10 points down would report zero risk, which is the opposite of true — the shortfall is real and the surplus cannot be transferred.

> ### `Revenue at Risk` does not sum across practices — and should not
>
> The four practice rows come to **€2,382,972** against a firm card of **€2,280,493**. Both are correct.
>
> `Hours Below Target` *is* additive — 19,154.55 hours either way. `Effective Hourly Rate` is not: it re-evaluates in every filter context, so each practice values its own gap at its own realised rate while the card values every hour at the firm's blended €119.06.
>
> The **€102,479** difference is entirely Design's rate premium — it holds 77% of the shortfall hours and bills €125.40 against a blend of €119.06. Whenever the shortfall concentrates in an above-blend practice, the rows will exceed the total.
>
> **Forcing them to agree would destroy the finding.** Valuing every idle hour at the firm average erases the fact that the idle capacity sits in the *expensive* practice — which is the whole point. So the rows stay at practice rates, the card stays blended, and €2.28M is read as the conservative figure of the two.
>
> A second non-additivity is latent here. `MAX(…, 0)` would also stop the *hours* summing if any practice were over target. All four are under, so they happen to agree — a property of this data, not of the measure.
>
> **Never divide a locally-rated numerator by a blend-rated denominator.** Design's share of the shortfall is 77% (hours) or 78% (money, like-for-like) — not the 81% that €1,851,313 ÷ €2,280,493 appears to give.

---

## The findings

### 1. Design is a quarter of the firm and three quarters of the problem

| Practice | Utilisation | Target | Gap | Revenue at risk |
|---|---:|---:|---:|---:|
| **Design** | **48.2%** | 72.1% | **−23.9 pp** | **€1,851,313** |
| Data | 65.3% | 69.9% | −4.6 pp | €284,754 |
| Advisory | 72.0% | 76.4% | −4.4 pp | €177,627 |
| Delivery | 69.0% | 69.9% | −0.9 pp | €69,278 |

Design carries **77%** of the shortfall — 14,763 of 19,155 unbilled hours — with **28%** of the headcount, and bills at the **highest** effective rate in the firm, €125.40/hour against a blend of €119.06. Its idle capacity is the expensive kind.

*(Share stated in hours because the euro figures are non-additive — see §04. Like-for-like on money it is 78%: €1,851,313 of the €2,382,972 practice total.)*

It has also been below target since the first quarter of 2024 and is still falling, while Delivery holds steady:

| | 2024 Q1 | Q2 | Q3 | Q4 | 2025 Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|---|---|---|---|
| **Design** | 52% | 51% | 51% | 51% | 49% | 47% | 43% | **42%** |
| Delivery | 70% | 70% | 69% | 68% | 68% | 69% | 69% | 69% |

**Decision this supports:** a persistent, worsening gap in one practice while its peers hold steady is a **demand problem, not an effort problem**. The answer is sales pipeline or capacity reallocation, not performance management.

### 2. Raw utilisation ranks the roles almost exactly backwards

| Role | Utilisation | Own target | Gap | People |
|---|---:|---:|---:|---:|
| Principal | 53.9% | 55% | **−1.1 pp** | 6 |
| Manager | 25.9% | 30% | −4.1 pp | 3 |
| Consultant | 71.8% | 78% | −6.2 pp | 17 |
| Junior | 69.4% | 80% | −10.6 pp | 12 |
| **Senior** | **59.5%** | **72%** | **−12.5 pp** | **22** |

Read the utilisation column alone and Manager is the firm's worst performer at 25.9%, while Senior looks unremarkable at 59.5%. Read the gap column and the order inverts: **Manager is the second-best in the firm, and Senior is the worst — in the largest role group there is, 22 of 60 people.**

This is the report's founding premise stopped being an argument and became a number. A manager billing 25.9% against a 30% target is doing the job as designed; their week is meant to be management. Flagging them, and missing a senior 12.5 points down, is exactly the failure the role-specific target exists to prevent.

**The matrix therefore shows `Utilisation %` and `Utilisation Gap pp` side by side.** Showing utilisation alone would reproduce the blanket-target error inside a report built to correct it.

It also does not compete with finding 1 — it corroborates it:

| Senior, by practice | Utilisation | Gap | People |
|---|---:|---:|---:|
| **Design** | **48.1%** | **−23.9 pp** | 10 |
| Advisory | 67.3% | −4.7 pp | 3 |
| Data | 67.4% | −4.6 pp | 4 |
| Delivery | 71.2% | −0.8 pp | 5 |

Ten of the firm's 22 seniors sit in Design. Seniors elsewhere are within 5 points of target. **There is no senior problem — there is a Design problem, seen a second time through a different dimension.**

**Decision this supports:** do not open a performance conversation with the senior cohort. The gap is a demand problem in one practice, and the same intervention fixes both views.

### 3. Client-facing weeks bill; remote weeks do not — but read it carefully

Measured as `Billable Share %` — of the hours worked in each setting, the share that was billable.

| Where the hours were worked | Billable share |
|---|---:|
| Client site | **77.2%** |
| Office | 63.6% |
| Home | 62.3% |

Office and home are within one point of each other. **The distinction that matters is not remote versus in-office — it is client-facing versus not.**

> ### The limit of this finding
>
> This is an **association, not a demonstrated cause**. The likeliest explanation is selection: people are at a client site *because* billable work is happening there. Sending someone to a client site would not create billable work.
>
> What the data can support: client-facing weeks and billable weeks travel together. What it cannot support: a return-to-office policy.
>
> Stating that limit is the point. A dashboard that overclaims is worse than one that says less.
