"""Check crash recovery decisions without running MATLAB or touching saved results."""
import re
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import run_remaining_PhaseE as runner


def scenario(count, saved, behavior):
    calls = []
    jobs = pd.DataFrame({'tag': [str(i) for i in range(1, count + 1)]})

    def execute(command, **kwargs):
        match = re.search(r'phaseE_inject_batch\((\d+),(\d+)\)', ' '.join(command))
        assert match
        a, b = map(int, match.groups())
        calls.append((a, b))
        return SimpleNamespace(returncode=behavior(a, b, saved))

    runner.STOP.clear()
    with patch.object(runner, 'guard'), patch.object(
        runner, 'valid_record', side_effect=lambda out, tag, n: int(tag) in saved
    ), patch.object(runner.subprocess, 'run', side_effect=execute):
        error = None
        try:
            runner.run_batch('D', 1, count, jobs)
        except RuntimeError as exc:
            error = str(exc)
    return calls, error


def main():
    heap = 3221226356

    def fail_large(a, b, saved):
        if b - a + 1 > 2:
            saved.add(a)  # A crash can still leave a completed input.
            return heap
        saved.update(range(a, b + 1))
        return 0

    saved = {2}
    calls, error = scenario(4, saved, fail_large)
    assert error is None and saved == {1, 2, 3, 4}
    assert calls == [(1, 4)] * 3 + [(3, 4)], calls

    calls, error = scenario(1, set(), lambda a, b, saved: heap)
    assert len(calls) == 3 and 'single D input 1' in error

    calls, error = scenario(4, set(), lambda a, b, saved: 7)
    assert len(calls) == 1 and 'exit 7' in error

    calls, error = scenario(4, {1, 2, 3, 4}, lambda *args: 7)
    assert calls == [] and error is None

    def saved_before_crash(a, b, saved):
        saved.update(range(a, b + 1))
        return heap

    calls, error = scenario(4, set(), saved_before_crash)
    assert len(calls) == 1 and error is None
    print('PASS: split after heap crashes, skip saved inputs, bounded single-input failure, stop other errors, retain completed outputs.')


if __name__ == '__main__':
    main()
