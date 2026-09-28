/*
 * app.js — progressive enhancement for assets/frontend-template/.
 *
 * Three small behaviours, each independently guarded so removing one leaves the
 * page working. That is what makes this a template rather than a dependency:
 * there is no bundle, and a missing block costs a feature rather than the page.
 *
 * The theme choice is applied from localStorage in a try/catch, because
 * localStorage throws in a private window in some browsers and an uncaught
 * throw here would stop every other behaviour on the page from initialising.
 *
 * PROVENANCE
 *   Part of assets/frontend-template/ in this skill's assets. The three
 *   behaviours and their guards are this file's own.
 */

(function () {
  "use strict";

  /* --- Theme toggle ---------------------------------------------------------
     Follows the OS setting until the user chooses, then follows the choice.
     The class goes on <html> so tokens.css can override the media query. */

  var STORAGE_KEY = "template-theme";

  function readStoredTheme() {
    try {
      return window.localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      // Private browsing, disabled storage, or a file:// origin in some
      // browsers. Not a reason to fail; just fall back to the OS setting.
      return null;
    }
  }

  function storeTheme(theme) {
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      /* The choice still applies for this page view. */
    }
  }

  function prefersDark() {
    return (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    );
  }

  function applyTheme(theme) {
    var root = document.documentElement;
    if (theme === "light" || theme === "dark") {
      root.setAttribute("data-theme", theme);
    } else {
      root.removeAttribute("data-theme");
    }
    var toggle = document.querySelector(".theme-toggle");
    if (!toggle) return;
    var isDark = theme ? theme === "dark" : prefersDark();
    toggle.setAttribute("aria-pressed", String(isDark));
    var label = toggle.querySelector("[data-theme-label]");
    if (label) label.textContent = isDark ? "Light" : "Dark";
  }

  function initTheme() {
    // Applied before first paint of the content, so there is no flash of the
    // wrong scheme. Defer means this runs after parsing, which is early enough
    // for a static page and late enough that the DOM exists.
    applyTheme(readStoredTheme());

    var toggle = document.querySelector(".theme-toggle");
    if (!toggle) return;
    toggle.addEventListener("click", function () {
      var current = document.documentElement.getAttribute("data-theme");
      var next = current
        ? (current === "dark" ? "light" : "dark")
        : (prefersDark() ? "light" : "dark");
      applyTheme(next);
      storeTheme(next);
    });
  }

  /* --- Navigation disclosure -------------------------------------------------
     aria-expanded is the state. The CSS keys off it, and a screen reader
     announces it, so one attribute does both jobs. */

  function initNav() {
    var toggle = document.querySelector(".nav-toggle");
    if (!toggle) return;
    toggle.addEventListener("click", function () {
      var expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!expanded));
    });
  }

  /* --- Copy to clipboard ----------------------------------------------------
     navigator.clipboard needs a secure context, which a file:// page is not.
     The textarea fallback is what makes this work when the template is opened
     straight from disk, which is how most people will first look at it. */

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var field = document.createElement("textarea");
      field.value = text;
      field.setAttribute("readonly", "");
      field.style.position = "fixed";
      field.style.opacity = "0";
      document.body.appendChild(field);
      field.select();
      try {
        document.execCommand("copy") ? resolve() : reject(new Error("copy refused"));
      } catch (error) {
        reject(error);
      } finally {
        document.body.removeChild(field);
      }
    });
  }

  function initCopy() {
    var buttons = document.querySelectorAll("[data-copy-target]");
    Array.prototype.forEach.call(buttons, function (button) {
      button.addEventListener("click", function () {
        var target = document.getElementById(button.getAttribute("data-copy-target"));
        if (!target) return;
        var status = button.parentElement.querySelector(".status");
        copyText(target.textContent.trim()).then(
          function () {
            if (status) status.textContent = "Copied.";
          },
          function () {
            // Say what to do rather than failing silently. A copy button that
            // does nothing on an insecure origin is indistinguishable from a
            // broken one.
            if (status) {
              status.textContent = "Could not copy. Select the text and copy it manually.";
            }
          }
        );
      });
    });
  }

  function init() {
    initTheme();
    initNav();
    initCopy();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
}());
