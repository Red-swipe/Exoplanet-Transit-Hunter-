"""Test bare KepID vs 'KIC ' prefixed search."""
import lightkurve as lk
import time

for target in ["10000162", "KIC 10000162"]:
    t0 = time.time()
    try:
        result = lk.search_lightcurve(target, mission="Kepler")
        t1 = time.time()
        n = 0 if result is None else len(result)
        print(f'target={target!r:20s}  {n:2d} results  in {t1-t0:.1f}s')
        if result is not None and n > 0:
            print(f'  First row target_name={result[0].target_name!r}, author={result[0].author!r}')
    except Exception as e:
        t1 = time.time()
        print(f'target={target!r:20s}  FAIL ({t1-t0:.1f}s): {e}')
