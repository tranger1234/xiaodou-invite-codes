#!/usr/bin/env python3
"""Generate index.html (shareable live-ish page) from data.json.

The page embeds the current 20 codes for first paint, then polls
data.json every 20 seconds and re-renders when the data changes.
Data itself is refreshed by the sync job (~every 10 minutes) which
rewrites data.json from the live library and pushes it here.
"""
import json
import html
from datetime import datetime, timezone, timedelta

DATA = "data.json"
OUT = "index.html"
POLL_SEC = 20

with open(DATA, encoding="utf-8") as f:
    state = json.load(f)

codes = state["codes"]  # already newest-first (id desc) as returned by getstate
assert len(codes) >= 1, len(codes)
shown = codes[:20]  # page shows only the latest 20

cst = timezone(timedelta(hours=8))
now = datetime.now(cst)
now_s = now.strftime("%Y-%m-%d %H:%M")
synced_ms = state.get("syncedAt")
if synced_ms:
    sync_s = datetime.fromtimestamp(synced_ms / 1000, tz=cst).strftime("%Y-%m-%d %H:%M")
    sync_ms_js = synced_ms
else:
    sync_s = now_s
    sync_ms_js = int(now.timestamp() * 1000)
found_fmt = lambda ms: datetime.fromtimestamp(ms / 1000, tz=cst).strftime("%Y-%m-%d %H:%M")


def source_text(c):
    platform = c["platform"]
    name = c["sourceName"]
    if name.startswith(platform + " · "):
        return name
    return platform + " · " + name


def row_html(i, c):
    cls = ' class="new"' if i < 10 else ""
    badge = ' <span class="badge">最新</span>' if i == 0 else ""
    snippet = c.get("snippet") or ""
    note = f'<div class="note">{html.escape(snippet)}</div>' if snippet else ""
    return (
        f'<tr{cls} data-platform="{html.escape(c["platform"])}">'
        f"<td>{i + 1}</td>"
        f'<td><code class="copyable" data-code="{html.escape(c["code"])}" title="点击复制">{html.escape(c["code"])}</code>{badge}</td>'
        f"<td>{html.escape(source_text(c))}{note}</td>"
        f"<td>{found_fmt(c['foundAt'])}</td>"
        f'<td><a href="{html.escape(c["sourceUrl"], quote=True)}" target="_blank" rel="noopener">查看原文</a></td>'
        "</tr>"
    )


rows = "\n".join(row_html(i, c) for i, c in enumerate(shown))

counts = {}
for c in codes:
    counts[c["platform"]] = counts.get(c["platform"], 0) + 1
stats = " · ".join(f"{p} {n}" for p, n in sorted(counts.items(), key=lambda kv: -kv[1]))
codes_json = json.dumps(shown, ensure_ascii=False)

page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>小豆邀请码全网搜索</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f6f7f9;color:#1c1c1e}
.wrap{max-width:980px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:22px;margin:6px 0 4px}
.sub{color:#666;font-size:14px;margin:0 0 4px}
.notice{background:#fff7e6;border:1px solid #f2d191;color:#8a6d1b;border-radius:10px;padding:10px 14px;font-size:14px;margin:12px 0}
.status{display:flex;justify-content:space-between;align-items:baseline;gap:12px;color:#666;font-size:13px;margin:0 0 6px}
.status b{color:#1c1c1e}
.progress{height:6px;background:#e5e5ea;border-radius:3px;overflow:hidden;margin:0 0 12px}
.progress i{display:block;height:100%;width:100%;background:#34c759;border-radius:3px;transition:width 1s linear}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 14px}
.fbtn{border:1px solid #d0d0d5;background:#fff;border-radius:999px;padding:6px 14px;font-size:13px;cursor:pointer;color:#1c1c1e}
.fbtn.active{background:#1c1c1e;color:#fff;border-color:#1c1c1e}
.stats{color:#666;font-size:13px;margin:0 0 14px}
.table-wrap{overflow-x:auto;background:#fff;border:1px solid #e5e5ea;border-radius:12px}
table{border-collapse:collapse;width:100%;min-width:720px;font-size:14px}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #eee;vertical-align:top}
thead th{background:#f2f2f7;position:sticky;top:0;white-space:nowrap}
tbody tr:last-child td{border-bottom:none}
tr.new{background:#fff8e1}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:700;font-size:15px;letter-spacing:.5px;cursor:pointer;padding:2px 4px;border-radius:6px}
code.copyable:hover{background:#e8f0fe}
code.copied{background:#d9f2e3}
.badge{display:inline-block;background:#ff3b30;color:#fff;font-size:11px;border-radius:8px;padding:1px 6px;margin-left:6px;vertical-align:2px}
.note{color:#888;font-size:12px;margin-top:4px}
a{color:#0a6cff;text-decoration:none}
.foot{color:#999;font-size:12px;margin-top:16px;line-height:1.7}
.empty{padding:28px 12px;text-align:center;color:#999}
</style>
</head>
<body>
<div class="wrap">
<h1>小豆邀请码全网搜索</h1>
<p class="sub">字节跳动 AI 助手「小豆」邀请码全网搜集（小红书 / Threads / 论坛）</p>
<div class="notice">本页每 20 秒自动检查更新；数据由实时版每 10 分钟同步一次，最新同步于 __SYNC_TIME__（北京时间）。</div>
<p class="status"><span>最后同步 <b id="syncTime">__SYNC_TIME__</b></span><span id="countdownText">下次检查 20 秒</span></p>
<div class="progress"><i id="progressBar"></i></div>
<div class="filters" id="filters"></div>
<p class="stats" id="statsLine">库里共 __TOTAL__ 条邀请码（__STATS__），按发现时间从新到旧排列，前 10 条为最新；点击邀请码即可复制。</p>
<div class="table-wrap">
<table>
<thead><tr><th>序号</th><th>邀请码</th><th>来源</th><th>发现时间</th><th>原文链接</th></tr></thead>
<tbody id="tbody">
__ROWS__
</tbody>
</table>
</div>
<p class="foot">提示：邀请码多为一次性、48 小时内过期，先到先得；本页所列邀请码未逐一实测是否可用，部分在原文评论区已被反馈“不行”或“可能已被使用”，请以实际填写结果为准。</p>
</div>
<script>
var POLL_SEC = 20;
var codes = __CODES_JSON__;
var syncedMs = __SYNCED_MS__;
var currentFilter = '全部';
var countdown = POLL_SEC;

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function pad(n){ return (n < 10 ? '0' : '') + n; }
function fmt(ms){ var d = new Date(ms); return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()); }
function srcText(c){ var name = c.sourceName; if (name.indexOf(c.platform + ' · ') === 0) return name; return c.platform + ' · ' + name; }
function rowHtml(i, c){
  var cls = i < 10 ? ' class="new"' : '';
  var badge = i === 0 ? ' <span class="badge">最新</span>' : '';
  var note = c.snippet ? '<div class="note">' + esc(c.snippet) + '</div>' : '';
  return '<tr' + cls + ' data-platform="' + esc(c.platform) + '">'
    + '<td>' + (i + 1) + '</td>'
    + '<td><code class="copyable" data-code="' + esc(c.code) + '" title="点击复制">' + esc(c.code) + '</code>' + badge + '</td>'
    + '<td>' + esc(srcText(c)) + note + '</td>'
    + '<td>' + fmt(c.foundAt) + '</td>'
    + '<td><a href="' + esc(c.sourceUrl) + '" target="_blank" rel="noopener">查看原文</a></td>'
    + '</tr>';
}
function visibleCodes(){ return currentFilter === '全部' ? codes : codes.filter(function(c){ return c.platform === currentFilter; }); }
function render(){
  var list = visibleCodes();
  var tbody = document.getElementById('tbody');
  if (!list.length) {
    tbody.innerHTML = '<tr><td colspan="5"><div class="empty">该来源暂无邀请码</div></td></tr>';
  } else {
    tbody.innerHTML = list.map(function(c, i){ return rowHtml(i, c); }).join('\\n');
  }
  var counts = {};
  codes.forEach(function(c){ counts[c.platform] = (counts[c.platform] || 0) + 1; });
  var parts = Object.keys(counts).sort(function(a, b){ return counts[b] - counts[a]; }).map(function(p){ return p + ' ' + counts[p]; });
  document.getElementById('statsLine').textContent = '库里共 ' + codes.length + ' 条邀请码（' + parts.join(' · ') + '），按发现时间从新到旧排列，前 10 条为最新；点击邀请码即可复制。';
  var filters = document.getElementById('filters');
  var html = '<button class="fbtn' + (currentFilter === '全部' ? ' active' : '') + '" data-filter="全部">全部来源 (' + codes.length + ')</button>';
  Object.keys(counts).forEach(function(p){
    html += '<button class="fbtn' + (currentFilter === p ? ' active' : '') + '" data-filter="' + esc(p) + '">' + esc(p) + ' (' + counts[p] + ')</button>';
  });
  filters.innerHTML = html;
  document.getElementById('syncTime').textContent = fmt(syncedMs);
}
document.getElementById('filters').addEventListener('click', function(e){
  var btn = e.target.closest('button.fbtn');
  if (!btn) return;
  currentFilter = btn.getAttribute('data-filter');
  render();
});
document.getElementById('tbody').addEventListener('click', function(e){
  var el = e.target.closest('code.copyable');
  if (!el) return;
  var code = el.getAttribute('data-code');
  var orig = el.textContent;
  function done(){
    el.textContent = '已复制 ✓';
    el.classList.add('copied');
    setTimeout(function(){ el.textContent = orig; el.classList.remove('copied'); }, 1500);
  }
  function fallback(){
    var ta = document.createElement('textarea');
    ta.value = code;
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); done(); } catch(err) {}
    document.body.removeChild(ta);
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(code).then(done).catch(function(){ fallback(); });
  } else { fallback(); }
});
function tick(){
  var bar = document.getElementById('progressBar');
  var text = document.getElementById('countdownText');
  bar.style.width = (countdown / POLL_SEC * 100) + '%';
  text.textContent = '下次检查 ' + countdown + ' 秒';
  countdown -= 1;
  if (countdown < 0) {
    countdown = POLL_SEC;
    text.textContent = '正在检查更新…';
    fetch('data.json?v=' + Date.now(), {cache: 'no-store'}).then(function(r){ return r.json(); }).then(function(data){
      if (data && data.codes && JSON.stringify(data.codes) !== JSON.stringify(codes)) {
        codes = data.codes.slice(0, 20);
        if (data.syncedAt) syncedMs = data.syncedAt;
        render();
      }
    }).catch(function(){});
  }
}
render();
setInterval(tick, 1000);
</script>
</body>
</html>
"""

page = (
    page.replace("__ROWS__", rows)
    .replace("__CODES_JSON__", codes_json)
    .replace("__SYNCED_MS__", str(sync_ms_js))
    .replace("__SYNC_TIME__", sync_s)
    .replace("__TOTAL__", str(len(codes)))
    .replace("__STATS__", stats)
)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(page)

print("wrote", OUT, "rows:", len(shown), "of", len(codes), "snapshot:", now_s, "synced:", sync_s)
