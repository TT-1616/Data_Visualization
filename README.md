# U.S. Airport Passenger Traffic Visualization

This project uses annual U.S. airport enplanement data from 2001 to 2023 to support a Tableau data visualization project. The dataset includes airport-level passenger boarding records across the United States, with fields such as airport code, airport name, city, state, FAA region, service level, hub type, annual enplanements, and year-over-year change.

## Project Goal

The goal is to analyze long-term trends in U.S. airport passenger traffic and create visualizations that highlight:

- Overall passenger traffic growth from 2001 to 2023
- The impact of COVID-19 on airport traffic in 2020
- Recovery trends from 2021 to 2023
- Top airports by annual passenger enplanements
- Differences by state, FAA region, service level, and hub type

## Data

The raw data files are stored as annual Excel files in this repository. Each file represents one calendar year or a year-over-year comparison table.

Years covered:

- 2001-2023

Main metric:

- Passenger enplanements, also listed in some files as boardings

## Cleaned Data

The cleaned Tableau-ready dataset is available at:

- `data_cleaned/airport_enplanements_2001_2023_clean.csv`

Supporting summary files:

- `data_cleaned/annual_totals.csv`
- `data_cleaned/data_quality_summary.csv`

The cleaning script is:

- `clean_airport_data.py`

The cleaned dataset uses one row per airport per year and includes standardized fields for year, airport code, airport name, city, state, FAA region, service level, hub type, enplanements, rank, source file, and data scope.

## Notes

The raw files are not perfectly standardized. Some years use different column names, and several files include total rows, count rows, blank rows, or extra unnamed columns. Before building the final Tableau dashboard, the data should be cleaned and combined into one consistent table.

Recommended cleaned fields:

- `year`
- `locid`
- `airport_name`
- `city`
- `state`
- `faa_region`
- `service_level`
- `hub_type`
- `enplanements`
- `rank`
- `source_file`

Important caveat:

- The 2010 and 2011 source files appear to include primary airports only, while most other years include both primary and non-primary commercial service airports. The cleaned data keeps a `data_scope` field to make this visible during analysis.

## Tools

- Excel files for raw data storage
- Tableau for dashboard design and visualization
- GitHub for version control and project documentation

## Possible Dashboard Views

- National passenger traffic trend over time
- Top 10 airports by year
- 2019 vs. 2020 vs. 2023 recovery comparison
- Passenger traffic by state or FAA region
- Hub type comparison
