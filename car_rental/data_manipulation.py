# =========================================================================================
# File for data manipulation
#
# Only to transform the original dataset to the usable database the app will have
# =========================================================================================

import pandas as pd
from pathlib import Path
import random
from datetime import date, timedelta
import numpy as np
import string


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "src" / "original" / "car_details_v4.csv"

df = pd.read_csv(CSV_PATH)

pd.set_option("display.max_columns", None)
print(df.head())

def show_value_counts(max_unique: int = 30) -> None:
    for col in df.columns:
        n_unique = df[col].nunique(dropna=False)
        n_missing = df[col].isna().sum()
        pct_missing = n_missing / len(df) * 100

        print(f"\n=== {col} ===")
        print(f"unique values: {n_unique} | missing: {n_missing} ({pct_missing:.1f}%)")

        if n_unique <= max_unique:
            counts = df[col].value_counts(dropna=False, normalize=True) * 100
            for value, pct in counts.items():
                print(f"  {value!r}: {pct:.1f}%")
        else:
            print("  (too many unique values to list — showing top 10)")
            counts = df[col].value_counts(dropna=False, normalize=True).head(10) * 100
            for value, pct in counts.items():
                print(f"  {value!r}: {pct:.1f}%")

COLUMNS_TO_DROP = [
    "Owner",
    "Seller Type",
    "Engine",
    "Max Power",
    "Max Torque",
    "Drivetrain",
    "Length",
    "Width",
    "Height",
    "Fuel Tank Capacity",
]

RENAME_MAP = {
    "Make": "brand",
    "Model": "model",
    "Seating Capacity": "seat_num",
    "Kilometer": "km",
    "Color": "color",
    "Fuel Type": "fuel",
    "Transmission": "transmission",
}

df = df.drop(columns=COLUMNS_TO_DROP)
df = df.rename(columns=RENAME_MAP)

# seat number has 64 missing values, replace with 5 (majority of cars have 5 seats)
df["seat_num"] = df["seat_num"].fillna(5)

# seat_num: CSV has it as float (5.0) -> cast to int
df["seat_num"] = df["seat_num"].astype(int)

# fuel / transmission: CSV uses "Petrol"/"Manual" -> enum values are lowercase
df["fuel"] = df["fuel"].str.lower()
df["transmission"] = df["transmission"].str.lower()


def random_manufacture_date(year: int) -> date:
    """Pick a random day within the given year."""
    year = int(year)
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    days_in_year = (end - start).days
    offset = random.randint(0, days_in_year)
    return start + timedelta(days=offset)


def random_registration_date(manufacture_date: date, max_years_after: int = 5) -> date:
    """Pick a random day after manufacture_date, at most max_years_after later,
    and never after today (a car can't register in the future).
    """
    max_offset_days = max_years_after * 365
    latest_possible = min(
        manufacture_date + timedelta(days=max_offset_days),
        date.today(),
    )
    span_days = (latest_possible - manufacture_date).days
    span_days = max(span_days, 0)  # guard: manufacture_date itself could already be < 5 yrs from today
    offset = random.randint(0, span_days)
    return manufacture_date + timedelta(days=offset)

df["manufacture_date"] = df["Year"].apply(random_manufacture_date)
df["registration_date"] = df["manufacture_date"].apply(random_registration_date)

df = df.drop(columns=["Year"])

INR_TO_EUR = 0.011
AGE_DEPRECIATION_RATE = 0.08
KM_DEPRECIATION_RATE = 0.00002
MIN_VALUE_FLOOR = 0.15


def estimate_daily_rate(price_inr: float, manufacture_date: date, km: int, as_of: date = None) -> float:
    as_of = as_of or date.today()
    age_years = max(as_of.year - manufacture_date.year, 0)

    base_value_eur = price_inr * INR_TO_EUR
    age_factor = (1 - AGE_DEPRECIATION_RATE) ** age_years
    km_factor = max(1 - (km * KM_DEPRECIATION_RATE), 0)

    depreciation_factor = max(age_factor * km_factor, MIN_VALUE_FLOOR)
    return base_value_eur * depreciation_factor


df["daily_rate"] = df.apply(
    lambda row: estimate_daily_rate(row["Price"], row["manufacture_date"], row["km"]),
    axis=1,
)
df = df.drop(columns=["Price"])
NEW_MIN = 15.0
NEW_MAX = 400.0


def rescale_daily_rate(df: pd.DataFrame, column: str = "daily_rate") -> pd.DataFrame:
    """Linearly rescale the existing daily_rate distribution so its
    minimum becomes NEW_MIN and its maximum becomes NEW_MAX, preserving
    the relative shape of the distribution (skew, clustering, etc.).
    """
    df = df.copy()

    old_min = df[column].min()
    old_max = df[column].max()
    old_range = old_max - old_min

    if old_range == 0:
        # guard: every row had the same value, can't infer a distribution shape
        df[column] = NEW_MIN
        return df

    scaled = (df[column] - old_min) / old_range          # normalize to 0..1
    df[column] = (scaled * (NEW_MAX - NEW_MIN) + NEW_MIN).round(2)  # stretch to new range

    return df


df = rescale_daily_rate(df)

def generate_fuel_targets(seed: int = None, electric_range: tuple = (0.20, 0.30)) -> dict:
    rng = random.Random(seed)
    lo, hi = electric_range

    while True:
        diesel = rng.uniform(0.30, 0.35)
        petrol = rng.uniform(0.25, 0.30)
        hybrid = rng.uniform(0.20, 0.30)
        electric = 1.0 - (diesel + petrol + hybrid)

        if lo <= electric <= hi:
            return {"diesel": diesel, "petrol": petrol, "hybrid": hybrid, "electric": electric}

FUEL_TARGETS = generate_fuel_targets(seed=142)

def reassign_fuel(df, seed: int = 142) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = len(df)

    targets = {k: round(v * n) for k, v in FUEL_TARGETS.items()}
    diff = n - sum(targets.values())
    targets["electric"] += diff

    diesel_idx = df.index[df["fuel"] == "diesel"].to_numpy().copy()
    petrol_idx = df.index[df["fuel"] == "petrol"].to_numpy().copy()
    other_idx = df.index[~df["fuel"].isin(["diesel", "petrol"])].to_numpy().copy()

    rng.shuffle(diesel_idx)
    rng.shuffle(petrol_idx)
    rng.shuffle(other_idx)

    keep_diesel = diesel_idx[: targets["diesel"]]
    excess_diesel = diesel_idx[targets["diesel"] :]
    keep_petrol = petrol_idx[: targets["petrol"]]
    excess_petrol = petrol_idx[targets["petrol"] :]

    to_reassign = np.concatenate([other_idx, excess_diesel, excess_petrol])
    rng.shuffle(to_reassign)

    n_hybrid = targets["hybrid"]
    hybrid_idx = to_reassign[:n_hybrid]
    electric_idx = to_reassign[n_hybrid:]

    df = df.copy()
    df.loc[keep_diesel, "fuel"] = "diesel"
    df.loc[keep_petrol, "fuel"] = "petrol"
    df.loc[hybrid_idx, "fuel"] = "hybrid"
    df.loc[electric_idx, "fuel"] = "electric"

    return df

df = reassign_fuel(df)

SPANISH_PLATE_LETTERS = "BCDFGHJKLMNPRSTVWXYZ"


def random_spanish_plate(rng: random.Random = None) -> str:
    """Generate a plate in the current Spanish format: NNNN LLL
    e.g. '4829 KLM'
    """
    rng = rng or random
    digits = f"{rng.randint(0, 9999):04d}"
    letters = "".join(rng.choices(SPANISH_PLATE_LETTERS, k=3))
    return f"{digits} {letters}"

def generate_unique_plates(n: int, seed: int = 142) -> list[str]:
    rng = random.Random(seed)
    plates = set()
    while len(plates) < n:
        plates.add(random_spanish_plate(rng))
    return list(plates)


plates = generate_unique_plates(len(df), seed=142)
random.Random(142).shuffle(plates)  # avoid any ordering bias from set insertion
df["plate"] = plates

VIN_CHARS = "".join(c for c in string.ascii_uppercase + string.digits if c not in "IOQ")


def random_vin(rng: random.Random = None) -> str:
    """Generate a 17-character VIN-like string (format only, no real
    check-digit validation — simplified for this project).
    e.g. '1HGCM82633A004352'
    """
    rng = rng or random
    return "".join(rng.choices(VIN_CHARS, k=17))

def generate_unique_vins(n: int, seed: int = 142) -> list[str]:
    rng = random.Random(seed)
    vins = set()
    while len(vins) < n:
        vins.add(random_vin(rng))
    return list(vins)


vins = generate_unique_vins(len(df), seed=142)
random.Random(142).shuffle(vins)
df["reg_num"] = vins

def generate_location_targets(seed: int = None, mallorca_range: tuple = (0.03, 0.08)) -> dict:
    """Randomize percentages for the first 6 cities within their ranges,
    then set mallorca to whatever is left so everything sums to 1.0.
    """
    rng = random.Random(seed)
    lo, hi = mallorca_range

    while True:
        madrid = rng.uniform(0.20, 0.25)
        barcelona = rng.uniform(0.15, 0.20)
        valencia = rng.uniform(0.12, 0.17)
        sevilla = rng.uniform(0.11, 0.16)
        malaga = rng.uniform(0.07, 0.12)
        tenerife = rng.uniform(0.04, 0.09)

        mallorca = 1.0 - (madrid + barcelona + valencia + sevilla + malaga + tenerife)

        if lo <= mallorca <= hi:
            return {
                "madrid": madrid,
                "barcelona": barcelona,
                "valencia": valencia,
                "sevilla": sevilla,
                "malaga": malaga,
                "tenerife": tenerife,
                "mallorca": mallorca,
            }


LOCATION_TARGETS = generate_location_targets(seed=142)


def reassign_location(df: pd.DataFrame, seed: int = 142) -> pd.DataFrame:
    """Replace the CSV's Indian-city Location column with a random
    assignment across the Spanish cities, matching LOCATION_TARGETS.
    """
    rng = np.random.default_rng(seed)
    n = len(df)

    targets = {k: round(v * n) for k, v in LOCATION_TARGETS.items()}
    diff = n - sum(targets.values())
    targets["mallorca"] += diff  # absorb rounding drift

    # build a flat array of city labels matching the target counts, then shuffle
    labels = np.concatenate([np.full(count, city) for city, count in targets.items()])
    rng.shuffle(labels)

    df = df.copy()
    df["location"] = labels
    df = df.drop(columns=["Location"])  # drop the original Indian-city column

    return df

df = reassign_location(df)

def assign_category(daily_rate: float) -> str:
    """Map a daily_rate to a RentalTier based on fixed price bands."""
    if daily_rate < 30:
        return "economy"
    elif daily_rate < 100:
        return "midsize"
    else:
        return "luxury"


df["category"] = df["daily_rate"].apply(assign_category)

def generate_status_targets(seed: int = None, retired_range: tuple = (0.05, 0.15)) -> dict:
    """Randomize active/maintenance within their ranges, retired gets the remainder."""
    rng = random.Random(seed)
    lo, hi = retired_range

    while True:
        active = rng.uniform(0.75, 0.85)
        maintenance = rng.uniform(0.08, 0.13)
        retired = 1.0 - (active + maintenance)

        if lo <= retired <= hi:
            return {"active": active, "maintenance": maintenance, "retired": retired}


STATUS_TARGETS = generate_status_targets(seed=142)


def assign_status(df: pd.DataFrame, seed: int = 142) -> pd.DataFrame:
    """Randomly assign status to each row matching STATUS_TARGETS."""
    rng = np.random.default_rng(seed)
    n = len(df)

    targets = {k: round(v * n) for k, v in STATUS_TARGETS.items()}
    diff = n - sum(targets.values())
    targets["retired"] += diff  # absorb rounding drift

    labels = np.concatenate([np.full(count, status) for status, count in targets.items()])
    rng.shuffle(labels)

    df = df.copy()
    df["status"] = labels
    return df

df = assign_status(df)

SUV_KEYWORDS = [
    "suv", "xuv", "creta", "venue", "seltos", "compass", "harrier",
    "scorpio", "fortuner", "duster", "ecosport", "brezza", "nexon",
    "hector", "safari", "thar", "kushaq", "taigun",
]
VAN_KEYWORDS = ["van", "tourer", "carnival", "innova", "ertiga", "marazzo"]


def assign_type(seat_num: int, model: str) -> str:
    model_lower = model.lower()

    if any(kw in model_lower for kw in VAN_KEYWORDS):
        return "van"
    if any(kw in model_lower for kw in SUV_KEYWORDS):
        return "suv"

    # fallback: no keyword matched, decide from seat count
    if seat_num == 2:
        return "mini"
    if seat_num >= 6:
        return "suv"
    return "car"


df["type"] = df.apply(lambda row: assign_type(row["seat_num"], row["model"]), axis=1)

COLUMN_ORDER = [
    "reg_num",
    "type",
    "brand",
    "model",
    "category",
    "daily_rate",
    "seat_num",
    "plate",
    "color",
    "fuel",
    "transmission",
    "km",
    "status",
    "location",
    "manufacture_date",
    "registration_date",
]

df = df[COLUMN_ORDER]

show_value_counts()
print(df.head())

import sqlite3 as sql

DB_PATH = PROJECT_ROOT / "src" / "vehicles.db"
conn = sql.connect(DB_PATH)
df.to_sql("vehicles", conn, if_exists="replace", index=False)
conn.close()