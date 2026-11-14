"""Editable example runs, based on Power NI's appliance guide."""
SOURCE = "https://powerni.co.uk/help/energy-guides/which-appliances-use-the-most-electricity/"
# Duration is an example run, and energy is an estimate rather than a meter reading.
APPLIANCES = {
    "Washing machine": {"minutes": 60, "kwh": 1.2},
    "Dishwasher": {"minutes": 120, "kwh": 2.4},
    "Tumble dryer": {"minutes": 60, "kwh": 2.5},
    "Electric oven": {"minutes": 60, "kwh": 2.2},
    "Electric hob": {"minutes": 30, "kwh": 0.75},
    "Air fryer": {"minutes": 30, "kwh": 0.75},
    "Vacuum cleaner": {"minutes": 30, "kwh": 0.35},
    "Kettle": {"minutes": 3, "kwh": 0.135},
}
