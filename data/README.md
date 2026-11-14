# PeakShift data

## Active dataset: Swiss residential electricity profiles

- Authors: Katharina Kaiser, Markus Kreft, Marina González Vayá, and Gabriela Hug.
- Dataset: https://zenodo.org/records/21398769 (version v1).
- DOI: https://doi.org/10.5281/zenodo.21398769.
- Description paper: https://arxiv.org/abs/2607.19294.
- License: Creative Commons Attribution 4.0, https://creativecommons.org/licenses/by/4.0/.
- Downloaded: 14 November 2026.

The published dataset covers 2,447 residential installations in Switzerland in 2023–2024. This project currently contains a **five-household subset**, not all installations. Original CSV files, the complete metadata, and tariff data are in `raw/swiss/`. File hashes and original ZIP CRC values are in `raw/swiss/manifest.json`. Each extracted member passed the ZIP integrity check. The raw data remains outside Git.

The selected meters are 133930, 100003, 112545, 121380, and 132540. Selection used metadata only: household installation type (apartment or single-family house), at least 99% coverage, no recorded PV injection, no recorded equipment change, no experimental tariff, and no pilot device control. Candidates were sorted by coverage descending, then meter ID ascending. Forecast performance was not used for selection. This convenience subset is not a representative sample of all homes.

`explore.py` defaults to **133930**, a single-family house with all 70,176 quarter-hour import readings present. Its local timestamps span 1 January 2023 through 31 December 2024. Change `METER_ID` to one of the other downloaded IDs to inspect it. The other four meters each have two missing import readings. Equipment metadata can itself be incomplete; absence of a reported feature is not proof of absence.

### Units and missing readings

`timestamp_utc` marks the **start** of the interval. `kWh_to_installation` is imported energy **during each 15-minute interval**, already differenced by the data publishers. Do not difference it again. Divide it by 0.25 hours to get average imported power in kW, then average the four quarter-hour powers for each hour. An hour without all four valid readings remains missing, rather than becoming zero.

Hours are aggregated in UTC and then labelled in `Europe/Zurich` local time. The repeated autumn clock hour retains both UTC offsets; local daylight-saving transition days have 23 or 25 hours. Future daily forecasting/evaluation must account for this. Imported power is the current target; it is not automatically total behind-the-meter demand for homes with solar generation.

### Reproducing the download

Download `dataset.zip` from the versioned Zenodo record. Extract `metadata.csv`, `tariff_data.csv`, and the five selected `smart_meter_data/<meter_id>.csv` files into `data/raw/swiss/`. The original archive is approximately 904 MB and all extracted data is approximately 7.9 GB; only the subset (about 20.5 MB) was retained here. HTTP byte-range downloads from the original archive were used to fetch just those members.

## Previous dataset retained

The original UCI household file remains at `raw/household_power_consumption.txt`; it is no longer loaded by `explore.py`.

- Hebrail, G. & Berard, A. (2006). Individual Household Electric Power Consumption [Dataset]. UCI Machine Learning Repository.
- Source: https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption.
- DOI: https://doi.org/10.24432/C58K54.
- License: Creative Commons Attribution 4.0.

## Run and verify

From the PeakShift folder, activate `.venv`. Run `python explore.py` to inspect the data, or `python train.py` to train the model, compare it with the baseline, and run the one-hour scheduling example.
Run conversion and missing-data checks with `python -B -m unittest discover -s tests -v`.

The current model is a decision tree evaluated on validation dates and a separate final period. The final evaluation has now been run with unchanged model settings; results are in `../results/evaluation.json` and `../results/test-scheduling.csv`. One 25-hour clock-change day was excluded from both forecast and scheduling comparisons. Final hourly MAE improved slightly, daily peak MAE worsened, and model scheduling tied the baseline scheduler on all evaluated final-test days. These limitations must be reported. The scheduling example adds an assumed 1 kW, one-hour task to the first validation day; it does not control an appliance. Tariff data is retained but is not used by the current code.
