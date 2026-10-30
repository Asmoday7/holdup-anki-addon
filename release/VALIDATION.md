# HoldUp 1.0.0 validation

Stable release: **1.0.0**. Automated reports use UTC; the owner reported manual
acceptance on **30 October 2026**.

## Manual acceptance

Asmoday7 reported: «я все проверил уже как неделю примерно» and requested the
final stable release. This closes the requested Windows manual checks, including
the real next-study-day check, on the basis of the owner's all-checks report.

The [original attributed report](manual-validation.json) is included in the stable
release's machine-readable validation record. The exact installed candidate,
Windows/Anki/Python/Qt versions and individual case logs were not restated.
These results are attributed to the owner; they are not a new independent manual
test by the assistant. Manual evidence does not automatically extend to macOS,
other card templates or live multi-device sync.

## Automated validation

The stable release workflow runs the full **236-test** suite in four environments:

| Environment | Checks |
| --- | --- |
| Linux / Python 3.12 / Anki 26.09 | Full suite, four packaged desktop scenarios |
| Linux / Python 3.12 / Anki 26.09.3 | Full suite, four packaged desktop scenarios |
| Windows runner / Python 3.13 / Anki 26.09 | Full suite, four packaged desktop scenarios |
| Windows runner / Python 3.13 / Anki 26.09.3 | Full suite, four packaged desktop scenarios |

Publication requires all four jobs to pass without skips and their installers to
be byte-identical. Stable publication also requires the recorded manual approval
to match the release version. Missing, incomplete and wrong-version approvals have
regression checks. The actual stable results are attached as `validation-1.0.0.json`
to the [release](https://github.com/Asmoday7/holdup-anki-addon/releases/tag/v1.0.0).

The desktop probe waits for Anki's complete native cleanup and requires a clean
subprocess exit. Its stale-queue case externally buries the displayed card to
guarantee a different head. JavaScript errors and missing GUI cases remain failures.

## Storage and load

Integration tests restore modern and legacy full exports and a native backup.
A 2000-appearance regression covers selective Repeat, clearing, Undo/Redo and
unchanged native schedule/history. APKG tests verify the documented lack of the
current collection queue after a deck import.

The initial synthetic 1000-item benchmark on Linux took 7.858 seconds to clear;
after the snapshot fix it took 0.014 seconds. These are observations, not timing
guarantees. Each stable CI job records its own 1000-item benchmark.

## Earlier evidence

The preceding rc.3 passed **231 tests in each of four Windows/Linux jobs**:
[tagged run](https://github.com/Asmoday7/holdup-anki-addon/actions/runs/40094640748),
[unaltered published report](validation-1.0.0-rc.3.json).
[Local rc.1 results](local-validation.json) and [benchmarks](benchmarks) are retained
as historical evidence. These reports are not relabelled as stable test runs.

macOS remains unverified. Live multi-device sync/conflict resolution is outside
the first release's support guarantee.
