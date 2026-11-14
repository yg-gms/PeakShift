# PeakShift

**Track:** AI + Climate  
**Team:** [Add your registered name, school, and any other required team details before submitting.]

## The problem

PeakShift is for a household member deciding when to run a flexible task before a deadline. Running several loads together can increase peak power demand. We investigate whether a learned demand forecast can support a better scheduling decision than repeating yesterday's demand pattern.

## What we built

The app now lets users add multiple appliances to a dated plan using editable energy/run-time presets. It coordinates allowed windows, task dependencies, and other scheduled runs, and saves running/done status locally. Household data shows observed meter readings. The original benchmark below evaluates the earlier decision-tree scheduler. The current greedy daily planner has not received a new held-out evaluation. Appliance references and assumptions are in `docs/APPLIANCE_PRESETS.md`.

## What we added

Our own idea: connect household demand forecasting to a constrained scheduling decision, then test whether a better forecast also improves that decision. We compare the model with a persistence forecast and compare its scheduling with both the original plan and persistence-based scheduling.

## Original experiment and current planner

We use meter 133930 from Kaiser et al.'s Swiss residential electricity dataset: 70,176 quarter-hour readings covering 2023–2024. Divide interval energy in kWh by 0.25 hours to obtain average kW, then calculate hourly averages. Incomplete hours remain missing. Timezone conversion preserves distinct clock-change hours.

The decision tree uses demand 24 and 168 hours earlier, the hour, and the weekday. Actual target demand is not included as an input. The first week supplies lag history, not training targets. We train on eligible targets from 8 January 2023 to 25 May 2024, validate on 26 May–12 September 2024, and test on 13 September–31 December. The model uses absolute error, maximum depth 5, and random seed 42; settings were fixed before accessing the final period. We exclude non-24-hour or incomplete days from the reported comparisons.

The scheduler tries each permitted hourly start and selects the lowest predicted whole-day peak. The benchmark task is 1 kW for one hour, allowed 18:00–22:00, originally planned for 18:00. Actual measurements are used afterward to evaluate the simulated choice.

The current weekday-average planner uses 1 January 2023–25 May 2024 only. It has not received a new held-out evaluation. The results below describe the original decision tree and earliest-start tie rule.

## Results and failure

Validation included 110 days; final testing included 109 complete days and skipped the 25-hour day on 27 October.

| Metric | Validation baseline / model | Final baseline / model |
|---|---:|---:|
| Hourly MAE (kW) | 0.564 / 0.453 | 0.807 / 0.781 |
| Daily peak MAE (kW) | 2.998 / 2.487 | 2.272 / 2.604 |
| Average simulated daily peak after scheduling (kW) | 4.894 / 4.715 | 12.141 / 12.141 |

The model's schedule beat persistence-based scheduling on 20 validation days, tied on 89, and worsened the peak on 1. On all 109 final-test days it tied the baseline scheduler. Therefore, lower validation error did not establish a final-test scheduling advantage. On the first validation day, all candidate forecast peaks tie and the tool recommends the original 18:00 start, with zero improvement. We show both the weak result and successful validation decisions instead of presenting only wins.

This is one historical household, not a validated service for new homes. Peak reduction does not establish lower electricity use or emissions. We have not determined why performance changed between periods.

## What we'd do next

Evaluate the same approach on more households and genuinely new future data, with particular attention to peak timing and unexpected appliance use. For real use, obtain the intended household's recent readings and validate its forecasts and constraints before relying on recommendations.

## Sources and assistance

- Kaiser, K., Kreft, M., González Vayá, M., and Hug, G. [Dataset on residential electricity load profiles in Switzerland, v1](https://zenodo.org/records/21398769), DOI 10.5281/zenodo.21398769, CC BY 4.0. [Paper](https://arxiv.org/abs/2607.19294).
- [pandas](https://pandas.pydata.org/), [scikit-learn DecisionTreeRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeRegressor.html), [Matplotlib](https://matplotlib.org/), and [Streamlit](https://docs.streamlit.io/).
- OpenAI Codex/ChatGPT assisted with planning, implementation, debugging, tests, UI, and documentation. The student is reviewing the implementation and preparing their own explanation. shadcn and pick-ui-library guidance informed UI choices; the app uses Python/Streamlit, not React components.
