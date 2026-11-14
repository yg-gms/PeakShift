import json
from pathlib import Path

from evaluation import evaluate_period
from explore import METER_ID
from forecast import MODEL_SETTINGS, build_forecasts


if __name__ == "__main__":
    comparison, validation_start, test_start = build_forecasts()
    results_folder = Path(__file__).resolve().parent / "results"
    results_folder.mkdir(exist_ok=True)
    report = {}

    for name, period in {
        "validation": comparison.loc[comparison.index < test_start],
        "test": comparison.loc[comparison.index >= test_start],
    }.items():
        scores, schedules = evaluate_period(period)
        report[name] = scores
        schedules.to_csv(results_folder / f"{name}-scheduling.csv")
        print(f"{name.upper()}: {scores['days']} days, {scores['hours']} hours; "
              f"{scores['skipped_days']} skipped days {scores['skipped_dates']}")
        print(f"Hourly MAE: baseline {scores['baseline_hourly_mae_kw']:.3f}, "
              f"model {scores['model_hourly_mae_kw']:.3f} kW")
        print(f"Daily peak MAE: baseline {scores['baseline_peak_mae_kw']:.3f}, "
              f"model {scores['model_peak_mae_kw']:.3f} kW")
        print("Average simulated daily peaks (kW):")
        print(schedules.mean().round(3))
        for reference in ["Original", "Baseline"]:
            reduction = (schedules[reference] - schedules["Model"]).round(9)
            outcomes = {
                "better": int((reduction > 0).sum()),
                "equal": int((reduction == 0).sum()),
                "worse": int((reduction < 0).sum()),
            }
            scores[f"model_vs_{reference.lower()}"] = outcomes
            print(f"Model vs {reference}: {outcomes}")
        scores["average_simulated_peak_kw"] = schedules.mean().to_dict()

    report["model"] = {"meter_id": METER_ID, **MODEL_SETTINGS}
    report["validation_start"] = str(validation_start)
    report["test_start"] = str(test_start)
    (results_folder / "evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
