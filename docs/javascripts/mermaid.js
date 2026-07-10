(function () {
    "use strict";

    var _observer = null;

    function attachViewer(svg) {
        if (!svg || svg.dataset.viewerAttached) return;
        svg.dataset.viewerAttached = "true";
        svg.style.cursor = "zoom-in";
        svg.addEventListener("click", function () {
            createViewer(svg);
        });
    }

    function scanAndAttach() {
        document.querySelectorAll(".mermaid svg").forEach(attachViewer);
    }

    function initMermaidViewer() {
        scanAndAttach();

        if (_observer) return;

        _observer = new MutationObserver(function (mutations) {
            for (var i = 0; i < mutations.length; i++) {
                var nodes = mutations[i].addedNodes;
                for (var j = 0; j < nodes.length; j++) {
                    var node = nodes[j];
                    if (node.nodeType !== 1) continue;

                    if (node.tagName === "svg" && node.closest(".mermaid")) {
                        attachViewer(node);
                        continue;
                    }

                    if (node.classList && node.classList.contains("mermaid")) {
                        node.querySelectorAll("svg").forEach(attachViewer);
                        continue;
                    }

                    if (node.querySelectorAll) {
                        node.querySelectorAll(".mermaid svg").forEach(attachViewer);
                    }
                }
            }
        });

        _observer.observe(document.body, { childList: true, subtree: true });
    }

    function createViewer(svg) {
        var overlay = document.createElement("div");
        overlay.className = "mermaid-overlay";

        var container = document.createElement("div");
        container.className = "mermaid-container";

        var clone = svg.cloneNode(true);
        clone.style.width = "auto";
        clone.style.height = "auto";
        clone.style.maxWidth = "none";
        clone.style.maxHeight = "none";
        clone.style.transformOrigin = "center center";
        clone.style.cursor = "grab";

        var scale = 1, x = 0, y = 0;

        function update() {
            clone.style.transform = "translate(" + x + "px, " + y + "px) scale(" + scale + ")";
        }

        container.addEventListener("wheel", function (e) {
            e.preventDefault();
            scale += e.deltaY < 0 ? 0.1 : -0.1;
            scale = Math.min(Math.max(scale, 0.2), 8);
            update();
        }, { passive: false });

        var dragging = false, sx = 0, sy = 0;

        clone.addEventListener("mousedown", function (e) {
            dragging = true;
            sx = e.clientX - x;
            sy = e.clientY - y;
            clone.style.cursor = "grabbing";
        });

        window.addEventListener("mousemove", function (e) {
            if (!dragging) return;
            x = e.clientX - sx;
            y = e.clientY - sy;
            update();
        });

        window.addEventListener("mouseup", function () {
            dragging = false;
            clone.style.cursor = "grab";
        });

        container.appendChild(clone);
        overlay.appendChild(container);
        document.body.appendChild(overlay);

        function escHandler(e) {
            if (e.key === "Escape") close();
        }
        document.addEventListener("keydown", escHandler);

        overlay.addEventListener("click", function (e) {
            if (e.target === overlay) close();
        });

        function close() {
            overlay.remove();
            document.removeEventListener("keydown", escHandler);
        }
    }

    if (typeof document$ !== "undefined") {
        document$.subscribe(initMermaidViewer);
    } else {
        document.addEventListener("DOMContentLoaded", initMermaidViewer);
    }

})();
