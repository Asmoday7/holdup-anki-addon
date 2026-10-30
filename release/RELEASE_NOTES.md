# HoldUp 1.0.0

The first stable release of HoldUp: schedule another look at a card while keeping
its normal Anki/FSRS review. Show the answer, press HoldUp, then give the original
your normal Again, Hard, Good or Easy rating.

- Extra practice appears in the same reviewer, with no separate window.
- Choose 1 second to 24 hours, or the next Anki study day using Anki's day-start setting.
- Every HoldUp press adds an independent appearance. Earlier appointments keep their deadlines.
- Repeat and Done affect only the extra appearance on screen, without submitting an FSRS rating.
- Native ratings, daily new-card limits and Undo/Redo remain available.
- Ready counts and deck-list clock badges make extra practice visible.
- English and Russian are included in one package and follow Anki's language.
- Existing HoldUp appointments are preserved when upgrading.

Runtime code is unchanged from 1.0.0-rc.3, apart from the version number.
On 30 October 2026 the owner reported completing all requested manual checks
after approximately a week of use and approved stable publication.
The attached validation JSON records this attributed report separately from the
actual Windows/Linux CI results for Anki 26.09 and 26.09.3.

Install `holdup-1.0.0.ankiaddon` through **Tools → Add-ons → Install from file**, then
restart Anki. Keep one enabled copy. Upload the same `.ankiaddon` to AnkiWeb;
the identical `.zip` is available if the upload form explicitly requires ZIP.

Support is one desktop installation per collection. Full collection `.colpkg`
exports and native backups preserve the queue; a deck `.apkg` does not transfer
the complete queue. Live multi-device conflict resolution is unverified.
AnkiDroid and AnkiMobile do not run this desktop add-on.

Free and open source under AGPL-3.0-or-later. Source, license and project notice
are included in the archive.

[User guide](https://github.com/Asmoday7/holdup-anki-addon/blob/main/USER_GUIDE.md) ·
[Русская инструкция](https://github.com/Asmoday7/holdup-anki-addon/blob/main/USER_GUIDE.ru.md) ·
[Validation](https://github.com/Asmoday7/holdup-anki-addon/blob/main/release/VALIDATION.md) ·
[Report a bug](https://github.com/Asmoday7/holdup-anki-addon/issues/new?template=bug_report.yml)
