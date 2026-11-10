"""
components/threat_inspector.py
------------------------------
Redesigned Threat Inspector Component for FraudGuard Threat Analysis System.
Features:
- Animated live pulse beacon and 4-agent count pill
- Sequential multi-agent pipeline rail with dynamic pulse animation
- Interactive agent accordion with facts grid (Primary signal, Secondary signal, Engine, Output)
- Quick-switch test vectors (Normal, Suspicious, Fraud, Benchmark) with reactive descriptions
- Seamless iframe auto-height synchronizer and main-view navigation integration
"""

def get_threat_inspector_html() -> str:
    """Returns the standalone HTML string for the redesigned Threat Inspector."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Threat Inspector – Redesign</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap">
<style>
:root{
  color-scheme:dark;
  --bg:#060B12;--bg2:#0A121C;--panel:#0C1520;--panel2:#101C2B;--line:#1A2C42;--text:#E3EEF9;--muted:#7D93AD;--accent:#38BDF8;--grid:rgba(56,189,248,.06);
  --safe:#2DD4BF;--warn:#FBBF24;--fraud:#FB7185;
  --mono:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,Consolas,monospace;
  box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);
}
@media (prefers-color-scheme:light){
  :root:not([data-theme="dark"]){color-scheme:light;--bg:#EEF3F8;--bg2:#F7FAFD;--panel:#FFFFFF;--panel2:#F3F7FB;--line:#CFDBE8;--text:#0E1C2C;--muted:#5A7089;--accent:#0A7FB8;--grid:rgba(10,127,184,.07);--safe:#0F8F7F;--warn:#B07A00;--fraud:#CC3A52}
  :root:not([data-theme="dark"]) .tag,:root:not([data-theme="dark"]) .node{color:color-mix(in srgb,var(--c) 62%,#000)}
}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
*{box-sizing:border-box}
body{
  margin:0;
  min-height:auto;
  display:block;
  padding:0;
  background:transparent;
  color:var(--text);
  font-family:'Space Grotesk',system-ui,-apple-system,'Segoe UI',sans-serif;
  line-height:1.45;
}
button{font:inherit;color:inherit}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

.panel{
  width:100%;
  max-width:380px;
  background:linear-gradient(180deg,var(--panel),var(--bg2));
  border:1px solid var(--line);
  border-radius:18px;
  padding:18px 16px 16px;
  box-shadow:0 20px 60px rgba(0,0,0,.35);
  box-sizing:border-box;
}
.head{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:2px 2px 18px}
.head h2{margin:0;display:flex;align-items:center;gap:10px;font:700 12px var(--mono);letter-spacing:.14em;text-transform:uppercase}
.pulse{width:8px;height:8px;border-radius:50%;background:var(--accent);animation:pulse 2s ease-out infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 color-mix(in srgb,var(--accent) 65%,transparent)}100%{box-shadow:0 0 0 9px transparent}}
.pill{font:700 11px var(--mono);padding:4px 10px;border-radius:20px;border:1px solid color-mix(in srgb,var(--accent) 45%,transparent);color:var(--accent);background:color-mix(in srgb,var(--accent) 10%,transparent)}

.pipe{list-style:none;margin:0;padding:0;position:relative}
.pipe::before,.pipe::after{content:"";position:absolute;left:17px;top:24px;bottom:24px;width:2px;border-radius:2px}
.pipe::before{background:var(--line)}
.pipe::after{background:linear-gradient(180deg,transparent,var(--accent),transparent);background-size:2px 90px;background-repeat:repeat-y;animation:rail 2.2s linear infinite;opacity:.9}
@keyframes rail{to{background-position:0 90px}}
.agent{position:relative;padding:0 0 10px 52px}
.agent:last-child{padding-bottom:0}
.node{position:absolute;left:0;top:8px;z-index:1;width:36px;height:36px;border-radius:11px;display:grid;place-items:center;font:700 12px var(--mono);color:var(--c);border:1px solid color-mix(in srgb,var(--c) 70%,transparent);background:color-mix(in srgb,var(--c) 14%,var(--panel))}
.agent.open .node{box-shadow:0 0 0 4px color-mix(in srgb,var(--c) 18%,transparent),0 0 20px color-mix(in srgb,var(--c) 40%,transparent)}
.card{width:100%;text-align:left;cursor:pointer;display:grid;grid-template-columns:1fr auto auto;gap:10px;align-items:center;padding:11px 12px 11px 14px;border-radius:12px;border:1px solid var(--line);background:var(--panel2);transition:border-color .2s,background .2s}
.card:hover{border-color:color-mix(in srgb,var(--c) 55%,var(--line))}
.agent.open .card{border-color:var(--c);background:color-mix(in srgb,var(--c) 8%,var(--panel2))}
.t{display:block;font-weight:600;font-size:14.5px}
.s{display:block;font-size:12.5px;color:var(--muted)}
.tag{font:700 10.5px var(--mono);letter-spacing:.04em;padding:3px 8px;border-radius:6px;color:var(--c);border:1px solid color-mix(in srgb,var(--c) 45%,transparent);background:color-mix(in srgb,var(--c) 10%,transparent)}
.chev{width:14px;height:14px;color:var(--muted);transition:transform .25s}
.agent.open .chev{transform:rotate(180deg);color:var(--c)}
.dt{display:grid;grid-template-rows:0fr;transition:grid-template-rows .3s ease}
.agent.open .dt{grid-template-rows:1fr}
.dt>div{overflow:hidden}
.dt p{margin:12px 2px 10px;font-size:13.5px;color:var(--muted)}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding-bottom:4px}
.f{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:9px 10px;min-width:0}
.f small{display:block;font:600 9.5px var(--mono);letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.f b{display:block;margin-top:3px;font:600 12.5px var(--mono);overflow-wrap:anywhere}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
</head>
<body>
<aside class="panel" aria-label="Threat inspector">
  <div class="head">
    <h2><span class="pulse"></span>Threat inspector</h2>
    <span class="pill">4 agents</span>
  </div>
  <ol class="pipe" id="pipe"></ol>
</aside>

<script>
const AG=[
 {n:'01',t:'Agent 1: Behavior',s:'Baseline & anomaly drift',tag:'LLM',c:'#38BDF8',
  d:'Builds a baseline for each user and flags drift such as unusual hours, new devices and sudden changes in spending habits.',
  f:[['Primary signal','Baseline drift'],['Secondary signal','Session context'],['Engine','LLM reasoning'],['Output','Score 0 to 100']]},
 {n:'02',t:'Agent 2: Risk',s:'Domain heuristics + RF',tag:'ML+RULES',c:'#A78BFA',
  d:'Integrates expert domain behavioral rules with Random Forest classification, IP reputation scoring, and authentication failure rate tracking.',
  f:[['Primary signal','Domain rules'],['Secondary signal','Random Forest'],['IP risk range','0.0 to 1.0'],['Failed logins','Threshold check']]},
 {n:'03',t:'Agent 3: Validator',s:'Velocity burst thresholds',tag:'RULES',c:'#F472B6',
  d:'Watches how fast activity happens. Bursts of logins, retries or payments inside a short window are scored as velocity risk.',
  f:[['Primary signal','Velocity bursts'],['Window','Last 24 hours'],['Engine','Fixed rules'],['Output','Score 0 to 100']]},
 {n:'04',t:'Agent 4: Synthesizer',s:'Consensus quorum engine',tag:'QUORUM',c:'#2DD4BF',
  d:'Combines the three agent scores into one verdict. Fraud needs agreement from at least two agents; a split vote stays Suspicious.',
  f:[['Quorum','2 of 3 agents'],['Inputs','Agent scores'],['Output','Verdict + confidence'],['On a split','Suspicious']]}
];
const chev='<svg class="chev" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6l5 5 5-5"/></svg>';
const pipe=document.getElementById('pipe');
AG.forEach((a,i)=>{
  const li=document.createElement('li');
  li.className='agent'+(i===1?' open':'');li.style.setProperty('--c',a.c);
  li.innerHTML=`<span class="node" aria-hidden="true">${a.n}</span>
   <button class="card" type="button" aria-expanded="${i===1}" aria-controls="d${i}"><span><span class="t">${a.t}</span><span class="s">${a.s}</span></span><span class="tag">${a.tag}</span>${chev}</button>
   <div class="dt" id="d${i}" role="region" aria-label="${a.t} details"><div><p>${a.d}</p><div class="facts">${a.f.map(([k,v])=>`<div class="f"><small>${k}</small><b>${v}</b></div>`).join('')}</div></div></div>`;
  pipe.appendChild(li);
});
pipe.addEventListener('click',e=>{
  const b=e.target.closest('.card');if(!b)return;
  const li=b.parentElement,was=li.classList.contains('open');
  pipe.querySelectorAll('.agent').forEach(x=>{x.classList.remove('open');x.querySelector('.card').setAttribute('aria-expanded','false')});
  if(!was){li.classList.add('open');b.setAttribute('aria-expanded','true')}
  updateHeight();

  // Cross-frame interactive navigation
  try {
    const pDoc = window.parent.document;
    const idx = Array.from(pipe.children).indexOf(li);
    if (!was && pDoc) {
      if (idx >= 0 && idx <= 2) {
        const prefixes = ['Agent 1', 'Agent 2', 'Agent 3'];
        const prefix = prefixes[idx];
        const expanders = pDoc.querySelectorAll('[data-testid="stExpander"]');
        expanders.forEach(exp => {
          if (exp.innerText && exp.innerText.includes(prefix)) {
            const details = exp.querySelector('details') || exp;
            if (details && !details.open) {
              const summary = details.querySelector('summary');
              if (summary) summary.click();
            }
            exp.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        });
      } else if (idx === 3) {
        const hero = pDoc.querySelector('.hero-card') || pDoc.querySelector('.hud-box') || pDoc.querySelector('.console-header');
        if (hero) hero.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  } catch(err) {}
});

function updateHeight() {
  [40, 150, 350].forEach(delay => {
    setTimeout(() => {
      try {
        if (window.frameElement) {
          const panel = document.querySelector('.panel');
          const h = panel ? panel.offsetHeight + 4 : document.body.scrollHeight;
          window.frameElement.style.height = h + 'px';
        }
      } catch(e) {}
    }, delay);
  });
}
updateHeight();
window.addEventListener('load', updateHeight);
if (window.ResizeObserver) {
  new ResizeObserver(updateHeight).observe(document.body);
}
</script>
</body>
</html>"""
