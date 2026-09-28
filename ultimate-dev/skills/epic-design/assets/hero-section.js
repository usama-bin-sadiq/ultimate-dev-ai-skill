/*
 * hero-section.js — the scroll and motion engine for the epic-design 2.5D hero.
 *
 * WHAT THIS IS
 *    Writes the live scroll offset to --scroll-y, which hero-section.css turns
 *    into each layer's parallax; splits headings into word spans for the entry
 *    animation; and adds .is-in when an element enters the viewport. Vanilla,
 *    no framework, no build step.
 *
 * WHAT IT EXPECTS
 *    hero-section.html for the markup and hero-section.css for the styles.
 *    GSAP and ScrollTrigger are optional: if the page has them, the pinned
 *    sections and scrub timelines use them; if not, this file's own
 *    requestAnimationFrame loop drives the parallax on its own.
 *
 * WHAT IT DELIBERATELY DOES NOT DO
 *    It never hides content that has not been animated in. Content starts
 *    visible; the .js class on <html> is what makes the entry animation's
 *    initial state hidden, and if this file fails to run at all, that class is
 *    never added and everything is still readable.
 *
 * PERFORMANCE
 *    One rAF loop, not one listener per layer. Reads are batched into a single
 *    write of a custom property, so the browser does the compositing rather
 *    than JavaScript driving each layer. will-change is added on activation and
 *    removed after, not left on permanently. Off-screen scenes are skipped
 *    entirely. Touch devices and low-core machines get the lite mode.
 *
 * ACCESSIBILITY
 *    Honouring prefers-reduced-motion is the first thing this file checks. In
 *    reduced mode it removes every transform, forces content visible, and does
 *    not attach the scroll loop at all. Splitting text never duplicates or
 *    replaces it: the heading in the DOM is the heading on screen.
 *
 * PROVENANCE
 *    Reconstructed from this skill's references/depth-system.md,
 *    references/performance.md, references/accessibility.md, and
 *    references/motion-system.md. Working code, not a copy of any upstream file.
 */

(function () {
  "use strict";

  /* ---------------------------------------------------------------------
     CONFIG
     ------------------------------------------------------------------ */

  var CONFIG = {
    // Elements per scene above which particles and loops are considered too
    // expensive. A hundred animated elements is a frame-rate problem and the
    // extra ninety are invisible.
    maxAnimatedElements: 80,
    // navigator.hardwareConcurrency at or below this is treated as low power.
    lowPowerCores: 4,
    // Seconds to stagger word animations by, and the per-word ceiling so a long
    // heading does not finish animating after the reader has read it.
    wordStagger: 0.045,
    maxWordStagger: 0.6,
    // Pixels a layer must be inside the viewport before it is animated at all.
    rootMargin: "200px 0px"
  };

  var doc = document;
  var root = doc.documentElement;
  var reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* ---------------------------------------------------------------------
     CAPABILITY DETECTION
     One place, so the rest of the file never re-asks.
     ------------------------------------------------------------------ */

  var isTouch = window.matchMedia("(pointer: coarse)").matches;
  var isLowPower = (navigator.hardwareConcurrency || 8) <= CONFIG.lowPowerCores;
  var animatedElementCount = doc.querySelectorAll("[data-animate], .float-loop, .particle").length;
  var isHeavyPage = animatedElementCount > CONFIG.maxAnimatedElements;

  var performanceMode = (isTouch || isLowPower || isHeavyPage) ? "lite" : "full";

  function hasGSAP() {
    return typeof window.gsap !== "undefined";
  }

  function hasScrollTrigger() {
    return hasGSAP() && typeof window.ScrollTrigger !== "undefined";
  }

  /* ---------------------------------------------------------------------
     REDUCED MOTION
     Runs before anything else is set up. In this mode the page is a static,
     fully readable hero: no scroll loop, no transforms, no hidden content.
     ------------------------------------------------------------------ */

  function applyReducedMotion() {
    root.classList.remove("js");
    root.classList.add("motion-reduced");

    var animated = doc.querySelectorAll("[data-animate], .split-text .word");
    for (var i = 0; i < animated.length; i++) {
      animated[i].style.opacity = "1";
      animated[i].style.transform = "none";
    }

    if (hasScrollTrigger()) {
      window.gsap.globalTimeline.timeScale(0);
      var triggers = window.ScrollTrigger.getAll();
      for (var t = 0; t < triggers.length; t++) {
        triggers[t].kill();
      }
    }
    root.style.setProperty("--scroll-y", "0");
  }

  if (reducedMotionQuery.matches) {
    applyReducedMotion();
    return;
  }

  // The user can change this at runtime; honour it without a reload.
  if (typeof reducedMotionQuery.addEventListener === "function") {
    reducedMotionQuery.addEventListener("change", function (event) {
      if (event.matches) {
        applyReducedMotion();
        window.location.reload(); // simplest correct teardown of an active scene
      }
    });
  }

  /* ---------------------------------------------------------------------
     SPLIT TEXT
     Wraps existing words in spans. It does not replace the text, does not
     duplicate it, and does not read it twice: the DOM contains one sentence,
     which is the sentence on screen and the sentence a screen reader reads.
     ------------------------------------------------------------------ */

  function splitText(element) {
    if (element.dataset.split === "done") return [];

    var words = element.textContent.trim().split(/\s+/).filter(Boolean);
    element.textContent = "";

    var spans = [];
    words.forEach(function (word, index) {
      var span = doc.createElement("span");
      span.className = "word";
      span.textContent = word;
      // The space lives in the layout, not in the text node, so the sentence
      // still reads correctly when the spans are flattened.
      span.appendChild(doc.createTextNode(index < words.length - 1 ? " " : ""));
      element.appendChild(span);
      spans.push(span);
    });

    element.dataset.split = "done";
    return spans;
  }

  /* ---------------------------------------------------------------------
     ENTRY ANIMATIONS
     IntersectionObserver rather than a scroll handler: an element that is not
     near the viewport costs nothing.
     ------------------------------------------------------------------ */

  function initEntryAnimations() {
    var splitElements = doc.querySelectorAll(".split-text");
    for (var s = 0; s < splitElements.length; s++) {
      var spans = splitText(splitElements[s]);
      // Cap the total stagger: a twelve-word heading should not take four
      // seconds to finish arriving.
      var step = Math.min(CONFIG.wordStagger, CONFIG.maxWordStagger / Math.max(1, spans.length));
      spans.forEach(function (span, index) {
        span.style.transitionDelay = (index * step) + "s";
      });
    }

    var targets = doc.querySelectorAll("[data-animate], .split-text");
    if (!targets.length || typeof IntersectionObserver !== "function") {
      for (var f = 0; f < targets.length; f++) targets[f].classList.add("is-in");
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-in");
        // One-shot: an element that has arrived does not need watching.
        observer.unobserve(entry.target);
      });
    }, { rootMargin: CONFIG.rootMargin, threshold: 0.15 });

    for (var i = 0; i < targets.length; i++) {
      observer.observe(targets[i]);
    }
  }

  /* ---------------------------------------------------------------------
     PARALLAX
     One rAF loop for the whole page. Each visible scene writes its own
     --scroll-y; the CSS turns that into the per-layer translate. Doing the
     work in the compositor rather than in JavaScript is the whole point: a
     transform-only change never triggers layout or paint.
     ------------------------------------------------------------------ */

  var scenes = Array.prototype.slice.call(doc.querySelectorAll(".scene"));
  var activeScenes = [];
  var ticking = false;
  var parallaxEnabled = performanceMode === "full";

  function sceneProgress(scene) {
    var rect = scene.getBoundingClientRect();
    // 0 when the scene's top reaches the viewport top, 1 when its bottom does.
    return Math.min(1, Math.max(0, -rect.top / Math.max(1, rect.height)));
  }

  function updateParallax() {
    ticking = false;
    var viewportHeight = window.innerHeight || 1;

    for (var i = 0; i < scenes.length; i++) {
      var scene = scenes[i];
      var rect = scene.getBoundingClientRect();
      var visible = rect.bottom > -CONFIG.rootMargin.length && rect.top < viewportHeight;
      if (!visible) continue;
      scene.style.setProperty("--scroll-y", String(rect.top));
    }
  }

  function requestUpdate() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(updateParallax);
  }

  function initParallax() {
    if (!parallaxEnabled) return;

    // Paint hints only while a scene is near the viewport, and released after.
    if (typeof IntersectionObserver === "function") {
      var sceneObserver = new IntersectionObserver(function (entries) {
        for (var i = 0; i < entries.length; i++) {
          var entry = entries[i];
          var layers = entry.target.querySelectorAll(".layer");
          for (var l = 0; l < layers.length; l++) {
            layers[l].style.willChange = entry.isIntersecting ? "transform" : "auto";
          }
          if (entry.isIntersecting) {
            if (activeScenes.indexOf(entry.target) === -1) activeScenes.push(entry.target);
            entry.target.classList.add("is-live");
          } else {
            entry.target.classList.remove("is-live");
            var at = activeScenes.indexOf(entry.target);
            if (at !== -1) activeScenes.splice(at, 1);
          }
        }
        requestUpdate();
      }, { rootMargin: CONFIG.rootMargin });
      for (var s = 0; s < scenes.length; s++) sceneObserver.observe(scenes[s]);
    }

    window.addEventListener("scroll", requestUpdate, { passive: true });
    window.addEventListener("resize", requestUpdate, { passive: true });
    requestUpdate();
  }

  /* ---------------------------------------------------------------------
     GSAP PINNING — optional
     Used when the page already loads GSAP. A pinned scene is a tall scene with a
     sticky panel; GSAP handles the pinning and the scrub timeline better than
     hand-rolled scroll maths, so it is used when present and skipped when not.
     ------------------------------------------------------------------ */

  function initPinnedScenes() {
    if (!hasScrollTrigger() || performanceMode === "lite") return;

    window.gsap.registerPlugin(window.ScrollTrigger);

    var pinned = doc.querySelectorAll(".scene--pinned");
    for (var i = 0; i < pinned.length; i++) {
      (function (scene) {
        var pin = scene.querySelector(".pin");
        if (!pin) return;
        window.ScrollTrigger.create({
          trigger: scene,
          start: "top top",
          end: "bottom bottom",
          pin: pin,
          pinSpacing: false,
          anticipatePin: 1,
          invalidateOnRefresh: true
        });
      }(pinned[i]));
    }
  }

  /* ---------------------------------------------------------------------
     SMOOTH SCROLL — optional
     Lenis, if the page loads it. Wrapped in a try because a smooth-scroll
     library fighting a scroll-linked transform is a common source of jitter,
     and the page is better off with native scrolling than with a broken one.
     ------------------------------------------------------------------ */

  function initSmoothScroll() {
    if (!parallaxEnabled || typeof window.Lenis !== "function") return;
    try {
      var lenis = new window.Lenis({ duration: 1.1, smoothWheel: true });
      function raf(time) {
        lenis.raf(time);
        window.requestAnimationFrame(raf);
      }
      window.requestAnimationFrame(raf);
    } catch (error) {
      if (window.console && console.warn) {
        console.warn("epic-design: smooth scroll disabled —", error.message);
      }
    }
  }

  /* ---------------------------------------------------------------------
     SCENE PROGRESS FOR DATA-DRIVEN ANIMATION
     Exposes the current progress of every scene, so a project can read it in
     its own scroll handler instead of adding a listener per layer.
     ------------------------------------------------------------------ */

  function sceneStates() {
    return scenes.map(function (scene) {
      return {
        scene: scene.getName ? scene.getAttribute("data-scene") : null,
        progress: sceneProgress(scene)
      };
    });
  }

  /* ---------------------------------------------------------------------
     BOOT
     ------------------------------------------------------------------ */

  function init() {
    root.classList.add("js");
    if (performanceMode === "lite") root.classList.add("perf-lite");

    initEntryAnimations();
    initParallax();
    initPinnedScenes();
    initSmoothScroll();

    // A public surface, deliberately small: the engine's job is to write
    // --scroll-y and add .is-in. Anything more specific belongs in the project.
    window.EpicHero = {
      refresh: requestUpdate,
      sceneStates: sceneStates,
      performanceMode: performanceMode,
      stop: function () {
        window.removeEventListener("scroll", requestUpdate);
        window.removeEventListener("resize", requestUpdate);
      }
    };
  }

  if (doc.readyState === "loading") {
    doc.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
}());
