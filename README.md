# PeakShift

PeakShift helps you schedule appliances for times when your household uses less electricity. Choose when each appliance can run, and the app suggests a schedule. You can link tasks, like drying after washing, and track what is running or finished.

Built for the Climate track of the Veritas AI Hackathon.

[Try PeakShift](https://yg-gms.github.io/PeakShift/)

## Run locally

Use Python 3.11. From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python build_site.py
python -m http.server 8000 --directory _site
```

Open [localhost:8000](http://localhost:8000). Sample data is included and no API key is needed.

Add appliances and set their allowed times. Use **Run after** to link tasks, then **Start** and **Mark done** to track them. Tasks that cannot fit are shown as unscheduled.

Plans are saved in your browser on each device. Clearing site data removes them. All planning times use Europe/Zurich.

## How it works

The planner uses past readings from one Swiss household to estimate typical electricity use for each weekday. It tries different appliance start times to spread out demand, though it may not find the best possible schedule. Appliance estimates can be changed in `appliances.py`.

We also tested a separate machine learning model for predicting electricity use. On the final test, it slightly improved hourly predictions, but predicted daily peaks less accurately and gave the same scheduling results as using yesterday's readings. The app uses weekday averages instead; those schedules have not had a separate final test.

This is a prototype. We haven't measured savings in electricity, bills, or carbon emissions.

To reproduce the prediction experiment, run `python train.py`. Results are saved in `results/`. Run `python explore.py` to view the household data.

## Data and credits

Electricity data: [Residential electricity load profiles in Switzerland](https://zenodo.org/records/21398769), by Katharina Kaiser, Markus Kreft, Marina González Vayá, and Gabriela Hug, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). We used meter 133930; see [data notes](data/README.md).

Appliance estimates are based on [Power NI's appliance guide](https://powerni.co.uk/help/energy-guides/which-appliances-use-the-most-electricity/).

ChatGPT and Codex helped with development and documentation.
