# PeakShift data

## Active dataset: Swiss residential electricity profiles

- Authors: Katharina Kaiser, Markus Kreft, Marina González Vayá, and Gabriela Hug.
- Dataset: https://zenodo.org/records/21398769 (version v1).
- DOI: https://doi.org/10.5281/zenodo.21398769.
- Description paper: https://arxiv.org/abs/2607.19294.
- License: Creative Commons Attribution 4.0, https://creativecommons.org/licenses/by/4.0/.
- Downloaded: 14 November 2026.

The published dataset covers 2,447 residential installations in Switzerland in 2023–2024. This repository bundles **one household**, meter 133930, in `data/household.csv.gz` (paths here are relative to the project root). It is the original meter CSV, gzip-compressed without changing its contents. No download, API key, or `data/raw/` folder is needed to run the app or evaluation.

The original five-household download, complete metadata, and tariff data remain locally available under `data/raw/swiss/`, outside Git. File hashes and original ZIP CRC values are in its `manifest.json`; each extracted member passed the ZIP integrity check. This optional download is not part of the runnable repository.

The original five selected meters were 133930, 100003, 112545, 121380, and 132540. Selection used metadata only: household installation type (apartment or single-family house), at least 99% coverage, no recorded PV injection, no recorded equipment change, no experimental tariff, and no pilot device control. Candidates were sorted by coverage descending, then meter ID ascending. Forecast performance was not used for selection. This convenience subset is not a representative sample of all homes.

`explore.py` loads **133930**, a single-family house with all 70,176 quarter-hour import readings present. Its local timestamps span 1 January 2023 through 31 December 2024. `DATA_FILE` selects the file; `METER_ID` only labels the output. To inspect another household, supply its CSV path to `load_hourly()`; changing `METER_ID` alone does not switch the data. The other four locally downloaded meters each have two missing import readings. Equipment metadata can itself be incomplete; absence of a reported feature is not proof of absence.

### Units and missing readings

`timestamp_utc` marks the **start** of the interval. `kWh_to_installation` is imported energy **during each 15-minute interval**, already differenced by the data publishers. Do not difference it again. Divide it by 0.25 hours to get average imported power in kW, then average the four quarter-hour powers for each hour. An hour without all four valid readings remains missing, rather than becoming zero.

Hours are aggregated in UTC and then labelled in `Europe/Zurich` local time. The repeated autumn clock hour retains both UTC offsets; local daylight-saving transition days have 23 or 25 hours. The app and evaluation exclude incomplete and non-24-hour days. Imported power is the current target; it is not automatically total behind-the-meter demand for homes with solar generation.

### Optional: reproducing the original download

Download `dataset.zip` from the versioned Zenodo record. Extract `metadata.csv`, `tariff_data.csv`, and the five selected `smart_meter_data/<meter_id>.csv` files into `data/raw/swiss/`. The original archive is approximately 904 MB and all extracted data is approximately 7.9 GB; only the subset (about 20.5 MB) was retained here. HTTP byte-range downloads from the original archive were used to fetch just those members.

## Previous dataset retained

The original UCI household file remains locally at `data/raw/household_power_consumption.txt`, outside Git. It is not required or loaded by the current code.

- Hebrail, G. & Berard, A. (2006). Individual Household Electric Power Consumption [Dataset]. UCI Machine Learning Repository.
- Source: https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption.
- DOI: https://doi.org/10.24432/C58K54.
- License: Creative Commons Attribution 4.0.

## Run and verify

Follow the setup commands in `README.md`. Run `python build_site.py` and `python -m http.server 8000 --directory _site` to preview the website. JavaScript connects the interface to the Python daily scheduler through Pyodide in the browser. The build exports training-period weekday/hour averages; the deployed planner does not run decision-tree predictions. Run `python explore.py` to inspect the bundled household or `python train.py` to reproduce the separate decision-tree benchmark.

The first week (1–7 January 2023) supplies lag history, not training targets. The 168-hour lag leaves those initial rows without complete inputs, so they are dropped before fitting. Training targets begin on 8 January 2023 and end on 25 May 2024. The current model is a decision tree evaluated on validation dates and a separate final period. The final evaluation has now been run with unchanged model settings; results are in `results/evaluation.json` and `results/test-scheduling.csv`. One 25-hour clock-change day was excluded from both forecast and scheduling comparisons. Final hourly MAE improved slightly, daily peak MAE worsened, and model scheduling tied the baseline scheduler on all evaluated final-test days. These limitations must be reported. The benchmark adds an assumed 1 kW, one-hour task on each eligible day; it does not control an appliance. Tariff data is retained but is not used by the current code.

## Browser plans and simulation limits

The current website saves appliance plans and status in browser local storage, not SQLite. Plans are separate from the bundled dataset and do not sync between browsers or devices. Clearing site data removes them.

Treat the output as a scheduling simulation, not a precise forecast for a particular home. Neither the planner nor the benchmark establishes reductions in electricity costs, consumption, or emissions; these require further data and measurements.
