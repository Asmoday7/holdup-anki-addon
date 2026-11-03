# HoldUp 1.0.1

Compatibility update for Advanced Review Bottombar (AnkiWeb 1136455830).
Promotes the owner-confirmed 1.0.1-rc.2 fixes to a stable release. The runtime
code is unchanged from that candidate; only the version metadata changes.

- Fix the overlap between the HoldUp waiting status and interval captions above
  Again/Hard/Good/Easy. Captions outside the buttons now occupy their own line.
- Add a regression check for actual text intersections after scheduling HoldUp,
  in English/Russian with waiting/ready appointments and different window/font sizes.

Also includes these compatibility fixes:

- HoldUp stays available when Good, Hard or Easy buttons are hidden.
- Question counts work with renamed/restyled Show Answer buttons and are not duplicated.
- Custom answer-table widths and wide button layouts remain under the other add-on's control.
- Native question rendering respects either add-on load order.
- Ready practice retains a Continue studying action when the deck overview is customized.
- Starting a practice-only session no longer makes the custom bottom bar read nonexistent native scheduling states.

Tests load the actual Advanced Review Bottombar source and exercise default,
hidden-button and wide-button configurations in both load orders and English/Russian, including
normal ratings, original Undo, Repeat/Done Undo and unchanged native review logs
through extra practice. See [compatibility evidence](BOTTOMBAR_COMPATIBILITY.md).

Install `holdup-1.0.1.ankiaddon` through **Tools → Add-ons → Install from file**
and restart Anki. Keep one HoldUp copy enabled. Existing cards and extra-practice
appointments are preserved; the queue data format is unchanged.

The owner confirmed that the fixed candidate works in their installation on
4 November 2026 (Asia/Vladivostok). Automated release checks cover Windows and
Linux with Anki 26.09 and 26.09.3; macOS remains unverified.
