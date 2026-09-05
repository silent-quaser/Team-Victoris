"""
GridGuard — Real Data Downloader

Downloads the DOE/PNNL Event-Correlated Outage Dataset v2 — our PRIMARY
real-world dataset — and provides references to EAGLE-I for further analysis.

==========================================================================
DATASET HIERARCHY
==========================================================================

1. EVENT-CORRELATED OUTAGE DATASET v2  [PRIMARY — download this first]
   Publisher: Pacific Northwest National Laboratory (PNNL) / Dept. of Energy
   Official:  https://catalog.data.gov/dataset/event-correlated-outage-dataset-in-america
   Download:  https://data.openei.org/files/6458/Outage_Dataset_R1.zip
   Guidelines:https://data.openei.org/files/6458/Guideline_OEDI_Updated.docx

   This processed dataset INTEGRATES:
       * EAGLE-I outage data (2014–2023)
       * DOE-417 electric emergency/disturbance reports
       * CO-EST2024-POP county population data (2024 Census Bureau)

   USE FOR:
       * Real outage event characteristics (storm type, duration, magnitude)
       * Calibrating our synthetic storm profiles
       * Validating our simulated scenario severity against real events

   KEY FIELDS:
       event_type         — storm/hurricane/ice/wind/equipment
       event_start/end    — UTC timestamps
       duration_hours     — how long the outage lasted
       customers_out_max  — peak customers without power
       mw_affected        — estimated MW demand affected
       state / county     — geographic scope
       cause              — primary cause (wind, ice, lightning, etc.)

---------------------------------------------------------------------------

2. EAGLE-I (Environment for Analysis of Geolocated Energy Information)
   Source: ORNL OpenEnergyHub
   2014 data:  https://openenergyhub.ornl.gov/explore/dataset/eaglei_outages_2014/
   2014–2022:  https://impact.ornl.gov/en/datasets/eagle-i-power-outage-data-2014-2022/
   2025 release (ORNL): https://doi.ccs.ornl.gov/dataset/c09fce3f-5faa-54ef-878a-cb0af6851cb6

   EAGLE-I is county-level outage data at 15-minute intervals.
   It does NOT contain component-level SCADA/topology/fault labels.

   KEY FIELDS:
       fips_code           — county FIPS code (5-digit)
       county              — county name
       state               — US state
       sum_c               — customers without power (count)
       run_start_time      — timestamp (15-min interval)

   USE FOR:
       * Outage evolution over time (temporal patterns)
       * Geographic spread (county-level spatial analysis)
       * Duration and magnitude validation
       * Validating our storm scenario severity

   NOTE: Do NOT download the full multi-year EAGLE-I archive automatically
   (several GB). The Event-Correlated v2 dataset already incorporates
   processed EAGLE-I data and is our primary download target.

   The 2025 ORNL EAGLE-I release provides a newer validation period if needed.

---------------------------------------------------------------------------

3. DOE-417 (Electric Emergency Incident and Disturbance Reports)
   Official: https://doe417.energy.gov/
   Archive:  https://www.eia.gov/electricity/data/disturbance/disturb_events_archive.html

   USE FOR:
       * Event-level context (utility name, NERC region, event cause)
       * Demand loss estimates
       * Geographic scope (states affected)

   NOTE: Already incorporated in the Event-Correlated v2 dataset.

==========================================================================
IMPORTANT — WHAT THESE DATASETS ARE NOT FOR
==========================================================================

These real public outage datasets do NOT provide:
    - Component-level SCADA telemetry
    - Individual transformer/line failure labels
    - IEEE bus-level topology data
    - Detailed protective relay operation data

That is why GridGuard uses the IEEE 33-bus simulation (pandapower) to
generate component-level synthetic training data, calibrated by the
real dataset's outage characteristics.

==========================================================================
"""
from __future__ import annotations
import os
import zipfile
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
RAW_DIR_EC = BASE_DIR / "data" / "raw" / "event_correlated"
RAW_DIR_EAGLEI = BASE_DIR / "data" / "raw" / "eagle_i"
RAW_DIR_DOE417 = BASE_DIR / "data" / "raw" / "doe_417"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
SYNTHETIC_DIR = BASE_DIR / "data" / "synthetic"

# ---------------------------------------------------------------------------
# Official download URLs
# ---------------------------------------------------------------------------
# Primary: Event-Correlated Outage Dataset v2 (PNNL/DOE via OpenEI)
EC_V2_URL = "https://data.openei.org/files/6458/Outage_Dataset_R1.zip"
EC_V2_GUIDELINES_URL = "https://data.openei.org/files/6458/Guideline_OEDI_Updated.docx"
EC_V1_URL = "https://data.openei.org/files/6458/correlated_outage_readme.zip"

# EAGLE-I references (do not auto-download unless explicitly requested)
EAGLEI_2014_URL = "https://openenergyhub.ornl.gov/explore/dataset/eaglei_outages_2014/"
EAGLEI_2022_URL = "https://impact.ornl.gov/en/datasets/eagle-i-power-outage-data-2014-2022/"
EAGLEI_2025_URL = "https://doi.ccs.ornl.gov/dataset/c09fce3f-5faa-54ef-878a-cb0af6851cb6"


def ensure_dirs() -> None:
    """Create all required data directories."""
    for d in [RAW_DIR_EC, RAW_DIR_EAGLEI, RAW_DIR_DOE417, PROCESSED_DIR, SYNTHETIC_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def download_event_correlated_v2(
    force: bool = False,
    timeout: int = 120,
) -> Optional[Path]:
    """
    Download the Event-Correlated Outage Dataset v2 (PRIMARY dataset).

    This is a ~5–20 MB ZIP containing the processed, integrated dataset
    combining EAGLE-I + DOE-417 + 2024 county population data.

    Parameters
    ----------
    force:   Re-download even if already present
    timeout: HTTP timeout in seconds

    Returns path to the downloaded ZIP, or None on failure.
    """
    import urllib.request

    ensure_dirs()
    zip_path = RAW_DIR_EC / "Outage_Dataset_v2.zip"

    if zip_path.exists() and not force:
        size_mb = zip_path.stat().st_size / 1e6
        print(f"[downloader] Event-Correlated v2 already present: {zip_path} ({size_mb:.1f} MB)")
        return zip_path

    urls_to_try = [EC_V2_URL, EC_V1_URL]
    for url in urls_to_try:
        try:
            print(f"[downloader] Downloading Event-Correlated Outage Dataset v2 from:\n  {url}")
            print("[downloader] This is the primary real-world dataset (EAGLE-I + DOE-417 integrated).")
            urllib.request.urlretrieve(url, zip_path)
            size_mb = zip_path.stat().st_size / 1e6
            print(f"[downloader] Downloaded: {zip_path} ({size_mb:.1f} MB)")
            return zip_path
        except Exception as e:
            print(f"[downloader] Failed ({url}): {e}")

    print("[downloader] All download attempts failed. See print_download_instructions() for manual steps.")
    return None


def extract_dataset(zip_path: Path) -> Optional[Path]:
    """Extract ZIP and return the path to the primary data file."""
    ensure_dirs()
    if not zip_path.exists():
        print(f"[downloader] ZIP not found: {zip_path}")
        return None

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        print(f"[downloader] ZIP contents: {names}")
        zf.extractall(RAW_DIR_EC)

    # Find main data file (CSV preferred, then XLSX)
    for ext in [".csv", ".xlsx", ".xls"]:
        candidates = sorted(RAW_DIR_EC.rglob(f"*{ext}"))
        if candidates:
            print(f"[downloader] Primary data file: {candidates[0]}")
            return candidates[0]

    print("[downloader] No CSV/XLSX found in ZIP.")
    return None


def get_dataset_path() -> Optional[Path]:
    """Return path to the extracted dataset file, downloading if necessary."""
    # Check for already-extracted file
    for ext in [".csv", ".xlsx"]:
        candidates = sorted(RAW_DIR_EC.rglob(f"*{ext}"))
        if candidates:
            return candidates[0]

    # Try existing ZIP
    for zip_name in ["Outage_Dataset_v2.zip", "Outage_Dataset_R1.zip",
                     "correlated_outage_readme.zip"]:
        zip_path = RAW_DIR_EC / zip_name
        if zip_path.exists():
            return extract_dataset(zip_path)

    return None


def print_download_instructions() -> None:
    """Print manual download instructions for all datasets."""
    print("""
==========================================================================
GridGuard — Real Dataset Download Instructions
==========================================================================

PRIMARY DATASET (download this first):
    Event-Correlated Outage Dataset v2
    Publisher: PNNL / Dept. of Energy
    Official:  https://catalog.data.gov/dataset/event-correlated-outage-dataset-in-america
    Download:  https://data.openei.org/files/6458/Outage_Dataset_R1.zip
    Guidelines:https://data.openei.org/files/6458/Guideline_OEDI_Updated.docx

    Automated:
        python -c "from data_pipeline.downloader import download_event_correlated_v2; download_event_correlated_v2()"

    Manual:
        1. Visit https://catalog.data.gov/dataset/event-correlated-outage-dataset-in-america
        2. Click "Outage Dataset v2.zip" resource → Download
        3. Place ZIP in: data/raw/event_correlated/

    This dataset integrates: EAGLE-I (2014-2023) + DOE-417 + 2024 County Population.
    County-level outage data at 15-minute intervals from EAGLE-I:
        FIPS code, county, state, customers without power, timestamp.

---------------------------------------------------------------------------

EAGLE-I (county-level, 15-minute outage data — optional extra validation):
    2014 data:     https://openenergyhub.ornl.gov/explore/dataset/eaglei_outages_2014/
    2014–2022:     https://impact.ornl.gov/en/datasets/eagle-i-power-outage-data-2014-2022/
    2025 release:  https://doi.ccs.ornl.gov/dataset/c09fce3f-5faa-54ef-878a-cb0af6851cb6
    Key fields:    fips_code, county, state, sum_c (customers out), run_start_time

    NOTE: Do NOT download the full multi-year archive automatically (several GB).
    The Event-Correlated v2 dataset already provides processed EAGLE-I data.

---------------------------------------------------------------------------

DOE-417 (emergency disturbance reports — already in Event-Correlated v2):
    https://doe417.energy.gov/
    https://www.eia.gov/electricity/data/disturbance/disturb_events_archive.html

---------------------------------------------------------------------------

Do NOT commit raw data to the repository. data/raw/ is in .gitignore.
==========================================================================
""")


if __name__ == "__main__":
    path = download_event_correlated_v2()
    if path:
        extracted = extract_dataset(path)
        if extracted:
            print(f"[downloader] Ready for preprocessing: {extracted}")
    else:
        print_download_instructions()
