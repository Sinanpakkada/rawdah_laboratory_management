odoo.define('rawdah_laboratory_management.enter_navigation', [], function (require) {
    "use strict";
    // debug marker
    console.log("RAWDAH ENTER LISTENER: loaded");
    window.__rawdah_enter_to_next_installed = true;

    // only install once
    if (window.__rawdah_enter_listener_installed) {
        return;
    }
    window.__rawdah_enter_listener_installed = true;

    // Capture-phase listener so we run before many widgets handle Enter.
    document.addEventListener('keydown', function (ev) {
        try {
            if (ev.key !== 'Enter') { return; }

            const target = ev.target;
            if (!target) { return; }

            // ignore if inside textarea or contenteditable
            if (target.tagName === 'TEXTAREA' || target.isContentEditable) { return; }

            // ignore if modifier keys are pressed
            if (ev.ctrlKey || ev.metaKey || ev.altKey) { return; }

            // ignore if input is disabled/readonly
            if (target.disabled || target.readOnly) { return; }

            // Limit scope: only when inside an Odoo backend view area
            // This will allow it in form pages but not break dialogs/lists.
            const allowedRoot = target.closest('.o_form_view, .o_form_sheet, .o_content, .o_main_content');
            if (!allowedRoot) { return; }

            // prevent default submit/save behavior
            ev.preventDefault();

            // Build list of focusable fields within the same container (prefer form root)
            const container = allowedRoot;
            const selector = [
                'input:not([type=hidden]):not([disabled]):not([readonly])',
                'select:not([disabled]):not([readonly])',
                'textarea:not([disabled])'
            ].join(',');

            const elems = Array.from(container.querySelectorAll(selector))
                .filter(el => el.offsetParent !== null); // visible

            // If nothing found in this container, fallback to global page
            if (elems.length === 0) {
                const globalElems = Array.from(document.querySelectorAll(selector))
                    .filter(el => el.offsetParent !== null);
                const gi = globalElems.indexOf(target);
                if (gi >= 0 && gi < globalElems.length - 1) {
                    globalElems[gi + 1].focus();
                }
                return;
            }

            const idx = elems.indexOf(target);
            if (idx === -1) {
                // If target not found in container, attempt global list
                const globalElems = Array.from(document.querySelectorAll(selector))
                    .filter(el => el.offsetParent !== null);
                const gidx = globalElems.indexOf(target);
                if (gidx >= 0 && gidx < globalElems.length - 1) {
                    globalElems[gidx + 1].focus();
                }
                return;
            }

            // focus next visible element
            const next = elems[idx + 1];
            if (next) {
                next.focus();
                // place cursor at end for text inputs
                try {
                    if (next.setSelectionRange && (next.type === 'text' || next.type === 'search' || next.type === 'tel' || next.type === 'email' || next.type === 'url')) {
                        const vlen = next.value ? next.value.length : 0;
                        next.setSelectionRange(vlen, vlen);
                    }
                } catch (err) { /* ignore */ }
            }
            // debug log
            console.log("RAWDAH ENTER LISTENER: Enter pressed, moved focus", target, "->", next || null);
        } catch (e) {
            // fail-safe: never crash the client
            console.error("RAWDAH ENTER LISTENER ERROR:", e);
        }
    }, true); // capture phase
});
