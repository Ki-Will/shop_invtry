/* Shop Inventory — plain JavaScript, no libraries. */
(function () {
  "use strict";

  /* 1) Auto-dismiss flash messages (click to dismiss early). */
  document.querySelectorAll(".messages .msg").forEach(function (el) {
    window.setTimeout(function () {
      el.classList.add("gone");
      window.setTimeout(function () { el.remove(); }, 500);
    }, 4000);
    el.addEventListener("click", function () { el.remove(); });
  });

  /* 2) Confirm destructive actions via data-confirm. */
  document.querySelectorAll("[data-confirm]").forEach(function (el) {
    el.addEventListener("click", function (event) {
      if (!window.confirm(el.getAttribute("data-confirm"))) {
        event.preventDefault();
      }
    });
  });

  /* 3) Client-side search over the products table. */
  var search = document.getElementById("product-search");
  var table = document.getElementById("product-table");
  if (search && table && table.tBodies.length) {
    var rows = Array.prototype.slice.call(table.tBodies[0].rows);
    var status = document.getElementById("search-status");

    var applyFilter = function () {
      var query = search.value.trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (row) {
        var haystack = (row.getAttribute("data-search") || row.textContent).toLowerCase();
        var matches = !query || haystack.indexOf(query) !== -1;
        row.hidden = !matches;
        if (matches) { shown += 1; }
      });
      if (status) {
        status.hidden = !query;
        if (query) {
          status.textContent =
            shown + " of " + rows.length + " products match “" + search.value.trim() + "”";
        }
      }
    };

    search.addEventListener("input", applyFilter);
    applyFilter();
  }

  /* 4) Live value preview on the product form — mirrors
   *    valcalc.round_money(quantity * unit_price) on the server. */
  var qty = document.getElementById("id_quantity");
  var price = document.getElementById("id_unit_price");
  var total = document.getElementById("live-total");
  var hint = document.getElementById("preview-hint");

  if (qty && price && total) {
    var updatePreview = function () {
      var q = parseFloat(String(qty.value).replace(/,/g, ""));
      var p = parseFloat(String(price.value).replace(/,/g, ""));
      if (isNaN(q) || isNaN(p)) {
        total.textContent = "—";
        if (hint) { hint.textContent = "Type a quantity and a price to see it update."; }
        return;
      }
      var value = Math.round(q * p * 100) / 100;
      total.textContent = "$" + value.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
      if (hint) {
        hint.textContent = q.toLocaleString() + " × " + p.toLocaleString(undefined, {
          minimumFractionDigits: 2
        }) + " — rounded to 2 decimals like valcalc.round_money().";
      }
    };
    qty.addEventListener("input", updatePreview);
    price.addEventListener("input", updatePreview);
    updatePreview();
  }
})();
