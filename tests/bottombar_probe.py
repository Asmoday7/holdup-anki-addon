"""Exercise two real add-ons in a disposable Anki profile, without AnkiWeb."""

import importlib
import json
from pathlib import Path
import shutil
import sys
import time


def main(base, archive, source, order, style):
    import anki.lang
    import aqt
    from aqt.profiles import ProfileManager, VideoDriver
    from aqt.qt import QEvent, QTimer

    anki.lang.set_lang("en")
    base.mkdir(parents=True)
    pm = ProfileManager(base)
    pm.setupMeta()
    pm.create("Compatibility")
    pm.load("Compatibility")
    pm.meta.update(firstRun=False, defaultLang="en")
    pm.profile["autoSync"] = False
    pm.set_update_check(False)
    pm.set_check_for_addon_updates(False)
    pm.set_video_driver(VideoDriver.Software)
    pm.save()
    pm.db.close()
    app = aqt._run(["holdup-compatibility", "-b", str(base), "-p", "Compatibility", "-l", "en"], exec=False)
    mw = aqt.mw
    assert app is not None and mw is not None
    alerts = []
    import aqt.webview
    aqt.webview.showInfo = lambda message, **_kwargs: alerts.append(message)

    def wait(predicate, label, seconds=20):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            app.processEvents()
            app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            assert not alerts, repr(alerts)
            if predicate():
                return
            time.sleep(.01)
        mw.grab().save(str(base / "timeout.png"))
        raise AssertionError(f"Timed out: {label}; state={mw.state}, reviewer={mw.reviewer.state}")

    def js(expression, web=None):
        result = []
        (web or mw.bottomWeb).evalWithCallback(expression, result.append)
        wait(lambda: bool(result), "JavaScript callback")
        return result[0]

    def loaded():
        return (not mw._background_op_count and mw.web._domDone and mw.bottomWeb._domDone
                and not mw.web.page().isLoading() and not mw.bottomWeb.page().isLoading())

    def undo():
        wait(lambda: not runtime.busy and not mw._background_op_count, "before Undo")
        mw.onUndo()

    def show_answer():
        wait(lambda: mw.reviewer.state == "question" and loaded(), "question")
        mw.reviewer._linkHandler("ans")
        wait(lambda: mw.reviewer.state == "answer", "answer")

    def snapshot(cid):
        card = mw.col.get_card(cid)
        return (card.due, card.queue, card.type, card.ivl, card.reps, card.lapses,
                card.memory_state.SerializeToString() if card.memory_state else None,
                [r.SerializeToString() for r in mw.col.get_review_logs(cid)])

    try:
        wait(lambda: mw.col is not None and mw.state == "deckBrowser" and loaded(), "profile")
        advanced = Path(mw.addonManager.addonsFolder("1136455830"))
        shutil.copytree(source, advanced, ignore=shutil.ignore_patterns(".git", "github_images", "__pycache__"))
        config = json.loads((source / "config.json").read_text())
        config["Button Label_ Show Answer"] = "Reveal (ARB)"
        if style != "default":
            config.update({" Review_ Bottombar Buttons Style": 1,
                           "Button_   Hide Easy": True,
                           "Button_  Custom Button Sizes": True,
                           "Button_ Width_ Review Buttons": 100,
                           "Button_ Width_ Edit Button": 65,
                           "Button_ Width_ More Button": 65,
                           "Button_ Width_ Info Button": 65,
                           "Button_ Width_ Skip Button": 65})
        if style == "hidden":
            config["Button_   Hide Good"] = True
            config["Button_   Hide Hard"] = True
        if style == "wide":
            config[" Review_ Buttons Style"] = 2
        mw.addonManager.writeConfig("1136455830", config)
        mw.addonManager.install(str(archive))
        mw.addonManager.writeConfig("holdup", {"interval_seconds": 7200, "interval_mode": "seconds"})
        for name in (["1136455830", "holdup"] if order == "before" else ["holdup", "1136455830"]):
            importlib.import_module(name)
        from holdup.practice import PracticeQueue
        from holdup.reviewer_adapter import _controller
        runtime = _controller.runtime
        queue = PracticeQueue(mw.col)
        col = mw.col
        col.set_config("fsrs", True)
        config = col.decks.config_dict_for_deck_id(1)
        config["new"].update(delays=[], perDay=10)
        config["autoplay"] = False
        col.decks.update_config(config)
        model = next(m for m in col.models.all() if m["type"] == 0 and len(m["flds"]) == 2 and len(m["tmpls"]) == 1)
        for index in range(2):
            note = col.new_note(model)
            note.fields[0], note.fields[1] = f"Compatibility {index}", "Answer"
            col.add_note(note, 1)
        mw.resize(1100, 850)
        mw.moveToState("review")
        wait(lambda: mw.reviewer.state == "question" and loaded(), "first native question")
        wait(lambda: js("document.querySelector('#holdup-queue-counts') !== null"), "question counters")
        assert js("document.querySelector('#middle').textContent.includes('Reveal (ARB)')"), "Late-loaded bottombar question renderer was lost"
        assert js("Array.from(document.querySelectorAll('#middle .stattxt')).every(s => getComputedStyle(s).display === 'none')"), "Duplicate native question counts"
        first = mw.reviewer.card.id
        before = snapshot(first)
        show_answer()
        wait(lambda: js("document.querySelector('#holdup-button:not(:disabled)') !== null"), "HoldUp with configured answer buttons")
        expected = [1] if style == "hidden" else ([1, 2, 3] if style == "wide" else [1, 2, 3, 4])
        assert js("Array.from(document.querySelectorAll('#middle button[data-ease]')).map(b=>Number(b.dataset.ease))") == expected
        dimensions = "Array.from(document.querySelectorAll('#middle button[data-ease]')).map(b=>[b.dataset.ease,b.offsetWidth,b.offsetHeight])"
        with_holdup = js(dimensions)
        js("window.HoldUpButton.hide(); true")
        assert js(dimensions) == with_holdup, "HoldUp changed the custom native button dimensions"
        _controller.on_answer(mw.reviewer.card)
        wait(lambda: js("document.querySelector('#holdup-button:not(:disabled)') !== null"), "rearmed layout")
        assert js(dimensions) == with_holdup
        geometry = """Array.from(document.querySelectorAll('#holdup-button, #holdup-interval')).every(b => {
            const box = b.getBoundingClientRect();
            const range = document.createRange(); range.selectNodeContents(b);
            const text = range.getBoundingClientRect();
            return box.width > 0 && box.height > 0 && box.left >= 0 && box.right <= innerWidth
                && box.bottom <= innerHeight + 1 && text.left >= box.left - 1
                && text.right <= box.right + 1 && text.top >= box.top - 1 && text.bottom <= box.bottom + 1;
        })"""
        try:
            wait(lambda: js(geometry), "HoldUp controls and their text fit after layout")
        except AssertionError:
            print("CONTROL GEOMETRY", js("""Array.from(document.querySelectorAll('#holdup-button, #holdup-interval')).map(b=>{
                const r=b.getBoundingClientRect(), t=document.createRange();t.selectNodeContents(b);
                const q=t.getBoundingClientRect();return {id:b.id,box:[r.x,r.y,r.width,r.height],
                    text:[q.x,q.y,q.width,q.height],viewport:[innerWidth,innerHeight],padding:getComputedStyle(b).padding};
            })"""), flush=True)
            raise
        mw.grab().save(str(base / "normal-controls.png"))
        native_styles = js("Array.from(document.querySelectorAll('#middle button[data-ease]')).map(b=>[b.dataset.ease,b.getAttribute('style'),getComputedStyle(b).color])")
        js("document.querySelector('#holdup-button').click(); true")
        wait(lambda: len(queue.for_card(first)) == 1 and not runtime.busy, "appointment")
        assert snapshot(first) == before
        wait(lambda: js("document.querySelector('#holdup-button').disabled"), "scheduled checkmark")
        assert js("Array.from(document.querySelectorAll('#middle button[data-ease]')).map(b=>[b.dataset.ease,b.getAttribute('style'),getComputedStyle(b).color])") == native_styles
        # Keyboard ratings remain valid even when the user hides their buttons.
        mw.reviewer._answerCard(4)
        wait(lambda: mw.reviewer.state == "question" and mw.reviewer.card.id != first and loaded(), "native rating")
        assert len(col.get_review_logs(first)) == 1
        undo()
        wait(lambda: mw.reviewer.card is not None and mw.reviewer.card.id == first and mw.reviewer.state == "question" and loaded(), "Undo original")
        assert snapshot(first) == before and len(queue.for_card(first)) == 1
        show_answer()
        mw.reviewer._answerCard(4)
        wait(lambda: mw.reviewer.state == "question" and mw.reviewer.card.id != first and loaded(), "original answered again")
        second = mw.reviewer.card.id
        show_answer()
        mw.reviewer._answerCard(4)
        wait(lambda: mw.state == "overview" and loaded(), "native finished overview")
        native_first, native_second = snapshot(first), snapshot(second)
        # Make one real extra appearance ready without altering any card state.
        queue.enqueue(first, 1, time.time_ns() // 1_000_000 - 2000)
        runtime._overview_count = None
        runtime.refresh()
        wait(lambda: loaded() and js("document.body.textContent.includes('Continue studying')"), "Continue studying with custom overview renderer")
        assert js("Array.from(document.querySelectorAll('button')).filter(b=>b.textContent.includes('Continue studying')).length") == 1
        js("Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('Continue studying')).click(); true")
        wait(lambda: mw.state == "review" and runtime.flow.active is not None and mw.reviewer.state == "question" and loaded(), "practice question")
        request = runtime.flow.active
        show_answer()
        wait(lambda: js("document.querySelector('#holdup-practice-repeat:not(:disabled)') !== null"), "practice controls")
        assert snapshot(first) == native_first
        mw.reviewer._answerCard(3)
        assert snapshot(first) == native_first
        js("document.querySelector('#holdup-practice-repeat').click(); true")
        wait(lambda: not runtime.busy and queue.get(first, request.request_id) != request and mw.state == "overview" and loaded(), "practice repeat")
        undo()
        wait(lambda: runtime.flow.active == request and mw.reviewer.state == "question" and loaded(), "Undo repeat")
        show_answer()
        wait(lambda: js("document.querySelector('#holdup-practice-release:not(:disabled)') !== null"), "Done button")
        js("document.querySelector('#holdup-practice-release').click(); true")
        wait(lambda: not runtime.busy and queue.get(first, request.request_id) is None and mw.state == "overview" and loaded(), "Done")
        undo()
        wait(lambda: runtime.flow.active == request and mw.reviewer.state == "question" and loaded(), "Undo Done")
        assert snapshot(first) == native_first and snapshot(second) == native_second
        assert len(col.find_cards("")) == 2
        mw.grab().save(str(base / "compatibility.png"))
        print(f"PASS compatibility: {order}, {style}; native ratings, original Undo, extra practice, Repeat/Done Undo, no extra FSRS logs", flush=True)
    finally:
        if mw.col is not None:
            watchdog = QTimer()
            watchdog.setSingleShot(True)
            watchdog.timeout.connect(lambda: app.exit(1))
            watchdog.start(20000)
            mw.unloadProfileAndExit()
            assert app.exec() == 0, "Anki cleanup timed out"
            watchdog.stop()
            print("CLEAN SHUTDOWN", flush=True)


if __name__ == "__main__":
    main(*(Path(x) for x in sys.argv[1:4]), *sys.argv[4:6])
