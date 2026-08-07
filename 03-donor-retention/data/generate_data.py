"""
Synthetic dataset for the Donor Retention & Fundraising Performance report.

Builds a fictional Nordic NGO's fundraising history over four years: 12,000
donors, ~125,000 gifts across seven channels, and what each campaign cost to
run.

Why synthetic: real donor records are GDPR-regulated personal data and have no
place in a public repository. Committing the generator instead means the whole
dataset is reproducible from one fixed seed — anyone can rebuild the exact CSVs
the report was built on.

Why not just random numbers: real fundraising data has structure, and a
dashboard built on uniform noise has nothing to say. Each channel is given its
own economics — acquisition cost, gift size, likelihood of recurring giving —
so that the relationships between them are genuine rather than accidental.

The relationship the report examines is between volume and value. Face-to-Face
is configured to recruit the most donors at the highest cost per donor, so
gross income ranks it near the top while return on investment ranks it last.
That reversal is the point of the report, and it emerges from the channel
economics below rather than being written in directly.

Seasonality is modelled too: December carries the Christmas appeal at roughly
a quarter of annual income, and the Nordic summer is quiet.

The dataset also carries structure the current report does not chart — notably
that emergency-appeal donors give again far more often when a follow-up
campaign ran. It is left in so the data rewards further analysis.

Deliberate imperfections, each cleaned in Power Query and documented in
docs/kpi-catalogue.md: ~360 donors with no country, 40 duplicate records, and
30 refunds recorded as negative gifts.

Usage:  pip install pandas numpy faker
        python generate_data.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from faker import Faker
from pathlib import Path

SEED = 20260802
rng = np.random.default_rng(SEED)
fake = Faker("en_GB")
Faker.seed(SEED)

OUT = Path(__file__).parent
START = pd.Timestamp("2022-01-01")
END = pd.Timestamp("2025-12-31")
N_DONORS = 12_000


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------

# Each channel behaves differently, and those differences are the whole story.
# share      – proportion of newly acquired donors
# cpa        – acquisition cost per donor, in EUR
# retention  – probability a donor is still giving 12 months on
# recurring  – probability the donor signs a monthly pledge rather than one-offs
# gift_mu    – lognormal mu for one-off gift size
CHANNELS = [
    # key, name,             group,        digital, share, cpa,  retention, recurring, gift_mu
    (1, "Face-to-Face", "Acquisition", False, 0.40, 180.0, 0.45, 0.88, 3.10),
    (2, "Digital Paid", "Acquisition", True, 0.24, 90.0, 0.60, 0.45, 3.25),
    (3, "Digital Organic", "Retention", True, 0.10, 12.0, 0.66, 0.35, 3.30),
    (4, "Direct Mail", "Retention", False, 0.12, 120.0, 0.78, 0.30, 3.70),
    (5, "Telemarketing", "Retention", False, 0.08, 70.0, 0.56, 0.60, 3.20),
    (6, "Events", "Acquisition", False, 0.05, 60.0, 0.50, 0.20, 3.45),
    (7, "Major Gifts", "High Value", False, 0.01, 2000.0, 0.90, 0.10, 8.40),
]

dim_channel = pd.DataFrame(
    [(k, n, g, d) for k, n, g, d, *_ in CHANNELS],
    columns=["ChannelKey", "Channel Name", "Channel Group", "Is Digital"],
)
CH = {k: dict(zip(["share", "cpa", "retention", "recurring", "gift_mu"], rest))
      for k, _n, _g, _d, *rest in CHANNELS}

COUNTRIES = ["FI", "SE", "NO", "DK"]
COUNTRY_W = [0.42, 0.28, 0.18, 0.12]
REGIONS = {
    "FI": ["Uusimaa", "Pirkanmaa", "Varsinais-Suomi", "Pohjois-Pohjanmaa"],
    "SE": ["Stockholm", "Västra Götaland", "Skåne", "Uppsala"],
    "NO": ["Oslo", "Vestland", "Trøndelag", "Rogaland"],
    "DK": ["Hovedstaden", "Midtjylland", "Syddanmark", "Sjælland"],
}
AGE_BANDS = ["18-29", "30-44", "45-59", "60-74", "75+"]
AGE_W = [0.14, 0.26, 0.27, 0.23, 0.10]

# Month-of-year weighting. December carries the Christmas appeal and is by far
# the biggest month; the Nordic summer is quiet.
MONTH_WEIGHT = {1: 0.70, 2: 0.80, 3: 0.95, 4: 0.95, 5: 1.00, 6: 0.75,
                7: 0.55, 8: 0.80, 9: 1.05, 10: 1.15, 11: 1.35, 12: 3.60}

# Emergency appeals: sudden, unplanned, and they pull in a burst of one-off
# donors who mostly never give again — unless a follow-up campaign runs.
EMERGENCIES = [
    ("2022-03-08", "Ukraine Emergency Appeal", False),
    ("2022-09-19", "Pakistan Floods Appeal", False),
    ("2023-02-07", "Türkiye–Syria Earthquake Appeal", True),
    ("2023-10-11", "Horn of Africa Drought Appeal", False),
    ("2024-04-15", "East Africa Floods Appeal", True),
    ("2024-09-02", "Sahel Hunger Crisis Appeal", True),
    ("2025-03-21", "Myanmar Earthquake Appeal", False),
    ("2025-08-14", "Caribbean Hurricane Appeal", True),
]


def build_campaigns() -> pd.DataFrame:
    rows, key = [], 1
    for year in range(START.year, END.year + 1):
        for ch_key, ch_name, *_ in CHANNELS:
            rows.append((key, f"{ch_name} Programme {year}", ch_key,
                         pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"),
                         "Regular", 250_000))
            key += 1
        rows.append((key, f"Christmas Appeal {year}", 2,
                     pd.Timestamp(f"{year}-11-15"), pd.Timestamp(f"{year}-12-31"),
                     "Christmas", 600_000))
        key += 1
        rows.append((key, f"Legacy Programme {year}", 4,
                     pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"),
                     "Legacy", 150_000))
        key += 1

    for date_str, name, _followup in EMERGENCIES:
        start = pd.Timestamp(date_str)
        rows.append((key, name, 2, start, start + pd.Timedelta(days=60),
                     "Emergency", 400_000))
        key += 1

    return pd.DataFrame(rows, columns=[
        "CampaignKey", "Campaign Name", "ChannelKey",
        "Start Date", "End Date", "Appeal Type", "Target Amount"])


dim_campaign = build_campaigns()
CAMPAIGN_BY_NAME = dict(zip(dim_campaign["Campaign Name"], dim_campaign["CampaignKey"]))
# Emergency appeal date -> (campaign key, had a follow-up thank-you campaign)
EMERGENCY_LOOKUP = {
    pd.Timestamp(d): (CAMPAIGN_BY_NAME[n], f) for d, n, f in EMERGENCIES
}


def regular_campaign(channel_key: int, when: pd.Timestamp) -> int:
    """The channel's standing programme for that year."""
    name = f"{dim_channel.loc[dim_channel.ChannelKey == channel_key, 'Channel Name'].iloc[0]} Programme {when.year}"
    return CAMPAIGN_BY_NAME[name]


# Fundraisers are no longer written out — the report does not use them. The
# block is kept because removing it would change how many draws the generator
# takes from the seeded random stream, which would shift every value downstream
# and desynchronise the CSVs from the .pbix that was built on them.
TEAMS = ["Tampere", "Helsinki", "Stockholm", "Oslo", "Copenhagen"]
dim_fundraiser = pd.DataFrame([
    (i + 1, fake.name(), TEAMS[i % len(TEAMS)], TEAMS[i % len(TEAMS)],
     START + pd.Timedelta(days=int(rng.integers(0, 900))))
    for i in range(40)
], columns=["FundraiserKey", "Fundraiser Name", "Team", "City", "Start Date"])


# ---------------------------------------------------------------------------
# Donors
# ---------------------------------------------------------------------------

def build_donors() -> pd.DataFrame:
    keys = np.arange(1, N_DONORS + 1)
    channel_keys = rng.choice([c[0] for c in CHANNELS], size=N_DONORS,
                              p=[c[4] for c in CHANNELS])

    # Acquisition is spread across the period but follows the seasonal shape,
    # so December and emergency months recruit more people.
    days = (END - START).days
    day_offsets = np.arange(days)
    dates = START + pd.to_timedelta(day_offsets, unit="D")
    weights = np.array([MONTH_WEIGHT[d.month] for d in dates], dtype=float)
    weights /= weights.sum()
    acquired = START + pd.to_timedelta(
        rng.choice(day_offsets, size=N_DONORS, p=weights), unit="D")

    countries = rng.choice(COUNTRIES, size=N_DONORS, p=COUNTRY_W)
    ages = rng.choice(AGE_BANDS, size=N_DONORS, p=AGE_W)

    return pd.DataFrame({
        "DonorKey": keys,
        "Donor Name": [fake.name() for _ in range(N_DONORS)],
        "Country": countries,
        "Region": [rng.choice(REGIONS[c]) for c in countries],
        "Age Band": ages,
        "Acquisition Date": acquired,
        "Acquisition ChannelKey": channel_keys,
        "Donor Type": rng.choice(["Individual", "Corporate", "Trust"],
                                 size=N_DONORS, p=[0.94, 0.045, 0.015]),
        "Consent Status": rng.choice(["Full", "Email only", "Post only"],
                                     size=N_DONORS, p=[0.72, 0.20, 0.08]),
    })


dim_donor = build_donors()


# ---------------------------------------------------------------------------
# Giving simulation
# ---------------------------------------------------------------------------

def month_starts(first: pd.Timestamp, last: pd.Timestamp):
    return pd.date_range(first.to_period("M").to_timestamp(), last, freq="MS")


def pledge_hazard(tenure: int, base: float) -> float:
    """
    Monthly probability a pledge is cancelled.

    Two spikes are deliberate and both are real patterns: month 3 is when the
    initial enthusiasm of a street sign-up wears off, and month 13 is when the
    card used at sign-up expires.
    """
    if tenure <= 1:
        return base * 1.6
    if tenure == 3:
        return base * 4.2
    if tenure == 13:
        return base * 5.0
    if tenure < 6:
        return base * 1.8
    return base


def simulate():
    donations, pledges = [], []
    donation_key, pledge_key = 1, 1
    payment_methods = ["Card", "Bank Transfer", "MobilePay", "Invoice"]

    for row in dim_donor.itertuples(index=False):
        ch = CH[row._6]  # Acquisition ChannelKey
        acquired = row._5  # Acquisition Date
        is_major = row._6 == 7
        is_recurring = rng.random() < ch["recurring"]

        # Was this donor recruited during an emergency appeal window?
        emergency_key, had_followup = None, False
        for e_date, (c_key, followup) in EMERGENCY_LOOKUP.items():
            if e_date <= acquired <= e_date + pd.Timedelta(days=45):
                emergency_key, had_followup = c_key, followup
                break

        # --- first gift ------------------------------------------------
        mu = ch["gift_mu"]
        if row._5.month == 12:
            mu += 0.15  # people give more generously at Christmas
        first_amount = float(np.round(rng.lognormal(mu, 1.0 if is_major else 0.85), 2))
        donations.append((donation_key, acquired, row.DonorKey,
                          emergency_key or regular_campaign(row._6, acquired),
                          row._6,
                          int(rng.integers(1, 41)) if row._6 in (1, 6) else None,
                          first_amount,
                          "Major Gift" if is_major else ("Recurring" if is_recurring else "One-off"),
                          rng.choice(payment_methods, p=[0.55, 0.25, 0.15, 0.05]),
                          True))
        donation_key += 1

        # --- recurring pledge ------------------------------------------
        if is_recurring:
            monthly = float(np.round(max(5.0, rng.lognormal(2.7, 0.5)), 2))
            base_hazard = 0.022 if ch["retention"] < 0.55 else 0.012
            status, cancelled_on = "Active", None

            for tenure, month in enumerate(month_starts(acquired, END)):
                if status == "Active" and tenure > 0:
                    if rng.random() < pledge_hazard(tenure, base_hazard):
                        status, cancelled_on = "Cancelled", month
                    elif rng.random() < 0.004:
                        status = "Failed Payment"

                pledges.append((pledge_key, row.DonorKey, month, monthly, status,
                                acquired, cancelled_on))
                pledge_key += 1

                if status == "Active" and month > acquired:
                    donations.append((donation_key, month + pd.Timedelta(days=3),
                                      row.DonorKey, regular_campaign(row._6, month),
                                      row._6, None, monthly, "Recurring",
                                      "Card", False))
                    donation_key += 1

                if status in ("Cancelled", "Failed Payment"):
                    break

        # --- one-off giving after acquisition ---------------------------
        # Survival: retention is the probability of still giving after 12
        # months, converted to a monthly continuation probability.
        monthly_survival = ch["retention"] ** (1 / 12)
        alive = 1.0
        for month in month_starts(acquired + pd.offsets.MonthBegin(1), END):
            alive *= monthly_survival
            propensity = alive * MONTH_WEIGHT[month.month] * (0.30 if is_recurring else 0.85)

            # Planted finding 2: an emergency-appeal donor is far likelier to
            # give again within six months when a thank-you campaign ran.
            # Kept moderate on purpose: a large multiplier pushes some cohorts
            # to a ~100% second-gift rate, which no real appeal achieves and
            # which would make the dataset look fabricated.
            if emergency_key and (month - acquired).days <= 190:
                propensity *= 1.65 if had_followup else 0.60

            if rng.random() < propensity * 0.16:
                amount = float(np.round(rng.lognormal(mu, 1.0 if is_major else 0.85), 2))
                is_christmas = month.month == 12
                campaign = (CAMPAIGN_BY_NAME[f"Christmas Appeal {month.year}"]
                            if is_christmas else regular_campaign(row._6, month))
                day = int(rng.integers(1, 27))
                donations.append((donation_key, month + pd.Timedelta(days=day - 1),
                                  row.DonorKey, campaign, row._6, None, amount,
                                  "Major Gift" if is_major else "One-off",
                                  rng.choice(payment_methods, p=[0.55, 0.25, 0.15, 0.05]),
                                  False))
                donation_key += 1

    fact_donation = pd.DataFrame(donations, columns=[
        "DonationKey", "Donation Date", "DonorKey", "CampaignKey", "ChannelKey",
        "FundraiserKey", "Gift Amount", "Gift Type", "Payment Method", "Is First Gift"])
    fact_pledge = pd.DataFrame(pledges, columns=[
        "PledgeKey", "DonorKey", "Month Start Date", "Monthly Amount",
        "Pledge Status", "Pledge Start Date", "Pledge End Date"])
    return fact_donation, fact_pledge


fact_donation, fact_pledge = simulate()
fact_donation = fact_donation[fact_donation["Donation Date"] <= END].copy()


# ---------------------------------------------------------------------------
# Campaign cost — without this there is no ROI, only a revenue report
# ---------------------------------------------------------------------------

def build_costs() -> pd.DataFrame:
    acquired_per_channel_month = (
        dim_donor.assign(m=dim_donor["Acquisition Date"].values.astype("datetime64[M]"))
        .groupby(["Acquisition ChannelKey", "m"]).size()
    )

    rows, key = [], 1
    for (ch_key, month), n_donors in acquired_per_channel_month.items():
        month = pd.Timestamp(month)
        spend = n_donors * CH[ch_key]["cpa"] * float(rng.normal(1.0, 0.07))
        campaign = regular_campaign(ch_key, month)
        # Split the spend across cost types so the model can be sliced by it.
        for cost_type, share in (("Media", 0.55), ("Agency", 0.20),
                                 ("Staff", 0.18), ("Materials", 0.07)):
            rows.append((key, month, campaign, ch_key,
                         float(np.round(spend * share, 2)), cost_type))
            key += 1

    return pd.DataFrame(rows, columns=[
        "CostKey", "Month Start Date", "CampaignKey", "ChannelKey",
        "Cost Amount", "Cost Type"])


fact_cost = build_costs()


# ---------------------------------------------------------------------------
# Realistic dirt — cleaned later in Power Query, and documented when it is
# ---------------------------------------------------------------------------

# ~3% of donors have no country recorded.
missing = rng.choice(dim_donor.index, size=int(len(dim_donor) * 0.03), replace=False)
dim_donor.loc[missing, "Country"] = None

# 40 donors were entered twice with a slightly different name spelling.
dupes = dim_donor.sample(40, random_state=SEED).copy()
dupes["DonorKey"] = np.arange(N_DONORS + 1, N_DONORS + 41)
dupes["Donor Name"] = dupes["Donor Name"].str.replace(" ", "  ", n=1)
dim_donor = pd.concat([dim_donor, dupes], ignore_index=True)

# A handful of refunds recorded as negative gifts — a business rule is needed.
refunds = fact_donation.sample(30, random_state=SEED).copy()
refunds["DonationKey"] = np.arange(fact_donation["DonationKey"].max() + 1,
                                   fact_donation["DonationKey"].max() + 31)
refunds["Gift Amount"] = -refunds["Gift Amount"]
refunds["Is First Gift"] = False
fact_donation = pd.concat([fact_donation, refunds], ignore_index=True)


# ---------------------------------------------------------------------------
# Write and report
#
# Only the five tables the report actually uses are written out. The pledge
# simulation above still runs, because it generates the recurring monthly
# donations that appear in FactDonation — but the pledge snapshots themselves,
# the fundraiser list and the security lookup are not part of this build.
# ---------------------------------------------------------------------------

TABLES = {
    "DimDonor": dim_donor,
    "DimChannel": dim_channel,
    "DimCampaign": dim_campaign,
    "FactDonation": fact_donation.sort_values("Donation Date"),
    "FactCampaignCost": fact_cost,
}

for name, frame in TABLES.items():
    path = OUT / f"{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    print(f"{name:<20} {len(frame):>8,} rows   {path.stat().st_size / 1024:>8,.0f} KB")

# --- self-check: confirm the data has the structure the report relies on ----
print("\n--- data checks ---")

paid = fact_donation[fact_donation["Gift Amount"] > 0]

# Only donors with a full 12 months of history can be judged on 12-month
# retention. Including 2025 recruits would count "not yet had the chance to
# lapse" as lapsed and flatten the difference between channels — the same trap
# the report itself has to avoid.
mature = dim_donor[dim_donor["Acquisition Date"] <= END - pd.Timedelta(days=365)]
first_year = mature.merge(
    paid.groupby("DonorKey")["Donation Date"].max().rename("last_gift"),
    on="DonorKey", how="left")
first_year["retained_12m"] = (
    (first_year["last_gift"] - first_year["Acquisition Date"]).dt.days >= 365)

print(f"\n1. Retention and cost by acquisition channel "
      f"(donors acquired on or before {(END - pd.Timedelta(days=365)).date()})")
summary = (first_year.merge(dim_channel, left_on="Acquisition ChannelKey",
                            right_on="ChannelKey")
           .groupby("Channel Name")
           .agg(donors=("DonorKey", "count"),
                retained_12m=("retained_12m", "mean")))
costs = fact_cost.groupby("ChannelKey")["Cost Amount"].sum()
income = paid.groupby("ChannelKey")["Gift Amount"].sum()
summary = summary.join(
    dim_channel.set_index("Channel Name")[["ChannelKey"]]).assign(
    cost=lambda d: d.ChannelKey.map(costs), income=lambda d: d.ChannelKey.map(income))

# Cost per donor divides by ALL donors the channel acquired, not just the
# mature subset used for the retention column above. Dividing full-period cost
# by a partial donor count inflates the figure — Face-to-Face reads 238 that
# way against a true 178 — and the report will never reproduce it.
# Excludes the 40 planted duplicate records (keys above N_DONORS). They carry
# no donations and are removed during cleaning, so counting them here would
# understate cost per donor against what the report shows.
all_donors_per_channel = (
    dim_donor[dim_donor["DonorKey"] <= N_DONORS]
    .merge(dim_channel, left_on="Acquisition ChannelKey", right_on="ChannelKey")
    .groupby("Channel Name").size())
summary["all_donors"] = summary.index.map(all_donors_per_channel)
summary["cost_per_donor"] = summary["cost"] / summary["all_donors"]
print(summary[["donors", "retained_12m", "all_donors", "cost_per_donor", "income"]]
      .rename(columns={"donors": "mature_donors"})
      .sort_values("all_donors", ascending=False)
      .to_string(float_format=lambda v: f"{v:,.2f}"))

print("\n2. Second-gift rate within 6 months, emergency cohorts")
print("   Not charted in the current report — structure left in the data for")
print("   further analysis. One-off donors only, since a recurring donor gives")
print("   again by standing order and would swamp the effect being measured.")
one_off_donors = set(
    paid.loc[paid["Is First Gift"] & (paid["Gift Type"] == "One-off"), "DonorKey"])
second_gift = (
    paid[~paid["Is First Gift"]]
    .merge(dim_donor[["DonorKey", "Acquisition Date"]], on="DonorKey")
    .assign(days=lambda d: (d["Donation Date"] - d["Acquisition Date"]).dt.days)
    .query("0 < days <= 180")
    .groupby("DonorKey").size().rename("later_gifts"))

rates = {True: [], False: []}
for e_date, (c_key, followup) in EMERGENCY_LOOKUP.items():
    window = dim_donor[(dim_donor["Acquisition Date"] >= e_date) &
                       (dim_donor["Acquisition Date"] <= e_date + pd.Timedelta(days=45)) &
                       (dim_donor["DonorKey"].isin(one_off_donors))]
    if len(window) < 20:
        continue
    rate = window["DonorKey"].isin(second_gift.index).mean()
    rates[followup].append(rate)
    label = "follow-up" if followup else "no follow-up"
    print(f"   {e_date.date()}  {label:<13} n={len(window):>5}  second gift {rate:6.1%}")

if rates[True] and rates[False]:
    with_f, without_f = np.mean(rates[True]), np.mean(rates[False])
    print(f"   -> with follow-up {with_f:.1%} vs without {without_f:.1%} "
          f"({with_f / without_f:.1f}x)")

print(f"\nTotal income  EUR {fact_donation['Gift Amount'].sum():,.2f}   (net of refunds)")
print(f"Gift count    {len(fact_donation):,}")
print(f"Donors        {fact_donation['DonorKey'].nunique():,}")
print(f"Date range    {fact_donation['Donation Date'].min().date()} "
      f"to {fact_donation['Donation Date'].max().date()}")
