"""Validate exact models and high-phase evaluation before selecting windows."""
import math
import time
from wide_common import HERE, RESEARCH, read, save, sha, utc, input_files
import wide_scan as scan


def main():
    started = time.perf_counter()
    plan = read(HERE / 'WIDE_PLAN.json')
    hashes = {p.relative_to(RESEARCH).as_posix(): sha(p) for p in input_files()}
    cached = HERE / 'SETUP_CHECKS.json'
    if cached.exists() and read(cached).get('input_sha256') == hashes and read(cached).get('status') == 'PASS':
        print('PREFLIGHT_ALREADY_PASSED', flush=True)
        return
    engine, np = scan.engine, scan.engine.np
    checks = []
    assert plan['regions_per_anchor'] % plan['strata_per_anchor'] == 0
    models = read(RESEARCH / plan['source_plan'])['models']
    for model in models:
        exact = [(n, int(math.gcd(n + model['m'], model['P']) == 1)
                      - int(math.gcd(n, model['P']) == 1)) for n in range(1, model['N'] + 1)]
        assert [(n, e) for n, e in exact if e] == list(zip(model['support'], model['signs']))
        patterns = engine.all_patterns(model['signs'])
        assert len(patterns) == (70 if model['k'] == 3 else 11440)
        sources = scan.sources(model, patterns, plan)
        base = scan.region_base(plan['anchors'][-1], plan['regions_per_anchor'] - 1, plan)
        for rule in plan['rules']:
            cs, ds, _ = engine.phase_grid(model['support'], rule, base, plan)
            coeff = engine.coefficients(patterns, rule)
            result, _ = engine.screen(coeff, cs, ds, rule, plan, plan['backend'])
            comparison = None
            if plan['backend'] == 'gpu':
                cpu, _ = engine.screen(coeff, cs, ds, rule, plan, 'cpu')
                assert np.array_equal(cpu[0], result[0]) and np.array_equal(cpu[2], result[2])
                mask = np.isfinite(cpu[1]) & np.isfinite(result[1])
                assert np.max(np.abs(cpu[1][mask] - result[1][mask])) < plan['validation_absolute_tolerance']
                comparison = True
            precision = engine.validate_precision(model, patterns, rule, base, plan, cs, ds, plan['backend'])
            for source in sources:
                index = int(result[0][source['pattern_index']])
                if index >= 0:
                    # An extremum too close to a block edge is a missing slot, not a failed run.
                    engine.refine(model, source['signs'], rule, base, index, plan)
            checks.append({'k': model['k'], 'rule': rule, 'base': base,
                           'CPU_GPU_indices_match': comparison, **precision})
    # Selection fixture uses its own fixed geometry, independent of run size.
    fixture_plan = {**plan, 'regions_per_anchor': 12, 'strata_per_anchor': 3}
    rows = []
    for index, merit, bracket in [(0, -.1, 2), (1, -.9, 3), (3, -.9, 4), (4, -.2, 5), (5, None, -1)]:
        rows.append({'anchor': plan['anchors'][0], 'k': 3, 'rule': 'A_min', 'region_index': index,
                     'base': scan.region_base(plan['anchors'][0], index, fixture_plan),
                     'selected_sources': [{'source': 'original', 'bracket_index': bracket, 'grid_merit': merit}]})
    selected = scan.select_winners(rows, fixture_plan)
    assert len(selected) == 2
    assert [x[1][0]['region_index'] for x in selected] == [1, 4]
    missing = {**rows[-1], 'region_index': 8}
    assert scan.select_winners([missing], fixture_plan)[0][1] is None
    save(cached, {'status': 'PASS', 'utc': utc(), 'target_zeta_called': False,
                 'checks': checks, 'stratification_tie_and_missing_tests': 'PASS',
                 'input_sha256': hashes, 'elapsed_seconds': time.perf_counter() - started})
    print('PREFLIGHT_PASS', len(checks), flush=True)


if __name__ == '__main__':
    main()
