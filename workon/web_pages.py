# coding: utf-8
"""技能工作台页面 HTML。

从 web.py 原样抽出：保留 r 前缀、缩进与全部字节（含反斜杠），哈希比对见交付说明。
"""

WORKBENCH_HTML = r"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#14110f">
<title>workon · 技能工作台</title>
<style>
:root{
  --primary:#ff7a1a; --primary-dark:#e8590c; --primary-soft:#2b1d0e; --accent-line:#5c3a17;
  --bg:#14110f; --surface:#1e1a17; --surface-soft:#262019;
  --text:#ddd2c6; --title:#fff4e8; --muted:#a3928a; --dim:#7a6c60;
  --line:#332a22; --line-strong:#4a3d31;
  --success:#34c77b; --danger:#e5484d; --warn:#e8a33d;
  --ink-term:#0e0b08;
  --shadow-sm:0 1px 2px rgba(0,0,0,.28);
  --shadow-md:0 8px 24px rgba(0,0,0,.34),0 2px 5px rgba(0,0,0,.22);
  --shadow-lg:0 14px 38px rgba(0,0,0,.42),0 3px 8px rgba(0,0,0,.28);
  --mono:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;
     background:
       radial-gradient(1100px 480px at 85% -10%, rgba(255,122,26,.06), transparent 60%),
       radial-gradient(900px 420px at -10% 110%, rgba(255,122,26,.045), transparent 55%),
       var(--bg);
     color:var(--text);min-height:100vh;font-size:14px;line-height:1.65;
     -webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
button,input,textarea,select{font:inherit}
button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible,select:focus-visible,.nav-item:focus-visible{outline:3px solid rgba(255,122,26,.30);outline-offset:3px}
::selection{background:#42301c;color:var(--title)}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:#3a3028;border-radius:8px;border:2px solid transparent;background-clip:content-box}
::-webkit-scrollbar-thumb:hover{background:#6b5c4e;background-clip:content-box}
::-webkit-scrollbar-track{background:transparent}

/* 顶栏 */
.header{height:64px;background:rgba(20,17,15,.92);border-bottom:1px solid var(--line);
        display:flex;align-items:center;justify-content:space-between;padding:0 30px;
        position:sticky;top:0;z-index:100;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}
.header-left{display:flex;align-items:center;gap:12px}
.header-logo{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;
        background:linear-gradient(145deg,#ff8f3c,#e8590c);color:#fff4e8;box-shadow:0 3px 10px rgba(255,122,26,.32)}
.header-logo svg{width:21px;height:21px}
.header-left h1{font-size:17px;font-weight:750;color:var(--title);letter-spacing:-.3px}
.header-left h1 span{font-weight:500;color:var(--dim);margin-left:8px;font-size:12px;letter-spacing:.02em}
.header-right{display:flex;align-items:center;gap:14px;color:var(--muted);font-size:12px}
.header-pill{background:var(--primary-soft);color:var(--primary-dark);padding:3px 10px;border-radius:999px;font-weight:650;font-family:var(--mono);font-size:10px;letter-spacing:.05em;border:1px solid var(--accent-line)}
.header-dot{width:6px;height:6px;border-radius:50%;background:var(--success);display:inline-block;margin-right:7px;box-shadow:0 0 0 3px rgba(255,122,26,.18)}
.header-clock{font-family:var(--mono);font-size:11px;color:var(--dim);letter-spacing:.02em}

/* 侧栏 + 主区 */
.layout{display:flex;min-height:calc(100vh - 64px);max-width:1560px;margin:0 auto}
.sidebar{width:228px;flex:0 0 228px;border-right:1px solid var(--line);padding:26px 14px 20px;
         display:flex;flex-direction:column;background:rgba(255,255,255,.04)}
.sidebar-section{font-size:10px;font-weight:700;color:var(--dim);text-transform:uppercase;letter-spacing:.16em;
        padding:0 12px;margin-bottom:10px}
.nav-item{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:9px;
        font-size:14px;font-weight:550;color:var(--muted);cursor:pointer;user-select:none;
        transition:background .18s,color .18s,box-shadow .18s;position:relative;margin-bottom:3px}
.nav-item:hover{background:var(--surface-soft);color:var(--title)}
.nav-item.active{background:var(--primary-soft);color:var(--primary-dark);font-weight:700;
        box-shadow:inset 3px 0 0 var(--primary)}
.nav-icon{width:18px;height:18px;text-align:center;flex:0 0 18px}
.nav-icon svg{width:18px;height:18px;display:block}
.sidebar-foot{margin-top:auto;padding:15px 16px;border-radius:11px;background:linear-gradient(160deg,#241c12,#2a2118);
        border:1px solid var(--accent-line);font-size:12px;line-height:1.8;color:var(--muted)}
.sidebar-foot b{display:flex;align-items:center;gap:6px;color:var(--primary-dark);font-size:11px;
        letter-spacing:.06em;text-transform:uppercase;margin-bottom:6px}
.sidebar-foot b svg{color:var(--primary)}
.main{flex:1;min-width:0;padding:34px 38px 60px;overflow-y:auto;max-width:1332px}
.page-section{display:none}
.page-section.active{display:block;animation:fade .22s ease}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.page-head{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:24px;gap:16px;flex-wrap:wrap}
.page-head h2{font-size:27px;color:var(--title);font-weight:760;letter-spacing:-.7px}
.page-head p{color:var(--muted);font-size:14px;margin-top:5px}
.kicker{display:flex;align-items:center;gap:8px;margin-bottom:9px;color:var(--primary);
        font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:.16em}
.kicker::before{content:"";width:16px;height:1.5px;background:var(--primary);border-radius:2px}

/* 使用指引 */
.guide-grid{display:grid;grid-template-columns:.8fr 1.2fr;gap:22px;align-items:start}
.guide-grid h2{font-size:27px;color:var(--title);font-weight:760;letter-spacing:-.7px}
.guide-desc{color:var(--muted);font-size:13px;line-height:1.95;margin-top:12px}
.guide-tip{margin-top:16px;padding:10px 13px;border:1px solid var(--accent-line);border-radius:9px;
        background:var(--primary-soft);color:var(--primary-dark);font-size:12px;line-height:1.8}
.guide-card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:11px}
.guide-card-head strong{color:var(--title);font-size:14px}
.guide-script{white-space:pre-wrap;word-break:break-word;line-height:1.95;font-size:13px}

/* 统计卡 */
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-bottom:20px}
.stat-card{position:relative;overflow:hidden;background:var(--surface);border:1px solid var(--line);
        border-radius:13px;padding:19px 21px;box-shadow:var(--shadow-sm);transition:border-color .2s,box-shadow .2s,transform .2s}
.stat-card:hover{border-color:var(--accent-line);box-shadow:var(--shadow-md);transform:translateY(-2px)}
.stat-card .stat-label{font-size:12px;color:var(--muted);font-weight:600;letter-spacing:.02em}
.stat-card .stat-val{font-size:30px;font-weight:740;color:var(--title);margin-top:3px;
        font-variant-numeric:tabular-nums;letter-spacing:-1.2px;line-height:1.2}
.stat-ico{position:absolute;right:16px;top:16px;width:34px;height:34px;border-radius:9px;display:flex;
        align-items:center;justify-content:center;background:var(--primary-soft);color:var(--primary)}
.stat-ico svg{width:17px;height:17px}
.stat-accent{position:absolute;left:0;top:14px;bottom:14px;width:3px;border-radius:0 3px 3px 0;background:var(--primary);opacity:.55}

/* 卡片 / 表格 */
.card{background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:22px 24px;
        margin-bottom:18px;box-shadow:var(--shadow-sm);transition:border-color .2s,box-shadow .2s}
.card:hover{border-color:var(--line-strong);box-shadow:var(--shadow-md)}
.card h3{font-size:15px;color:var(--title);margin-bottom:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.skill-card{position:relative;background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:21px;
        box-shadow:var(--shadow-sm);transition:border-color .2s,box-shadow .2s,transform .2s;display:flex;flex-direction:column;gap:12px}
.skill-card:hover{border-color:var(--accent-line);box-shadow:var(--shadow-lg);transform:translateY(-3px)}
.skill-card.official{border-color:var(--accent-line);background:linear-gradient(175deg,#241c12,#1e160e)}
.skill-top{display:flex;align-items:center;gap:12px}
.skill-avatar{width:42px;height:42px;flex:0 0 42px;border-radius:11px;display:flex;align-items:center;
        justify-content:center;color:var(--primary);background:var(--primary-soft);border:1px solid var(--accent-line)}
.skill-avatar.official{background:linear-gradient(145deg,#ff8f3c,#e8590c);color:#fff4e8;border:0;box-shadow:0 3px 10px rgba(255,122,26,.30)}
.skill-avatar svg{width:19px;height:19px}
.skill-name{font-size:15px;font-weight:720;color:var(--title);line-height:1.35}
.skill-ver{font-family:var(--mono);font-size:10px;color:var(--dim);font-weight:600;margin-left:6px;
        padding:1px 6px;border:1px solid var(--line);border-radius:5px;vertical-align:middle}
.tag{display:inline-block;background:var(--surface-soft);color:var(--muted);font-size:11px;font-weight:600;
        padding:2px 9px;border-radius:999px;margin:0 5px 5px 0;border:1px solid var(--line)}
.tag-primary{background:var(--primary-soft);color:var(--primary-dark);border-color:var(--accent-line)}
.muted{color:var(--dim);font-size:12px}
.skill-id{font-family:var(--mono);font-size:11px;color:var(--dim);letter-spacing:.01em}
.skill-desc{font-size:13px;color:var(--muted);line-height:1.75;min-height:44px}
.skill-foot{margin-top:auto;display:flex;align-items:center;justify-content:space-between;gap:8px;
        padding-top:13px;border-top:1px solid var(--line)}
.skill-source{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* 表单 / 按钮 */
label{display:block;font-size:13px;font-weight:650;color:var(--title);margin:16px 0 7px}
label .req{color:var(--danger)}
label .desc{display:block;font-weight:400;color:var(--dim);font-size:12px;line-height:1.7;margin:3px 0 0}
input,textarea,select{width:100%;padding:10px 12px;border:1px solid var(--line-strong);border-radius:9px;
        font-size:14px;font-family:inherit;color:var(--text);background:#1e1a17;outline:none;transition:border-color .18s,box-shadow .18s}
input:hover,textarea:hover,select:hover{border-color:#6b5c4e}
input:focus,textarea:focus,select:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(255,122,26,.15)}
input[type=file]{padding:8px 10px;background:#221b15;cursor:pointer}
input[type=file]::file-selector-button{margin-right:10px;padding:6px 12px;border:1px solid var(--line-strong);
        border-radius:7px;background:var(--surface-soft);color:var(--title);font-size:12px;font-weight:650;cursor:pointer;
        transition:background .18s,border-color .18s}
input[type=file]::file-selector-button:hover{background:var(--primary-soft);border-color:var(--accent-line);color:var(--primary-dark)}
input[type=checkbox]{width:auto;margin-right:7px;accent-color:var(--primary)}
select{cursor:pointer;appearance:none;
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='%23637068' stroke-width='1.6' stroke-linecap='round'%3E%3Cpath d='m4 6 4 4 4-4'/%3E%3C/svg%3E");
        background-repeat:no-repeat;background-position:right 11px center;background-size:15px;padding-right:34px}
.btn{padding:9px 17px;border-radius:9px;font-size:13px;font-weight:650;cursor:pointer;border:1px solid transparent;
        transition:background .18s,border-color .18s,box-shadow .18s,transform .1s;font-family:inherit;
        display:inline-flex;align-items:center;justify-content:center;gap:7px;white-space:nowrap}
.btn:active{transform:translateY(1px)}
.btn svg{width:13px;height:13px;flex:none}
.btn-primary{background:var(--primary);color:#fff;box-shadow:0 1px 2px rgba(0,0,0,.35)}
.btn-primary:hover{background:var(--primary-dark);box-shadow:0 4px 12px rgba(0,0,0,.42)}
.btn-primary:disabled{opacity:.65;cursor:not-allowed;transform:none}
.btn-ghost{background:var(--surface);border:1px solid var(--line-strong);color:var(--muted)}
.btn-ghost:hover{border-color:var(--primary);color:var(--primary);background:var(--primary-soft)}
.toast{position:fixed;bottom:28px;left:50%;transform:translateX(-50%) translateY(20px);
      background:#2a2118;color:#fff;padding:13px 22px;border-radius:12px;font-size:14px;font-weight:650;
      box-shadow:0 12px 36px rgba(0,0,0,.50);opacity:0;pointer-events:none;transition:all .25s;z-index:999;
      display:flex;flex-direction:column;gap:3px;align-items:center;text-align:center}
.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.toast span{font-size:11px;font-weight:450;color:#c9b8a8}
.form-actions{margin-top:22px;padding-top:18px;border-top:1px solid var(--line);display:flex;align-items:center;gap:12px}
.search-row{display:flex;align-items:center;gap:12px}
.search-wrap{position:relative;flex:1}
.search-wrap input{padding-left:38px}
.search-wrap::before{content:'';position:absolute;left:13px;top:50%;width:15px;height:15px;transform:translateY(-50%);
  background:no-repeat center/15px url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='none' stroke='%23808a84' stroke-width='1.6' stroke-linecap='round'%3E%3Ccircle cx='6.8' cy='6.8' r='4.3'/%3E%3Cpath d='m10.2 10.2 3 3'/%3E%3C/svg%3E")}

/* 终端 / 结果 */
.result-head{display:flex;align-items:center;justify-content:space-between;margin:20px 0 9px}
.result-head strong{font-size:13px;color:var(--title);letter-spacing:.01em}
.badge{font-size:11px;padding:3px 11px;border-radius:999px;background:var(--surface-soft);color:var(--muted);
        font-weight:700;letter-spacing:.03em;border:1px solid var(--line)}
.badge.success{background:#143226;color:#6ee7a8;border-color:#1f4d35}
.badge.failed,.badge.timeout,.badge.error{background:#331614;color:#f1978e;border-color:#5a2420}
.badge.running{background:#33240d;color:#f0b65e;border-color:#5a3c15}
.badge.badge-official{background:var(--primary-soft);color:var(--primary-dark);border:1px solid var(--accent-line);
        font-size:10px;padding:2px 8px;font-weight:700;white-space:nowrap;display:inline-flex;align-items:center;gap:4px}
.terminal{background:var(--ink-term);color:#e8ddd0;padding:18px 20px;border-radius:11px;overflow:auto;
        font-family:var(--mono);font-size:12.5px;line-height:1.85;max-height:380px;min-height:70px;
        white-space:pre-wrap;word-break:break-word;border:1px solid #3a2c1c;box-shadow:inset 0 1px 0 rgba(255,255,255,.05)}
.terminal-frame{border-radius:13px;overflow:hidden;border:1px solid var(--line);background:var(--surface);box-shadow:var(--shadow-sm)}
.terminal-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 14px;
        background:var(--surface-soft);border-bottom:1px solid var(--line);font-family:var(--mono);font-size:10px;
        letter-spacing:.12em;color:var(--dim)}
.window-dots{display:flex;gap:5px}
.window-dots span{width:8px;height:8px;border-radius:50%;background:#4a3f36}
.window-dots span:nth-child(1){background:#e08573}
.window-dots span:nth-child(2){background:#e8c07a}
.window-dots span:nth-child(3){background:#7fc79a}
.terminal-frame .terminal{border:0;border-radius:0;max-height:400px}

/* 历史 */
.history-item{display:flex;align-items:flex-start;gap:13px;padding:15px 18px;background:var(--surface);cursor:pointer;
        border:1px solid var(--line);border-radius:12px;margin-bottom:11px;box-shadow:var(--shadow-sm);
        transition:border-color .18s,box-shadow .18s,transform .18s}
.history-item:hover{border-color:var(--accent-line);box-shadow:var(--shadow-md);transform:translateY(-1px)}
.history-body{flex:1;min-width:0}
.history-name{font-weight:700;color:var(--title);font-size:14px}
.history-meta{font-size:12px;color:var(--dim);margin-top:5px}
.history-err{background:#331614;color:#f1978e;border-radius:8px;padding:8px 11px;margin-top:8px;
        font-family:var(--mono);font-size:12px;border:1px solid #5a2420}
.history-meta span{display:inline-block;margin-right:8px;padding:1px 8px;border:1px solid var(--line);border-radius:6px;
        background:var(--surface-soft);font-size:11px;color:var(--muted);font-family:var(--mono)}
.history-detail{margin-top:10px;padding-top:12px;border-top:1px dashed var(--line)}
.history-detail pre{margin:0;padding:13px 15px;border-radius:10px;background:var(--ink-term);color:#e8ddd0;
        font-family:var(--mono);font-size:12px;line-height:1.7;overflow:auto;white-space:pre-wrap}
.history-chev{flex:none;width:14px;height:14px;color:var(--dim);transition:transform .18s ease;margin-top:4px}
.history-item[aria-expanded="true"] .history-chev{transform:rotate(90deg)}
.empty{padding:46px 36px;text-align:center;color:var(--dim);background:var(--surface);
        border:1px dashed var(--line-strong);border-radius:13px}
.empty svg{width:30px;height:30px;margin:0 auto 12px;color:#6b5c4e}
.save-note{font-size:12px;font-weight:650}
.save-note.ok{color:var(--primary-dark)}
.save-note.err{color:#ef6b5e}
.hint{background:var(--primary-soft);border:1px solid var(--accent-line);color:#e8b88f;border-radius:11px;
        padding:13px 17px;font-size:13px;line-height:1.8;margin-bottom:18px;display:flex;gap:10px;align-items:flex-start}
.hint svg{flex:none;margin-top:3px;color:var(--primary)}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
@media(max-width:900px){.sidebar{width:66px;flex-basis:66px;padding:22px 8px}
  .sidebar-section,.nav-item>span:not(.nav-icon),.sidebar-foot{display:none}
  .nav-item{justify-content:center;padding:12px 0}.main{padding:24px 20px}}
@media(max-width:600px){.header{padding:0 15px}.header-left h1 span,.header-clock,.header-right>span:not(.header-pill){display:none}
  .header-right{gap:8px}
  .main{padding:22px 14px}.page-head h2{font-size:23px}
  .stats{grid-template-columns:1fr;gap:10px}.stat-card{padding:13px 17px;display:flex;align-items:center;justify-content:space-between}
  .stat-card .stat-val{font-size:23px;margin:0}.stat-ico{display:none}
  .grid{grid-template-columns:1fr}.skill-foot{align-items:flex-start;flex-direction:column}
  .skill-foot>span:last-child{width:100%}.skill-foot .btn{flex:1}
  .card{padding:17px}.page-head{margin-bottom:20px}.search-row{flex-direction:column;align-items:stretch}}
</style></head><body>

<header class="header">
  <div class="header-left">
    <a class="header-logo" href="/" aria-label="返回 workon 首页"><svg viewBox="0 0 34 34" fill="none" aria-hidden="true"><path d="M10 10h6v6h-6zM18 18h6v6h-6zM18 10h6M10 18v6h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></a>
    <h1>workon<span>技能工作台</span></h1>
  </div>
  <div class="header-right">
    <span><span class="header-dot"></span>本地服务运行中</span>
    <span id="clock" class="header-clock"></span>
    <span class="header-pill">v__VERSION__</span>
    <a class="btn btn-ghost" href="/logout" style="padding:5px 13px">退出</a>
  </div>
</header>

<div class="layout">
  <nav class="sidebar" aria-label="工作台导航">
    <div class="sidebar-section">工作区</div>
    <div class="nav-item active" data-page="guide" role="button" tabindex="0" aria-label="使用指引"><span class="nav-icon"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3V4Z" stroke="currentColor" stroke-width="1.6"/><path d="M8 8h7M8 12h7M8 16h4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></span><span>使用指引</span></div>
    <div class="nav-item" data-page="skills" role="button" tabindex="0" aria-label="技能库"><span class="nav-icon"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9 4H5a1 1 0 0 0-1 1v4h6V4Zm6 0v5h5V5a1 1 0 0 0-1-1h-4ZM4 15v4a1 1 0 0 0 1 1h4v-6H4Zm11 5h4a1 1 0 0 0 1-1v-4h-5v6Z" stroke="currentColor" stroke-width="1.6"/></svg></span><span>技能库</span></div>
    <div class="nav-item" data-page="run" role="button" tabindex="0" aria-label="召唤技能"><span class="nav-icon"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m9 6 9 6-9 6V6Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="M5 5v14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></span><span>召唤技能</span></div>
    <div class="nav-item" data-page="history" role="button" tabindex="0" aria-label="执行历史"><span class="nav-icon"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 12a8 8 0 1 0 2.3-5.7L4 8.6M4 4v4.6h4.6M12 7v5l3 2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span>执行历史</span></div>
    <div class="nav-item" data-page="settings" role="button" tabindex="0" aria-label="设置"><span class="nav-icon"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 7h16M4 17h16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="9" cy="7" r="2.5" fill="var(--surface)" stroke="currentColor" stroke-width="1.6"/><circle cx="15" cy="17" r="2.5" fill="var(--surface)" stroke="currentColor" stroke-width="1.6"/></svg></span><span>设置</span></div>
    <div class="sidebar-foot">
      <b><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/><path d="M8 7v4M8 4.6v.9"/></svg>小提示</b>
      技能是把确认过一次的工作固定下来的流程——填好输入、点一下召唤，就能得到相同的结果。
    </div>
  </nav>

  <main class="main">
    <section class="page-section active" id="page-guide">
      <div class="guide-grid">
        <div>
          <div class="kicker">GET STARTED</div>
          <h2>开始只需要两段话</h2>
          <p class="guide-desc">复制给你的 AI 助手（豆包、Kimi、Claude 等都可以），全程不用敲命令。第一次先装好 workon；以后每要把一件重复做的事变成技能，就用第二段。技能复现无需联网，数据始终留在你的机器上。</p>
          <div class="guide-tip"><b>两段都只要复制、粘贴给 AI 助手。</b><br>它问「确认保存成技能吗？」时回「确认」——这是全程唯一要你做的事。</div>
        </div>
        <div>
          <div class="card">
            <div class="guide-card-head"><strong>第一次 · 装好并开始</strong>
              <button class="btn btn-primary" data-copy="script-1"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="5" y="5" width="8" height="8" rx="1"/><path d="M11 5V3H3v8h2"/></svg>复制这段</button>
            </div>
            <pre class="terminal guide-script" id="script-1">请帮我安装并开始使用开源工具 workon：如果我的电脑上还没装好，请先按项目仓库的 README 帮我装好并启动本地工作台。装好后帮我把一件要重复做的事固化成技能，固化前让我确认结果。以后我自己在网页上点「召唤」就能复现，不用再找 AI。
项目地址：https://github.com/joutaojian/workon</pre>
          </div>
          <div class="card">
            <div class="guide-card-head"><strong>以后 · 固化成技能</strong>
              <button class="btn btn-primary" data-copy="script-2"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="5" y="5" width="8" height="8" rx="1"/><path d="M11 5V3H3v8h2"/></svg>复制这段</button>
            </div>
            <pre class="terminal guide-script" id="script-2">把刚刚的任务，固化成 workon 技能（开源工具，仓库：https://github.com/joutaojian/workon），请先做一份样例给我确认，我确认没问题后，再保存成技能，以后我自己在网页上点「召唤」就能复现</pre>
          </div>
        </div>
      </div>
    </section>

    <section class="page-section" id="page-skills">
      <div class="page-head">
        <div>
          <div class="kicker">SKILL LIBRARY</div>
          <h2>技能库</h2>
          <p>浏览所有已登记的技能，选一个点「召唤」即可复现工作。</p>
        </div>
      </div>
      <div class="stats">
        <div class="stat-card"><div class="stat-accent"></div><div class="stat-label">可用技能</div><div class="stat-val" id="stat-skills">0</div>
          <div class="stat-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M9 4H5a1 1 0 0 0-1 1v4h6V4Zm6 0v5h5V5a1 1 0 0 0-1-1h-4ZM4 15v4a1 1 0 0 0 1 1h4v-6H4Zm11 5h4a1 1 0 0 0 1-1v-4h-5v6Z"/></svg></div></div>
        <div class="stat-card"><div class="stat-accent"></div><div class="stat-label">标签数量</div><div class="stat-val" id="stat-tags">0</div>
          <div class="stat-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M4 11V5a1 1 0 0 1 1-1h6l9 9-7 7-9-9Z"/><circle cx="8" cy="8" r="1.4"/></svg></div></div>
        <div class="stat-card"><div class="stat-accent"></div><div class="stat-label">技能来源</div><div class="stat-val" id="stat-sources">0</div>
          <div class="stat-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M3 7h7l2 2h9v11H3zM3 7V4h7l2 3"/></svg></div></div>
      </div>
      <div class="card">
        <div class="search-row">
          <div class="search-wrap"><input id="search" placeholder="搜索技能名称、描述或标签…"></div>
          <button class="btn btn-ghost" onclick="reloadSkills()"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13.5 8a5.5 5.5 0 1 1-1.9-4.16"/><path d="M13.4 2.2v3.1h-3.1"/></svg>重新扫描</button>
        </div>
      </div>
      <div class="grid" id="skill-grid"></div>
    </section>

    <section class="page-section" id="page-run">
      <div class="page-head">
        <div>
          <div class="kicker">INVOKE</div>
          <h2>召唤技能</h2>
          <p>选好技能、填好内容，点一下「召唤」——不调用大模型，结果每次都一样。</p>
        </div>
      </div>
      <div class="card">
        <label>选择技能</label>
        <select id="skill-select"></select>
        <div id="form"></div>
        <div class="form-actions">
          <button class="btn btn-primary" id="run-btn" onclick="runSkill()"><svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M5.6 3.5v9l7.2-4.5z"/></svg>召唤</button>
          <span class="muted">运行固定脚本，不会再次调用 AI</span>
        </div>
        <div class="result-head"><strong>执行结果</strong><span class="badge" id="result-badge">待执行</span></div>
        <div class="terminal-frame">
          <div class="terminal-bar"><span class="window-dots" aria-hidden="true"><span></span><span></span><span></span></span><span>OUTPUT</span></div>
          <pre id="result" class="terminal">结果将显示在这里…</pre>
        </div>
      </div>
    </section>

    <section class="page-section" id="page-history">
      <div class="page-head">
        <div>
          <div class="kicker">HISTORY</div>
          <h2>执行历史</h2>
          <p>每一次召唤都留有记录，方便追溯。</p>
        </div>
        <button class="btn btn-ghost" onclick="loadHistory()"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13.5 8a5.5 5.5 0 1 1-1.9-4.16"/><path d="M13.4 2.2v3.1h-3.1"/></svg>刷新</button>
      </div>
      <div id="history"></div>
    </section>

    <section class="page-section" id="page-settings">
      <div class="page-head">
        <div>
          <div class="kicker">SETTINGS</div>
          <h2>设置</h2>
          <p>登记你的私有技能目录，保存后自动重新扫描。</p>
        </div>
      </div>
      <div class="hint"><svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/><path d="M8 7v4M8 4.6v.9"/></svg><span>这里只填你自己信任的脚本目录。workon 只会运行目录里登记过的技能。</span></div>
      <div class="card">
        <label>外部技能目录<span class="desc">（每行一个，指向你的私有项目目录）</span></label>
        <textarea id="dirs" rows="5" placeholder="D:/git/my-private-skills"></textarea>
        <label>访问密码<span class="desc">（修改后下次登录生效；留空则不修改）</span></label>
        <form onsubmit="event.preventDefault();saveSettings()"><input id="new-password" type="password" placeholder="留空表示不修改密码" autocomplete="new-password"></form>
        <div class="form-actions">
          <button class="btn btn-primary" onclick="saveSettings()"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13.5 8a5.5 5.5 0 1 1-1.9-4.16"/><path d="M13.4 2.2v3.1h-3.1"/></svg>保存并重新扫描</button>
          <span class="save-note" id="settings-note"></span>
        </div>
        <div class="result-head"><strong>保存结果</strong></div>
        <div class="terminal-frame">
          <div class="terminal-bar"><span class="window-dots" aria-hidden="true"><span></span><span></span><span></span></span><span>RESULT</span></div>
          <pre id="settings-result" class="terminal" style="min-height:0">尚未保存。</pre>
        </div>
      </div>
    </section>
  </main>
</div>

<div id="toast" class="toast"><span id="toast-main"></span><span id="toast-sub"></span></div>

<script>
let skills=[];
function clock(){
  const d=new Date();
  document.getElementById('clock').textContent=d.toLocaleString('zh-CN',{hour12:false});
}
clock();setInterval(clock,1000);
async function api(url,opts){const r=await fetch(url,opts);return r.json()}
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
const BS=String.fromCharCode(92);
// 统一的剪贴板复制：优先 navigator.clipboard，失败走 textarea+execCommand 兜底。
// onDone(ok) 在复制结束时回调；两种调用点（toast 提示 / 按钮反馈）都复用此函数。
function copyToClipboard(text,onDone){
  const fallback=()=>{
    const ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';
    document.body.appendChild(ta);ta.select();
    let ok=false;try{ok=document.execCommand('copy')}catch(e){ok=false}
    document.body.removeChild(ta);onDone(ok);
  };
  if(navigator.clipboard&&navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(()=>onDone(true),fallback);
  }else fallback();
}
function showToast(main,sub){
  document.getElementById('toast-main').textContent=main||'已复制，去粘贴给 AI 吧';
  document.getElementById('toast-sub').textContent=sub||'含私有逻辑，仅粘贴到可信 AI 环境';
  const t=document.getElementById('toast');t.classList.add('show');
  clearTimeout(window._toastTimer);window._toastTimer=setTimeout(()=>t.classList.remove('show'),3200);
}
function copyForAI(id){
  const s=skills.find(x=>x.id===id);if(!s)return;
  const script=(s.path||'')+BS+((s.entry&&s.entry.args||[])[0]||'run.py');
  const inputs=(s.inputs||[]).map(f=>f.name+'('+(f.type||'text')+')').join(', ')||'无';
  const desc=s.description||'';
  const text='你在协助使用 workon（把人工确认的工作流冻结成技能、可确定性复现的开源工具，https://github.com/joutaojian/workon）。技能「'+s.name+'」：'+desc+'。这是人已确认的固定工作流，请优先参考本地脚本 '+script+'（工作目录 '+(s.path||'')+'），按输入 '+inputs+' 执行，勿重新发明或临时发挥。若环境装有 workon，可用 python -m workon skill run '+s.id+' 复现；否则直接按脚本执行。';
  copyToClipboard(text,ok=>ok?showToast():showToast('复制失败，请手动复制'));
}
function switchPage(v){
  document.querySelectorAll('.nav-item').forEach(n=>{n.classList.toggle('active',n.dataset.page===v);n.setAttribute('aria-current',n.dataset.page===v?'page':'false')});
  document.querySelectorAll('.page-section').forEach(s=>s.classList.toggle('active',s.id==='page-'+v));
  if(v==='history')loadHistory();
  if(v==='settings')api('/api/settings').then(d=>document.getElementById('dirs').value=d.data.skill_dirs.join('\n'));
}
async function reloadSkills(){
  await api('/api/skills/reload',{method:'POST'});
  showToast('已重新扫描技能目录','');
  loadSkills();
}
async function loadSkills(){
  const d=await api('/api/skills?q='+encodeURIComponent(document.getElementById('search').value));
  // 官方能力排前，其余按 id；同组内官方徽章标识
  skills=d.data.slice().sort((a,b)=>(b.official?1:0)-(a.official?1:0)||String(a.id).localeCompare(String(b.id)));
  const grid=document.getElementById('skill-grid');
  grid.innerHTML=skills.map(s=>`<div class="skill-card${s.official?' official':''}">
    <div class="skill-top"><div class="skill-avatar${s.official?' official':''}" aria-hidden="true">${s.official?'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M8 1.8 9.7 6.3 14.2 8 9.7 9.7 8 14.2 6.3 9.7 1.8 8 6.3 6.3z"/></svg>':'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M6 4.5 2.5 8 6 11.5M10 4.5 13.5 8 10 11.5"/></svg>'}</div>
      <div><div class="skill-name">${esc(s.name)}<span class="skill-ver">v${esc(s.version)}</span></div>
      ${s.official?'<div style="margin-top:5px"><span class="badge badge-official">★ 官方能力 · 不可删除</span></div>':'<div class="skill-id" style="margin-top:2px">'+esc(s.id)+'</div>'}</div></div>
    <div class="skill-desc">${esc(s.description)}</div>
    <div>${s.tags.map(t=>`<span class="tag tag-primary">${esc(t)}</span>`).join('')}</div>
    <div class="skill-foot"><span class="muted skill-source" title="${esc(s.source)}">来源: ${esc((s.source||'').split(/[\\/]/).filter(Boolean).pop()||s.source)}</span>
      <span style="display:flex;gap:8px">
        <button class="btn btn-ghost" title="复制一段话术，粘贴给任意 AI，让它参考这个技能执行" onclick="copyForAI('${esc(s.id)}')"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><rect x="5.5" y="5.5" width="7.5" height="7.5" rx="1.2"/><path d="M10.5 5.5V3.4A1.4 1.4 0 0 0 9.1 2H3.4A1.4 1.4 0 0 0 2 3.4v5.7a1.4 1.4 0 0 0 1.4 1.4h2.1"/></svg>复制给 AI</button>
        <button class="btn btn-primary" onclick="pickSkill('${esc(s.id)}')"><svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M5.6 3.5v9l7.2-4.5z"/></svg>召唤</button>
      </span></div>
  </div>`).join('')||'<div class="empty"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M9 4H5a1 1 0 0 0-1 1v4h6V4Zm6 0v5h5V5a1 1 0 0 0-1-1h-4ZM4 15v4a1 1 0 0 0 1 1h4v-6H4Zm11 5h4a1 1 0 0 0 1-1v-4h-5v6Z"/></svg>暂无技能。可在 skills/ 目录或外部目录放置 manifest.json。</div>';
  const sel=document.getElementById('skill-select');
  sel.innerHTML=skills.map(s=>`<option value="${esc(s.id)}">${esc(s.name)} (${esc(s.id)})</option>`).join('');
  document.getElementById('stat-skills').textContent=skills.length;
  const tags=new Set();let src=new Set();
  skills.forEach(s=>{(s.tags||[]).forEach(t=>tags.add(t));src.add(s.source)});
  document.getElementById('stat-tags').textContent=tags.size;
  document.getElementById('stat-sources').textContent=src.size;
  if(sel.value)renderForm();
}
function pickSkill(id){switchPage('run');document.getElementById('skill-select').value=id;renderForm()}
function renderForm(){
  const s=skills.find(x=>x.id===document.getElementById('skill-select').value);if(!s)return;
  const form=document.getElementById('form');let html='';
  (s.inputs||[]).forEach(f=>{
    if(f.type==='text') html+=`<label>${esc(f.name)}${f.required?' <span class="req">*</span>':''}<span class="desc">${esc(f.description)}</span></label><input id="in-${esc(f.name)}" placeholder="输入文本">`;
    else {
      const attrs=f.type==='dir'?' webkitdirectory multiple':(f.multiple&&['file','docx','xlsx','image'].includes(f.type)?' multiple':'');
      html+=`<label>${esc(f.name)}${f.required?' <span class="req">*</span>':''}<span class="desc">${esc(f.description)}</span></label><input type="file" id="in-${esc(f.name)}"${attrs}>`;
    }
  });
  (s.params||[]).forEach(p=>{
    if(p.type==='boolean') html+=`<label><input type="checkbox" id="param-${esc(p.name)}"> ${esc(p.name)}</label>`;
    else if(p.choices&&p.choices.length) html+=`<label>${esc(p.name)}</label><select id="param-${esc(p.name)}">${p.choices.map(c=>`<option>${esc(c)}</option>`).join('')}</select>`;
    else html+=`<label>${esc(p.name)}</label><input id="param-${esc(p.name)}" value="${esc(p.default)}">`;
  });
  form.innerHTML=html;
}
async function runSkill(){
  const s=skills.find(x=>x.id===document.getElementById('skill-select').value);if(!s)return;
  const fd=new FormData();const inputs={},params={};
  (s.inputs||[]).forEach(f=>{
    const el=document.getElementById('in-'+f.name);
    if(f.type==='text')inputs[f.name]=el.value;
    else for(const file of el.files){
      if(f.type==='dir'&&file.webkitRelativePath)fd.append(f.name,file,file.webkitRelativePath);
      else fd.append(f.name,file,file.name);
    }
  });
  (s.params||[]).forEach(p=>{const el=document.getElementById('param-'+p.name);params[p.name]=p.type==='boolean'?el.checked:el.value});
  fd.append('inputs',JSON.stringify(inputs));fd.append('params',JSON.stringify(params));
  const badge=document.getElementById('result-badge');
  const runBtn=document.getElementById('run-btn');
  badge.className='badge running';badge.textContent='执行中…';
  runBtn.disabled=true;
  document.getElementById('result').textContent='执行中…';
  try{
    const r=await fetch('/api/skills/'+s.id+'/run',{method:'POST',body:fd});const d=await r.json();
    badge.className='badge '+(d.status||'failed');badge.textContent=d.status||'failed';
    let out=d.outputs||{};
    let text=Object.keys(out.text||{}).map(k=>k+': '+JSON.stringify(out.text[k])).join('\n');
    if(out.stdout&&!text)text=out.stdout;
    (out.files||[]).forEach(f=>{text+='\n文件: '+f.filename+' ('+f.size+' bytes)'});
    document.getElementById('result').textContent='状态: '+d.status+(d.error?'\n错误: '+d.error:'')+'\n'+(text||'(无文本输出)');
    loadHistory();
  }catch(e){
    badge.className='badge failed';badge.textContent='failed';
    document.getElementById('result').textContent='请求失败: '+e;
  }finally{runBtn.disabled=false}
}
async function loadHistory(){
  const d=await api('/api/history?limit=50');
  document.getElementById('history').innerHTML=d.data.map(r=>`<div class="history-item" role="button" tabindex="0" aria-expanded="false" data-run="${esc(r.run_id)}" onclick="toggleHistory(this)" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();toggleHistory(this)}">
    <span class="badge ${r.status}">${r.status}</span>
    <div class="history-body"><div class="history-name">${esc(r.skill_name)}</div>
      <div class="history-meta"><span>${esc(r.created_at)}</span><span>${r.duration_ms} ms</span><span>${esc((r.run_id||'').slice(0,8))}</span></div>
      ${r.error?`<div class="history-err">${esc(r.error)}</div>`:''}</div>
    <svg class="history-chev" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3.5 10.5 8 6 12.5"/></svg>
  </div>`).join('')||'<div class="empty"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg>暂无记录</div>';
}
async function toggleHistory(el){
  const open=el.getAttribute('aria-expanded')==='true';
  const next=el.nextElementSibling;
  if(open){el.setAttribute('aria-expanded','false');if(next&&next.classList.contains('history-detail'))next.remove();return}
  el.setAttribute('aria-expanded','true');
  const box=document.createElement('div');box.className='history-detail';
  const pre=document.createElement('pre');pre.textContent='加载中…';box.appendChild(pre);
  el.after(box);
  const d=await api('/api/history/'+encodeURIComponent(el.dataset.run));
  const out=(d.data&&d.data.outputs)||{};
  let text=Object.keys(out.text||{}).map(k=>k+': '+JSON.stringify(out.text[k])).join('\n');
  if(out.stdout&&!text)text=out.stdout;
  (out.files||[]).forEach(f=>{text+=(text?'\n':'')+'文件: '+f.filename+' ('+f.size+' bytes)'});
  pre.textContent='状态: '+((d.data&&d.data.status)||'-')+((d.data&&d.data.error)?'\n错误: '+d.data.error:'')+'\n'+(text||'(无文本输出)');
}
async function saveSettings(){
  const dirs=document.getElementById('dirs').value.split('\n').map(s=>s.trim()).filter(Boolean);
  const pw=document.getElementById('new-password').value;
  const payload={skill_dirs:dirs};if(pw)payload.password=pw;
  const d=await api('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  await api('/api/skills/reload',{method:'POST'});
  const ok=d.code===0;
  const dirsNow=(d.data&&d.data.skill_dirs)||dirs;
  document.getElementById('settings-result').textContent=(ok?'已保存，技能目录已重新扫描。':'保存失败：'+(d.message||'未知错误'))+(ok?'\n目录：\n'+dirsNow.map(x=>'  · '+x).join('\n'):'')+(ok&&pw?'\n密码已修改，下次登录生效。':'')+(ok?'':'\n'+JSON.stringify(d,null,2));
  if(pw)document.getElementById('new-password').value='';
  const note=document.getElementById('settings-note');
  if(note){note.textContent=ok?'✓ 已保存':'保存失败';note.className='save-note '+(ok?'ok':'err')}
  loadSkills();
}
function copyGuideText(id,btn){
  const el=document.getElementById(id);
  const text=el?el.textContent:'';
  copyToClipboard(text,ok=>{
    const old=btn.getAttribute('data-label')||btn.textContent.trim();
    btn.setAttribute('data-label',old);
    btn.textContent=ok?'已复制':'请手动复制';
    setTimeout(()=>btn.textContent=old,2200);
  });
}
document.querySelectorAll('[data-copy]').forEach(b=>{b.onclick=()=>copyGuideText(b.dataset.copy,b)});
document.querySelectorAll('.nav-item').forEach(n=>{n.onclick=()=>switchPage(n.dataset.page);n.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();switchPage(n.dataset.page)}}});
document.querySelector('.nav-item[data-page="guide"]').setAttribute('aria-current','page');
document.getElementById('search').oninput=loadSkills;
document.getElementById('skill-select').onchange=renderForm;
loadSkills();
</script></body></html>"""
