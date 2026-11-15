from copy import deepcopy
from daily_planner import plan_day


def task(id, appliance='Washer', after=None, **changes):
    return dict(id=id, appliance=appliance, after=after, minutes=60, kwh=1,
                earliest=480, deadline=720, status='Planned', start=None) | changes


def test_comparison():
    profile = [0.] * 24
    profile[8] = 3
    tasks = [task('a'), task('b', 'Dryer', 'a'), task('c')]
    original = deepcopy(tasks)
    earliest, curve = plan_day(profile, tasks, earliest_start=True)
    suggested, suggested_curve = plan_day(profile, tasks)
    assert [t['start'] for t in earliest] == [480, 540, 540]
    assert max(curve) == 4 and max(suggested_curve) < max(curve)
    assert abs(sum(curve) / 60 - sum(profile) - 3) < 1e-9
    assert abs(sum(curve) - sum(suggested_curve)) < 1e-9
    assert tasks == original
    fixed = [task('a', status='Running', start=540), task('b', 'Dryer', 'a')]
    result, _ = plan_day(profile, fixed, 570, earliest_start=True)
    assert [t['start'] for t in result] == [540, 600]
    result, _ = plan_day(profile, [task('a', deadline=510)], earliest_start=True)
    assert result[0]['start'] is None
    result, _ = plan_day(profile, [task('a')], 481, earliest_start=True)
    assert result[0]['start'] == 495
    print('Comparison checks passed: constraints, dependencies, fixed runs, energy, no mutation, infeasible windows, quarter-hours.')


if __name__ == '__main__':
    test_comparison()
