# Appliance defaults

These are editable example runs, researched on 14 November 2026 using [Power NI's appliance guide](https://powerni.co.uk/help/energy-guides/which-appliances-use-the-most-electricity/).

| Appliance | Example minutes | Estimated kWh/run |
|---|---:|---:|
| Washing machine | 60 | 1.2 |
| Dishwasher | 120 | 2.4 |
| Tumble dryer | 60 | 2.5 |
| Electric oven | 60 | 2.2 |
| Electric hob | 30 | 0.75 |
| Air fryer | 30 | 0.75 |
| Vacuum cleaner | 30 | 0.35 |
| Kettle | 3 | 0.135 |

Durations are planning assumptions. The reference's washing energy is used with a one-hour example. Cooking, kettle, and vacuum estimates use reference power multiplied by example run time. Programme, load, model, and cycling affect actual consumption. Users can replace defaults with label/manual values.

The scheduler spreads each run's energy evenly over its duration. This preserves kWh but cannot reproduce heating or motor spikes. Historical household demand may already include appliance use, so planned runs are additional hypothetical loads. Completion is manually reported. No metered energy, bill saving, or carbon saving is established.

Plans use local SQLite storage for one household installation. Multiple users on a hosted copy would share this store; separate-user hosting needs account-scoped storage first.
