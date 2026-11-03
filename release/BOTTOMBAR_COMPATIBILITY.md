# Advanced Review Bottombar compatibility

HoldUp 1.0.1-rc.2 addresses interaction with
[Advanced Review Bottombar](https://ankiweb.net/shared/info/1136455830).
Initial feedback did not include reproduction steps. Later screenshots exposed
the waiting-status/interval overlap missed by the first candidate. The problems
below were reproduced with the upstream source in disposable Anki profiles.

The upstream source used for the checks is
[`noobj2/Anki-Advanced-Review-Bottombar` at `7fd5c16090b5b7c0e2f26d040a6552680d29684c`](https://github.com/noobj2/Anki-Advanced-Review-Bottombar/tree/7fd5c16090b5b7c0e2f26d040a6552680d29684c).
It is downloaded separately for testing and is not bundled into HoldUp.

## Problems addressed

1. HoldUp's fifth-button placement previously required both Good and Easy.
   Bottombar can remove either button, so placement now uses an available rating.
2. Bottombar can rename or omit the Show Answer element ID and move the native
   counts outside that button. HoldUp recognizes the actual answer action and
   shows one set of counts.
3. Bottombar declares its own answer-table width. HoldUp puts its controls below
   custom-width tables instead of converting their native rows to its flex layout.
4. When Bottombar loads later, its class-level question renderer must not be
   lost behind HoldUp's previously saved bound method. Native dispatch now
   observes later class replacements while preserving explicit instance wrappers.
5. Bottombar's customized deck overview omits the standard bottom-render hook.
   HoldUp adds one Continue studying action and handles it through the normal bridge.
6. Bottombar's bottom HTML calls the native remaining-count renderer during
   practice-only startup, when there are deliberately no native scheduling
   states. HoldUp supplies its own counters without inventing scheduling states.
7. Bottombar places interval captions outside the rating buttons. Anki's default
   absolute positioning makes those captions escape above their row into the
   HoldUp waiting status. Direct table-cell captions now reserve their own height
   in normal flow. Captions inside standard Anki buttons keep their native layout.

## Reproducible checks

`tests/bottombar_probe.py` installs the actual upstream source and a freshly
packaged HoldUp into a disposable profile. It checks three configurations in
both load orders and in English/Russian: default, hidden Good/Hard/Easy with
custom sizes, and wide buttons with Easy hidden. It exercises native ratings, Undo of the original,
practice-only startup, Continue studying, Repeat, Done and their Undo actions.
Extra practice must leave native scheduling state and review logs unchanged.

After a real HoldUp press, text bounds are checked for overlaps between counts,
the visible waiting status, native interval captions and action labels. The check
includes waiting and already-ready appointments with the original answer still
open, window widths of 900/1100/1600 pixels, 100/150/200% CSS zoom and larger fonts.
Only the GUI clock advances for the ready-status check; native scheduling state
and the stored appointment remain unchanged. The new check fails on rc.1 with
the same waiting/interval overlap shown in the user's screenshots.

The default configuration on the original HoldUp reproduced duplicate question
counts before the fix. A subsequent run also exposed the practice-only startup
exception in the upstream bottom HTML.

To run locally, check out the upstream commit above, install
`requirements-gui.txt` in a virtual environment, and set
`HOLDUP_BOTTOMBAR_SOURCE` to that checkout before running pytest. The source path
is optional for local unit-only work; release CI provides it and requires all
twelve compatibility scenarios without skips.

CI runs these checks alongside the existing backend and four standalone desktop
scenarios on Windows/Python 3.13 and Linux/Python 3.12 with Anki 26.09 and 26.09.3.
Job results remain the evidence for which combinations actually passed.
Real-user confirmation of this candidate has not yet been reported.
