# PeakShift progress and remaining work

Updated: Saturday 14 November 2026, 16:56 Hong Kong time.

## Time and scope

Solo project. User attention budget: 6–8 hours total across Saturday and Sunday; no Monday-morning work. Active attention has not been timed, so the remaining estimates are not a measured budget balance. Finish and aim to submit on Sunday evening, before the official Monday 16 November 12:59 PM HKT deadline.

Keep the code short and understandable. The assistant handles repetitive implementation and preparation; the user understands the logic, reviews results, and records the demo. Update this tracker after each milestone with actual results and revised estimates.

## Current evidence

- Done: Swiss data subset downloaded and checked; one household used for the current model.
- Done: hourly conversion, missing-data handling, plots, chronological training/validation split.
- Working: decision-tree forecasting. Validation hourly MAE: baseline 0.564 kW, model 0.453 kW. Daily peak MAE: baseline 2.998 kW, model 2.487 kW.
- Done on validation: fixed one-hour, 1 kW scheduling across 110 days (0 skipped). Average simulated daily peak: original 5.194 kW, baseline schedule 4.894 kW, model schedule 4.715 kW. Model vs original: 57 better, 51 equal, 2 worse. Model vs baseline: 20 better, 89 equal, 1 worse. These are simulations, not measured interventions; final-test results are recorded below.
- Checked: six automated tests pass. Scheduler chooses using predictions; actual readings are used afterward for evaluation.
- Done: fixed-setting final evaluation on 109 complete days / 2,616 hours from 13 September to 31 December 2024; skipped the 25-hour day on 27 October. Hourly MAE: baseline 0.807, model 0.781 kW. Daily peak MAE: baseline 2.272, model 2.604 kW (model worse). Model scheduling: 1 better / 108 equal / 0 worse versus original; 0 better / 109 equal / 0 worse versus baseline scheduling. No model settings were changed after final-test access.
- Not done: usable app interface, submission write-up/video, submission. Keep one household/model for the required build; additional household models are deferred.

## Remaining milestones

These are estimates of the user's focused time; assistant implementation can take additional wall-clock time.

| Order | Deliverable | User time estimate | Finish condition |
|---|---|---|---|
| 1 | DONE: evaluate scheduling across all eligible validation days | 0 min | Compare original 18:00 start, yesterday-forecast scheduling, and model-forecast scheduling on the same days; report average peaks and counts of better/equal/worse decisions. Report skipped incomplete or clock-change days. |
| 2 | DONE: freeze the approach and run final evaluation | 0 min | Report forecast and scheduling results on the reserved test period, including failures; no tuning from final test results. |
| 3 | Small Python app | 45 min | One screen: historical day, one one-hour task, power and allowed-window inputs, recommended start, and original/recommended demand chart. Defaults match the current experiment. Clearly label the historical simulation. |
| 4 | Write-up and two-minute video | 60 min | Explain user, data, model, baseline, decision results, one failure, sources, and AI assistance. Assistant prepares the draft; user reviews and narrates. |
| 5 | Check links and submit | 15 min | Code and write-up accessible to judges; video link works; submission confirmed by user. |
| Buffer | Fixes and explanation | 30 min | Protect submission time. |

Target: about 2.5 additional hours of user attention for the app, write-up/video, submission, and buffer. Revise downward if less attention remains.

## Scope limits

One household for the main submission, one task at a time, and one-hour duration. No extra model search unless a concrete failure blocks the core experiment. No chatbot/API integration, multiple-appliance scheduling, live smart-meter connection, account system, carbon estimates, or bill-savings claims in the required build.

If time becomes tight, keep a simple runnable Python demo and complete the required code and write-up before polishing the interface or video. Weak or negative scheduling results must remain visible; do not choose only successful examples.

Latest scheduling results are saved in `results/validation-scheduling.csv` and reproduced by `python train.py`. About 2.5 hours of user attention remain estimated for the app, submission, and buffer; attention already spent is still unmeasured.

## Final-test interpretation

The model improved hourly MAE slightly but worsened daily peak MAE, and its scheduler did not beat the baseline scheduler in the final period. This limits the evidence for AI-assisted scheduling outside validation. Preserve and show this result. Changing the model or task after viewing this test would require a genuinely new unseen evaluation; do not reuse this period as an untouched final test. Next milestone: a small historical demonstration with honest results, not additional model search.
