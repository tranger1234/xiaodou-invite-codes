#!/usr/bin/env python3
"""Generate index.html (static snapshot) from data.json (getstate verbatim)."""
import json
import html
from datetime import datetime, timezone, timedelta

DATA = "data.json"
OUT = "index.html"

with open(DATA, encoding="utf-8") as f:
    state = json.load(f)

codes = state["codes"]  # already newest-first (id desc) as returned by getstate
assert len(codes) >= 1, len(codes)
shown = codes[:20]  # page shows only the latest 20

cst = timezone(timedelta(hours=8))
now = datetime.now(cst).strftime("%Y-%m-%d %H:%M")
found_fmt = lambda ms: datetime.fromtimestamp(ms / 1000, tz=cst).strftime("%Y-%m-%d %H:%M")


def source_text(c):
    platform = c["platform"]
    name = c["sourceName"]
    if name.startswith(platform + " · "):
        return name
    return platform + " · " + name


rows = []
for i, c in enumerate(shown):
    cls = ' class="new"' if i < 10 else ""
    badge = ' <span class="badge">最新</span>' if i == 0 else ""
    snippet = c.get("snippet") or ""
    note = f'<div class="note">{html.escape(snippet)}</div>' if snippet else ""
    rows.append(
        "<tr{cls}>"
        "<td>{seq}</td>"
        "<td><code>{code}</code>{badge}</td>"
        "<td>{src}{note}</td>"
        "<td>{found}</td>"
        '<td><a href="{url}" target="_blank" rel="noopener">查看原文</a></td>'
        '<td><button class="copy" data-code="{code}">复制</button></td>'
        "</tr>".format(
            cls=cls,
            seq=c["id"],
            code=html.escape(c["code"]),
            badge=badge,
            src=html.escape(source_text(c)),
            note=note,
            found=found_fmt(c["foundAt"]),
            url=html.escape(c["sourceUrl"], quote=True),
        )
    )

counts = {}
for c in codes:
    counts[c["platform"]] = counts.get(c["platform"], 0) + 1
stats = " · ".join(f"{p} {n}" for p, n in sorted(counts.items(), key=lambda kv: -kv[1]))

page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>小豆邀请码全网搜索</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;background:#f6f7f9;color:#1c1c1e}}
.wrap{{max-width:980px;margin:0 auto;padding:20px 16px 48px}}
h1{{font-size:22px;margin:6px 0 4px}}
.sub{{color:#666;font-size:14px;margin:0 0 4px}}
.notice{{background:#fff7e6;border:1px solid #f2d191;color:#8a6d1b;border-radius:10px;padding:10px 14px;font-size:14px;margin:12px 0}}
.stats{{color:#666;font-size:13px;margin:0 0 14px}}
.table-wrap{{overflow-x:auto;background:#fff;border:1px solid #e5e5ea;border-radius:12px}}
table{{border-collapse:collapse;width:100%;min-width:720px;font-size:14px}}
th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid #eee;vertical-align:top}}
thead th{{background:#f2f2f7;position:sticky;top:0;white-space:nowrap}}
tbody tr:last-child td{{border-bottom:none}}
tr.new{{background:#fff8e1}}
code{{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:700;font-size:15px;letter-spacing:.5px}}
.badge{{display:inline-block;background:#ff3b30;color:#fff;font-size:11px;border-radius:8px;padding:1px 6px;margin-left:6px;vertical-align:2px}}
.note{{color:#888;font-size:12px;margin-top:4px}}
a{{color:#0a6cff;text-decoration:none}}
button.copy{{border:1px solid #d0d0d5;background:#fff;border-radius:8px;padding:6px 12px;font-size:13px;cursor:pointer;white-space:nowrap}}
button.copy:active{{background:#f0f0f3}}
.foot{{color:#999;font-size:12px;margin-top:16px;line-height:1.7}}
</style>
</head>
<body>
<div class="wrap">
<h1>小豆邀请码全网搜索</h1>
<p class="sub">字节跳动 AI 助手「小豆」邀请码全网搜集（小红书 / Threads / 论坛）</p>
<div class="notice">这是数据快照，更新于 {now}（北京时间）。本页不会自动更新；实时每 20 秒更新的版本在 Muse 里。</div>
<p class="stats">库里共 {total} 条邀请码（{stats}），本页只展示最新的 20 条，按发现时间从新到旧排列，前 10 条为最新。</p>
<div class="table-wrap">
<table>
<thead><tr><th>序号</th><th>邀请码</th><th>来源</th><th>发现时间</th><th>原文链接</th><th>操作</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
</div>
<p class="foot">提示：邀请码多为一次性、48 小时内过期，先到先得；本页所列邀请码未逐一实测是否可用，部分在原文评论区已被反馈“不行”或“可能已被使用”，请以实际填写结果为准。</p>
</div>
<script>
document.querySelectorAll('button.copy').forEach(function(btn){{
  btn.addEventListener('click', function(){{
    var code = btn.getAttribute('data-code');
    function done(){{
      var old = btn.textContent;
      btn.textContent = '已复制 ✓';
      setTimeout(function(){{ btn.textContent = old; }}, 1500);
    }}
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(code).then(done).catch(function(){{ fallback(); }});
    }} else {{ fallback(); }}
    function fallback(){{
      var ta = document.createElement('textarea');
      ta.value = code;
      document.body.appendChild(ta);
      ta.select();
      try {{ document.execCommand('copy'); done(); }} catch(e) {{}}
      document.body.removeChild(ta);
    }}
  }});
}});
</script>
</body>
</html>
""".format(now=now, total=len(codes), stats=stats, rows="\n".join(rows))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(page)

print("wrote", OUT, "rows:", len(shown), "of", len(codes), "snapshot:", now)
