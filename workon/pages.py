# coding: utf-8
"""自包含的 HTML 页面常量（首页 / 登录页）。

零外部依赖：每个页面自带 <style>，不加载任何外部 CSS/JS/字体/CDN，离线可用。
使用 raw string 定义，避免反斜杠被 Python 转义（项目曾因此出过 bug）。
"""

HOME_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="workon 是开源、本地优先的 AI 产出冻结层。AI 做一次、人确认一次，将固定脚本和 manifest 固化为技能，此后填输入即可确定性复现，不再调用 AI。">
<meta name="theme-color" content="#14110f">
<title>workon — AI 只做一次，好结果随时复现</title>
<style>
:root{
  --bg:#14110f;
  --surface:#1e1a17;
  --surface-soft:#262019;
  --ink:#fff4e8;
  --muted:#a3928a;
  --faint:#9a8a7e;
  --line:#332a22;
  --line-strong:#4a3d31;
  --accent:#ff7a1a;
  --accent-dark:#e8590c;
  --accent-soft:#2b1d0e;
  --accent-line:#5c3a17;
  --mono:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;scroll-padding-top:92px}
body{
  background:var(--bg);
  color:var(--ink);
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  font-size:16px;
  line-height:1.65;
  -webkit-font-smoothing:antialiased;
}
a{color:inherit;text-decoration:none}
button,input{font:inherit}
button{color:inherit}
a,button{-webkit-tap-highlight-color:transparent}
a:focus-visible,button:focus-visible,input:focus-visible{
  outline:3px solid rgba(255,122,26,.32);
  outline-offset:4px;
}
::selection{background:#42301c;color:var(--ink)}
svg{display:block;flex:none}
.container{width:min(1180px,calc(100% - 64px));margin-inline:auto}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}

/* Navigation */
.site-header{
  position:sticky;top:0;z-index:20;
  width:100%;background:rgba(20,17,15,.94);
  border-bottom:1px solid var(--line);
  -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);
}
.navbar{min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:28px}
.brand{display:inline-flex;align-items:center;gap:10px;flex:none}
.brand-name{font-size:22px;font-weight:750;line-height:1;letter-spacing:-.7px}
.open-source{
  margin-left:3px;padding:3px 8px;border:1px solid var(--line-strong);border-radius:5px;
  color:var(--muted);font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.06em;line-height:1.5;
}
.nav-links{display:flex;align-items:center;gap:30px;margin-left:auto;margin-right:10px}
.nav-links a{color:var(--muted);font-size:14px;font-weight:550;transition:color .18s ease}
.nav-links a:hover{color:var(--accent)}
.nav-actions{display:flex;align-items:center;gap:12px}
.github-link{
  width:40px;height:40px;display:inline-flex;align-items:center;justify-content:center;
  border-radius:7px;color:var(--muted);transition:color .18s ease,background .18s ease;
}
.github-link:hover{color:var(--ink);background:var(--surface-soft)}
.btn{
  min-height:44px;display:inline-flex;align-items:center;justify-content:center;gap:9px;
  padding:10px 18px;border:1px solid transparent;border-radius:7px;
  font-size:14px;font-weight:650;line-height:1.4;cursor:pointer;
  transition:background .18s ease,border-color .18s ease,color .18s ease,box-shadow .18s ease;
}
.btn-primary{background:var(--accent);color:#fff;border-color:var(--accent);box-shadow:0 1px 2px rgba(0,0,0,.35)}
.btn-primary:hover{background:var(--accent-dark);border-color:var(--accent-dark);box-shadow:0 3px 8px rgba(0,0,0,.40)}
.btn-secondary{background:var(--surface);border-color:var(--line-strong);color:var(--ink)}
.btn-secondary:hover{background:var(--surface-soft);border-color:#6b5c4e}
.btn-lg{min-height:50px;padding:13px 22px;font-size:15px}
.nav-cta{min-height:40px;padding:8px 15px}

/* Hero */
.hero{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.08fr);align-items:center;gap:56px;padding-top:68px;padding-bottom:62px}
.hero-copy{min-width:0}
.badge{
  display:inline-flex;align-items:center;gap:8px;padding:6px 11px;
  border:1px solid var(--accent-line);border-radius:999px;background:var(--accent-soft);
  color:var(--accent-dark);font-size:12px;font-weight:650;letter-spacing:.02em;
}
.status-dot{width:6px;height:6px;border-radius:50%;background:var(--accent);flex:none}
.hero h1{margin-top:24px;font-size:clamp(40px,4.35vw,58px);font-weight:780;line-height:1.18;letter-spacing:-.055em}
.hero h1 span{display:block;white-space:nowrap}
.hero h1 .headline-accent{color:var(--accent)}
.hero-description{max-width:510px;margin-top:24px;color:var(--muted);font-size:16px;line-height:1.85}
.hero-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:30px}
.hero-facts{display:flex;flex-wrap:wrap;gap:11px 20px;margin-top:26px;color:var(--muted);font-size:12px}
.hero-fact{display:inline-flex;align-items:center;gap:6px}
.hero-fact svg{color:var(--accent)}

/* Product illustration */
.product-figure{min-width:0;margin:0}
.mockup-caption{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:10px;color:var(--faint);font-family:var(--mono);font-size:10px;letter-spacing:.08em}
.preview-label{display:inline-flex;align-items:center;gap:5px;padding:2px 7px;border:1px solid var(--line);border-radius:4px;background:var(--surface);font-family:inherit;font-size:11px;letter-spacing:0;color:var(--muted)}
.browser-window{overflow:hidden;border:1px solid var(--line-strong);border-radius:12px;background:var(--surface);box-shadow:0 12px 32px rgba(0,0,0,.38),0 2px 5px rgba(0,0,0,.28)}
.browser-bar{height:39px;display:flex;align-items:center;gap:14px;padding:0 13px;border-bottom:1px solid var(--line);background:#241e19}
.window-dots{display:flex;gap:5px}
.window-dots span{width:7px;height:7px;border-radius:50%;background:#4a3f36}
.browser-address{display:flex;align-items:center;justify-content:center;gap:5px;width:210px;max-width:60%;margin:auto;padding:3px 12px;border:1px solid #352c24;border-radius:5px;background:#2a231d;color:#9a8a7c;font-family:var(--mono);font-size:9px;white-space:nowrap}
.browser-spacer{width:31px}
.workspace{display:grid;grid-template-columns:132px minmax(0,1fr);min-height:420px;text-align:left}
.workspace-sidebar{display:flex;flex-direction:column;padding:17px 11px 13px;border-right:1px solid var(--line);background:#1a1512}
.demo-brand{display:flex;align-items:center;gap:6px;padding:0 5px 18px;font-size:13px;font-weight:750;letter-spacing:-.3px}
.demo-brand-mark{position:relative;width:17px;height:17px;border-radius:4px;background:var(--accent)}
.demo-brand-mark::before,.demo-brand-mark::after{content:"";position:absolute;width:4px;height:4px;border:1px solid #fff}
.demo-brand-mark::before{left:4px;top:4px}
.demo-brand-mark::after{right:3px;bottom:3px}
.workspace-label{padding:0 8px 7px;color:#98897b;font-size:8px;font-weight:700;letter-spacing:.12em}
.demo-nav-item{display:flex;align-items:center;gap:7px;padding:7px 8px;margin-bottom:3px;border-radius:5px;color:#a3928a;font-size:10px;font-weight:550}
.demo-nav-item.active{background:#3a2a14;color:#ff9244;font-weight:700}
.demo-nav-item svg{width:12px;height:12px}
.local-mode{display:flex;align-items:center;gap:5px;margin-top:auto;padding:10px 6px 0;border-top:1px solid var(--line);color:#9c8b7e;font-size:9px}
.local-mode .status-dot{width:5px;height:5px}
.workspace-main{min-width:0;padding:20px 21px 18px;background:#1e1a17}
.demo-breadcrumb{color:#9a8a7c;font-size:9px}
.demo-title-row{display:flex;align-items:center;gap:8px;margin-top:6px}
.demo-title-row h2{font-size:19px;line-height:1.35;letter-spacing:-.4px}
.official-tag{padding:2px 6px;border:1px solid var(--accent-line);border-radius:4px;background:var(--accent-soft);color:var(--accent-dark);font-size:8px;font-weight:650;white-space:nowrap}
.demo-description{margin-top:5px;color:#a3938a;font-size:10px}
.demo-form{margin-top:17px}
.demo-label{display:block;margin-bottom:6px;color:#e0d3c6;font-size:10px;font-weight:650}
.demo-file{display:flex;align-items:center;gap:8px;padding:8px 9px;border:1px solid #352c24;border-radius:6px;background:#221b15}
.demo-file + .demo-file{margin-top:6px}
.file-icon{display:flex;align-items:center;justify-content:center;width:26px;height:28px;border:1px solid #3a3028;border-radius:4px;background:#2b241d;color:#a19082;font-family:var(--mono);font-size:7px;font-weight:700}
.file-info{min-width:0;flex:1}
.file-name{display:block;overflow:hidden;color:#e5d8cb;font-size:10px;font-weight:600;text-overflow:ellipsis;white-space:nowrap}
.file-meta{display:block;margin-top:1px;color:#98897b;font-size:8px}
.file-order{color:#9c8d80;font-family:var(--mono);font-size:8px}
.demo-add-file{display:flex;align-items:center;justify-content:center;gap:5px;margin-top:7px;padding:6px;border:1px dashed #4a3d31;border-radius:5px;color:#a3928a;font-size:9px}
.demo-submit{display:flex;align-items:center;justify-content:center;gap:6px;width:100%;margin-top:12px;padding:8px;border-radius:6px;background:var(--accent);color:#fff;font-size:10px;font-weight:700}
.demo-note{margin-top:6px;text-align:center;color:#98897b;font-size:8px}
.demo-result{display:flex;align-items:flex-start;gap:8px;margin-top:14px;padding:10px;border:1px solid #3d2c15;border-radius:6px;background:#2b1d0e}
.result-check{display:flex;align-items:center;justify-content:center;width:21px;height:21px;border-radius:50%;background:#4a3115;color:var(--accent);flex:none}
.result-copy{min-width:0}
.result-title{display:block;color:#ff9244;font-size:10px;font-weight:700}
.result-path{display:block;overflow:hidden;margin-top:2px;color:#c9b09a;font-family:var(--mono);font-size:8px;text-overflow:ellipsis;white-space:nowrap}
.result-meta{display:block;margin-top:3px;color:#a19082;font-size:8px}

/* Product facts */
.fact-strip{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.fact-item{min-width:0;padding:25px 25px 25px 0}
.fact-item + .fact-item{padding-left:28px;border-left:1px solid var(--line)}
.fact-heading{display:flex;align-items:baseline;gap:8px}
.fact-value{font-size:29px;font-weight:730;line-height:1.2;letter-spacing:-1px}
.fact-name{font-size:13px;font-weight:650}
.fact-item p{margin-top:6px;color:var(--muted);font-size:12px}

/* Shared sections */
.section{padding-top:94px;padding-bottom:94px}
.section-heading{max-width:690px}
.kicker{display:flex;align-items:center;gap:9px;margin-bottom:13px;color:var(--accent);font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:.12em}
.kicker::before{content:"";width:19px;height:1px;background:var(--accent)}
.section-heading h2,.quick-copy h2{font-size:clamp(28px,3vw,38px);font-weight:740;line-height:1.3;letter-spacing:-1.2px}
.section-heading > p{margin-top:13px;color:var(--muted);font-size:15px;line-height:1.8}

/* Before and after */
.comparison-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:38px}
.compare-card{padding:29px 30px 25px;border:1px solid var(--line);border-radius:11px;background:var(--surface)}
.compare-card.after{border-color:var(--accent-line);box-shadow:inset 3px 0 0 var(--accent)}
.compare-top{display:flex;align-items:center;gap:12px;padding-bottom:22px;border-bottom:1px solid var(--line)}
.compare-icon{display:flex;align-items:center;justify-content:center;width:38px;height:38px;border:1px solid var(--line);border-radius:8px;color:var(--muted);background:var(--surface-soft)}
.after .compare-icon{border-color:var(--accent-line);background:var(--accent-soft);color:var(--accent)}
.compare-overline{display:block;color:var(--faint);font-family:var(--mono);font-size:9px;letter-spacing:.12em}
.compare-top h3{margin-top:1px;font-size:18px;font-weight:700}
.compare-list{list-style:none;display:grid;gap:14px;margin-top:23px}
.compare-list li{display:flex;align-items:flex-start;gap:10px;color:var(--muted);font-size:14px}
.compare-list svg{margin-top:5px;color:#7a6c60}
.after .compare-list li{color:#e5d8cb}
.after .compare-list svg{color:var(--accent)}
.compare-foot{margin-top:24px;padding-top:17px;border-top:1px solid var(--line);color:var(--faint);font-size:12px}
.after .compare-foot{color:var(--accent-dark);font-weight:600}

/* Process */
.section-band{border-top:1px solid var(--line);border-bottom:1px solid var(--line);background:var(--surface-soft)}
.process-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:38px;list-style:none}
.process-card{position:relative;min-width:0;padding:23px 21px 24px;border:1px solid var(--line);border-radius:9px;background:var(--surface)}
.process-meta{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px}
.step-number{color:var(--accent);font-family:var(--mono);font-size:12px;font-weight:700;letter-spacing:.08em}
.process-icon{color:#a3928a}
.process-card h3{font-size:16px;font-weight:700}
.process-card p{margin-top:9px;color:var(--muted);font-size:13px;line-height:1.8}
.process-action{display:inline-block;margin-top:15px;padding-top:12px;border-top:1px solid var(--line);color:#b5a697;font-family:var(--mono);font-size:10px}

/* Use cases */
.use-case-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:38px}
.use-card{display:flex;flex-direction:column;min-width:0;padding:27px 25px;border:1px solid var(--line);border-radius:10px;background:var(--surface);transition:border-color .18s ease,box-shadow .18s ease}
.use-card:hover{border-color:var(--line-strong);box-shadow:0 5px 16px rgba(0,0,0,.28)}
.use-card-top{display:flex;align-items:center;justify-content:space-between;gap:10px}
.use-icon{display:flex;align-items:center;justify-content:center;width:40px;height:40px;border:1px solid var(--accent-line);border-radius:8px;background:var(--accent-soft);color:var(--accent)}
.use-tag{padding:3px 7px;border:1px solid var(--line);border-radius:4px;color:var(--muted);font-size:9px;white-space:nowrap}
.use-tag.official{border-color:var(--accent-line);color:var(--accent-dark);background:#2b1d0e}
.use-card h3{margin-top:22px;font-size:18px;font-weight:700}
.use-card > p{margin-top:9px;color:var(--muted);font-size:13px;line-height:1.8}
.use-example{margin-top:20px;padding-top:15px;border-top:1px solid var(--line);color:#b5a697;font-size:11px}
.use-example span{display:block;margin-top:4px;color:var(--faint);font-size:10px}

/* Installation */
.quick-section{padding-top:10px}
.terminals{display:flex;flex-direction:column;gap:16px}
.quick-grid{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);align-items:center;gap:70px;padding:48px;border:1px solid var(--line);border-radius:12px;background:var(--surface)}
.quick-copy > p{margin-top:15px;color:var(--muted);font-size:14px;line-height:1.85}
.requirements{display:flex;flex-wrap:wrap;gap:9px 16px;margin-top:23px;color:#b5a697;font-size:11px}
.requirement{display:inline-flex;align-items:center;gap:5px}
.requirement svg{color:var(--accent)}
.terminal{min-width:0;overflow:hidden;border:1px solid #3a2c1c;border-radius:9px;background:#0e0b08;box-shadow:0 5px 16px rgba(0,0,0,.30)}
.terminal-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 13px;border-bottom:1px solid #2c2118;background:#17120d}
.terminal-title{display:flex;align-items:center;gap:10px;color:#c9b8a8;font-family:var(--mono);font-size:10px}
.terminal-title .window-dots span{width:6px;height:6px;background:#4a3f36}
.copy-button{display:inline-flex;align-items:center;gap:6px;padding:5px 8px;border:1px solid #4a3d31;border-radius:5px;background:transparent;color:#d8c8b8;font-size:10px;cursor:pointer;transition:background .18s ease,border-color .18s ease}
.copy-button:hover{background:#2c2118;border-color:#6b5c4e}
.terminal-body{overflow-x:auto;padding:23px 22px 25px}
.terminal code{color:#f0e4d6;font-family:var(--mono);font-size:13px;line-height:1.95;white-space:pre-wrap;word-break:break-word}
.command-line{display:block}
.command-line + .command-line{margin-top:13px;color:#d8c8b8}
.install-note{margin-top:12px;color:var(--faint);font-size:11px}

/* Closing and footer */
.closing{display:flex;align-items:center;justify-content:space-between;gap:30px;margin-top:0;margin-bottom:94px;padding:38px 42px;border:1px solid var(--accent-line);border-radius:11px;background:var(--accent-soft)}
.closing h2{font-size:26px;font-weight:730;line-height:1.4;letter-spacing:-.7px}
.closing p{margin-top:7px;color:#b5a697;font-size:13px}
.closing .btn{flex:none}
.site-footer{border-top:1px solid var(--line);background:var(--surface)}
.footer-main{display:flex;align-items:flex-start;justify-content:space-between;gap:40px;padding-top:35px;padding-bottom:35px}
.footer-brand .brand-name{font-size:19px}
.footer-brand p{margin-top:10px;color:var(--muted);font-size:12px}
.footer-links{display:flex;flex-wrap:wrap;gap:26px;color:var(--muted);font-size:12px}
.footer-links a{display:inline-flex;align-items:center;gap:6px;transition:color .18s ease}
.footer-links a:hover{color:var(--accent)}
.footer-bottom{display:flex;justify-content:space-between;gap:20px;padding-top:18px;padding-bottom:22px;border-top:1px solid var(--line);color:var(--faint);font-family:var(--mono);font-size:10px}

@media (max-width:1050px){
  .nav-links{gap:20px;margin-right:0}
  .hero{gap:32px}
  .hero h1{font-size:42px}
  .workspace{grid-template-columns:116px minmax(0,1fr)}
  .workspace-main{padding-inline:17px}
  .quick-grid{gap:40px;padding:38px}
}
@media (max-width:900px){
  .nav-links{display:none}
  .hero{grid-template-columns:1fr;gap:45px;padding-top:58px}
  .hero-copy{max-width:650px}
  .hero h1{font-size:clamp(42px,7vw,58px)}
  .hero-description{max-width:600px}
  .product-figure{width:min(680px,100%);margin-inline:auto}
  .workspace{grid-template-columns:140px minmax(0,1fr)}
  .process-grid{grid-template-columns:repeat(2,1fr)}
  .quick-grid{grid-template-columns:1fr;gap:30px}
  .quick-copy{max-width:620px}
}
@media (max-width:760px){
  .container{width:min(100% - 36px,1180px)}
  .navbar{min-height:64px;gap:14px}
  .brand-name{font-size:20px}
  .brand svg{width:30px;height:30px}
  .open-source{display:none}
  .nav-actions{gap:5px}
  .nav-cta{min-height:40px;padding:8px 12px;font-size:12px}
  .github-link{width:38px;height:38px}
  .hero{grid-template-columns:1fr;gap:36px;padding-top:44px;padding-bottom:44px}
  .hero h1{margin-top:20px;font-size:clamp(35px,9.4vw,50px);letter-spacing:-.055em}
  .hero-description{margin-top:20px;font-size:15px}
  .hero-actions{margin-top:25px}
  .hero-facts{gap:9px 15px;margin-top:22px}
  .mockup-caption{font-size:9px}
  .browser-bar{gap:8px;padding-inline:10px}
  .browser-spacer{width:25px}
  .workspace{grid-template-columns:104px minmax(0,1fr);min-height:390px}
  .workspace-sidebar{padding-inline:8px}
  .workspace-main{padding:17px 14px 15px}
  .demo-nav-item{gap:5px;padding-inline:6px;font-size:9px}
  .demo-title-row h2{font-size:17px}
  .fact-strip{grid-template-columns:repeat(2,1fr)}
  .fact-item{padding:21px 15px 21px 0}
  .fact-item + .fact-item{padding-left:20px}
  .fact-item:nth-child(3){padding-left:0;border-left:0;border-top:1px solid var(--line)}
  .fact-item:nth-child(4){border-top:1px solid var(--line)}
  .fact-value{font-size:26px}
  .section{padding-top:68px;padding-bottom:68px}
  .section-heading h2,.quick-copy h2{font-size:29px}
  .comparison-grid{grid-template-columns:1fr;gap:14px;margin-top:29px}
  .compare-card{padding:24px 22px}
  .process-grid{gap:12px;margin-top:29px}
  .process-card{padding:20px 18px}
  .process-meta{margin-bottom:22px}
  .use-case-grid{grid-template-columns:1fr;gap:13px;margin-top:29px}
  .use-card{padding:23px 22px}
  .use-card h3{margin-top:17px}
  .quick-section{padding-top:0}
  .quick-grid{gap:28px;padding:28px 22px}
  .terminal-body{padding:19px 17px 21px}
  .closing{align-items:flex-start;flex-direction:column;margin-top:0;margin-bottom:68px;padding:29px 25px}
  .closing h2{font-size:24px}
  .footer-main{flex-direction:column;gap:26px}
  .footer-bottom{flex-direction:column;gap:5px}
}
@media (max-width:480px){
  .container{width:calc(100% - 28px)}
  .brand{gap:8px}
  .navbar{gap:8px}
  .github-link{display:none}
  .hero h1{font-size:clamp(32px,9vw,42px)}
  .hero-actions{display:grid;grid-template-columns:1fr 1fr;gap:9px}
  .hero-actions .btn{padding-inline:12px;font-size:13px}
  .hero-facts{display:grid;grid-template-columns:1fr 1fr}
  .product-figure{width:100%}
  .browser-address{max-width:65%;font-size:8px}
  .workspace{grid-template-columns:1fr;min-height:0}
  .workspace-sidebar{display:none}
  .workspace-main{padding:19px 17px}
  .demo-title-row h2{font-size:19px}
  .demo-description,.demo-label,.file-name,.demo-submit,.result-title{font-size:11px}
  .demo-add-file{font-size:10px}
  .fact-item + .fact-item{padding-left:14px}
  .fact-name{font-size:12px}
  .fact-item p{font-size:11px}
  .process-grid{grid-template-columns:1fr}
  .process-card{padding:21px}
  .process-meta{margin-bottom:17px}
  .process-action{margin-top:12px}
  .use-card-top{align-items:flex-start}
  .quick-grid{padding:25px 16px}
  .terminal-title{font-size:9px}
  .terminal code{font-size:11px}
  .closing{padding:26px 21px}
  .footer-links{gap:18px}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation:none !important;transition:none !important;scroll-behavior:auto !important}
}
</style>
</head>
<body>
<header class="site-header">
  <div class="container navbar">
    <a class="brand" href="/" aria-label="workon 首页">
      <svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true"><rect x="1" y="1" width="32" height="32" rx="9" fill="#ff7a1a"/><path d="M10 10h6v6h-6zM18 18h6v6h-6zM18 10h6M10 18v6h6" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
      <span class="brand-name">workon</span>
      <span class="open-source">OPEN SOURCE</span>
    </a>
    <nav class="nav-links" aria-label="页面导航">
      <a href="#start">快速开始</a>
      <a href="#how">工作原理</a>
      <a href="#features">应用场景</a>
    </nav>
    <div class="nav-actions">
      <a class="github-link" href="https://github.com/joutaojian/workon" target="_blank" rel="noopener noreferrer" aria-label="在 GitHub 查看 workon">
        <svg width="21" height="21" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.87c-2.78.6-3.37-1.18-3.37-1.18-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.56-1.11-4.56-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02A9.56 9.56 0 0 1 12 6.82a9.6 9.6 0 0 1 2.5.34c1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85V21c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"/></svg>
      </a>
      <a class="btn btn-primary nav-cta" href="/login">打开工作台<svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 10h12M11 5l5 5-5 5"/></svg></a>
    </div>
  </div>
</header>

<main>
  <section class="container hero" aria-labelledby="hero-title">
    <div class="hero-copy">
      <div class="badge"><span class="status-dot" aria-hidden="true"></span>开源 · 本地优先的 AI 产出冻结层</div>
      <h1 id="hero-title"><span>AI 只做一次。</span><span class="headline-accent">好结果，随时复现。</span></h1>
      <p class="hero-description">AI 帮你做一次，你点头确认，这件工作就保存成一个技能。下次只要填上新的输入、点一下「召唤」，同样的结果就出来，不用再等 AI、不再花 Token。</p>
      <div class="hero-actions">
        <a class="btn btn-primary btn-lg" href="/login">打开工作台<svg width="17" height="17" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 10h12M11 5l5 5-5 5"/></svg></a>
        <a class="btn btn-secondary btn-lg" href="#start">怎么开始</a>
      </div>
      <div class="hero-facts" aria-label="产品特点">
        <span class="hero-fact"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg>复现零 Token</span>
        <span class="hero-fact"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg>复现零联网</span>
        <span class="hero-fact"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg>数据留在本机</span>
      </div>
    </div>

    <figure class="product-figure">
      <figcaption class="mockup-caption"><span>WORKSPACE / PREVIEW</span><span class="preview-label"><svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><rect x="2" y="3" width="12" height="10" rx="1.5"/><path d="M2 6h12"/></svg>界面示意</span></figcaption>
      <div class="browser-window" aria-hidden="true">
        <div class="browser-bar">
          <div class="window-dots"><span></span><span></span><span></span></div>
          <div class="browser-address"><svg width="9" height="9" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="4" y="7" width="8" height="6" rx="1"/><path d="M6 7V5a2 2 0 0 1 4 0v2"/></svg>localhost / workon</div>
          <div class="browser-spacer"></div>
        </div>
        <div class="workspace">
          <aside class="workspace-sidebar">
            <div class="demo-brand"><span class="demo-brand-mark"></span>workon</div>
            <div class="workspace-label">工作台</div>
            <div class="demo-nav-item active"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M3 2.5h7l3 3v8h-10z"/><path d="M10 2.5v3h3M5.5 8h5M5.5 10.5h5"/></svg>技能库</div>
            <div class="demo-nav-item"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3"><circle cx="8" cy="8" r="5.5"/><path d="M8 5v3l2 1.5"/></svg>运行记录</div>
            <div class="demo-nav-item"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3"><circle cx="8" cy="8" r="2"/><path d="M8 2v1.5M8 12.5V14M2 8h1.5M12.5 8H14M3.8 3.8 4.8 4.8M11.2 11.2l1 1M3.8 12.2l1-1M11.2 4.8l1-1"/></svg>设置</div>
            <div class="local-mode"><span class="status-dot"></span>本地运行</div>
          </aside>
          <div class="workspace-main">
            <div class="demo-breadcrumb">技能库 / 文档处理</div>
            <div class="demo-title-row"><h2>PDF 合并</h2><span class="official-tag">官方技能</span></div>
            <p class="demo-description">将多个 PDF 按列表顺序合并为一个文件。</p>
            <div class="demo-form">
              <span class="demo-label">输入文件 · 按顺序合并</span>
              <div class="demo-file"><span class="file-icon">PDF</span><div class="file-info"><span class="file-name">01_季度报告_封面.pdf</span><span class="file-meta">已添加 · 等待召唤</span></div><span class="file-order">01</span></div>
              <div class="demo-file"><span class="file-icon">PDF</span><div class="file-info"><span class="file-name">02_季度报告_正文.pdf</span><span class="file-meta">已添加 · 等待召唤</span></div><span class="file-order">02</span></div>
              <div class="demo-add-file"><svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M8 3v10M3 8h10"/></svg>添加 PDF 文件</div>
              <div class="demo-submit"><svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><path d="m8 2 1.3 3.7L13 7l-3.7 1.3L8 12 6.7 8.3 3 7l3.7-1.3z"/></svg>召唤技能</div>
              <div class="demo-note">运行固定脚本，不会再次调用 AI</div>
            </div>
            <div class="demo-result">
              <span class="result-check"><svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m3 8 3 3 7-7"/></svg></span>
              <div class="result-copy"><span class="result-title">合并完成</span><span class="result-path">output/季度报告_合并.pdf</span><span class="result-meta">2 个输入文件 · 已按列表顺序合并</span></div>
            </div>
          </div>
        </div>
      </div>
    </figure>
  </section>

  <section id="start" class="container section quick-section" aria-labelledby="quick-title">
    <div class="quick-grid">
      <div class="quick-copy">
        <div class="kicker">GET STARTED</div>
        <h2 id="quick-title">开始只需要两段话</h2>
        <p>把话复制给你的 AI 助手（豆包、Kimi、Claude 等都可以），全程不用敲命令。第一次先装好 workon；以后每要把一件重复做的事变成技能，就用第二段。技能复现无需联网，数据始终留在你的机器上。</p>
        <div class="requirements">
          <span class="requirement"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg>Python 3.9+</span>
          <span class="requirement"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg>核心零依赖</span>
          <span class="requirement"><svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg>MIT 开源</span>
        </div>
        <p class="install-note">两段都只要复制、粘贴给 AI 助手。</p>
      </div>
      <div class="terminals">
        <div class="terminal">
          <div class="terminal-bar">
            <div class="terminal-title"><span class="window-dots" aria-hidden="true"><span></span><span></span><span></span></span>第一次 · 装好并开始</div>
            <button class="copy-button" id="copy-install" type="button" data-copy-button="install-command"><svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><rect x="5" y="5" width="8" height="8" rx="1"/><path d="M11 5V3H3v8h2"/></svg><span class="copy-label">复制这段话</span></button>
          </div>
          <div class="terminal-body"><pre id="install-command" aria-label="第一次装好 workon 的一段话"><code><span class="command-line"><span class="command">请帮我安装并开始使用开源工具 workon：如果我的电脑上还没装好，请先按项目仓库的 README 帮我装好并启动本地工作台。装好后帮我把一件要重复做的事固化成技能，固化前让我确认结果。以后我自己在网页上点「召唤」就能复现，不用再找 AI。</span></span><span class="command-line"><span class="command">项目地址：https://github.com/joutaojian/workon</span></span></code></pre></div>
        </div>
        <div class="terminal">
          <div class="terminal-bar">
            <div class="terminal-title"><span class="window-dots" aria-hidden="true"><span></span><span></span><span></span></span>以后 · 固化成技能</div>
            <button class="copy-button" id="copy-freeze" type="button" data-copy-button="freeze-command"><svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><rect x="5" y="5" width="8" height="8" rx="1"/><path d="M11 5V3H3v8h2"/></svg><span class="copy-label">复制这段话</span></button>
          </div>
          <div class="terminal-body"><pre id="freeze-command" aria-label="以后固化技能的一段话"><code><span class="command-line"><span class="command">把刚刚的任务，固化成 workon 技能（开源工具，仓库：https://github.com/joutaojian/workon），请先做一份样例给我确认，我确认没问题后，再保存成技能，以后我自己在网页上点「召唤」就能复现</span></span></code></pre></div>
        </div>
      </div>
    <span class="sr-only" id="copy-status" role="status" aria-live="polite"></span>
  </section>

  <section class="container fact-strip" aria-label="workon 产品事实">
    <div class="fact-item"><div class="fact-heading"><strong class="fact-value">0</strong><span class="fact-name">复现 Token</span></div><p>固化后不再调用 AI</p></div>
    <div class="fact-item"><div class="fact-heading"><strong class="fact-value">0</strong><span class="fact-name">核心依赖</span></div><p>核心能力轻量运行</p></div>
    <div class="fact-item"><div class="fact-heading"><strong class="fact-value">100%</strong><span class="fact-name">本地数据</span></div><p>输入与产出留在本机</p></div>
    <div class="fact-item"><div class="fact-heading"><strong class="fact-value">MIT</strong><span class="fact-name">开源许可</span></div><p>开放源码，自由使用</p></div>
  </section>

  <section class="container section" aria-labelledby="compare-title">
    <div class="section-heading">
      <div class="kicker">WHY WORKON</div>
      <h2 id="compare-title">别把同一个好结果，交给下一次运气</h2>
      <p>真正需要重复的是已经验证过的流程，不是重复生成。workon 把「生成」与「复现」分开。</p>
    </div>
    <div class="comparison-grid">
      <article class="compare-card">
        <div class="compare-top"><span class="compare-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M20 11a8 8 0 1 0-2.34 5.66M20 5v6h-6"/></svg></span><div><span class="compare-overline">REPEAT GENERATION</span><h3>重复让 AI 重做</h3></div></div>
        <ul class="compare-list">
          <li><svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="m4 4 8 8M12 4l-8 8"/></svg><span>每次重新描述需求、等待模型生成</span></li>
          <li><svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="m4 4 8 8M12 4l-8 8"/></svg><span>反复消耗 Token，还要重新核对产出</span></li>
          <li><svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="m4 4 8 8M12 4l-8 8"/></svg><span>同一任务，生成结果仍可能发生变化</span></li>
        </ul>
        <div class="compare-foot">每次执行，都重新走一遍生成流程</div>
      </article>
      <article class="compare-card after">
        <div class="compare-top"><span class="compare-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M7 3h10v4H7zM5 7h14v14H5zM9 12h6M9 16h4"/></svg></span><div><span class="compare-overline">FREEZE &amp; REPRODUCE</span><h3>固化后随时复现</h3></div></div>
        <ul class="compare-list">
          <li><svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg><span>填写新的输入点，点击「召唤」即可</span></li>
          <li><svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg><span>运行已确认的固定脚本与 manifest</span></li>
          <li><svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="m3 8 3 3 7-7"/></svg><span>确定性复现，不再调用 AI</span></li>
        </ul>
        <div class="compare-foot">零复现 Token · 零联网 · 数据留在本机</div>
      </article>
    </div>
  </section>

  <section id="how" class="section-band" aria-labelledby="how-title">
    <div class="container section">
      <div class="section-heading">
        <div class="kicker">HOW IT WORKS</div>
        <h2 id="how-title">一次确认，之后只需召唤</h2>
        <p>AI 负责第一次生成，你负责确认结果。被冻结的是流程，之后每次执行都不再生成。</p>
      </div>
      <ol class="process-grid">
        <li class="process-card"><div class="process-meta"><span class="step-number">01</span><svg class="process-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8zM18.5 16l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z"/></svg></div><h3>让 AI 做一次</h3><p>描述任务，由 AI 生成固定脚本，并完成第一次样例处理。</p><span class="process-action">动作：生成并运行</span></li>
        <li class="process-card"><div class="process-meta"><span class="step-number">02</span><svg class="process-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="2.7"/></svg></div><h3>人工确认一次</h3><p>检查样例产出是否符合预期，确认这次流程值得被保留。</p><span class="process-action">动作：核对并确认</span></li>
        <li class="process-card"><div class="process-meta"><span class="step-number">03</span><svg class="process-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M7 3h10v4H7zM5 7h14v14H5zM9 12h6M9 16h4"/></svg></div><h3>固化为技能</h3><p>保存固定脚本和 manifest，把输入点与产出方式写清楚。</p><span class="process-action">动作：冻结脚本 + manifest</span></li>
        <li class="process-card"><div class="process-meta"><span class="step-number">04</span><svg class="process-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8zM5 17v4M3 19h4"/></svg></div><h3>填输入并召唤</h3><p>替换输入文件或内容，点击「召唤」，即可复现已确认的流程。</p><span class="process-action">动作：填输入 → 召唤</span></li>
      </ol>
    </div>
  </section>

  <section id="features" class="container section" aria-labelledby="scenarios-title">
    <div class="section-heading">
      <div class="kicker">USE CASES</div>
      <h2 id="scenarios-title">从官方 PDF 技能开始</h2>
      <p>开箱即用的文档能力，以及更多可以由你固化的重复工作。</p>
    </div>
    <div class="use-case-grid">
      <article class="use-card">
        <div class="use-card-top"><span class="use-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M6 2.5h8l4 4V21H6zM14 2.5v4h4M9 11h6M9 15h6M9 18h4"/></svg></span><span class="use-tag official">官方技能 · 开箱即用</span></div>
        <h3>PDF 文档处理</h3><p>使用官方 PDF 合并与拆分技能，按固定流程处理本地文档。</p>
        <div class="use-example">内置能力<span>合并多个 PDF / 拆分 PDF</span></div>
      </article>
      <article class="use-card">
        <div class="use-card-top"><span class="use-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg></span><span class="use-tag">场景示例 · 需自行固化</span></div>
        <h3>报表自动化</h3><p>把已确认的数据整理与报表生成脚本固化，下次替换输入即可复现。</p>
        <div class="use-example">适合固化的流程<span>固定格式的周期性报表</span></div>
      </article>
      <article class="use-card">
        <div class="use-card-top"><span class="use-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M3 7h7l2 2h9v11H3zM3 7V4h7l2 3M8 14h8M12 10v8"/></svg></span><span class="use-tag">场景示例 · 需自行固化</span></div>
        <h3>文件批处理</h3><p>将重复的文件整理与转换脚本做成技能，减少每次重新配置的工作。</p>
        <div class="use-example">适合固化的流程<span>规则明确、反复执行的批处理</span></div>
      </article>
    </div>
  </section>

  <section class="container closing" aria-labelledby="closing-title">
    <div><h2 id="closing-title">下一次，不必再让 AI 重做。</h2><p>把验证过的好结果留在本机，变成随时可用的技能。</p></div>
    <a class="btn btn-primary btn-lg" href="/login">打开工作台<svg width="17" height="17" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 10h12M11 5l5 5-5 5"/></svg></a>
  </section>
</main>

<footer class="site-footer">
  <div class="container footer-main">
    <div class="footer-brand">
      <a class="brand" href="/" aria-label="workon 首页"><svg width="29" height="29" viewBox="0 0 34 34" aria-hidden="true"><rect x="1" y="1" width="32" height="32" rx="9" fill="#ff7a1a"/><path d="M10 10h6v6h-6zM18 18h6v6h-6zM18 10h6M10 18v6h6" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg><span class="brand-name">workon</span></a>
      <p>开源、本地优先的 AI 产出冻结层。</p>
    </div>
    <nav class="footer-links" aria-label="页脚导航"><a href="#start">快速开始</a><a href="#how">工作原理</a><a href="#features">应用场景</a><a href="https://github.com/joutaojian/workon" target="_blank" rel="noopener noreferrer">GitHub<svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M5 11 11 5M5 5h6v6"/></svg></a></nav>
  </div>
  <div class="container footer-bottom"><span>workon · AI 做一次，人确认一次</span><span>MIT LICENSE · PYTHON 3.9+</span></div>
</footer>
<script>
(function () {
  var status = document.getElementById('copy-status');
  var buttons = document.querySelectorAll('[data-copy-button]');
  Array.prototype.forEach.call(buttons, function (button) {
    var source = document.getElementById(button.getAttribute('data-copy-button'));
    if (!source) return;
    var command = Array.prototype.map.call(
      source.querySelectorAll('.command'),
      function (line) { return line.textContent; }
    ).join('\n');
    var label = button.querySelector('.copy-label');
    var timer;

    function fallbackCopy() {
      var textarea = document.createElement('textarea');
      textarea.value = command;
      textarea.setAttribute('readonly', '');
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      var copied = document.execCommand('copy');
      document.body.removeChild(textarea);
      if (!copied) throw new Error('copy failed');
    }

    button.addEventListener('click', async function () {
      window.clearTimeout(timer);
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(command);
        } else {
          fallbackCopy();
        }
        label.textContent = '已复制';
        status.textContent = '这段话已复制到剪贴板。';
        timer = window.setTimeout(function () { label.textContent = '复制这段话'; }, 2200);
      } catch (error) {
        label.textContent = '请手动复制';
        status.textContent = '自动复制失败，请手动选择上面这段话。';
      }
    });
  });
</script>
</body>
</html>"""


LOGIN_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="登录 workon 本地技能工作台，召唤已固化的技能，确定性复现 AI 产出。">
<meta name="theme-color" content="#14110f">
<meta name="robots" content="noindex">
<title>登录工作台 · workon</title>
<style>
:root{
  --bg:#14110f;
  --surface:#1e1a17;
  --surface-soft:#262019;
  --ink:#fff4e8;
  --muted:#a3928a;
  --faint:#9a8a7e;
  --line:#332a22;
  --line-strong:#4a3d31;
  --accent:#ff7a1a;
  --accent-dark:#e8590c;
  --accent-soft:#2b1d0e;
  --accent-line:#5c3a17;
  --error:#e5484d;
  --error-bg:#2b1412;
  --error-line:#5a2420;
  --mono:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{
  min-width:280px;min-height:100vh;background:var(--bg);color:var(--ink);
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  line-height:1.65;-webkit-font-smoothing:antialiased;
}
a{color:inherit;text-decoration:none}
button,input{font:inherit}
a:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid rgba(255,122,26,.32);outline-offset:4px}
::selection{background:#42301c;color:var(--ink)}
svg{display:block;flex:none}
.login-page{position:relative;min-height:100vh;min-height:100svh}
.login-header{
  position:absolute;top:0;left:50%;transform:translateX(-50%);
  width:min(1180px,calc(100% - 64px));min-height:80px;
  display:flex;align-items:center;gap:24px;
}
.brand{display:inline-flex;align-items:center;gap:10px;flex:none}
.brand-name{font-size:22px;font-weight:750;line-height:1;letter-spacing:-.7px}
.header-divider{width:1px;height:19px;background:var(--line-strong)}
.back-link{display:inline-flex;align-items:center;gap:6px;color:var(--muted);font-size:13px;font-weight:550;transition:color .18s ease}
.back-link:hover{color:var(--accent)}
.login-main{min-height:100vh;min-height:100svh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:116px 24px 42px}
.login-card{width:100%;max-width:430px;padding:35px 34px 29px;border:1px solid var(--line);border-radius:12px;background:var(--surface);box-shadow:0 10px 30px rgba(0,0,0,.34),0 1px 3px rgba(0,0,0,.24)}
.local-badge{display:inline-flex;align-items:center;gap:7px;color:var(--accent-dark);font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:.1em}
.local-badge svg{width:14px;height:14px}
.login-card h1{margin-top:17px;font-size:28px;font-weight:740;line-height:1.35;letter-spacing:-.8px}
.subtitle{margin-top:8px;color:var(--muted);font-size:13px}
.login-form{margin-top:28px;padding-top:25px;border-top:1px solid var(--line)}
.field-label{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px;font-size:13px;font-weight:650}
.field-label span{color:var(--faint);font-size:10px;font-weight:450}
.password-field{position:relative}
.password-icon{position:absolute;left:13px;top:50%;transform:translateY(-50%);color:#98897b;pointer-events:none}
input[type=password]{
  display:block;width:100%;height:47px;padding:11px 13px 11px 41px;
  border:1px solid var(--line-strong);border-radius:7px;background:#221b15;color:var(--ink);
  font-size:14px;outline:none;transition:border-color .18s ease,box-shadow .18s ease,background .18s ease;
}
input[type=password]::placeholder{color:#98897b}
input[type=password]:hover{border-color:#6b5c4e}
input[type=password]:focus{border-color:var(--accent);background:#1e1a17;box-shadow:0 0 0 3px rgba(255,122,26,.15)}
.password-field:focus-within .password-icon{color:var(--accent)}
.login-hint{display:flex;align-items:flex-start;gap:8px;margin-top:13px;color:var(--muted);font-size:11px;line-height:1.75}
.login-hint svg{margin-top:3px;color:var(--accent)}
.login-hint code{padding:1px 4px;border:1px solid var(--accent-line);border-radius:3px;background:var(--accent-soft);color:var(--accent-dark);font-family:var(--mono);font-size:11px;font-weight:700}
.error-msg{display:flex;align-items:flex-start;gap:7px;margin-top:14px;padding:9px 11px;border:1px solid var(--error-line);border-radius:6px;background:var(--error-bg);color:var(--error);font-size:12px;line-height:1.6}
.error-msg:empty{display:none}
.btn-login{
  width:100%;min-height:47px;display:flex;align-items:center;justify-content:center;gap:9px;margin-top:22px;
  padding:11px 18px;border:1px solid var(--accent);border-radius:7px;background:var(--accent);color:#fff;
  font-size:14px;font-weight:650;cursor:pointer;box-shadow:0 1px 2px rgba(0,0,0,.35);
  transition:background .18s ease,border-color .18s ease,box-shadow .18s ease;
}
.btn-login:hover{background:var(--accent-dark);border-color:var(--accent-dark);box-shadow:0 3px 8px rgba(0,0,0,.40)}
.trust-note{display:flex;align-items:flex-start;gap:9px;margin-top:24px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted)}
.trust-note > svg{margin-top:2px;color:var(--accent)}
.trust-note strong{display:block;color:#d8cabd;font-size:11px;font-weight:650}
.trust-note p{margin-top:2px;font-size:10px;line-height:1.7}
.login-meta{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:9px;margin-top:20px;color:var(--faint);font-family:var(--mono);font-size:10px}
.meta-dot{width:3px;height:3px;border-radius:50%;background:#5a4d42}
.login-meta a{transition:color .18s ease}
.login-meta a:hover{color:var(--accent)}
@media (max-width:760px){
  .login-header{width:calc(100% - 36px);min-height:70px;gap:17px}
  .brand-name{font-size:20px}
  .brand svg{width:30px;height:30px}
  .back-link{font-size:12px}
  .login-main{padding:100px 18px 32px}
  .login-card{max-width:420px;padding:30px 27px 26px}
}
@media (max-width:420px){
  .login-header{gap:12px}
  .header-divider{height:16px}
  .login-main{padding-inline:14px}
  .login-card{padding:27px 22px 24px}
  .login-card h1{font-size:26px}
}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none !important;transition:none !important;scroll-behavior:auto !important}
}
</style>
</head>
<body>
<div class="login-page">
  <header class="login-header">
    <a class="brand" href="/" aria-label="workon 首页"><svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true"><rect x="1" y="1" width="32" height="32" rx="9" fill="#ff7a1a"/><path d="M10 10h6v6h-6zM18 18h6v6h-6zM18 10h6M10 18v6h6" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg><span class="brand-name">workon</span></a>
    <span class="header-divider" aria-hidden="true"></span>
    <a class="back-link" href="/"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M16 10H4M9 5l-5 5 5 5"/></svg>返回首页</a>
  </header>

  <main class="login-main">
    <section class="login-card" aria-labelledby="login-title">
      <div class="local-badge"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><rect x="2" y="2" width="12" height="12" rx="2"/><path d="M5 6h6M5 9h4"/></svg>LOCAL WORKSPACE</div>
      <h1 id="login-title">登录工作台</h1>
      <p class="subtitle">输入访问密码，继续使用你的本地技能。</p>
      <form class="login-form" method="post" action="/login">
        <label class="field-label" for="password">访问密码<span>本机访问凭证</span></label>
        <div class="password-field">
          <svg class="password-icon" width="17" height="17" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="4" y="8" width="12" height="9" rx="2"/><path d="M7 8V6a3 3 0 0 1 6 0v2M10 12v2"/></svg>
          <input type="password" id="password" name="password" placeholder="请输入访问密码" autocomplete="current-password" required autofocus>
        </div>
        <div class="login-hint"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><circle cx="8" cy="8" r="6"/><path d="M8 7v4M8 4.5v1"/></svg><span>首次使用？默认密码为 <code>workon</code>。登录后请在「设置」中尽快修改。</span></div>
        <div class="error-msg" role="alert">__ERROR_MSG__</div>
        <button type="submit" class="btn-login">进入工作台<svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 10h12M11 5l5 5-5 5"/></svg></button>
      </form>
      <div class="trust-note"><svg width="17" height="17" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M10 2.5 16 5v4.5c0 3.8-2.5 6.5-6 8-3.5-1.5-6-4.2-6-8V5z"/><path d="m7 10 2 2 4-4"/></svg><div><strong>本地运行，数据留在本机</strong><p>技能复现零 Token、零联网，不再调用 AI。</p></div></div>
    </section>
    <div class="login-meta"><span>MIT LICENSE</span><span class="meta-dot" aria-hidden="true"></span><span>PYTHON 3.9+</span><span class="meta-dot" aria-hidden="true"></span><a href="https://github.com/joutaojian/workon" target="_blank" rel="noopener noreferrer">GITHUB</a></div>
  </main>
</div>
</body>
</html>"""
