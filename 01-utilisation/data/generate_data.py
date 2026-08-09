"""
Synthetic dataset for the Consultancy Utilisation & Bench Cost report.

Builds two years of weekly timesheets for a fictional 60-person Nordic
software consultancy: four practices, five role levels, three offices, and a
hybrid mix of office, home and client-site working.

Why synthetic: timesheet data is commercially sensitive and identifies
individuals. Shipping the generator instead makes the whole dataset
reproducible from one fixed seed.

Why not just random numbers: the report's question is whether a practice is
above or below *its own* target, and that only means something if practices
and role levels genuinely differ. Each is given its own utilisation profile,
billing rate and working pattern.

Two relationships the report examines:

  1. The Design practice runs well below its target through 2025 while
     Delivery runs slightly above. Design also bills at a higher rate, so its
     idle capacity is the expensive kind — visible only once the gap is
     priced rather than left as a percentage.
  2. Weeks worked mainly at a client site show higher billable utilisation
     than weeks worked from home. This is the hybrid-work question the
     underlying Master's thesis set out to answer.

The data is clean on purpose. No nulls, no duplicates, no inconsistent
spellings. Power Query here is load, check types, apply.

Capacity Hours, Revenue and Cost are pre-computed as columns. Deriving
capacity in DAX means reconstructing headcount by week from hire and exit
dates; as a column it is a plain SUM.

Usage:  pip install pandas numpy faker
        python generate_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from faker import Faker
from pathlib import Path

SEED = 20260808
rng = np.random.default_rng(SEED)
fake = Faker("en_GB")
Faker.seed(SEED)

OUT = Path(__file__).parent
START = pd.Timestamp("2024-01-01")   # a Monday
END = pd.Timestamp("2025-12-29")
STANDARD_WEEK = 37.5                  # Finnish norm
N_EMPLOYEES = 60


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

# target – the utilisation this role is expected to hit. Varying it by level
#          is the point of the report: a principal at 55% billable is
#          performing well, a junior at 55% is a problem. A blanket 75% target
#          would make the whole comparison meaningless.
# rate   – billing rate per hour, EUR
ROLES = [
    # level,        share, target, rate
    ("Junior",      0.22,  0.80,   65),
    ("Consultant",  0.34,  0.78,   95),
    ("Senior",      0.24,  0.72,   130),
    ("Principal",   0.12,  0.55,   175),
    ("Manager",     0.08,  0.30,   150),
]

# multiplier – how this practice performs against its people's targets
# rate_mult  – practices sell at different price points
PRACTICES = [
    # name,       share, multiplier, rate_mult
    ("Delivery",  0.40,  1.03,       1.00),
    ("Design",    0.20,  0.74,       1.15),   # planted: well below target
    ("Data",      0.25,  0.99,       1.10),
    ("Advisory",  0.15,  0.94,       1.25),
]

OFFICES = ["Tampere", "Helsinki", "Stockholm"]
OFFICE_W = [0.45, 0.40, 0.15]

LOCATIONS = [
    (1, "Office", True),
    (2, "Home", False),
    (3, "Client Site", True),
]
dim_work_location = pd.DataFrame(LOCATIONS, columns=[
    "WorkLocationKey", "Work Location", "Is Onsite"])

# Practices differ in how they work: Advisory lives at client sites, Data
# barely leaves home.
LOCATION_MIX = {
    "Delivery": [0.35, 0.50, 0.15],
    "Design":   [0.40, 0.55, 0.05],
    "Data":     [0.25, 0.70, 0.05],
    "Advisory": [0.30, 0.30, 0.40],
}

INDUSTRIES = ["IoT", "HealthTech", "Textile", "Energy", "Fintech", "Public Sector"]

CLIENTS = [
    ("Nordkraft Energi", "Energy"), ("Vantaa Health Group", "HealthTech"),
    ("Lumi Textiles", "Textile"), ("Sensora IoT", "IoT"),
    ("Aurora Pay", "Fintech"), ("City of Tampere", "Public Sector"),
    ("Baltic Grid", "Energy"), ("MediSuomi", "HealthTech"),
    ("Pohjola Mills", "Textile"), ("Nordic Ledger", "Fintech"),
    ("Kaiku Devices", "IoT"), ("Helsinki Transit", "Public Sector"),
]
dim_client = pd.DataFrame(
    [(i + 1, n, ind) for i, (n, ind) in enumerate(CLIENTS)],
    columns=["ClientKey", "Client Name", "Industry"])

PROJECT_TYPES = ["Time & Materials", "Fixed Price", "Internal"]


def build_employees() -> pd.DataFrame:
    levels = rng.choice([r[0] for r in ROLES], size=N_EMPLOYEES,
                        p=[r[1] for r in ROLES])
    practices = rng.choice([p[0] for p in PRACTICES], size=N_EMPLOYEES,
                           p=[p[1] for p in PRACTICES])
    target = {r[0]: r[2] for r in ROLES}
    rate = {r[0]: r[3] for r in ROLES}
    rate_mult = {p[0]: p[3] for p in PRACTICES}

    rows = []
    for i in range(N_EMPLOYEES):
        level, practice = levels[i], practices[i]
        rows.append((
            i + 1, fake.name(), practice, level,
            rng.choice(OFFICES, p=OFFICE_W),
            round(target[level], 2),
            round(rate[level] * rate_mult[practice], 2),
        ))
    return pd.DataFrame(rows, columns=[
        # "Role Target %", not "Target Utilisation %". The model has a measure
        # of that name already, and a column sharing it shows up twice in the
        # field list with no way to tell them apart. They are also different
        # things: this is one role's flat target, the measure is the
        # capacity-weighted target of whatever group is in filter context.
        "EmployeeKey", "Employee Name", "Practice", "Role Level", "Office",
        "Role Target %", "Billing Rate"])


dim_employee = build_employees()
EMP = dim_employee.set_index("EmployeeKey").to_dict("index")


def build_projects() -> pd.DataFrame:
    """
    Client name and industry are carried on the project rather than held in a
    separate DimClient. A client dimension would have to hang off DimProject,
    since the fact has no ClientKey — and a dimension joined to another
    dimension is a snowflake, not a star. Denormalising one level keeps every
    relationship running dimension to fact.
    """
    rows = []
    for i in range(28):
        client = int(rng.integers(0, len(CLIENTS)))
        client_name, industry = CLIENTS[client]
        practice = rng.choice([p[0] for p in PRACTICES],
                              p=[p[1] for p in PRACTICES])
        ptype = rng.choice(PROJECT_TYPES, p=[0.60, 0.30, 0.10])
        work = rng.choice(["Platform", "Migration", "Discovery", "Rollout", "Support"])
        rows.append((i + 1, f"{client_name} - {work}", client_name, industry,
                     practice, ptype))
    # Every practice needs an internal bucket for non-billable time.
    for j, (practice, *_) in enumerate(PRACTICES):
        rows.append((29 + j, f"Internal - {practice}", "Internal",
                     "Internal", practice, "Internal"))
    return pd.DataFrame(rows, columns=[
        "ProjectKey", "Project Name", "Client Name", "Industry",
        "Practice", "Project Type"])


dim_project = build_projects()
PROJECTS_BY_PRACTICE = {
    p[0]: dim_project[(dim_project["Practice"] == p[0]) &
                      (dim_project["Project Type"] != "Internal")]["ProjectKey"].tolist()
    for p in PRACTICES}
INTERNAL_BY_PRACTICE = {
    p[0]: dim_project[(dim_project["Practice"] == p[0]) &
                      (dim_project["Project Type"] == "Internal")]["ProjectKey"].iloc[0]
    for p in PRACTICES}


# ---------------------------------------------------------------------------
# Weekly simulation
# ---------------------------------------------------------------------------

WEEKS = pd.date_range(START, END, freq="W-MON")

# Finnish summer. Almost the whole country is on holiday in July, and the
# report has to show that as a real seasonal dip rather than a data problem.
SEASON = {1: 0.95, 2: 1.00, 3: 1.00, 4: 0.97, 5: 1.00, 6: 0.88,
          7: 0.55, 8: 0.92, 9: 1.02, 10: 1.02, 11: 1.00, 12: 0.80}


def design_dip(practice: str, week: pd.Timestamp) -> float:
    """
    Planted relationship 1 — Design falls away through 2025.

    Delivery holds slightly above target throughout, so the contrast is
    between two practices rather than one practice against an average.
    """
    if practice != "Design":
        return 1.0
    if week.year < 2025:
        return 1.0
    progress = (week - pd.Timestamp("2025-01-01")).days / 364
    return 1.0 - min(progress, 1.0) * 0.22


def simulate():
    timesheets, capacity = [], []
    ts_key = cap_key = 1

    for emp_key, emp in EMP.items():
        practice = emp["Practice"]
        base_target = emp["Role Target %"]
        practice_mult = dict((p[0], p[2]) for p in PRACTICES)[practice]
        loc_mix = LOCATION_MIX[practice]

        for week in WEEKS:
            # --- capacity -------------------------------------------
            cap = STANDARD_WEEK * SEASON[week.month]
            cap = float(np.round(cap, 1))
            # Target Hours is capacity at this person's own target. Carrying
            # it as a column keeps the target role-specific without needing
            # DAX to average targets across a mixed group, which would be
            # wrong whenever the role mix differs between practices.
            target_hours = float(np.round(cap * base_target, 2))
            capacity.append((cap_key, week, emp_key, cap, target_hours))
            cap_key += 1

            # --- how the week was worked ----------------------------
            location = int(rng.choice([1, 2, 3], p=loc_mix))

            # Planted relationship 2: a week spent mainly at a client site
            # converts to billable time more readily than a week at home.
            location_effect = {1: 1.00, 2: 0.96, 3: 1.12}[location]

            billable_share = (base_target * practice_mult
                              * design_dip(practice, week)
                              * location_effect
                              * float(rng.normal(1.0, 0.10)))
            billable_share = float(np.clip(billable_share, 0.05, 0.98))

            worked = cap * float(np.clip(rng.normal(0.97, 0.06), 0.55, 1.10))
            billable_hours = float(np.round(worked * billable_share, 1))
            other_hours = float(np.round(max(worked - billable_hours, 0), 1))

            rate = emp["Billing Rate"]
            cost_rate = round(rate * 0.45, 2)

            # --- billable time, split across one or two projects -----
            if billable_hours > 0.5:
                pool = PROJECTS_BY_PRACTICE[practice]
                n_proj = 1 if rng.random() < 0.65 else 2
                chosen = rng.choice(pool, size=min(n_proj, len(pool)), replace=False)
                splits = rng.dirichlet(np.ones(len(chosen)))
                for proj, share in zip(chosen, splits):
                    hrs = float(np.round(billable_hours * share, 1))
                    if hrs < 0.5:
                        continue
                    timesheets.append((
                        ts_key, week, emp_key, int(proj), location, hrs, True,
                        float(np.round(hrs * rate, 2)),
                        float(np.round(hrs * cost_rate, 2))))
                    ts_key += 1

            # --- non-billable time ----------------------------------
            if other_hours > 0.5:
                timesheets.append((
                    ts_key, week, emp_key, int(INTERNAL_BY_PRACTICE[practice]),
                    location, other_hours, False,
                    0.0, float(np.round(other_hours * cost_rate, 2))))
                ts_key += 1

    fact_timesheet = pd.DataFrame(timesheets, columns=[
        "TimesheetKey", "Week Start Date", "EmployeeKey", "ProjectKey",
        "WorkLocationKey", "Hours", "Is Billable", "Revenue", "Cost"])
    fact_capacity = pd.DataFrame(capacity, columns=[
        "CapacityKey", "Week Start Date", "EmployeeKey",
        "Capacity Hours", "Target Hours"])
    return fact_timesheet, fact_capacity


fact_timesheet, fact_capacity = simulate()


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

TABLES = {
    "DimEmployee": dim_employee,
    "DimProject": dim_project,
    "DimWorkLocation": dim_work_location,
    "FactTimesheet": fact_timesheet,
    "FactCapacity": fact_capacity,
}

for name, frame in TABLES.items():
    path = OUT / f"{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    print(f"{name:<18} {len(frame):>7,} rows   {path.stat().st_size / 1024:>7,.0f} KB")


# ---------------------------------------------------------------------------
# Self-check — the report is verified against these figures
# ---------------------------------------------------------------------------

billable = fact_timesheet[fact_timesheet["Is Billable"]]
cap_total = fact_capacity["Capacity Hours"].sum()
target_total = fact_capacity["Target Hours"].sum()
billable_hours = billable["Hours"].sum()
util = billable_hours / cap_total
revenue = fact_timesheet["Revenue"].sum()
cost = fact_timesheet["Cost"].sum()
eff_rate = revenue / billable_hours
below = max(target_total - billable_hours, 0)

print("\n--- data checks ---\n")
print(f"Utilisation %      {util:8.1%}")
print(f"Target %           {target_total / cap_total:8.1%}")
print(f"Gap to target      {(util - target_total / cap_total) * 100:8.1f} pp")
print(f"Revenue        EUR {revenue:12,.0f}")
print(f"Delivery cost  EUR {cost:12,.0f}")
print(f"Gross margin %     {(revenue - cost) / revenue:8.1%}")
print(f"Capacity hours     {cap_total:12,.0f}")
print(f"Target hours       {target_total:12,.0f}")
print(f"Billable hours     {billable_hours:12,.0f}")
print(f"Hours below target {below:12,.0f}")
print(f"Effective rate EUR {eff_rate:12,.2f}")
print(f"Revenue at risk EUR {below * eff_rate:11,.0f}")

print("\n1. Utilisation vs target by practice")
merged = fact_timesheet.merge(dim_employee, on="EmployeeKey")
capm = fact_capacity.merge(dim_employee, on="EmployeeKey")
cap_by = capm.groupby("Practice")["Capacity Hours"].sum()
tgt_by = capm.groupby("Practice")["Target Hours"].sum()
bill_by = merged[merged["Is Billable"]].groupby("Practice")["Hours"].sum()
rev_by = merged.groupby("Practice")["Revenue"].sum()
rate_by = rev_by / bill_by
summary = pd.DataFrame({
    "utilisation": bill_by / cap_by,
    "target": tgt_by / cap_by,
    "gap_pp": (bill_by / cap_by - tgt_by / cap_by) * 100,
    "eff_rate": rate_by,
    "hrs_below": (tgt_by - bill_by).clip(lower=0),
}).sort_values("gap_pp")
summary["revenue_at_risk"] = summary["hrs_below"] * summary["eff_rate"]
print(summary.to_string(float_format=lambda v: f"{v:,.2f}"))

print("\n   Design vs Delivery, utilisation by quarter")
merged["Q"] = pd.PeriodIndex(merged["Week Start Date"], freq="Q").astype(str)
capq = fact_capacity.merge(dim_employee, on="EmployeeKey")
capq["Q"] = pd.PeriodIndex(capq["Week Start Date"], freq="Q").astype(str)
for practice in ("Design", "Delivery"):
    b = merged[(merged["Practice"] == practice) & merged["Is Billable"]] \
        .groupby("Q")["Hours"].sum()
    c = capq[capq["Practice"] == practice].groupby("Q")["Capacity Hours"].sum()
    series = "  ".join(f"{q} {v:.0%}" for q, v in (b / c).items())
    print(f"     {practice:<9} {series}")

# Billable share, not utilisation. FactCapacity has no work location --
# capacity is not worked anywhere, it simply exists -- so dividing billable
# hours by capacity here would mean back-filling a location onto capacity
# from whatever the employee happened to log that week. That is what this
# check used to do, and it printed 74.8 / 61.4 / 60.4: numbers that appear
# nowhere in the report and disagree with every figure in the README.
# Billable share takes both halves from the timesheet, where a location
# genuinely exists, and matches the report exactly.
print("\n2. Billable share by work location")
loc = merged.merge(dim_work_location, on="WorkLocationKey")
b = loc[loc["Is Billable"]].groupby("Work Location")["Hours"].sum()
t = loc.groupby("Work Location")["Hours"].sum()
for name, v in (b / t).sort_values(ascending=False).items():
    print(f"   {name:<13} {v:6.1%}  {'#' * int(v * 60)}")
