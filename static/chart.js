// small chart-less plot using inline SVG. keeps the deps tiny.
// renders a moving average bar chart for the 3 windows.

(function () {
  function color(score) {
    if (score >= 0.05) return "#5cb85c";
    if (score <= -0.05) return "#d9534f";
    return "#aaa";
  }

  function pillClass(label) {
    return label;
  }

  function renderTweets(items) {
    var html = "";
    if (!items.length) {
      html = '<p class="meta">No tweets yet. The stream worker may still be starting up.</p>';
    } else {
      items.slice().reverse().forEach(function (t) {
        html +=
          '<div class="tweet">' +
            '<span class="pill ' + pillClass(t.label) + '">' + t.label + '</span> ' +
            '<strong>@' + t.user + '</strong> ' +
            '<span class="meta">[' + t.score.toFixed(2) + ']</span>' +
            '<div>' + escapeHtml(t.text) + '</div>' +
          '</div>';
      });
    }
    document.getElementById("tweets").innerHTML = html;
  }

  function renderSummary(data) {
    var w = data.windows || [];
    var maxBarWidth = 280;
    var html = '<table style="border-collapse:collapse;">';
    html += '<tr><th style="text-align:left;padding-right:1em;">window</th><th style="text-align:left;">count</th><th style="text-align:left;">avg</th><th></th></tr>';
    w.forEach(function (row) {
      var label = row.window_seconds < 120 ? row.window_seconds + "s"
                : row.window_seconds < 3600 ? Math.round(row.window_seconds / 60) + "m"
                : Math.round(row.window_seconds / 3600) + "h";
      var width = Math.abs(row.avg_score) * maxBarWidth;
      var fill = color(row.avg_score);
      html += '<tr>' +
        '<td style="padding:4px 1em 4px 0;">' + label + '</td>' +
        '<td style="padding:4px 1em 4px 0;">' + row.count + '</td>' +
        '<td style="padding:4px 1em 4px 0;">' + row.avg_score.toFixed(3) + '</td>' +
        '<td style="padding:4px;"><div style="display:inline-block;height:14px;width:' + width + 'px;background:' + fill + ';"></div></td>' +
      '</tr>';
    });
    html += '</table>';
    html += '<p class="meta">total in buffer: ' + (data.total_in_buffer || 0) + '</p>';
    document.getElementById("summary").innerHTML = html;
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function tick() {
    fetch("/api/tweets?n=30")
      .then(function (r) { return r.json(); })
      .then(function (d) { renderTweets(d.tweets || []); })
      .catch(function (e) { console.warn("tweets fetch failed", e); });
    fetch("/api/sentiment-summary")
      .then(function (r) { return r.json(); })
      .then(function (d) { renderSummary(d); })
      .catch(function (e) { console.warn("summary fetch failed", e); });
  }

  // refresh interval can be overridden via ?refresh=10 in seconds
  var params = new URLSearchParams(window.location.search);
  var refreshSec = parseInt(params.get("refresh") || "5", 10);
  tick();
  setInterval(tick, Math.max(1, refreshSec) * 1000);
})();
