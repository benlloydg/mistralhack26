<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TriageNet v2 — PRD</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

/* Dark theme (default) */
:root, [data-theme="dark"] {
  --red: #ff2d46;
  --red-dim: #ff2d4618;
  --red-glow: #ff2d4644;
  --amber: #ffb020;
  --amber-dim: #ffb02018;
  --green: #00e676;
  --green-dim: #00e67618;
  --blue: #2d9cff;
  --blue-dim: #2d9cff18;
  --blue-glow: #2d9cff33;
  --purple: #a855f7;
  --purple-dim: #a855f718;
  --white: #f0f2f5;
  --text: #c8cdd8;
  --text-dim: #5a6178;
  --text-bright: #ffffff;
  --bg: #08090e;
  --bg-panel: #0c0e15;
  --bg-card: #10121c;
  --bg-card-hover: #141828;
  --border: #1c2035;
  --border-active: #2d9cff33;
  --ambient-r: #ff2d4606;
  --ambient-b: #2d9cff04;
  --grid-opacity: 0.025;
  --nav-bg: #08090ecc;
  --severity-high-bg: #ef444420;
  --severity-med-bg: #f59e0b20;
  --severity-low-bg: #22c55e20;
  --terminal-bg: #060810;
  --callout-border-alpha: 15;
}

/* Light theme */
[data-theme="light"] {
  --red: #dc2636;
  --red-dim: #dc263612;
  --red-glow: #dc263618;
  --amber: #d97706;
  --amber-dim: #d9770612;
  --green: #16a34a;
  --green-dim: #16a34a12;
  --blue: #2563eb;
  --blue-dim: #2563eb12;
  --blue-glow: #2563eb18;
  --purple: #7c3aed;
  --purple-dim: #7c3aed12;
  --white: #1a1a2e;
  --text: #3a3a4a;
  --text-dim: #7a7a8a;
  --text-bright: #111118;
  --bg: #faf9f7;
  --bg-panel: #f2f1ee;
  --bg-card: #ffffff;
  --bg-card-hover: #f8f7f5;
  --border: #e5e4e0;
  --border-active: #2563eb28;
  --ambient-r: #dc263604;
  --ambient-b: #2563eb03;
  --grid-opacity: 0.04;
  --nav-bg: #faf9f7dd;
  --severity-high-bg: #ef444410;
  --severity-med-bg: #f59e0b10;
  --severity-low-bg: #22c55e10;
  --terminal-bg: #f5f4f1;
  --callout-border-alpha: 25;
}

html { scroll-behavior: smooth; }
body { background: var(--bg); color: var(--text); font-family: 'Space Grotesk', sans-serif; font-weight: 400; line-height: 1.7; overflow-x: hidden; transition: background 0.4s, color 0.4s; }

.ambient { position: fixed; inset: 0; z-index: 0; pointer-events: none; background: radial-gradient(ellipse 60% 40% at 15% 0%, var(--ambient-r) 0%, transparent 60%), radial-gradient(ellipse 50% 50% at 85% 100%, var(--ambient-b) 0%, transparent 60%), var(--bg); transition: background 0.4s; }
.grid-overlay { position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: var(--grid-opacity); background-image: linear-gradient(var(--text-dim) 1px, transparent 1px), linear-gradient(90deg, var(--text-dim) 1px, transparent 1px); background-size: 60px 60px; transition: opacity 0.4s; }

.container { position: relative; z-index: 2; max-width: 1080px; margin: 0 auto; padding: 0 24px; }

/* HERO */
.hero { min-height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; padding: 80px 24px; max-width: 1080px; margin: 0 auto; position: relative; }
.hero-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 500; color: var(--red); letter-spacing: 0.3em; text-transform: uppercase; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; opacity: 0; animation: fadeIn 0.8s 0.2s forwards; }
.hero-eyebrow::before { content: ''; width: 8px; height: 8px; background: var(--red); border-radius: 50%; animation: pulse 2s infinite; }
.hero-title { font-family: 'Instrument Serif', serif; font-weight: 400; font-size: clamp(3rem, 8vw, 6.5rem); color: var(--text-bright); line-height: 1.05; letter-spacing: -0.03em; opacity: 0; animation: fadeSlideUp 1s 0.4s forwards; }
.hero-title em { font-style: italic; color: var(--red); text-shadow: 0 0 60px var(--red-glow); transition: color 0.4s; }
.hero-sub { font-weight: 300; font-size: clamp(1rem, 2vw, 1.25rem); color: var(--text-dim); max-width: 580px; margin-top: 28px; line-height: 1.8; opacity: 0; animation: fadeSlideUp 1s 0.7s forwards; }
.hero-badges { display: flex; gap: 10px; margin-top: 36px; flex-wrap: wrap; opacity: 0; animation: fadeSlideUp 1s 1s forwards; }
.badge { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; font-weight: 500; letter-spacing: 0.12em; text-transform: uppercase; padding: 7px 14px; border-radius: 3px; }
.badge.red { color: var(--red); background: var(--red-dim); border: 1px solid #ff2d4622; }
.badge.blue { color: var(--blue); background: var(--blue-dim); border: 1px solid #2d9cff22; }
.badge.amber { color: var(--amber); background: var(--amber-dim); border: 1px solid #ffb02022; }
.hero-stat-row { display: flex; gap: 48px; margin-top: 48px; flex-wrap: wrap; opacity: 0; animation: fadeSlideUp 1s 1.2s forwards; }
.hero-stat-value { font-family: 'Instrument Serif', serif; font-size: 2.4rem; color: var(--text-bright); line-height: 1; }
.hero-stat-value.red { color: var(--red); } .hero-stat-value.blue { color: var(--blue); } .hero-stat-value.amber { color: var(--amber); }
.hero-stat-label { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: var(--text-dim); letter-spacing: 0.15em; text-transform: uppercase; margin-top: 6px; }
.scroll-hint { position: absolute; bottom: 32px; left: 24px; font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: var(--text-dim); letter-spacing: 0.15em; text-transform: uppercase; display: flex; align-items: center; gap: 8px; opacity: 0; animation: fadeIn 1s 2s forwards; }
.scroll-hint .arrow { animation: scrollBounce 2s infinite; display: inline-block; }

/* NAV */
.nav { position: sticky; top: 0; z-index: 100; background: var(--nav-bg); backdrop-filter: blur(24px); border-bottom: 1px solid var(--border); padding: 0 24px; transition: background 0.4s; }
.nav-inner { max-width: 1080px; margin: 0 auto; display: flex; align-items: center; gap: 6px; overflow-x: auto; padding: 10px 0; scrollbar-width: none; }
.nav-inner::-webkit-scrollbar { display: none; }
.nav-link { font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; font-weight: 500; color: var(--text-dim); text-decoration: none; letter-spacing: 0.1em; text-transform: uppercase; padding: 5px 12px; border-radius: 3px; white-space: nowrap; transition: all 0.2s; border: 1px solid transparent; }
.nav-link:hover, .nav-link.active { color: var(--red); border-color: var(--red-dim); background: var(--red-dim); }

/* SECTIONS */
section { padding: 80px 0; opacity: 0; transform: translateY(24px); transition: all 0.7s cubic-bezier(0.16, 1, 0.3, 1); }
section.visible { opacity: 1; transform: translateY(0); }
.s-label { font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; font-weight: 500; color: var(--red); letter-spacing: 0.25em; text-transform: uppercase; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
.s-label::before { content: ''; width: 20px; height: 1px; background: var(--red); }
.s-title { font-family: 'Instrument Serif', serif; font-weight: 400; font-size: clamp(1.5rem, 4vw, 2.5rem); color: var(--text-bright); line-height: 1.15; letter-spacing: -0.02em; margin-bottom: 28px; }
.s-body { font-size: 1rem; color: var(--text); line-height: 1.85; max-width: 720px; }
.s-body + .s-body { margin-top: 16px; }
.hl { color: var(--red); font-weight: 600; } .hl-blue { color: var(--blue); font-weight: 600; } .hl-amber { color: var(--amber); font-weight: 600; } .hl-green { color: var(--green); font-weight: 600; } .hl-purple { color: var(--purple); font-weight: 600; }

.divider { height: 1px; background: linear-gradient(90deg, transparent, var(--border), #ff2d4611, var(--border), transparent); }

/* CARDS */
.card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-top: 28px; }
.card-grid-3 { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
.card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; padding: 24px; position: relative; transition: all 0.3s; overflow: hidden; }
.card:hover { border-color: var(--border-active); background: var(--bg-card-hover); transform: translateY(-1px); box-shadow: 0 8px 24px #00000022; }
.card-stripe { position: absolute; top: 0; left: 0; width: 3px; height: 100%; }
.card-stripe.red { background: var(--red); } .card-stripe.blue { background: var(--blue); } .card-stripe.amber { background: var(--amber); } .card-stripe.green { background: var(--green); } .card-stripe.purple { background: var(--purple); }
.card-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 0.58rem; font-weight: 500; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 10px; }
.card-eyebrow.red { color: var(--red); } .card-eyebrow.blue { color: var(--blue); } .card-eyebrow.amber { color: var(--amber); } .card-eyebrow.green { color: var(--green); } .card-eyebrow.purple { color: var(--purple); }
.card-title { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 1rem; color: var(--text-bright); margin-bottom: 10px; }
.card-body { font-size: 0.88rem; color: var(--text-dim); line-height: 1.7; }

/* TABLES */
.table-wrap { overflow-x: auto; margin-top: 24px; border-radius: 6px; border: 1px solid var(--border); }
table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
thead th { font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; font-weight: 600; color: var(--red); letter-spacing: 0.15em; text-transform: uppercase; padding: 14px 18px; text-align: left; background: var(--bg-card); border-bottom: 1px solid var(--border); }
tbody td { padding: 14px 18px; border-bottom: 1px solid var(--border); color: var(--text); vertical-align: top; }
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover { background: var(--bg-card); }
td:first-child { font-weight: 500; color: var(--text-bright); }

/* TERMINAL */
.terminal { background: var(--terminal-bg); border: 1px solid var(--border); border-radius: 6px; margin-top: 24px; overflow: hidden; transition: background 0.4s; }
.terminal-bar { background: var(--bg-card); border-bottom: 1px solid var(--border); padding: 8px 16px; display: flex; align-items: center; gap: 8px; }
.terminal-dot { width: 8px; height: 8px; border-radius: 50%; }
.terminal-dot.r { background: #ff5f57; } .terminal-dot.y { background: #ffbd2e; } .terminal-dot.g { background: #28ca41; }
.terminal-title { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: var(--text-dim); letter-spacing: 0.1em; margin-left: 8px; }
.terminal-body { padding: 20px; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; line-height: 1.9; color: var(--text-dim); overflow-x: auto; white-space: pre; }
.t-red { color: var(--red); } .t-blue { color: var(--blue); } .t-amber { color: var(--amber); } .t-green { color: var(--green); } .t-purple { color: var(--purple); } .t-white { color: var(--text-bright); } .t-dim { color: var(--text-dim); }

/* THEME TOGGLE */
.theme-toggle {
  position: fixed; top: 16px; right: 20px; z-index: 200;
  display: flex; align-items: center; gap: 8px;
  padding: 7px 14px; border-radius: 20px;
  background: var(--bg-card); border: 1px solid var(--border);
  color: var(--text-dim); cursor: pointer; font-size: 0.65rem;
  font-family: 'JetBrains Mono', monospace; letter-spacing: 0.08em;
  text-transform: uppercase; transition: all 0.3s;
  backdrop-filter: blur(12px);
}
.theme-toggle:hover { border-color: var(--border-active); color: var(--text); }
.theme-toggle svg { width: 14px; height: 14px; }

/* TIMELINE */
.timeline { margin-top: 32px; position: relative; padding-left: 36px; }
.timeline::before { content: ''; position: absolute; left: 8px; top: 0; bottom: 0; width: 2px; background: linear-gradient(180deg, var(--red), var(--amber), var(--blue), var(--purple), var(--green)); border-radius: 2px; }
.tl-item { position: relative; margin-bottom: 40px; }
.tl-item:last-child { margin-bottom: 0; }
.tl-dot { position: absolute; left: -33px; top: 4px; width: 13px; height: 13px; border-radius: 50%; border: 2px solid var(--bg); }
.tl-dot.red { background: var(--red); box-shadow: 0 0 14px var(--red-glow); }
.tl-dot.amber { background: var(--amber); box-shadow: 0 0 14px #ffb02044; }
.tl-dot.blue { background: var(--blue); box-shadow: 0 0 14px var(--blue-glow); }
.tl-dot.purple { background: var(--purple); box-shadow: 0 0 14px #a855f744; }
.tl-dot.green { background: var(--green); box-shadow: 0 0 14px #00e67644; }
.tl-time { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; font-weight: 500; letter-spacing: 0.15em; margin-bottom: 6px; }
.tl-time.red { color: var(--red); } .tl-time.amber { color: var(--amber); } .tl-time.blue { color: var(--blue); } .tl-time.purple { color: var(--purple); } .tl-time.green { color: var(--green); }
.tl-title { font-family: 'Instrument Serif', serif; font-weight: 400; font-size: 1.2rem; color: var(--text-bright); margin-bottom: 12px; }
.tl-body { font-size: 0.9rem; color: var(--text-dim); line-height: 1.8; }
.tl-body em { color: var(--text); font-style: italic; }

/* AGENT CARDS */
.agent-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 28px; }
.agent-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; padding: 20px; }
.agent-status { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; animation: pulse 2s infinite; }
.status-dot.active { background: var(--green); box-shadow: 0 0 8px var(--green); }
.status-dot.standby { background: var(--amber); box-shadow: 0 0 8px var(--amber); }
.agent-name { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 600; color: var(--text-bright); letter-spacing: 0.08em; text-transform: uppercase; }
.agent-role { font-size: 0.82rem; color: var(--text-dim); margin-bottom: 10px; }
.agent-tag { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; padding: 3px 8px; border-radius: 2px; display: inline-block; margin-right: 4px; margin-bottom: 4px; }
.agent-tag.blue { color: var(--blue); background: var(--blue-dim); }
.agent-tag.amber { color: var(--amber); background: var(--amber-dim); }
.agent-tag.red { color: var(--red); background: var(--red-dim); }
.agent-tag.green { color: var(--green); background: var(--green-dim); }
.agent-tag.purple { color: var(--purple); background: var(--purple-dim); }

/* CALLOUT */
.callout { background: var(--terminal-bg); border-left: 3px solid var(--red); padding: 20px 24px; margin: 24px 0; border-radius: 0 6px 6px 0; transition: background 0.4s; }
.callout.amber { border-left-color: var(--amber); } .callout.blue { border-left-color: var(--blue); } .callout.green { border-left-color: var(--green); }
.callout-label { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; font-weight: 600; color: var(--red); letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 8px; }
.callout-label.amber { color: var(--amber); } .callout-label.blue { color: var(--blue); } .callout-label.green { color: var(--green); }
.callout-text { font-size: 0.95rem; color: var(--text); line-height: 1.75; font-style: italic; }

/* PRIORITY */
.priority-section { margin-top: 28px; }
.priority-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.p-tag { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; padding: 4px 10px; border-radius: 3px; }
.p-tag.p1 { color: var(--red); background: var(--red-dim); } .p-tag.p2 { color: var(--amber); background: var(--amber-dim); } .p-tag.p3 { color: var(--text-dim); background: #5a617811; }
.p-label { font-weight: 600; font-size: 0.95rem; color: var(--text-bright); }
.p-list { list-style: none; padding: 0; }
.p-list li { font-size: 0.9rem; color: var(--text-dim); line-height: 1.75; padding: 5px 0 5px 18px; position: relative; }
.p-list li::before { content: '›'; position: absolute; left: 0; font-weight: 700; }
.p-list.red li::before { color: var(--red); } .p-list.amber li::before { color: var(--amber); } .p-list.dim li::before { color: var(--text-dim); }

/* SUBMISSION */
.submission { background: var(--bg-card); border: 1px solid var(--border-active); border-radius: 6px; padding: 40px; margin-top: 28px; position: relative; }
.submission::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, var(--red), var(--blue)); }
.sub-title { font-family: 'Instrument Serif', serif; font-size: 1.4rem; color: var(--text-bright); margin-bottom: 20px; }
.sub-text { font-size: 0.92rem; color: var(--text); line-height: 1.85; margin-bottom: 14px; }
.sub-tracks { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px; }

footer { text-align: center; padding: 60px 24px 40px; border-top: 1px solid var(--border); }
.footer-title { font-family: 'Instrument Serif', serif; font-size: 1.3rem; color: var(--text-dim); }
.footer-sub { font-family: 'JetBrains Mono', monospace; font-size: 0.62rem; color: var(--text-dim); letter-spacing: 0.15em; margin-top: 8px; }

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeSlideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes scrollBounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(4px); } }

@media (max-width: 768px) {
  .hero { padding: 60px 16px; }
  .card-grid, .agent-grid { grid-template-columns: 1fr; }
  .container { padding: 0 16px; }
  section { padding: 60px 0; }
  .hero-stat-row { gap: 28px; }
  .submission { padding: 24px; }
}
</style>
</head>
<body>

<div class="ambient"></div>
<div class="grid-overlay"></div>

<!-- Theme Toggle -->
<button class="theme-toggle" id="themeToggle" onclick="toggleTheme()">
  <svg id="sunIcon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:none"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
  <svg id="moonIcon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
  <span id="themeLabel">Light</span>
</button>

<!-- HERO -->
<header class="hero">
  <div class="hero-eyebrow">Multi-Incident Active — 3 Callers — 4 Languages</div>
  <h1 class="hero-title">Triage<em>Net</em></h1>
  <p class="hero-sub">A multimodal, multi-agent emergency operating system. Multiple callers. Multiple languages. One evolving case file. Zero human bottleneck.</p>
  <div class="hero-badges">
    <span class="badge red">Mistral API Track</span>
    <span class="badge blue">ElevenLabs Challenge</span>
    <span class="badge amber">Hugging Face Best Agent</span>
  </div>
  <div class="hero-stat-row">
    <div><div class="hero-stat-value red">3</div><div class="hero-stat-label">Concurrent Callers</div></div>
    <div><div class="hero-stat-value blue">4</div><div class="hero-stat-label">Languages Live</div></div>
    <div><div class="hero-stat-value amber">7</div><div class="hero-stat-label">Autonomous Agents</div></div>
  </div>
  <div class="scroll-hint"><span class="arrow">↓</span> Full system specification</div>
</header>

<!-- NAV -->
<nav class="nav">
  <div class="nav-inner">
    <a href="#problem" class="nav-link">Problem</a>
    <a href="#system" class="nav-link">Architecture</a>
    <a href="#agents" class="nav-link">Agents</a>
    <a href="#callers" class="nav-link">Multi-Caller</a>
    <a href="#casefile" class="nav-link">Case File</a>
    <a href="#demo" class="nav-link">Demo Script</a>
    <a href="#ui" class="nav-link">UI Layout</a>
    <a href="#elevenlabs" class="nav-link">ElevenLabs</a>
    <a href="#mistral" class="nav-link">Mistral</a>
    <a href="#stack" class="nav-link">Stack</a>
    <a href="#scope" class="nav-link">MVP Scope</a>
    <a href="#engineering" class="nav-link">Engineering</a>
    <a href="#submission" class="nav-link">Submission</a>
    <a href="#risks" class="nav-link">Risks</a>
  </div>
</nav>

<main class="container">

  <!-- 1. PROBLEM -->
  <section id="problem">
    <div class="s-label">01 — The Problem</div>
    <h2 class="s-title">Three callers. Three languages. One crash. No one can talk to each other.</h2>
    <p class="s-body"><span class="hl">25 million people</span> in the US have limited English proficiency. When they call 911, they wait for a human interpreter. But real emergencies don't have one caller — they have many. A panicked wife in Spanish. A bystander in Mandarin. A shopkeeper in French. Each sees a different piece of the picture. No human operator can handle all three simultaneously in three languages while also watching a video feed.</p>
    <p class="s-body">TriageNet can. It <span class="hl-blue">speaks every language</span> simultaneously, <span class="hl-amber">sees the scene</span> through video analysis, <span class="hl-green">merges intelligence</span> from multiple callers into one evolving case file, and <span class="hl-purple">dispatches autonomously</span> — medical, fire, police — each in the responder's operating language, all in parallel.</p>
    <div class="callout">
      <div class="callout-label">The Mic Drop Line</div>
      <div class="callout-text">"In 120 seconds, TriageNet handled three callers in three languages, detected an escalating fire via computer vision, corroborated a human report with visual evidence, proactively warned two callers to evacuate, dispatched four response units in two languages, and built a complete case file with an auto-updating action plan. We didn't build a chatbot. We built the future of civic infrastructure."</div>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 2. SYSTEM ARCHITECTURE -->
  <section id="system">
    <div class="s-label">02 — System Architecture</div>
    <h2 class="s-title">Decoupled agents. Shared state. Every call is live.</h2>
    <p class="s-body">TriageNet is a decoupled multi-agent system built on <span class="hl">Mistral</span> and <span class="hl-blue">ElevenLabs</span>. Each agent operates autonomously — voice agents keep callers calm while the vision agent analyzes the scene, while the triage agent classifies severity and updates the action plan, while dispatch agents contact responders. No agent waits for another. They communicate through a shared state object.</p>

    <div class="terminal">
      <div class="terminal-bar">
        <div class="terminal-dot r"></div><div class="terminal-dot y"></div><div class="terminal-dot g"></div>
        <span class="terminal-title">triagenet / multi-caller-architecture</span>
      </div>
      <div class="terminal-body">
<span class="t-dim">┌──────────────────────────────────────────────────────────────────┐</span>
<span class="t-dim">│</span>  <span class="t-red">CALLER 1 (ES)</span>    <span class="t-amber">CALLER 2 (ZH)</span>    <span class="t-blue">CALLER 3 (FR)</span>          <span class="t-dim">│</span>
<span class="t-dim">│</span>      <span class="t-dim">│</span>                  <span class="t-dim">│</span>                  <span class="t-dim">│</span>                <span class="t-dim">│</span>
<span class="t-dim">│</span>      <span class="t-dim">▼</span>                  <span class="t-dim">▼</span>                  <span class="t-dim">▼</span>                <span class="t-dim">│</span>
<span class="t-dim">│</span>  <span class="t-blue">[EL Transcribe]</span>  <span class="t-blue">[EL Transcribe]</span>  <span class="t-blue">[EL Transcribe]</span>        <span class="t-dim">│</span>
<span class="t-dim">│</span>      <span class="t-dim">│</span>                  <span class="t-dim">│</span>                  <span class="t-dim">│</span>                <span class="t-dim">│</span>
<span class="t-dim">│</span>      <span class="t-dim">▼</span>                  <span class="t-dim">▼</span>                  <span class="t-dim">▼</span>                <span class="t-dim">│</span>
<span class="t-dim">│</span>  <span class="t-red">[Voice Agent]</span>    <span class="t-amber">[Voice Agent]</span>    <span class="t-blue">[Voice Agent]</span>          <span class="t-dim">│</span>
<span class="t-dim">│</span>  <span class="t-dim">EL Agents+ES</span>     <span class="t-dim">EL Agents+ZH</span>     <span class="t-dim">EL Agents+FR</span>           <span class="t-dim">│</span>
<span class="t-dim">│</span>      <span class="t-dim">│</span>                  <span class="t-dim">│</span>                  <span class="t-dim">│</span>                <span class="t-dim">│</span>
<span class="t-dim">│</span>      <span class="t-dim">└──────────────────┼──────────────────┘</span>                <span class="t-dim">│</span>
<span class="t-dim">│</span>                         <span class="t-dim">▼</span>                                       <span class="t-dim">│</span>
<span class="t-dim">│</span>          <span class="t-white">[ SHARED STATE + CASE FILE ]</span>  ←──  <span class="t-purple">[VISION AGENT]</span>  <span class="t-dim">│</span>
<span class="t-dim">│</span>          <span class="t-dim">Cross-language entity merge</span>        <span class="t-dim">Pixtral/3s</span>      <span class="t-dim">│</span>
<span class="t-dim">│</span>                         <span class="t-dim">│</span>                                       <span class="t-dim">│</span>
<span class="t-dim">│</span>                         <span class="t-dim">▼</span>                                       <span class="t-dim">│</span>
<span class="t-dim">│</span>               <span class="t-red">[ TRIAGE AGENT (Mistral Large) ]</span>                <span class="t-dim">│</span>
<span class="t-dim">│</span>               <span class="t-dim">Severity + Action Plan + Dispatch</span>               <span class="t-dim">│</span>
<span class="t-dim">│</span>                    <span class="t-dim">│          │          │</span>                   <span class="t-dim">│</span>
<span class="t-dim">│</span>                    <span class="t-dim">▼</span>          <span class="t-dim">▼</span>          <span class="t-dim">▼</span>                   <span class="t-dim">│</span>
<span class="t-dim">│</span>              <span class="t-green">[MEDICAL]</span>  <span class="t-amber">[FIRE]</span>    <span class="t-blue">[POLICE]</span>              <span class="t-dim">│</span>
<span class="t-dim">│</span>              <span class="t-dim">EN voice</span>   <span class="t-dim">EN voice</span>  <span class="t-dim">EN voice</span>               <span class="t-dim">│</span>
<span class="t-dim">│</span>              <span class="t-dim">EL Speech</span>  <span class="t-dim">EL Speech</span> <span class="t-dim">EL Speech</span>              <span class="t-dim">│</span>
<span class="t-dim">└──────────────────────────────────────────────────────────────────┘</span>
      </div>
    </div>

    <div class="callout amber">
      <div class="callout-label amber">Key Architectural Insight</div>
      <div class="callout-text">All agents are decoupled through shared state. When Pixtral detects fire, it writes to state. All three voice agents poll state — they simultaneously warn their respective callers in their respective languages. When Caller 2 reports "child in vehicle," the triage agent merges it into the case file and escalates severity, triggering a pediatric dispatch. No agent calls another directly. They communicate through state.</div>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 3. AGENTS -->
  <section id="agents">
    <div class="s-label">03 — Agent Architecture</div>
    <h2 class="s-title">Seven agents. All Mistral-powered. All autonomous.</h2>
    <p class="s-body">Every agent in TriageNet is powered by the <span class="hl">Mistral API</span>. The triage agent and vision agent use <span class="hl">Mistral Large</span> with structured tool calling. Voice agents are <span class="hl-blue">ElevenLabs Conversational Agents</span> backed by Mistral for reasoning. Dispatch agents use Mistral for decision-making with <span class="hl-blue">ElevenLabs Generate Speech</span> for multilingual voice output.</p>

    <div class="agent-grid">
      <div class="agent-card">
        <div class="agent-status"><div class="status-dot active"></div><span class="agent-name">Voice Agent ×3</span></div>
        <div class="agent-role">One per caller. Speaks their language. Keeps them calm. Proactively interrupts on hazard detection. Extracts new intelligence from conversation.</div>
        <span class="agent-tag blue">ElevenLabs Agents</span>
        <span class="agent-tag red">Mistral Reasoning</span>
      </div>
      <div class="agent-card">
        <div class="agent-status"><div class="status-dot active"></div><span class="agent-name">Vision Agent</span></div>
        <div class="agent-role">Screenshots video every 3s. Pixtral extracts scene features, hazards, casualty count. Writes detections + confidence to shared state.</div>
        <span class="agent-tag purple">Pixtral Vision</span>
        <span class="agent-tag red">Mistral API</span>
      </div>
      <div class="agent-card">
        <div class="agent-status"><div class="status-dot active"></div><span class="agent-name">Triage Agent</span></div>
        <div class="agent-role">The brain. Merges intelligence from all sources. Classifies severity. Generates and versions the action plan. Routes dispatch. Escalates on state change.</div>
        <span class="agent-tag red">Mistral Large</span>
        <span class="agent-tag amber">Tool Calling</span>
      </div>
      <div class="agent-card">
        <div class="agent-status"><div class="status-dot standby"></div><span class="agent-name">Medical Dispatch</span></div>
        <div class="agent-role">Contacts hospitals. Communicates patient details in operating language. Dispatches pediatric unit when child detected.</div>
        <span class="agent-tag blue">ElevenLabs Speech</span>
        <span class="agent-tag red">Mistral</span>
      </div>
      <div class="agent-card">
        <div class="agent-status"><div class="status-dot standby"></div><span class="agent-name">Fire Dispatch</span></div>
        <div class="agent-role">Routes nearest engine. Auto-escalates when vision detects fire. Updates responding unit with hazard changes.</div>
        <span class="agent-tag blue">ElevenLabs Speech</span>
        <span class="agent-tag red">Mistral</span>
      </div>
      <div class="agent-card">
        <div class="agent-status"><div class="status-dot standby"></div><span class="agent-name">Police Dispatch</span></div>
        <div class="agent-role">Traffic control and scene security. Coordinates jurisdiction. Structured alert generation.</div>
        <span class="agent-tag red">Mistral</span>
        <span class="agent-tag green">Tool Call</span>
      </div>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 4. MULTI-CALLER -->
  <section id="callers">
    <div class="s-label">04 — Multi-Caller Intelligence</div>
    <h2 class="s-title">Each caller sees a different piece. TriageNet sees everything.</h2>
    <p class="s-body">The breakthrough insight: real emergencies have multiple callers who each contribute unique information. TriageNet doesn't just handle them — it <span class="hl-green">merges their intelligence</span> into a single evolving picture, cross-referencing across languages and corroborating with visual evidence.</p>

    <div class="card-grid">
      <div class="card">
        <div class="card-stripe red"></div>
        <div class="card-eyebrow red">Caller 1 — Spanish</div>
        <div class="card-title">The Wife</div>
        <div class="card-body">Panicked. Reports the crash. Describes location (Market & 5th). Says her husband is trapped. Provides the emotional anchor. The voice agent keeps her calm while extracting details: "How many vehicles? Can you see other people?"</div>
      </div>
      <div class="card">
        <div class="card-stripe amber"></div>
        <div class="card-eyebrow amber">Caller 2 — Mandarin</div>
        <div class="card-title">The Bystander</div>
        <div class="card-body">Across the street. Sees the same crash from a different angle. Reports something Caller 1 didn't: "There's a child in the back seat." System detects same-incident (location match), merges into existing case file. Triage escalates. Pediatric unit dispatched.</div>
      </div>
      <div class="card">
        <div class="card-stripe blue"></div>
        <div class="card-eyebrow blue">Caller 3 — French</div>
        <div class="card-title">The Shopkeeper</div>
        <div class="card-body">Doesn't know about the crash. Reports "smoke coming from a car." Three seconds later, Pixtral confirms: ENGINE FIRE (0.99). The case file updates with corroboration: visual evidence matches human report. Fire dispatch activates.</div>
      </div>
    </div>

    <div class="callout green">
      <div class="callout-label green">Cross-Language Entity Resolution</div>
      <div class="callout-text">When Caller 2 says "小孩在后座" (child in back seat) in Mandarin, and Caller 1 said "mi esposo está atrapado" (my husband is trapped) in Spanish, the triage agent — powered by Mistral Large — resolves these as the same incident (location match), merges the intelligence (2 adults + 1 child), and updates the action plan. This cross-language entity resolution is the core technical differentiator.</div>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 5. CASE FILE -->
  <section id="casefile">
    <div class="s-label">05 — Evolving Case File</div>
    <h2 class="s-title">The case file gets smarter with every second.</h2>
    <p class="s-body">The case file isn't a static report — it's a <span class="hl">living document</span> that the triage agent regenerates every time new intelligence arrives. The action plan versions automatically. Judges watch it evolve from v1 to v2 to v3 in real time.</p>

    <div class="terminal">
      <div class="terminal-bar">
        <div class="terminal-dot r"></div><div class="terminal-dot y"></div><div class="terminal-dot g"></div>
        <span class="terminal-title">triagenet / case-file / TN-2025-00417</span>
      </div>
      <div class="terminal-body">
<span class="t-red">CASE TN-2025-00417</span> │ <span class="t-red">SEVERITY: CRITICAL ▲</span> <span class="t-dim">(escalated 2x)</span>
<span class="t-dim">═══════════════════════════════════════════════════════════</span>
<span class="t-white">INCIDENT:</span>  Vehicle Collision + Engine Fire
<span class="t-white">LOCATION:</span>  Market St & 5th, San Francisco
<span class="t-white">SOURCES:</span>   3 callers <span class="t-dim">(ES, ZH, FR)</span> + 1 CCTV feed
<span class="t-white">CASUALTIES:</span> 2 adults + <span class="t-amber">1 child (Caller 2, 0:30)</span>

<span class="t-blue">TIMELINE:</span>
  <span class="t-dim">00:15</span>  <span class="t-red">Caller 1 (ES)</span> — Vehicle collision reported
  <span class="t-dim">00:18</span>  <span class="t-purple">Vision</span>       — Collision confirmed <span class="t-green">(0.94)</span>
  <span class="t-dim">00:20</span>  <span class="t-white">Triage</span>       — Severity: HIGH
  <span class="t-dim">00:22</span>  <span class="t-green">Medical</span>      — Dispatched → Mass General <span class="t-dim">(EN)</span>
  <span class="t-dim">00:30</span>  <span class="t-amber">Caller 2 (ZH)</span> — <span class="t-amber">Child in vehicle (NEW INTEL)</span>
  <span class="t-dim">00:31</span>  <span class="t-white">Triage</span>       — <span class="t-red">Severity: CRITICAL ▲</span>
  <span class="t-dim">00:33</span>  <span class="t-green">Medical</span>      — Pediatric unit → UCSF Children's <span class="t-dim">(EN)</span>
  <span class="t-dim">00:45</span>  <span class="t-blue">Caller 3 (FR)</span> — Smoke from vehicle reported
  <span class="t-dim">00:48</span>  <span class="t-purple">Vision</span>       — <span class="t-red">ENGINE FIRE</span> <span class="t-green">(0.99)</span>
  <span class="t-dim">00:48</span>  <span class="t-white">Triage</span>       — <span class="t-green">CORROBORATED: Vision + Caller 3</span>
  <span class="t-dim">00:49</span>  <span class="t-red">Voice→C1</span>     — Fire warning issued <span class="t-dim">(ES)</span>
  <span class="t-dim">00:49</span>  <span class="t-amber">Voice→C2</span>     — Evacuation order <span class="t-dim">(ZH)</span>
  <span class="t-dim">00:51</span>  <span class="t-amber">Fire</span>         — Dispatched → Station 4 <span class="t-dim">(EN)</span>

<span class="t-white">ACTION PLAN v3</span> <span class="t-dim">(auto-updated @ 00:51)</span>
  <span class="t-green">✓</span> Ambulance dispatched — AMB-7 — ETA 6 min
  <span class="t-green">✓</span> Pediatric unit dispatched — PED-2 — ETA 9 min
  <span class="t-green">✓</span> Fire engine dispatched — ENG-4 — ETA 4 min
  <span class="t-amber">◎</span> Police — traffic control requested
  <span class="t-amber">◎</span> Caller 1 — monitor for shock symptoms
  <span class="t-amber">◎</span> Caller 2 — guide to safe distance

<span class="t-white">LANGUAGES:</span> <span class="t-red">ES</span> <span class="t-amber">ZH</span> <span class="t-blue">FR</span> <span class="t-green">EN</span>  │  <span class="t-white">AGENTS ACTIVE:</span> 7
      </div>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 6. DEMO SCRIPT -->
  <section id="demo">
    <div class="s-label">06 — Demo Script</div>
    <h2 class="s-title">120 seconds. Five "wow" moments. Choreographed to win.</h2>
    <p class="s-body">This is a theatrical performance. You hit "Start Call" and take your hands off the keyboard. Everything that follows is autonomous. Each new caller is a pre-recorded audio file that plays on a timer. Every API call — transcription, voice generation, vision analysis, dispatch — is real and live.</p>

    <div class="timeline">
      <div class="tl-item">
        <div class="tl-dot red"></div>
        <div class="tl-time red">0:00 – 0:15 // The Setup</div>
        <div class="tl-title">The Problem & The Button</div>
        <div class="tl-body"><em>"When you call 911, the operator is blind to the scene. And if you don't speak English, the delay can be fatal. But real emergencies don't have one caller — they have many, in many languages. We built TriageNet."</em> You hit START CALL. Hands off the keyboard. The system takes over.</div>
      </div>
      <div class="tl-item">
        <div class="tl-dot amber"></div>
        <div class="tl-time amber">0:15 – 0:30 // Wow Moment 1</div>
        <div class="tl-title">Caller 1 — Spanish</div>
        <div class="tl-body">Audio plays: a woman screaming in Spanish about a crash at Market & 5th. Her husband is trapped. The ElevenLabs voice agent responds instantly in Spanish — calm, authoritative: <em>"Tranquila, señora. La ayuda está en camino."</em> The center panel shows live transcript: Spanish + English translation. The CCTV panel snaps to life with dashcam footage. Agent log streams: INTENT DETECTED, ENTITY EXTRACTED, CCTV ACTIVATED. Case file opens: Severity HIGH. Medical dispatched to Mass General (English voice call plays).</div>
      </div>
      <div class="tl-item">
        <div class="tl-dot blue"></div>
        <div class="tl-time blue">0:30 – 0:45 // Wow Moment 2 & 3</div>
        <div class="tl-title">Caller 2 — Mandarin + New Intelligence</div>
        <div class="tl-body">Second audio stream starts: a man speaking Mandarin. He sees the crash from across the street and reports a child in the back seat. Agent log: <em>CALLER 2 (ZH): New entity — CHILD IN VEHICLE. INCIDENT MATCH: Market & 5th. MERGING INTO CASE TN-2025-00417.</em> The case file updates live — casualties change from "2 adults" to "2 adults + 1 child (NEW)." Severity escalates to CRITICAL. A second voice agent responds to the Mandarin caller. A pediatric trauma unit is dispatched — ElevenLabs voice call to UCSF in English plays over speakers. <em>Three languages. Two dispatch calls. All running simultaneously.</em></div>
      </div>
      <div class="tl-item">
        <div class="tl-dot purple"></div>
        <div class="tl-time purple">0:45 – 1:05 // Wow Moment 4 — The "Oh Shit"</div>
        <div class="tl-title">Fire Detection + Caller 3 Corroboration</div>
        <div class="tl-body">Third audio: a shopkeeper in French reports smoke. Three seconds later, the car in the video catches fire. Pixtral catches it — agent log flashes RED: <em>PIXTRAL: {"hazard": "engine_fire", "confidence": 0.99}.</em> Then the magic line appears: <em>CORROBORATION: Visual detection matches Caller 3 (FR) report. Sources confirmed.</em> All three voice agents interrupt their callers simultaneously — Caller 1 gets a fire warning in Spanish, Caller 2 gets an evacuation order in Mandarin. Fire engine dispatched. The case file shows Action Plan v3 with all units. <em>"The AI didn't wait. It saw the fire, corroborated it with a human report in French, and warned two callers in two other languages — all autonomously."</em></div>
      </div>
      <div class="tl-item">
        <div class="tl-dot green"></div>
        <div class="tl-time green">1:05 – 2:00 // Architecture + Close</div>
        <div class="tl-title">The System + The Impact + The Mic Drop</div>
        <div class="tl-body">Quick architecture overview: <em>"Every agent runs on Mistral. The triage agent uses Mistral Large with tool calling. Voice agents are ElevenLabs Conversational Agents. Pixtral handles vision. Shared state means any agent can trigger any other. The case file is regenerated by the triage agent every time new intelligence arrives — from any caller, in any language, or from the video feed."</em> The human impact: <em>"25 million Americans wait for an interpreter when they call 911. TriageNet handles three callers in three languages while watching the scene, corroborating evidence, and dispatching four units — simultaneously."</em> Gesture to the dashboard: the case file is complete, the action plan is on v3, four languages are active, seven agents ran. <em>"We didn't build a chatbot wrapper. We built the future of civic infrastructure."</em></div>
      </div>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 7. UI LAYOUT -->
  <section id="ui">
    <div class="s-label">07 — UI Layout</div>
    <h2 class="s-title">The "Palantir" Control Center.</h2>
    <p class="s-body">A three-panel dark-mode dashboard. Every panel proves a different technical capability. Judges see vision, language, multi-caller intelligence, and agent orchestration all at once.</p>

    <div class="card-grid">
      <div class="card">
        <div class="card-stripe red"></div>
        <div class="card-eyebrow red">Left Panel</div>
        <div class="card-title">CCTV / Video Feed</div>
        <div class="card-body">Starts as [FEED: OFFLINE]. Snaps to life when vision agent activates. Pixtral detection overlays: bounding boxes, hazard labels, confidence scores. Border flashes red on fire detection. Shows the scene judges can watch while audio plays.</div>
      </div>
      <div class="card">
        <div class="card-stripe amber"></div>
        <div class="card-eyebrow amber">Center Panel</div>
        <div class="card-title">Case File + Transcript</div>
        <div class="card-body">Top: live transcripts from all active callers — color-coded by language with English translations. Bottom: the auto-generating case file with severity badge, casualty count, timeline, dispatched units, action plan version. Updates live as agents report. This is the panel that proves intelligence fusion.</div>
      </div>
      <div class="card">
        <div class="card-stripe blue"></div>
        <div class="card-eyebrow blue">Right Panel</div>
        <div class="card-title">Agent Activity Log</div>
        <div class="card-body">Terminal-style real-time agent reasoning. Tool calls, vision detections, dispatch decisions, severity escalations, corroboration events. Color-coded by agent. Key moments (FIRE DETECTED, CHILD IN VEHICLE, CORROBORATED) flash with emphasis. This is the "wow" panel.</div>
      </div>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 8. ELEVENLABS -->
  <section id="elevenlabs">
    <div class="s-label">08 — ElevenLabs Integration</div>
    <h2 class="s-title">Every call is live. Every language is real. Nothing is cached.</h2>
    <p class="s-body">TriageNet uses ElevenLabs as the <span class="hl-blue">voice layer of the entire system</span>. Every transcription, every voice agent response, every dispatch call is generated live during the demo. You are showcasing ElevenLabs' flagship capability — 32-language real-time speech — as the core product mechanic.</p>

    <div class="card-grid card-grid-3">
      <div class="card">
        <div class="card-stripe blue"></div>
        <div class="card-eyebrow blue">Input × 3</div>
        <div class="card-title">Transcribe Speech</div>
        <div class="card-body">Three concurrent transcription streams — Spanish, Mandarin, French. Each with language auto-detection. Feeds into voice agents and case file simultaneously.</div>
      </div>
      <div class="card">
        <div class="card-stripe red"></div>
        <div class="card-eyebrow red">Voice Agents × 3</div>
        <div class="card-title">Deploy Agents</div>
        <div class="card-body">One ElevenLabs conversational agent per caller. Each speaks the caller's language. Backed by Mistral for reasoning. Can be interrupted by shared state (hazard warnings).</div>
      </div>
      <div class="card">
        <div class="card-stripe amber"></div>
        <div class="card-eyebrow amber">Dispatch × 3</div>
        <div class="card-title">Generate Speech</div>
        <div class="card-body">Medical dispatch voice call in English. Fire dispatch voice call in English. Pediatric dispatch voice call in English. Each with a distinct professional voice. All generated live.</div>
      </div>
    </div>

    <div class="callout blue">
      <div class="callout-label blue">Why This Wins the ElevenLabs Challenge</div>
      <div class="callout-text">Nine live ElevenLabs API calls in a single demo: three Transcribe streams, three conversational voice agents, and three Generate Speech dispatch calls, across four languages. Every call is real-time, not pre-cached. You're not demoing a feature. You're demoing the full platform at scale, in a life-or-death context. This is the deepest possible ElevenLabs integration.</div>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 9. MISTRAL -->
  <section id="mistral">
    <div class="s-label">09 — Mistral Integration</div>
    <h2 class="s-title">Every agent thinks with Mistral. Every decision is structured.</h2>
    <p class="s-body">Mistral isn't just the LLM behind one agent — it's the <span class="hl">reasoning layer of the entire system</span>. The triage agent uses Mistral Large with structured tool calling. The vision agent uses Pixtral. Voice agents use Mistral for conversational reasoning. Dispatch agents use Mistral for decision-making.</p>

    <div class="card-grid">
      <div class="card">
        <div class="card-stripe red"></div>
        <div class="card-eyebrow red">Mistral Large</div>
        <div class="card-title">Triage Agent</div>
        <div class="card-body">The brain of the system. Receives all intelligence from shared state. Uses structured tool calling: classify_severity(), update_action_plan(), dispatch_unit(), merge_caller_intel(). Returns structured JSON that updates the case file and triggers dispatch agents. Regenerates action plan on every state change.</div>
      </div>
      <div class="card">
        <div class="card-stripe purple"></div>
        <div class="card-eyebrow purple">Pixtral (Mistral Vision)</div>
        <div class="card-title">Vision Agent</div>
        <div class="card-body">Screenshots the video feed every 3 seconds. Pixtral extracts: incident type, vehicle count, person count, hazards, fire/smoke, and environmental conditions. Returns structured JSON with confidence scores. Writes detections to shared state for other agents to consume.</div>
      </div>
      <div class="card">
        <div class="card-stripe amber"></div>
        <div class="card-eyebrow amber">Mistral Agents</div>
        <div class="card-title">Voice Agent Reasoning</div>
        <div class="card-body">Each ElevenLabs voice agent is backed by Mistral for conversational reasoning. Mistral determines what questions to ask the caller, when to extract new intelligence, and how to respond to hazard interruptions. The voice is ElevenLabs. The brain is Mistral.</div>
      </div>
    </div>

    <h3 class="s-title" style="margin-top:48px; font-size:1.3rem;">Triage Agent Tool Definitions</h3>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Tool</th><th>Input</th><th>Output</th></tr></thead>
        <tbody>
          <tr><td>classify_severity()</td><td>Full shared state object</td><td>Severity level (LOW/MEDIUM/HIGH/CRITICAL) + reasoning</td></tr>
          <tr><td>merge_caller_intel()</td><td>New caller transcript + existing case</td><td>Updated case with merged entities, deduplicated, cross-referenced</td></tr>
          <tr><td>update_action_plan()</td><td>Current case + all dispatches</td><td>Versioned action plan (v1, v2, v3...) with pending/completed items</td></tr>
          <tr><td>dispatch_unit()</td><td>Unit type, severity, location</td><td>Dispatch confirmation + ETA + assigned unit ID</td></tr>
          <tr><td>corroborate_sources()</td><td>Vision detections + caller reports</td><td>Corroboration flag + confidence boost when sources match</td></tr>
          <tr><td>escalate_severity()</td><td>New intelligence trigger</td><td>Updated severity + reason + cascading dispatch triggers</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 10. TECH STACK -->
  <section id="stack">
    <div class="s-label">10 — Technology Stack</div>
    <h2 class="s-title">The full picture.</h2>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Component</th><th>Technology</th><th>Purpose</th></tr></thead>
        <tbody>
          <tr><td>Triage Agent</td><td>Mistral Large + Tool Calling</td><td>Severity classification, intel fusion, action plan, dispatch routing</td></tr>
          <tr><td>Vision Agent</td><td>Pixtral (Mistral Vision API)</td><td>Scene analysis, hazard detection, casualty count, confidence scoring</td></tr>
          <tr><td>Voice Agents ×3</td><td>ElevenLabs Conversational Agents + Mistral</td><td>Multilingual caller interaction, intel extraction, hazard warnings</td></tr>
          <tr><td>Transcription ×3</td><td>ElevenLabs Transcribe</td><td>Real-time speech-to-text with language detection per caller</td></tr>
          <tr><td>Dispatch Voices ×3</td><td>ElevenLabs Generate Speech</td><td>Outbound dispatch calls in responder's language</td></tr>
          <tr><td>Frontend</td><td>React / Next.js + TailwindCSS</td><td>Three-panel Palantir-style control center</td></tr>
          <tr><td>Backend</td><td>Python FastAPI</td><td>Agent orchestration, shared state management, WebSocket</td></tr>
          <tr><td>Shared State</td><td>In-memory JSON (or Redis)</td><td>Decoupled agent communication + case file storage</td></tr>
          <tr><td>Video Processing</td><td>Python + Pixtral API</td><td>Frame extraction every 3s → vision inference → state write</td></tr>
          <tr><td>Caller Simulation</td><td>Pre-recorded MP3s on timers</td><td>Reliable demo input — 3 audio files triggered at 0:15, 0:30, 0:45</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 11. MVP SCOPE -->
  <section id="scope">
    <div class="s-label">11 — MVP Scope</div>
    <h2 class="s-title">24 hours. Three tiers. Ship P1 no matter what.</h2>

    <div class="priority-section">
      <div class="priority-header"><span class="p-tag p1">P1 — Must Ship</span><span class="p-label">The Core Demo Loop</span></div>
      <ul class="p-list red">
        <li>Three-panel React dashboard (CCTV feed, case file/transcript, agent log)</li>
        <li>Pre-recorded Caller 1 (Spanish) audio plays on "Start Call"</li>
        <li>ElevenLabs voice agent responds in Spanish in real time</li>
        <li>Live transcript with dual-language display (original + English)</li>
        <li>Local video file plays as "CCTV feed" when vision agent activates</li>
        <li>Pixtral screenshots every 3s, writes detections to shared state</li>
        <li>Voice agent proactively interrupts on fire detection</li>
        <li>Triage agent (Mistral Large) classifies severity and generates case file</li>
        <li>At least 1 dispatch agent makes a voice call in English (ElevenLabs Generate Speech)</li>
        <li>Agent activity log streams in right panel with color-coded entries</li>
      </ul>
    </div>

    <div class="priority-section">
      <div class="priority-header"><span class="p-tag p2">P2 — Should Ship</span><span class="p-label">Multi-Caller + Intelligence Fusion</span></div>
      <ul class="p-list amber">
        <li>Caller 2 (Mandarin) audio triggers at 0:30 — second ElevenLabs voice agent activates</li>
        <li>Caller 3 (French) audio triggers at 0:45 — third voice agent activates</li>
        <li>Cross-language entity resolution: "child in vehicle" merges into existing case</li>
        <li>Severity escalation (HIGH → CRITICAL) visible on dashboard</li>
        <li>Corroboration event: vision fire detection matches Caller 3's smoke report</li>
        <li>Action plan versioning: v1 → v2 → v3 visible in case file</li>
        <li>3 dispatch agents in parallel (medical, pediatric, fire) with distinct ElevenLabs voices</li>
        <li>Simultaneous hazard warnings to Caller 1 (Spanish) and Caller 2 (Mandarin)</li>
      </ul>
    </div>

    <div class="priority-section">
      <div class="priority-header"><span class="p-tag p3">P3 — Nice to Have</span><span class="p-label">Polish & Extra Credit</span></div>
      <ul class="p-list dim">
        <li>Detection overlays on video feed (bounding boxes, confidence labels)</li>
        <li>Severity badge animation (GREEN → AMBER → RED with glow)</li>
        <li>Live map showing dispatch unit positions and ETAs</li>
        <li>Audio waveform visualization for caller and agent voices</li>
        <li>Exportable case file summary at end of incident</li>
        <li>Anti-swatting validation agent (cross-reference audio + visual evidence)</li>
      </ul>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 12. ENGINEERING REALITY -->
  <section id="engineering">
    <div class="s-label">12 — Hackathon Engineering</div>
    <h2 class="s-title">Smart smoke. Honest mirrors.</h2>
    <p class="s-body">Every API call is real. Every agent decision is real. The only things pre-prepared are the <span class="hl-amber">input data</span> — and that's exactly how a real emergency system works. It processes whatever input arrives. Yours just happens to be choreographed for reliability.</p>

    <div class="card-grid">
      <div class="card">
        <div class="card-stripe red"></div>
        <div class="card-eyebrow red">The Video</div>
        <div class="card-title">Local MP4, Real Vision</div>
        <div class="card-body">Download a dashcam video of a car catching fire. When the Mistral agent triggers fetch_cctv(), the frontend unhides and plays the local file. The tool call is real. The Pixtral inference is real. The video is local for reliability. Time the fire to start at ~40s into the video.</div>
      </div>
      <div class="card">
        <div class="card-stripe amber"></div>
        <div class="card-eyebrow amber">The Callers</div>
        <div class="card-title">Pre-Recorded, Real Transcription</div>
        <div class="card-body">Three MP3 files. Caller 1 (Spanish) at 0:15. Caller 2 (Mandarin) at 0:30. Caller 3 (French) at 0:45. Clean studio audio. ElevenLabs Transcribe processes them live — the transcription is real, the language detection is real, the voice agent responses are real. Only the input audio is pre-prepared.</div>
      </div>
      <div class="card">
        <div class="card-stripe blue"></div>
        <div class="card-eyebrow blue">The Vision Loop</div>
        <div class="card-title">3-Second Screenshots</div>
        <div class="card-body">Python script takes a screenshot from the MP4 every 3 seconds, sends it to Pixtral, writes the response to shared state. Not streaming 30FPS — that's impractical. The 3-second interval is honest and sufficient. Pre-test which frame catches the fire so you can time the demo.</div>
      </div>
      <div class="card">
        <div class="card-stripe green"></div>
        <div class="card-eyebrow green">The Interruption</div>
        <div class="card-title">State-Driven, Not Scripted</div>
        <div class="card-body">Voice agents poll shared state. The moment Pixtral writes "engine_fire" to state, the voice agents' Mistral reasoning layer generates the warning text, ElevenLabs produces the audio, and the caller audio pauses. The interruption is autonomous. The timing is engineered by when the fire appears in the video.</div>
      </div>
    </div>

    <div class="callout">
      <div class="callout-label">The Golden Rule</div>
      <div class="callout-text">If a judge asks "is this live?" the answer is: "Every API call is live. Every agent decision is autonomous. The input data — the video and caller audio — is pre-prepared, exactly as it would be in a real system receiving calls and camera feeds. We choreographed the scenario for the demo, but the processing is 100% real."</div>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 13. SUBMISSION -->
  <section id="submission">
    <div class="s-label">13 — Submission</div>
    <h2 class="s-title">Ready to paste into hackiterate.com.</h2>

    <div class="submission">
      <div class="sub-title">TriageNet — Multimodal Multi-Agent Emergency Operating System</div>
      <p class="sub-text">TriageNet is a multimodal, multi-agent emergency dispatch system that handles multiple callers in multiple languages simultaneously while watching the scene through computer vision — all autonomously.</p>
      <p class="sub-text">In a single demo, TriageNet processes three concurrent callers in Spanish, Mandarin, and French. Each caller interacts with their own ElevenLabs conversational voice agent backed by Mistral reasoning. A Pixtral vision agent analyzes the video feed every 3 seconds, detecting hazards with confidence scores. A Mistral Large triage agent fuses intelligence from all sources — merging cross-language entity reports (a child reported in Mandarin, smoke reported in French) into a single evolving case file with auto-versioning action plans. When the vision agent detects a fire that corroborates a caller's report, all voice agents simultaneously warn their callers in their respective languages. Dispatch agents contact hospitals, fire units, and police through ElevenLabs Generate Speech, each in the responder's operating language.</p>
      <p class="sub-text">The system uses nine live ElevenLabs API calls (three Transcribe streams, three conversational agents, three dispatch voices) across four languages, all in real time. Every agent runs on Mistral. Every decision is autonomous. 25 million Americans have limited English proficiency. TriageNet eliminates the interpreter delay entirely.</p>
      <div class="sub-tracks">
        <span class="badge red">Mistral AI Track (Primary)</span>
        <span class="badge blue">ElevenLabs — Best Use</span>
        <span class="badge amber">Hugging Face — Best Agent Skills</span>
      </div>
    </div>
  </section>

  <div class="divider"></div>

  <!-- 14. RISKS -->
  <section id="risks">
    <div class="s-label">14 — Risks & Mitigations</div>
    <h2 class="s-title">What breaks and how to survive it.</h2>

    <div class="table-wrap">
      <table>
        <thead><tr><th>Risk</th><th>Impact</th><th>Mitigation</th></tr></thead>
        <tbody>
          <tr><td style="color:var(--red)">3 concurrent ElevenLabs streams</td><td>Rate limiting or latency spike</td><td>Use separate API keys or stagger caller starts by 15s. If rate-limited, drop to 2 callers (still impressive). Test concurrency before demo day.</td></tr>
          <tr><td style="color:var(--red)">Pixtral misses the fire</td><td>No "oh shit" moment</td><td>Pre-test which video frame shows fire clearly. Adjust 3s screenshot timing so one lands exactly on the fire frame. Have a manual fallback trigger.</td></tr>
          <tr><td style="color:var(--amber)">Hackathon Wi-Fi dies</td><td>All API calls fail</td><td>Mobile hotspot backup. All input data is local. Pre-warm API connections. Consider pre-generating one dispatch voice as fallback.</td></tr>
          <tr><td style="color:var(--amber)">Mandarin transcription weak</td><td>Caller 2's intel not extracted</td><td>Record clean Mandarin audio with clear pronunciation. Test ElevenLabs Mandarin transcription 5+ times. Have the key phrase ("child in back seat") spoken slowly and clearly.</td></tr>
          <tr><td>Case file merging fails</td><td>Intelligence not fused across callers</td><td>Triage agent prompt explicitly instructs: "When multiple callers report on the same location, merge into one case." Zod validation on output. Fallback: separate case entries still show multi-caller capability.</td></tr>
          <tr><td>Demo overruns 2 min</td><td>Cut off before closing line</td><td>Rehearse 10+ times with stopwatch. Fire MUST happen by 0:48. If late, skip architecture and jump to mic drop. The demo is impressive even without the architecture slide.</td></tr>
          <tr><td>Callers overlap confusingly</td><td>Audio cacophony, judges can't follow</td><td>Caller 1 audio fades to background when Caller 2 starts. Only one caller audio is prominent at a time. Voice agent responses are sequenced, not simultaneous. The VISUAL (dashboard) shows all three; the AUDIO is focused.</td></tr>
        </tbody>
      </table>
    </div>

    <h3 class="s-title" style="margin-top:48px; font-size:1.3rem;">Success Criteria</h3>
    <ul class="p-list red">
      <li>Caller 1 (Spanish) plays → ElevenLabs voice agent responds in Spanish within 2 seconds</li>
      <li>Video feed activates on dashboard with Pixtral processing visible</li>
      <li>Caller 2 (Mandarin) → "child in vehicle" intelligence merges into existing case file</li>
      <li>Severity escalates from HIGH to CRITICAL visibly on dashboard</li>
      <li>Pixtral detects fire with confidence ≥ 0.90, writes to shared state</li>
      <li>Voice agents interrupt callers with fire warnings in their respective languages</li>
      <li>Corroboration event: vision + Caller 3 report flagged as matching</li>
      <li>At least 2 dispatch calls made via ElevenLabs Generate Speech</li>
      <li>Case file shows action plan versioning (at least v1 → v2)</li>
      <li>Total demo under 120 seconds with closing line delivered</li>
    </ul>
  </section>

</main>

<footer>
  <div class="footer-title">TriageNet v2 — Multi-Caller Architecture</div>
  <div class="footer-sub">Mistral × ElevenLabs Hackathon — San Francisco — March 2025</div>
</footer>

<script>
// Theme toggle
function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  document.getElementById('sunIcon').style.display = next === 'light' ? 'block' : 'none';
  document.getElementById('moonIcon').style.display = next === 'dark' ? 'block' : 'none';
  document.getElementById('themeLabel').textContent = next === 'dark' ? 'Light' : 'Dark';
}

// Scroll-triggered section reveals
const sections = document.querySelectorAll('section');
const obs = new IntersectionObserver(e => e.forEach(x => { if (x.isIntersecting) x.target.classList.add('visible'); }), { threshold: 0.08 });
sections.forEach(s => obs.observe(s));

// Active nav link
const navLinks = document.querySelectorAll('.nav-link');
const navObs = new IntersectionObserver(e => e.forEach(x => { if (x.isIntersecting) { navLinks.forEach(l => l.classList.remove('active')); const a = document.querySelector(`.nav-link[href="#${x.target.id}"]`); if (a) a.classList.add('active'); } }), { threshold: 0.25 });
sections.forEach(s => navObs.observe(s));
</script>
</body>
</html>