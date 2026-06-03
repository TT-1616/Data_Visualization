from pathlib import Path
import re

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "data_cleaned"


COLUMN_ALIASES = {
    "faa_region": ["FAA Region", "RO", "Region"],
    "state": ["ST", "State"],
    "locid": ["Locid"],
    "city": ["City"],
    "airport_name": ["Airport Name"],
    "service_level": ["Service Level", "Svc Lvl", "SL", "S/L", "Arpt Category"],
    "hub_type": ["Hub", "Hub Type"],
}


def clean_column_name(value):
    return re.sub(r"\s+", " ", str(value).replace("\n", " ")).strip()


def clean_text(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\n", " ")).strip()


def year_from_filename(path):
    match = re.search(r"(?:cy|CY)(\d{2})", path.name)
    if not match:
        raise ValueError(f"Could not identify year from filename: {path.name}")
    return int(f"20{match.group(1)}")


def find_column(columns, aliases):
    normalized = {clean_column_name(column).lower(): column for column in columns}
    for alias in aliases:
        column = normalized.get(alias.lower())
        if column is not None:
            return column
    return None


def find_rank_column(columns, year):
    candidates = ["Rank", f"CY {str(year)[-2:]} Rank"]
    return find_column(columns, candidates) or next(
        (column for column in columns if "rank" in clean_column_name(column).lower()),
        None,
    )


def find_enplanement_column(columns, year):
    data_columns = [
        column
        for column in columns
        if re.search(r"enplan|board", clean_column_name(column), re.IGNORECASE)
    ]
    year_patterns = [
        f"CY {str(year)[-2:]}",
        f"CY{str(year)[-2:]}",
        f"CY {year}",
        f"CY{year}",
        str(year),
    ]
    for pattern in year_patterns:
        for column in data_columns:
            if pattern.lower() in clean_column_name(column).lower():
                return column
    if data_columns:
        return data_columns[0]
    raise ValueError(f"Could not identify enplanement column for {year}")


def source_scope(path, service_values):
    if path.name in {"cy10_primary_enplanements.xls", "cy11_primary_enplanements.xlsx"}:
        return "primary_only_source"
    if set(service_values).issubset({"P"}):
        return "primary_only_source"
    return "commercial_service_source"


def read_year_file(path):
    year = year_from_filename(path)
    dataframe = pd.read_excel(path, sheet_name=0, header=0).dropna(how="all")
    dataframe.columns = [clean_column_name(column) for column in dataframe.columns]

    column_map = {
        field: find_column(dataframe.columns, aliases)
        for field, aliases in COLUMN_ALIASES.items()
    }
    rank_column = find_rank_column(dataframe.columns, year)
    enplanement_column = find_enplanement_column(dataframe.columns, year)

    locid = dataframe[column_map["locid"]].map(clean_text)
    service_level = dataframe[column_map["service_level"]].map(clean_text)
    enplanements = pd.to_numeric(dataframe[enplanement_column], errors="coerce")

    valid_airport_row = (
        enplanements.notna()
        & locid.ne("")
        & locid.ne("nan")
        & ~locid.str.contains("total|count|airport|primary|non", case=False, na=False)
        & service_level.isin(["P", "CS"])
    )

    cleaned = pd.DataFrame(
        {
            "year": year,
            "rank": pd.to_numeric(dataframe[rank_column], errors="coerce")
            if rank_column
            else pd.NA,
            "locid": locid,
            "airport_name": dataframe[column_map["airport_name"]].map(clean_text),
            "city": dataframe[column_map["city"]].map(clean_text),
            "state": dataframe[column_map["state"]].map(clean_text),
            "faa_region": dataframe[column_map["faa_region"]].map(clean_text)
            if column_map["faa_region"]
            else "",
            "service_level": service_level,
            "hub_type": dataframe[column_map["hub_type"]].map(clean_text)
            if column_map["hub_type"]
            else "",
            "enplanements": enplanements,
            "source_file": path.name,
        }
    )
    cleaned = cleaned.loc[valid_airport_row].copy()
    cleaned["rank"] = cleaned["rank"].astype("Int64")
    cleaned["enplanements"] = cleaned["enplanements"].astype("Int64")
    cleaned["data_scope"] = source_scope(path, cleaned["service_level"].dropna().unique())

    summary = {
        "source_file": path.name,
        "year": year,
        "sheet_rows": len(dataframe),
        "clean_rows": len(cleaned),
        "unique_airports": cleaned["locid"].nunique(),
        "service_levels": ",".join(sorted(cleaned["service_level"].dropna().unique())),
        "data_scope": cleaned["data_scope"].iloc[0] if not cleaned.empty else "",
        "enplanements_total": int(cleaned["enplanements"].sum()),
        "enplanement_source_column": enplanement_column,
    }
    return cleaned, summary


def main():
    files = sorted(PROJECT_DIR.glob("*.xls*"))
    if not files:
        raise SystemExit("No Excel files found.")

    cleaned_frames = []
    summaries = []
    for path in files:
        cleaned, summary = read_year_file(path)
        cleaned_frames.append(cleaned)
        summaries.append(summary)

    combined = pd.concat(cleaned_frames, ignore_index=True)
    combined = combined.sort_values(["year", "rank", "locid"], na_position="last")

    duplicate_count = int(combined.duplicated(["year", "locid"]).sum())
    if duplicate_count:
        raise ValueError(f"Found {duplicate_count} duplicate year-locid rows.")

    OUTPUT_DIR.mkdir(exist_ok=True)
    combined.to_csv(OUTPUT_DIR / "airport_enplanements_2001_2023_clean.csv", index=False)

    summary_frame = pd.DataFrame(summaries).sort_values(["year", "source_file"])
    summary_frame.to_csv(OUTPUT_DIR / "data_quality_summary.csv", index=False)

    by_year = (
        combined.groupby("year", as_index=False)
        .agg(
            airport_rows=("locid", "count"),
            unique_airports=("locid", "nunique"),
            total_enplanements=("enplanements", "sum"),
        )
        .sort_values("year")
    )
    by_year.to_csv(OUTPUT_DIR / "annual_totals.csv", index=False)

    print(f"Wrote {len(combined):,} cleaned airport-year rows.")
    print(f"Years: {combined['year'].min()}-{combined['year'].max()}")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
