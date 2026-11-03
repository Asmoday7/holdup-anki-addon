// Reviewer layout only: preserve Anki's native answer handlers.
(() => {
    "use strict";
    const strings = __HOLDUP_STRINGS__;
    const tr = (key, values = {}) => strings[key].replace(/\{(\w+)\}/g, (_, name) => String(values[name]));
    window.HoldUpButton?.destroy();
    let token = null;
    let intervalLabel = "1 " + tr("d");
    let studyDay = false;
    let pending = false;
    let scheduled = false;
    let counts = null;
    const cellId = "holdup-button-cell";
    let frame = null;
    let lastHeight = null;
    const style = document.createElement("style");
    style.textContent = `
        #holdup-queue-counts {
            font-size: small;
            line-height: 1.4;
            padding-top: 5px;
            text-align: center;
            white-space: nowrap;
        }
        #middle.holdup-counts-visible .stattxt { display: none; }
        #holdup-waiting {
            font-size: small;
            line-height: 1.4;
            opacity: .75;
            text-align: center;
            cursor: default;
        }
        .holdup-current-count { text-decoration: underline; }
        body.holdup-compact #innertable > tbody > tr > .stat { display: none; }
        .holdup-answer-table, .holdup-answer-table > tbody { display: block; }
        .holdup-answer-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: flex-end;
        }
        .holdup-answer-row > td { flex: 0 0 auto; }
        .holdup-answer-row button { margin-inline: 3px; }
        .holdup-answer-row button[data-ease], #holdup-button {
            box-sizing: border-box;
            width: var(--holdup-action-width, auto);
        }
        #holdup-button-cell > .nobold { display: block; }
        #holdup-practice-actions {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            padding-top: 10px;
        }
        #holdup-practice-actions button { margin-inline: 3px; }
    `;
    document.head.appendChild(style);

    function fitHeight() {
        const height = document.documentElement?.offsetHeight || 0;
        if (!height) return;
        if (height !== lastHeight && typeof window.pycmd === "function") {
            lastHeight = height;
            window.pycmd("holdup-layout");
        }
    }

    function scheduleRender() {
        if (frame === null) {
            frame = requestAnimationFrame(() => {
                frame = null;
                render();
                fitHeight();
            });
        }
    }

    function renderCounts() {
        const middle = document.getElementById("middle");
        if (!middle) return;
        let bar = document.getElementById("holdup-queue-counts");
        let status = document.getElementById("holdup-waiting");
        const question = Array.from(middle.querySelectorAll("button")).find(button =>
            button.id === "ansbut" || /\bpycmd\s*\(\s*(['"])ans\1\s*\)/.test(button.getAttribute("onclick") || ""));
        const matches = counts && (counts.phase === "question"
            ? question
            : middle.querySelector("button[data-ease], #holdup-practice-actions"));
        middle.classList.toggle("holdup-counts-visible", Boolean(matches));
        if (!matches) {
            bar?.remove();
            status?.remove();
            return;
        }
        if (!bar) {
            bar = document.createElement("div");
            bar.id = "holdup-queue-counts";
            bar.setAttribute("role", "status");
            middle.prepend(bar);
        }
        const signature = JSON.stringify(counts);
        if (!status) {
            status = document.createElement("div");
            status.id = "holdup-waiting";
            status.setAttribute("role", "status");
            bar.after(status);
        }
        const statusText = tr("HoldUp: waiting {count}", {count: counts.total - counts.ready});
        if (status.textContent !== statusText) status.textContent = statusText;
        status.hidden = counts.total === 0;
        status.dataset.ready = counts.ready;
        status.dataset.waiting = counts.total - counts.ready;
        if (bar.dataset.signature === signature) return;
        bar.dataset.signature = signature;
        const classes = ["new-count", "learn-count", "review-count"];
        const titles = [tr("New"), tr("Learning"),
            tr("Reviews: Anki {native}, HoldUp {ready}", {native: counts.native[2], ready: counts.ready})];
        const values = [...counts.native];
        values[2] += counts.ready;
        bar.replaceChildren();
        values.forEach((value, index) => {
            if (index) bar.append(" + ");
            const span = document.createElement("span");
            span.className = classes[index];
            span.textContent = String(value);
            span.title = titles[index];
            span.setAttribute("aria-label", titles[index] + ": " + value);
            if (index === counts.active) {
                span.classList.add("holdup-current-count");
                span.setAttribute("aria-current", "true");
            }
            bar.append(span);
        });
    }

    function render() {
        renderCounts();
        let cell = document.getElementById(cellId);
        let controls = document.getElementById("holdup-controls-table");
        const hasOwnUI = cell || document.getElementById("holdup-practice-actions")
            || document.getElementById("holdup-practice-question");
        const nativeShell = Boolean(document.getElementById("time")?.closest("button"));
        document.body.classList.toggle("holdup-compact", Boolean(hasOwnUI) && nativeShell && document.body.clientWidth < 583);
        const nativeButtons = Array.from(document.querySelectorAll("#middle button[data-ease]"));
        const good = nativeButtons.find(button => button.dataset.ease === "3") || nativeButtons[0];
        const nativeRow = good?.closest("tr");
        if ((!token && !pending && !scheduled) || !nativeRow) {
            cell?.remove();
            controls?.remove();
            document.querySelectorAll(".holdup-answer-row, .holdup-answer-table").forEach(el => {
                el.classList.remove("holdup-answer-row", "holdup-answer-table");
            });
            return;
        }
        const nativeTable = nativeRow.closest("table");
        // A custom table owns its declared sizing (including wide buttons).
        // Put our controls below it instead of rewriting its rows or widths.
        const separate = nativeTable.hasAttribute("width");
        let row = nativeRow;
        if (separate) {
            if (!controls || controls.previousElementSibling !== nativeTable) {
                controls?.remove();
                controls = document.createElement("table");
                controls.id = "holdup-controls-table";
                controls.cellPadding = controls.cellSpacing = "0";
                controls.insertRow();
                nativeTable.after(controls);
            }
            row = controls.rows[0];
        } else {
            controls?.remove();
        }
        if (!cell || cell.parentElement !== row) {
            cell?.remove();
            cell = document.createElement("td");
            cell.id = cellId;
            cell.style.textAlign = "center";
            cell.style.whiteSpace = "nowrap";
            const button = document.createElement("button");
            button.id = "holdup-button";
            button.type = "button";
            // Match the native action's dimensions, including at larger fonts.
            button.style.boxSizing = "border-box";
            button.textContent = "HoldUp";
            const caption = document.createElement("span");
            caption.className = "nobold";
            button.appendChild(caption);
            button.addEventListener("click", () => {
                if (!token || button.disabled) {
                    return;
                }
                pending = true;
                button.disabled = true;
                window.pycmd("holdup-button:" + token);
            });
            cell.appendChild(button);
            const settings = document.createElement("button");
            settings.id = "holdup-interval";
            settings.type = "button";
            settings.textContent = "⋯";
            settings.title = tr("Change the extra practice interval");
            settings.setAttribute("aria-label", settings.title);
            settings.style.minWidth = "0";
            settings.style.boxSizing = "border-box";
            settings.style.paddingInline = "0";
            settings.addEventListener("click", () => {
                if (token && !settings.disabled) {
                    pending = true;
                    settings.disabled = true;
                    window.pycmd("holdup-interval:" + token);
                }
            });
            cell.appendChild(settings);
            row.appendChild(cell);
            document.body.classList.toggle("holdup-compact", nativeShell && document.body.clientWidth < 583);
        }
        const button = cell.querySelector("#holdup-button");
        row.classList.add("holdup-answer-row");
        row.closest("table").classList.add("holdup-answer-table");
        row.style.removeProperty("--holdup-action-width");
        const nativeStyle = getComputedStyle(good);
        button.style.font = nativeStyle.font;
        button.style.padding = nativeStyle.padding;
        button.style.height = good.offsetHeight + "px";
        const width = Math.max(button.offsetWidth, ...Array.from(
            nativeButtons, b => b.offsetWidth));
        row.style.setProperty("--holdup-action-width", width + "px");
        const settings = cell.querySelector("#holdup-interval");
        settings.style.font = nativeStyle.font;
        settings.style.padding = "0";
        settings.style.width = settings.style.height = good.offsetHeight + "px";
        button.dataset.token = token;
        button.title = (studyDay ? tr("Extra practice at the start of the next Anki study day.")
            : tr("Extra practice in {interval}.", {interval: intervalLabel})) + " " +
            tr("No FSRS rating is recorded. The original stays in Anki: choose a normal rating separately.")
            + " " + tr("Each press adds a separate extra appearance.");
        const caption = cell.querySelector(".nobold");
        if (separate && caption.parentElement !== cell) cell.prepend(caption);
        button.disabled = pending || scheduled;
        cell.querySelector('#holdup-interval').disabled = pending || scheduled;
        const text = (scheduled ? "✓ " : "") + intervalLabel;
        if (scheduled) button.title = tr("Extra practice scheduled. Now choose a normal Anki rating.");
        // Updating identical text would retrigger our child-list observer forever.
        if (caption.textContent !== text) {
            caption.textContent = text;
        }
    }

    const observer = new MutationObserver(scheduleRender);
    const resizeObserver = new ResizeObserver(scheduleRender);
    function observe() {
        observer.observe(document.body, { childList: true, subtree: true });
        resizeObserver.observe(document.body);
        scheduleRender();
    }
    if (document.body) {
        observe();
    } else {
        document.addEventListener("DOMContentLoaded", observe, { once: true });
    }
    window.HoldUpButton = {
        counts(value) {
            counts = value;
            scheduleRender();
        },
        show(value) {
            token = value.token;
            intervalLabel = value.label;
            studyDay = Boolean(value.study_day);
            pending = scheduled = false;
            // Closing settings can reuse the DOM; enable only on a fresh show.
            document.getElementById("holdup-button")?.removeAttribute("disabled");
            document.getElementById("holdup-interval")?.removeAttribute("disabled");
            render();
            scheduleRender();
        },
        hide() {
            token = null;
            pending = scheduled = false;
            render();
            scheduleRender();
        },
        pending() {
            token = null;
            pending = true;
            render();
            scheduleRender();
        },
        scheduled() {
            token = null;
            pending = false;
            scheduled = true;
            render();
            scheduleRender();
        },
        destroy() {
            observer.disconnect();
            resizeObserver.disconnect();
            if (frame !== null) cancelAnimationFrame(frame);
            style.remove();
            document.body.classList.remove("holdup-compact");
            document.getElementById("holdup-queue-counts")?.remove();
            document.getElementById("holdup-waiting")?.remove();
            document.getElementById("middle")?.classList.remove("holdup-counts-visible");
            document.querySelectorAll(".holdup-answer-row, .holdup-answer-table").forEach(el => {
                el.classList.remove("holdup-answer-row", "holdup-answer-table");
            });
            document.removeEventListener("DOMContentLoaded", observe);
            document.getElementById(cellId)?.remove();
            document.getElementById("holdup-controls-table")?.remove();
        },
    };
})();
