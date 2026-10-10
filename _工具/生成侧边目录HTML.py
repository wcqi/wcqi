# -*- coding: utf-8 -*-
"""
把 Markdown 学习笔记转换成带左侧可跳转目录的 HTML 阅读版。
- 左侧固定侧边栏目录(可折叠 / 搜索 / 滚动高亮 / 自动展开)
- 右侧正文,标题带锚点,平滑滚动
- 支持浅色 / 深色主题切换,完全离线可用

用法:
    python 生成侧边目录HTML.py <输入.md> [输出.html]
不传输出路径时,默认在 md 同目录生成同名 .html
"""
import re
import sys
import pathlib
import markdown
from markdown.extensions.toc import TocExtension

TOC_MAX_LEVEL = 3          # 侧边栏最多显示到三级标题

if len(sys.argv) < 2:
    sys.exit("用法: python 生成侧边目录HTML.py <输入.md> [输出.html]")

SRC = pathlib.Path(sys.argv[1]).expanduser().resolve()
if not SRC.is_file():
    sys.exit("找不到文件: %s" % SRC)
DST = (
    pathlib.Path(sys.argv[2]).expanduser().resolve()
    if len(sys.argv) > 2
    else SRC.with_suffix(".html")
)


# ---------------------------------------------------------------- slugify
# 中文标题默认 slugify 会生成中文 id,这里统一改成 sec-N,保证锚点稳定可用
class _Slug:
    def __init__(self):
        self.n = 0

    def __call__(self, value, separator="-"):
        self.n += 1
        return "sec-%d" % self.n


slug = _Slug()

md = markdown.Markdown(
    extensions=[
        "tables",
        "fenced_code",
        "attr_list",
        "md_in_html",
        "sane_lists",
        "pymdownx.superfences",
        "pymdownx.details",
        TocExtension(slugify=slug, toc_depth="1-6", permalink=False),
    ],
    extension_configs={
        "pymdownx.superfences": {"custom_fences": []},
    },
)

src_text = SRC.read_text(encoding="utf-8")

# 文档标题取正文中第一个一级标题
_m = re.search(r"^#\s+(.+?)\s*$", src_text, re.M)
DOC_TITLE = _m.group(1).strip() if _m else SRC.stem

content_html = md.convert(src_text)
tokens = md.toc_tokens

# ---------------------------------------------------------------- 构建目录树
def collect_roots(tokens):
    """主标题作为文档名,把它下面的内容提升为顶层。"""
    roots = []
    for i, tok in enumerate(tokens):
        if i == 0 and tok["level"] == 1:
            roots.extend(tok.get("children", []))
        else:
            roots.append(tok)
    # 正文里若有"目录 / 目录速览 / 目录索引"之类的章节,侧边栏不再重复列出
    roots = [
        t for t in roots
        if not re.search(r"目录\s*(速览|索引|一览)?\s*$", t["name"].strip())
    ]
    return roots


def render_toc(nodes, level=1):
    if not nodes:
        return ""
    out = ['<ul class="toc-sub">']
    for node in nodes:
        if node["level"] > TOC_MAX_LEVEL:
            continue
        if node["name"].strip().startswith("结语"):
            continue
        kids = [c for c in node.get("children", []) if c["level"] <= TOC_MAX_LEVEL]
        has_children = bool(kids)
        cls = "toc-item" + (" has-children" if has_children else "")
        out.append(
            '<li class="%s" data-id="%s" data-level="%d">' % (cls, node["id"], node["level"])
        )
        if has_children:
            out.append(
                '<div class="toc-row"><button class="toc-toggle" type="button" '
                'aria-label="展开或折叠">'
                '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5" '
                'fill="none" stroke="currentColor" stroke-width="1.8" '
                'stroke-linecap="round" stroke-linejoin="round"/></svg>'
                '</button><a class="toc-link" href="#%s">%s</a></div>'
                % (node["id"], node["name"])
            )
            out.append(render_toc(kids, level + 1))
        else:
            out.append(
                '<div class="toc-row"><span class="toc-spacer"></span>'
                '<a class="toc-link" href="#%s">%s</a></div>' % (node["id"], node["name"])
            )
        out.append("</li>")
    out.append("</ul>")
    return "".join(out)


toc_html = render_toc(collect_roots(tokens))

# ---------------------------------------------------------------- HTML 模板
TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__DOC_TITLE__</title>
<style>
:root{
  --bg:#ffffff; --bg-alt:#f6f8fa; --side-bg:#f6f8fa; --border:#d0d7de;
  --text:#1f2328; --muted:#656d76; --accent:#0969da; --accent-soft:#ddf4ff;
  --code-bg:#f6f8fa; --code-border:#d0d7de; --mark:#fff8c5;
  --shadow:0 1px 3px rgba(0,0,0,.08);
  --topbar-h:56px; --side-w:330px;
  --syn-c:#6e7781; --syn-k:#cf222e; --syn-s:#0a3069; --syn-m:#0550ae;
  --syn-o:#cf222e; --syn-f:#8250df; --syn-nc:#953800; --syn-nt:#116329;
  --syn-nv:#953800; --syn-nb:#953800; --syn-err:#cb2431; --syn-gh:#0550ae;
  --syn-go:#0550ae; --syn-gd:#82071e; --syn-gi:#116329;
}
html.dark{
  --bg:#0d1117; --bg-alt:#161b22; --side-bg:#010409; --border:#30363d;
  --text:#e6edf3; --muted:#8b949e; --accent:#58a6ff; --accent-soft:#1f6feb33;
  --code-bg:#161b22; --code-border:#30363d; --mark:#4b3f04;
  --shadow:0 1px 3px rgba(0,0,0,.5);
  --syn-c:#8b949e; --syn-k:#ff7b72; --syn-s:#a5d6ff; --syn-m:#79c0ff;
  --syn-o:#ff7b72; --syn-f:#d2a8ff; --syn-nc:#ffa657; --syn-nt:#7ee787;
  --syn-nv:#ffa657; --syn-nb:#ffa657; --syn-err:#ff7b72; --syn-gh:#79c0ff;
  --syn-go:#79c0ff; --syn-gd:#ffa198; --syn-gi:#7ee787;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--bg); color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
    "Hiragino Sans GB","Microsoft YaHei",sans-serif;
  font-size:15px; line-height:1.75; -webkit-font-smoothing:antialiased;
}

/* ---------- 顶栏 ---------- */
.topbar{
  position:fixed; inset:0 0 auto 0; height:var(--topbar-h); z-index:50;
  display:flex; align-items:center; gap:12px; padding:0 16px;
  background:var(--bg); border-bottom:1px solid var(--border);
}
.icon-btn{
  display:inline-flex; align-items:center; justify-content:center;
  width:34px; height:34px; border:1px solid var(--border); border-radius:6px;
  background:var(--bg-alt); color:var(--text); cursor:pointer; flex:none;
  transition:background .15s;
}
.icon-btn:hover{background:var(--accent-soft); border-color:var(--accent)}
.icon-btn svg{width:18px; height:18px}
.topbar-title{
  font-size:15px; font-weight:600; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis;
}
.topbar-spacer{flex:1}
.progress{
  position:absolute; left:0; bottom:-1px; height:2px; width:0;
  background:var(--accent); transition:width .1s linear;
}

/* ---------- 侧边栏 ---------- */
.sidebar{
  position:fixed; top:var(--topbar-h); left:0; bottom:0; width:var(--side-w);
  z-index:40; display:flex; flex-direction:column;
  background:var(--side-bg); border-right:1px solid var(--border);
  transition:transform .25s ease;
}
.sidebar.hidden{transform:translateX(-100%)}
.side-head{padding:12px 14px; border-bottom:1px solid var(--border); flex:none}
.search-wrap{position:relative}
.search-wrap svg{
  position:absolute; left:9px; top:50%; transform:translateY(-50%);
  width:15px; height:15px; color:var(--muted); pointer-events:none;
}
#search{
  width:100%; padding:7px 28px 7px 30px; font-size:13px;
  border:1px solid var(--border); border-radius:6px;
  background:var(--bg); color:var(--text); outline:none;
}
#search:focus{border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-soft)}
#clearSearch{
  position:absolute; right:6px; top:50%; transform:translateY(-50%);
  display:none; border:0; background:transparent; color:var(--muted);
  cursor:pointer; font-size:16px; line-height:1; padding:2px 4px;
}
#clearSearch.show{display:block}
.side-meta{
  display:flex; justify-content:space-between; align-items:center;
  margin-top:8px; font-size:11.5px; color:var(--muted);
}
.side-meta button{
  border:0; background:transparent; color:var(--accent);
  cursor:pointer; font-size:11.5px; padding:0;
}
.side-body{flex:1; overflow-y:auto; overscroll-behavior:contain; padding:8px 8px 40px}
.side-body::-webkit-scrollbar{width:8px}
.side-body::-webkit-scrollbar-thumb{background:var(--border); border-radius:4px}
.side-body::-webkit-scrollbar-thumb:hover{background:var(--muted)}

.toc-sub{list-style:none; margin:0; padding:0}
.toc-sub .toc-sub{padding-left:14px; display:none}
.toc-item.open > .toc-sub{display:block}
.toc-row{display:flex; align-items:flex-start; gap:2px; border-radius:5px}
.toc-row:hover{background:var(--accent-soft)}
.toc-link{
  flex:1; display:block; padding:5px 8px 5px 2px; font-size:13.5px;
  color:var(--text); text-decoration:none; line-height:1.5;
  overflow-wrap:anywhere;
}
.toc-item[data-level="1"] > .toc-row > .toc-link{font-weight:600; font-size:13.5px}
.toc-item[data-level="2"] > .toc-row > .toc-link{font-size:13px; color:var(--text)}
.toc-item[data-level="3"] > .toc-row > .toc-link{font-size:12.5px; color:var(--muted)}
.toc-row:hover .toc-link{color:var(--accent)}
.toc-link.active{color:var(--accent); font-weight:600; background:var(--accent-soft); border-radius:4px}
.toc-link mark{background:var(--mark); color:inherit; padding:0 1px; border-radius:2px}
.toc-toggle,.toc-spacer{
  flex:none; width:18px; height:26px; display:flex; align-items:center;
  justify-content:center;
}
.toc-toggle{
  border:0; background:transparent; color:var(--muted); cursor:pointer; padding:0;
}
.toc-toggle svg{width:11px; height:11px; transition:transform .18s}
.toc-item.open > .toc-row > .toc-toggle svg{transform:rotate(90deg)}
.toc-item.filtered{display:none}
.no-result{padding:16px 10px; font-size:13px; color:var(--muted); display:none}

/* ---------- 内容区 ---------- */
.main{
  margin-left:var(--side-w); padding:calc(var(--topbar-h) + 28px) 24px 120px;
  transition:margin-left .25s ease;
}
body.side-collapsed .main{margin-left:0}
.content{max-width:960px; margin:0 auto}
.content h1,.content h2,.content h3,.content h4{
  scroll-margin-top:calc(var(--topbar-h) + 16px); line-height:1.4;
}
.content h1{
  font-size:26px; margin:44px 0 18px; padding-bottom:10px;
  border-bottom:2px solid var(--accent);
}
.content h1:first-child{margin-top:0}
.content h2{
  font-size:20px; margin:34px 0 14px; padding-bottom:7px;
  border-bottom:1px solid var(--border);
}
.content h3{font-size:17px; margin:26px 0 10px}
.content h4{font-size:15px; margin:20px 0 8px; color:var(--accent)}
.content p{margin:12px 0}
.content a{color:var(--accent); text-decoration:none}
.content a:hover{text-decoration:underline}
.content ul,.content ol{padding-left:26px; margin:12px 0}
.content li{margin:5px 0}
.content blockquote{
  margin:16px 0; padding:2px 16px; border-left:4px solid var(--accent);
  background:var(--bg-alt); color:var(--muted); border-radius:0 4px 4px 0;
}
.content hr{border:0; border-top:1px solid var(--border); margin:36px 0}
.content table{
  border-collapse:collapse; width:100%; margin:18px 0; font-size:13.5px;
  display:block; overflow-x:auto;
}
.content th,.content td{
  border:1px solid var(--border); padding:7px 12px; text-align:left;
}
.content th{background:var(--bg-alt); font-weight:600}
.content tr:nth-child(even) td{background:var(--bg-alt)}
.content code{
  background:var(--code-bg); padding:2px 6px; border-radius:4px;
  font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
  font-size:13px;
}
.content pre{
  background:var(--code-bg); border:1px solid var(--code-border);
  border-radius:8px; padding:14px 16px; overflow-x:auto; margin:16px 0;
  line-height:1.6;
}
.content pre code{background:none; padding:0; font-size:12.8px; white-space:pre}
.content img{max-width:100%}

/* Pygments 语法着色 */
.highlight .c{color:var(--syn-c); font-style:italic}
.highlight .k,.highlight .kn,.highlight .kd,.highlight .kt{color:var(--syn-k)}
.highlight .s,.highlight .s1,.highlight .s2,.highlight .sb,
.highlight .sc,.highlight .sd,.highlight .se,.highlight .sh,
.highlight .si,.highlight .sx,.highlight .ss,.highlight .sr{color:var(--syn-s)}
.highlight .m,.highlight .mi,.highlight .mf,.highlight .mh,
.highlight .mo,.highlight .il{color:var(--syn-m)}
.highlight .o,.highlight .ow{color:var(--syn-o)}
.highlight .nf,.highlight .py,.highlight .fm{color:var(--syn-f)}
.highlight .nc,.highlight .ne,.highlight .nn{color:var(--syn-nc)}
.highlight .nt{color:var(--syn-nt)}
.highlight .nv,.highlight .vc,.highlight .vg,.highlight .vi,
.highlight .vm{color:var(--syn-nv)}
.highlight .nb,.highlight .bp{color:var(--syn-nb)}
.highlight .nd{color:var(--syn-f); font-weight:600}
.highlight .err{color:var(--syn-err)}
.highlight .gh{color:var(--syn-gh); font-weight:700}
.highlight .gu{color:var(--syn-gh); font-weight:700}
.highlight .go{color:var(--syn-go)}
.highlight .gd{color:var(--syn-gd)}
.highlight .gi{color:var(--syn-gi)}
.highlight .gs{font-weight:700}
.highlight .ge{font-style:italic}
.highlight .p{color:var(--text)}

/* ---------- 悬浮按钮 ---------- */
#toTop{
  position:fixed; right:22px; bottom:26px; width:40px; height:40px;
  border:1px solid var(--border); border-radius:50%; background:var(--bg);
  color:var(--text); cursor:pointer; display:none; align-items:center;
  justify-content:center; box-shadow:var(--shadow); z-index:45;
}
#toTop.show{display:flex}
#toTop:hover{background:var(--accent-soft); border-color:var(--accent)}
#toTop svg{width:18px; height:18px}
.mask{
  position:fixed; inset:0; background:rgba(0,0,0,.4); z-index:35;
  display:none;
}
.mask.show{display:block}

@media (max-width:900px){
  .main{margin-left:0; padding-left:16px; padding-right:16px}
  body.side-collapsed .main{margin-left:0}
  .sidebar{box-shadow:var(--shadow)}
  #toTop{right:14px; bottom:16px}
  .content h1{font-size:22px}
  .content h2{font-size:18px}
}
@media print{
  .topbar,.sidebar,#toTop,.mask{display:none}
  .main{margin:0; padding:0}
}
</style>
</head>
<body>

<header class="topbar">
  <button class="icon-btn" id="toggleSide" title="显示/隐藏目录" aria-label="显示或隐藏目录">
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6">
      <path d="M1.5 3.5h13M1.5 8h13M1.5 12.5h13"/>
    </svg>
  </button>
  <div class="topbar-title">__DOC_TITLE__</div>
  <div class="topbar-spacer"></div>
  <button class="icon-btn" id="toggleTheme" title="切换深色/浅色" aria-label="切换主题">
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
      <path id="themeIcon" d="M8 1.5a6.5 6.5 0 1 0 6.5 6.5A5 5 0 0 1 8 1.5z"/>
    </svg>
  </button>
  <div class="progress" id="progress"></div>
</header>

<aside class="sidebar" id="sidebar">
  <div class="side-head">
    <div class="search-wrap">
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6">
        <circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5 14 14" stroke-linecap="round"/>
      </svg>
      <input id="search" type="search" placeholder="搜索目录,如 MySQL / K8s / 第 38 步" autocomplete="off">
      <button id="clearSearch" title="清空" aria-label="清空搜索">&times;</button>
    </div>
    <div class="side-meta">
      <span id="tocCount"></span>
      <span>
        <button id="expandAll" type="button">全部展开</button> ·
        <button id="collapseAll" type="button">全部折叠</button>
      </span>
    </div>
  </div>
  <nav class="side-body" id="tocNav">
__TOC_HTML__
    <div class="no-result" id="noResult">没有匹配的章节</div>
  </nav>
</aside>

<div class="mask" id="mask"></div>

<main class="main">
  <article class="content" id="content">
__CONTENT_HTML__
  </article>
</main>

<button id="toTop" title="回到顶部" aria-label="回到顶部">
  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7"
       stroke-linecap="round" stroke-linejoin="round">
    <path d="M8 13V3.5M3.5 8 8 3.5 12.5 8"/>
  </svg>
</button>

<script>
(function(){
  "use strict";
  var STORE = "kb42_";
  var nav = document.getElementById("tocNav");
  var sidebar = document.getElementById("sidebar");
  var links = Array.prototype.slice.call(nav.querySelectorAll("a.toc-link"));
  var items = Array.prototype.slice.call(nav.querySelectorAll("li.toc-item"));
  var searchInput = document.getElementById("search");
  var clearBtn = document.getElementById("clearSearch");
  var noResult = document.getElementById("noResult");
  var toTop = document.getElementById("toTop");
  var progress = document.getElementById("progress");
  var mask = document.getElementById("mask");
  var isNarrow = function(){ return window.innerWidth <= 900; };

  document.getElementById("tocCount").textContent = "共 " + links.length + " 个章节";

  /* ---------- 折叠 / 展开 ---------- */
  function setOpen(item, open){
    item.classList.toggle("open", open);
    if(open){
      var p = item.parentElement;
      while(p && p !== nav){
        if(p.tagName === "LI") p.classList.add("open");
        p = p.parentElement;
      }
    }
  }
  nav.addEventListener("click", function(e){
    var btn = e.target.closest(".toc-toggle");
    if(!btn) return;
    e.preventDefault();
    var li = btn.closest("li.toc-item");
    setOpen(li, !li.classList.contains("open"));
  });

  document.getElementById("expandAll").addEventListener("click", function(){
    items.forEach(function(i){ if(i.querySelector(":scope > .toc-sub")) i.classList.add("open"); });
  });
  document.getElementById("collapseAll").addEventListener("click", function(){
    items.forEach(function(i){ i.classList.remove("open"); });
    // 只保留第一个阶段展开,避免目录区空白
    var first = nav.querySelector("li.toc-item[data-level='1']");
    if(first) setOpen(first, true);
  });

  /* ---------- 点击跳转 ---------- */
  nav.addEventListener("click", function(e){
    var a = e.target.closest("a.toc-link");
    if(!a) return;
    var li = a.closest("li.toc-item");
    if(li && li.querySelector(":scope > .toc-sub")) setOpen(li, true);
    links.forEach(function(l){ l.classList.remove("active"); });
    a.classList.add("active");
    if(isNarrow()) hideSide();
  });

  /* ---------- 搜索过滤 ---------- */
  function escapeRe(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  function highlight(text, kw){
    var html = text.replace(/[&<>]/g, function(c){
      return { "&":"&amp;", "<":"&lt;", ">":"&gt;" }[c];
    });
    if(!kw) return html;
    var re = new RegExp("(" + escapeRe(kw) + ")", "gi");
    return html.replace(re, "<mark>$1</mark>");
  }
  var original = links.map(function(a){ return a.textContent; });
  function doSearch(){
    var kw = searchInput.value.trim();
    clearBtn.classList.toggle("show", !!kw);
    var hit = 0;
    items.forEach(function(li){ li.classList.remove("filtered"); });
    links.forEach(function(a, idx){
      a.innerHTML = highlight(original[idx], kw);
    });
    if(!kw){
      noResult.style.display = "none";
      return;
    }
    var lower = kw.toLowerCase();
    var keep = new Set();
    links.forEach(function(a, idx){
      if(original[idx].toLowerCase().indexOf(lower) === -1) return;
      hit++;
      var li = a.closest("li.toc-item");
      keep.add(li);
      var p = li.parentElement;
      while(p && p !== nav){
        if(p.tagName === "LI") keep.add(p);
        p = p.parentElement;
      }
      // 命中项自身展开,便于看到子章节
      if(li.querySelector(":scope > .toc-sub")) li.classList.add("open");
    });
    items.forEach(function(li){
      if(!keep.has(li)) li.classList.add("filtered");
    });
    noResult.style.display = hit ? "none" : "block";
  }
  searchInput.addEventListener("input", doSearch);
  clearBtn.addEventListener("click", function(){
    searchInput.value = ""; doSearch(); searchInput.focus();
  });
  searchInput.addEventListener("keydown", function(e){
    if(e.key === "Escape"){ searchInput.value = ""; doSearch(); }
  });

  /* ---------- 滚动高亮 + 进度 + 回到顶部 ---------- */
  var headings = [];
  links.forEach(function(a){
    var el = document.getElementById(a.getAttribute("href").slice(1));
    if(el) headings.push({ el: el, link: a });
  });

  function onScroll(){
    var y = window.scrollY;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    progress.style.width = (max > 0 ? (y / max) * 100 : 0) + "%";
    toTop.classList.toggle("show", y > 500);

    var target = null, probe = y + 90;
    for(var i = 0; i < headings.length; i++){
      var top = headings[i].el.getBoundingClientRect().top + y;
      if(top <= probe) target = headings[i]; else break;
    }
    if(!target && headings.length) target = headings[0];
    links.forEach(function(l){ l.classList.remove("active"); });
    if(target && !searchInput.value.trim()){
      target.link.classList.add("active");
      var li = target.link.closest("li.toc-item");
      if(li) setOpen(li, true);
      // 把高亮项滚进侧边栏可视区
      var navBox = nav.getBoundingClientRect();
      var linkBox = target.link.getBoundingClientRect();
      if(linkBox.top < navBox.top + 20){
        nav.scrollTop += linkBox.top - navBox.top - 60;
      } else if(linkBox.bottom > navBox.bottom - 20){
        nav.scrollTop += linkBox.bottom - navBox.bottom + 60;
      }
    }
  }
  var ticking = false;
  window.addEventListener("scroll", function(){
    if(ticking) return;
    ticking = true;
    requestAnimationFrame(function(){ onScroll(); ticking = false; });
  }, { passive: true });
  window.addEventListener("resize", onScroll);

  toTop.addEventListener("click", function(){
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  /* ---------- 侧边栏显隐 ---------- */
  function showSide(){
    sidebar.classList.remove("hidden");
    document.body.classList.remove("side-collapsed");
    if(isNarrow()) mask.classList.add("show");
  }
  function hideSide(){
    sidebar.classList.add("hidden");
    document.body.classList.add("side-collapsed");
    mask.classList.remove("show");
  }
  document.getElementById("toggleSide").addEventListener("click", function(){
    sidebar.classList.contains("hidden") ? showSide() : hideSide();
  });
  mask.addEventListener("click", hideSide);

  /* ---------- 主题 ---------- */
  var SUN = "M8 1.5a6.5 6.5 0 1 0 6.5 6.5A5 5 0 0 1 8 1.5z";
  var MOON = "M8 2.2v1.6M8 12.2v1.6M2.2 8h1.6M12.2 8h1.6M3.9 3.9l1.1 1.1M11 11l1.1 1.1M12.1 3.9 11 5M5 11l-1.1 1.1";
  var CIRCLE = ", M13.8 8a5.8 5.8 0 1 1-11.6 0 5.8 5.8 0 0 1 11.6 0z";
  function applyTheme(dark){
    document.documentElement.classList.toggle("dark", dark);
    document.getElementById("themeIcon").setAttribute("d", dark ? MOON + CIRCLE : SUN);
    try{ localStorage.setItem(STORE + "theme", dark ? "dark" : "light"); }catch(e){}
  }
  document.getElementById("toggleTheme").addEventListener("click", function(){
    applyTheme(!document.documentElement.classList.contains("dark"));
  });
  var saved = null;
  try{ saved = localStorage.getItem(STORE + "theme"); }catch(e){}
  applyTheme(saved ? saved === "dark"
    : window.matchMedia("(prefers-color-scheme: dark)").matches);

  /* ---------- 快捷键 ---------- */
  document.addEventListener("keydown", function(e){
    if(e.key === "/" && document.activeElement !== searchInput){
      e.preventDefault(); searchInput.focus(); searchInput.select();
    }
    if(e.key === "b" && (e.ctrlKey || e.metaKey)){
      e.preventDefault();
      document.getElementById("toggleSide").click();
    }
  });

  /* ---------- 初始状态 ---------- */
  var firstStage = nav.querySelector("li.toc-item[data-level='1']");
  if(firstStage) setOpen(firstStage, true);
  if(isNarrow()) hideSide();
  onScroll();

  // 支持 #锚点 直接打开并定位
  if(location.hash){
    var t = document.getElementById(location.hash.slice(1));
    if(t){
      setTimeout(function(){ t.scrollIntoView({ behavior: "smooth", block: "start" }); }, 120);
    }
  }
})();
</script>
</body>
</html>
"""

html = (
    TEMPLATE.replace("__DOC_TITLE__", DOC_TITLE)
    .replace("__TOC_HTML__", toc_html)
    .replace("__CONTENT_HTML__", content_html)
)
DST.write_text(html, encoding="utf-8")

n_links = toc_html.count('class="toc-link"')
print("已生成:", DST)
print("目录条目:", n_links)
print("HTML 大小: %.1f KB" % (len(html.encode("utf-8")) / 1024))
