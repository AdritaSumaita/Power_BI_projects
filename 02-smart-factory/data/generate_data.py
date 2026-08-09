"""
Synthetic dataset for the Smart Textile Factory OEE report.

Builds 18 months of production for a fictional Finnish textile mill: 12 machines
across three lines, running three shifts a day.

Why synthetic: real manufacturing telemetry is commercially sensitive. Shipping
the generator instead means the whole dataset is reproducible from one fixed
seed, so anyone can rebuild the exact CSVs the report was built on.

Why not just random numbers: OEE only means something if the three losses it
decomposes into behave differently from each other. Each machine is given its
own reliability, speed and scrap profile, and each shift its own operating
pattern, so the relationships between them are genuine rather than accidental.

Two relationships the report examines:

  1. One weaving machine degrades over the period — its stoppages become more
     frequent and its OEE slides. The signature of an asset heading for an
     unplanned failure.
  2. Changeovers on the Finishing line take about twice as long on night shift,
     with the same machines running the same products. That makes it a process
     and training problem rather than an equipment one — which is exactly the
     distinction decomposing OEE is for.

The data is clean on purpose. No nulls, no duplicates, no inconsistent
spellings. Power Query here is load, check types, apply.

Ideal Minutes is pre-computed as a column. Deriving it in DAX needs SUMX with
RELATED against each machine's cycle time; as a column, Performance % is a
single DIVIDE.

Usage:  pip install pandas numpy
        python generate_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

SEED = 20260807
rng = np.random.default_rng(SEED)

OUT = Path(__file__).parent
START = pd.Timestamp("2025-01-01")
END = pd.Timestamp("2026-06-30")
SHIFT_MINUTES = 480  # three 8-hour shifts a day

# Annual maintenance shutdown — the mill stops entirely.
SHUTDOWN = (pd.Timestamp("2025-07-07"), pd.Timestamp("2025-07-20"))


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

# cycle_sec   – ideal seconds per unit; the speed the machine was sold at
# reliability – lower means more frequent and longer stoppages
# perf        – typical speed against ideal, once running
# quality     – typical share of good units
# Values are tuned so plant OEE lands in the high sixties. World class is 85%,
# and a real textile mill typically runs 60–75%. A plant already at 80% would
# have little to improve, which would leave the report with nothing to say.
MACHINES = [
    # id,      name,              line,        maker,      year, cycle, reliab, perf, qual
    ("SPN-01", "Ring Frame 1",    "Spinning",  "Rieter",   2019, 12.0, 0.93, 0.89, 0.988),
    ("SPN-02", "Ring Frame 2",    "Spinning",  "Rieter",   2019, 12.0, 0.92, 0.88, 0.986),
    ("SPN-03", "Ring Frame 3",    "Spinning",  "Trützschler", 2012, 13.5, 0.86, 0.83, 0.978),
    ("SPN-04", "Open-End Frame",  "Spinning",  "Rieter",   2021, 9.5, 0.95, 0.91, 0.990),
    ("WEV-01", "Air-Jet Loom 1",  "Weaving",   "Picanol",  2018, 21.0, 0.90, 0.86, 0.982),
    ("WEV-02", "Air-Jet Loom 2",  "Weaving",   "Picanol",  2018, 21.0, 0.89, 0.85, 0.980),
    ("WEV-03", "Rapier Loom 1",   "Weaving",   "Dornier",  2011, 24.0, 0.85, 0.82, 0.974),
    ("WEV-04", "Rapier Loom 2",   "Weaving",   "Dornier",  2016, 23.0, 0.88, 0.85, 0.979),
    ("WEV-05", "Air-Jet Loom 3",  "Weaving",   "Picanol",  2022, 19.0, 0.94, 0.90, 0.987),
    ("FIN-01", "Stenter Frame",   "Finishing", "Monforts", 2017, 15.0, 0.91, 0.87, 0.984),
    ("FIN-02", "Dyeing Range",    "Finishing", "Thies",    2014, 17.5, 0.88, 0.85, 0.977),
    ("FIN-03", "Coating Line",    "Finishing", "Monforts", 2020, 16.0, 0.93, 0.88, 0.986),
]

dim_machine = pd.DataFrame(
    [(i + 1, m[0], m[1], m[2], m[3], m[4], m[5]) for i, m in enumerate(MACHINES)],
    columns=["MachineKey", "Machine ID", "Machine Name", "Production Line",
             "Manufacturer", "Install Year", "Ideal Cycle Time Sec"])

MACHINE_PROFILE = {i + 1: dict(cycle=m[5], reliability=m[6], perf=m[7],
                               quality=m[8], line=m[2], mid=m[0])
                   for i, m in enumerate(MACHINES)}

SHIFTS = [
    (1, "Morning", 6, "Aino Virtanen"),
    (2, "Evening", 14, "Mikko Laine"),
    (3, "Night", 22, "Petri Koskinen"),
]
dim_shift = pd.DataFrame(SHIFTS, columns=[
    "ShiftKey", "Shift Name", "Shift Start Hour", "Supervisor"])

# Downtime reasons. The weights create a Pareto: the first three account for
# roughly two thirds of unplanned stop time, which is what makes a sorted bar
# chart tell the improvement team where to aim.
REASONS = [
    # key, reason,                 category,    is_planned, weight, typical minutes
    (1, "Yarn Break",             "Material",   False, 0.28, 9),
    (2, "Changeover",             "Operator",   False, 0.22, 26),
    (3, "No Material",            "Material",   False, 0.15, 17),
    (4, "Mechanical Failure",     "Equipment",  False, 0.10, 38),
    (5, "Quality Stop",           "Operator",   False, 0.08, 14),
    (6, "Electrical Fault",       "Equipment",  False, 0.06, 31),
    (7, "Operator Unavailable",   "Operator",   False, 0.06, 12),
    (8, "Waiting for Inspection", "Operator",   False, 0.05, 11),
]
dim_reason = pd.DataFrame(
    [(k, r, c, p) for k, r, c, p, *_ in REASONS] +
    [(9, "Planned Maintenance", "Planned", True),
     (10, "Scheduled Cleaning", "Planned", True)],
    columns=["ReasonKey", "Reason", "Reason Category", "Is Planned"])

REASON_KEYS = [r[0] for r in REASONS]
REASON_W = np.array([r[4] for r in REASONS], dtype=float)
REASON_W /= REASON_W.sum()
REASON_MINUTES = {r[0]: r[5] for r in REASONS}


# ---------------------------------------------------------------------------
# Production simulation
# ---------------------------------------------------------------------------

def degradation_factor(machine_key: int, day_index: int, total_days: int) -> float:
    """
    Planted relationship 1 — WEV-03 deteriorates across the period.

    Returns a multiplier on stoppage frequency and length. Flat at 1.0 for
    every other machine, climbing steadily for WEV-03 from roughly month four
    so the trend is visible on a monthly chart rather than as a single step.
    """
    if MACHINE_PROFILE[machine_key]["mid"] != "WEV-03":
        return 1.0
    progress = day_index / total_days
    if progress < 0.22:
        return 1.0
    return 1.0 + (progress - 0.22) * 2.6


def changeover_factor(machine_key: int, shift_key: int) -> float:
    """
    Planted relationship 2 — Finishing changeovers run long on night shift.

    Same machines, same products, roughly double the time. That points at
    process and training rather than equipment, which is the distinction the
    OEE decomposition exists to expose.
    """
    if MACHINE_PROFILE[machine_key]["line"] == "Finishing" and shift_key == 3:
        return 2.1
    return 1.0


def simulate():
    production, downtime = [], []
    prod_key = down_key = 1
    days = pd.date_range(START, END, freq="D")
    total_days = len(days)

    # Planned maintenance: each machine gets a slot roughly every six weeks,
    # staggered so the whole plant is never down at once.
    maintenance_offset = {k: int(rng.integers(0, 42)) for k in MACHINE_PROFILE}

    for day_index, day in enumerate(days):
        in_shutdown = SHUTDOWN[0] <= day <= SHUTDOWN[1]

        for machine_key, profile in MACHINE_PROFILE.items():
            for shift_key, shift_name, *_ in SHIFTS:

                if in_shutdown:
                    # Whole plant stopped: planned time is zero, so these
                    # shifts contribute nothing to OEE rather than dragging it
                    # to zero. Recording them at all would misstate the metric.
                    continue

                planned = float(SHIFT_MINUTES)
                stops = []

                # --- planned maintenance -------------------------------
                is_maint_day = (day_index + maintenance_offset[machine_key]) % 42 == 0
                if is_maint_day and shift_key == 1:
                    mins = float(np.round(rng.normal(180, 30), 1))
                    mins = float(np.clip(mins, 90, 300))
                    # Maintenance is scheduled, so it comes out of planned time
                    # rather than counting as a loss. This is the standard OEE
                    # treatment and it is documented in the KPI catalogue.
                    planned -= mins
                    stops.append((9, mins, 1))

                if shift_key == 3 and rng.random() < 0.08:
                    mins = float(np.round(rng.normal(35, 8), 1))
                    planned -= max(mins, 0)
                    stops.append((10, max(mins, 0), 1))

                planned = max(planned, 120.0)

                # --- unplanned stoppages -------------------------------
                degrade = degradation_factor(machine_key, day_index, total_days)
                unreliability = (1.0 - profile["reliability"]) * degrade
                # Night shift runs a little thinner on support.
                if shift_key == 3:
                    unreliability *= 1.18

                n_stops = int(rng.poisson(max(unreliability * 36, 0.2)))
                n_stops = min(n_stops, 10)

                for _ in range(n_stops):
                    reason = int(rng.choice(REASON_KEYS, p=REASON_W))
                    base = REASON_MINUTES[reason]
                    mins = float(np.round(rng.gamma(2.2, base / 2.2), 1))
                    if reason == 2:  # Changeover
                        mins *= changeover_factor(machine_key, shift_key)
                    mins = float(np.round(min(mins, planned * 0.5), 1))
                    if mins > 0.5:
                        stops.append((reason, mins, 1))

                unplanned_minutes = sum(m for r, m, _ in stops if r not in (9, 10))
                run = max(planned - unplanned_minutes, 30.0)

                # --- speed and quality ---------------------------------
                perf = profile["perf"] * float(rng.normal(1.0, 0.02))
                if shift_key == 3:
                    perf *= 0.97
                if degrade > 1.0:
                    perf *= 1.0 - (degrade - 1.0) * 0.06
                perf = float(np.clip(perf, 0.60, 0.99))

                quality = float(np.clip(profile["quality"] * rng.normal(1.0, 0.004),
                                        0.90, 0.999))

                units = int(round(run * 60.0 / profile["cycle"] * perf))
                ideal_minutes = round(units * profile["cycle"] / 60.0, 1)
                units_good = int(round(units * quality))

                production.append((prod_key, day, machine_key, shift_key,
                                   round(planned, 1), round(run, 1),
                                   ideal_minutes, units, units_good))
                prod_key += 1

                # Roll the stops up to one row per reason per shift.
                if stops:
                    frame = {}
                    for reason, mins, count in stops:
                        acc = frame.setdefault(reason, [0.0, 0])
                        acc[0] += mins
                        acc[1] += count
                    for reason, (mins, count) in frame.items():
                        downtime.append((down_key, day, machine_key, shift_key,
                                         reason, round(mins, 1), count))
                        down_key += 1

    fact_production = pd.DataFrame(production, columns=[
        "ProductionKey", "Date", "MachineKey", "ShiftKey",
        "Planned Minutes", "Run Minutes", "Ideal Minutes",
        "Units Produced", "Units Good"])
    fact_downtime = pd.DataFrame(downtime, columns=[
        "DowntimeKey", "Date", "MachineKey", "ShiftKey", "ReasonKey",
        "Downtime Minutes", "Stop Count"])
    return fact_production, fact_downtime


fact_production, fact_downtime = simulate()


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

TABLES = {
    "DimMachine": dim_machine,
    "DimShift": dim_shift,
    "DimReason": dim_reason,
    "FactProduction": fact_production,
    "FactDowntime": fact_downtime,
}

for name, frame in TABLES.items():
    path = OUT / f"{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    print(f"{name:<18} {len(frame):>8,} rows   {path.stat().st_size / 1024:>7,.0f} KB")


# ---------------------------------------------------------------------------
# Self-check — the report is verified against these figures
# ---------------------------------------------------------------------------

def oee(frame: pd.DataFrame) -> tuple[float, float, float, float]:
    a = frame["Run Minutes"].sum() / frame["Planned Minutes"].sum()
    p = frame["Ideal Minutes"].sum() / frame["Run Minutes"].sum()
    q = frame["Units Good"].sum() / frame["Units Produced"].sum()
    return a, p, q, a * p * q

print("\n--- data checks ---")

a, p, q, o = oee(fact_production)
print(f"\nPlant totals")
print(f"  Availability   {a:6.1%}")
print(f"  Performance    {p:6.1%}")
print(f"  Quality        {q:6.1%}")
print(f"  OEE            {o:6.1%}")
print(f"  Planned min    {fact_production['Planned Minutes'].sum():>12,.0f}")
print(f"  Run min        {fact_production['Run Minutes'].sum():>12,.0f}")
print(f"  Units produced {fact_production['Units Produced'].sum():>12,.0f}")
print(f"  Downtime min   {fact_downtime['Downtime Minutes'].sum():>12,.0f}")

print("\n1. OEE by machine  (WEV-03 should be lowest)")
by_machine = (fact_production.merge(dim_machine, on="MachineKey")
              .groupby(["Production Line", "Machine ID"])
              .apply(lambda f: pd.Series(dict(zip(
                  ["Availability", "Performance", "Quality", "OEE"], oee(f)))),
                  include_groups=False))
print(by_machine.to_string(float_format=lambda v: f"{v:.1%}"))

print("\n   WEV-03 OEE by quarter (should decline)")
wev = fact_production.merge(dim_machine, on="MachineKey")
wev = wev[wev["Machine ID"] == "WEV-03"].copy()
wev["Quarter"] = wev["Date"].dt.to_period("Q").astype(str)
for quarter, grp in wev.groupby("Quarter"):
    _, _, _, o_q = oee(grp)
    bar = "#" * int(o_q * 70)
    print(f"     {quarter}  {o_q:6.1%}  {bar}")

print("\n2. Changeover minutes per shift, Finishing line (night should be ~2x)")
chg = (fact_downtime[fact_downtime["ReasonKey"] == 2]
       .merge(dim_machine, on="MachineKey").merge(dim_shift, on="ShiftKey"))
fin = chg[chg["Production Line"] == "Finishing"]
other = chg[chg["Production Line"] != "Finishing"]
for label, frame in (("Finishing", fin), ("Other lines", other)):
    per_shift = frame.groupby("Shift Name")["Downtime Minutes"].mean()
    line = "  ".join(f"{s} {v:5.1f}" for s, v in per_shift.items())
    print(f"   {label:<12} {line}")
night = fin[fin["Shift Name"] == "Night"]["Downtime Minutes"].mean()
day = fin[fin["Shift Name"] == "Morning"]["Downtime Minutes"].mean()
print(f"   -> Finishing night is {night / day:.1f}x the morning average")

print("\n3. Downtime Pareto  (top three should be ~65% of unplanned time)")
unplanned = fact_downtime.merge(dim_reason, on="ReasonKey")
unplanned = unplanned[~unplanned["Is Planned"]]
share = (unplanned.groupby("Reason")["Downtime Minutes"].sum()
         .sort_values(ascending=False))
cum = 0.0
for reason, minutes in share.items():
    pct = minutes / share.sum()
    cum += pct
    print(f"   {reason:<24} {minutes:>9,.0f} min  {pct:5.1%}  cumulative {cum:5.1%}")
