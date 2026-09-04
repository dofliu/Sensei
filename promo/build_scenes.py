#!/usr/bin/env python3
"""Generate the 22 standalone scene HTML files for the Sensei intro video.

Each scene is written out as a self-contained 1920x1080 HTML page (no external
resources) that repo-intro-video's render_scenes.py turns into an MP4.

To tweak a line of copy: edit that scene's entry below, re-run this script, then
re-render only that scene:

    python3 build_scenes.py
    python3 <skill>/scripts/render_scenes.py storyboard.json --workdir work --only scene09_enum

Chapter tinting: each chapter overrides --c1/--c2 (the two aurora hues) so the
video changes tonality every 3-4 scenes without changing its overall darkness.
Colours are Sensei's own palette (frontend/renderers.py THEMES).
"""
from pathlib import Path

OUT = Path(__file__).parent

# Sensei brand palette (from frontend/renderers.py)
TEAL = "45,212,191"
VIOLET = "139,92,246"
ORANGE = "217,119,87"     # #D97757
SAGE = "74,124,89"        # #4A7C59
BLUE = "31,58,110"        # #1F3A6E
PLUM = "125,46,110"       # #7D2E6E
AMBER = "194,116,27"      # #C2741B

SHELL = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>__TITLE__</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:#070d17}
body{font-family:"Noto Sans CJK TC","Noto Sans TC",sans-serif;color:#e8eef7;position:relative;
 --c1:__C1__;--c2:__C2__}
.bg{position:absolute;inset:0;background:
 radial-gradient(1200px 800px at 24% 18%,rgba(var(--c1),.14),transparent 62%),
 radial-gradient(1100px 760px at 78% 82%,rgba(var(--c2),.15),transparent 60%),
 linear-gradient(160deg,#0d1b2e 0%,#070d17 58%,#05070d 100%)}
.aur{position:absolute;width:1500px;height:1500px;border-radius:50%;filter:blur(90px);opacity:.5;mix-blend-mode:screen}
.aur.a{background:radial-gradient(circle,rgba(var(--c1),.32),transparent 62%);left:-460px;top:-560px;animation:drift1 22s ease-in-out infinite alternate}
.aur.b{background:radial-gradient(circle,rgba(var(--c2),.30),transparent 62%);right:-520px;bottom:-620px;animation:drift2 26s ease-in-out infinite alternate}
@keyframes drift1{to{transform:translate(150px,90px) scale(1.12)}}
@keyframes drift2{to{transform:translate(-130px,-80px) scale(1.08)}}
.vig{position:absolute;inset:0;background:radial-gradient(1600px 1000px at 50% 46%,transparent 58%,rgba(0,0,0,.5) 100%);pointer-events:none}
.grid{position:absolute;inset:0;opacity:.05;background-image:linear-gradient(rgba(232,238,247,.5) 1px,transparent 1px),linear-gradient(90deg,rgba(232,238,247,.5) 1px,transparent 1px);background-size:64px 64px}
.stage{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
 --dur:__DUR__s;animation:cam var(--dur) ease-in-out both}
@keyframes cam{from{transform:scale(1)}to{transform:scale(1.055)}}
.kicker{font-size:30px;font-weight:700;letter-spacing:.55em;text-indent:.55em;color:rgb(var(--c1));text-transform:uppercase}
.h1{font-size:112px;font-weight:900;line-height:1.14;text-align:center;letter-spacing:.01em;
 background:linear-gradient(100deg,#f4f8ff 20%,#9be8db 50%,#c4b5fd 80%);-webkit-background-clip:text;background-clip:text;color:transparent;
 filter:drop-shadow(0 8px 40px rgba(var(--c1),.18))}
.h2{font-size:76px;font-weight:800;line-height:1.2;text-align:center;color:#f4f8ff}
.sub{font-size:40px;font-weight:400;color:rgba(232,238,247,.78);text-align:center;line-height:1.6}
.accent{color:rgb(var(--c1));font-weight:700}
.chip{display:inline-flex;align-items:center;gap:16px;padding:20px 38px;border-radius:999px;font-size:36px;font-weight:700;white-space:nowrap;
 background:rgba(20,32,52,.82);border:1.5px solid rgba(150,200,255,.22);box-shadow:0 14px 40px rgba(0,0,0,.45),inset 0 1px 0 rgba(255,255,255,.07)}
.card{background:linear-gradient(165deg,rgba(24,38,62,.92),rgba(12,20,36,.94));border:1.5px solid rgba(150,200,255,.20);
 border-radius:26px;box-shadow:0 30px 80px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.08)}
.badge{display:inline-block;padding:12px 26px;border-radius:12px;font-size:28px;font-weight:700;white-space:nowrap;
 background:rgba(var(--c1),.14);border:1.5px solid rgba(var(--c1),.45);color:#7ff0df}
.in{opacity:0;animation:rise 1s cubic-bezier(.16,1,.3,1) both;animation-delay:var(--d,0s)}
@keyframes rise{from{opacity:0;transform:translateY(56px)}to{opacity:1;transform:none}}
.pop{opacity:0;animation:pop .8s cubic-bezier(.2,1.4,.35,1) both;animation-delay:var(--d,0s)}
@keyframes pop{from{opacity:0;transform:scale(.55)}to{opacity:1;transform:scale(1)}}
.fadein{opacity:0;animation:fi .9s ease both;animation-delay:var(--d,0s)}
@keyframes fi{to{opacity:1}}
.glow{animation:glow 2.6s ease-in-out infinite}
@keyframes glow{0%,100%{filter:drop-shadow(0 0 18px rgba(var(--c1),.25))}50%{filter:drop-shadow(0 0 42px rgba(var(--c1),.55))}}
.in.glow{animation:rise 1s cubic-bezier(.16,1,.3,1) var(--d,0s) both,glow 2.6s ease-in-out infinite}
.pop.glow{animation:pop .8s cubic-bezier(.2,1.4,.35,1) var(--d,0s) both,glow 2.6s ease-in-out infinite}
/* Sensei paper card mock — what the projector actually shows */
.paper{background:#fffdf6;border:1.5px solid #d8cdb3;border-radius:22px;padding:44px 48px;
 box-shadow:0 40px 100px rgba(0,0,0,.6);color:#29261b;text-align:left}
.paper .pt{font-family:"Noto Serif CJK TC","Noto Sans CJK TC",serif;font-size:52px;font-weight:700;color:#0f0d0a;line-height:1.1}
.paper .pm{font-family:"Noto Sans Mono CJK TC",monospace;font-size:19px;letter-spacing:.18em;text-transform:uppercase;color:#7a6a52}
.pcard{background:#fffdf6;border:1px solid #d8cdb3;border-radius:12px;padding:22px 24px;border-top:4px solid var(--ac,#D97757)}
.pcard .n{font-family:"Noto Serif CJK TC","Noto Sans CJK TC",serif;font-size:34px;font-weight:700;color:#0f0d0a;white-space:nowrap}
.pcard .d{font-family:"Noto Sans Mono CJK TC",monospace;font-size:18px;color:#7a6a52;margin-top:8px;white-space:nowrap}
__CSS__
</style></head>
<body>
<div class="bg"></div><div class="aur a"></div><div class="aur b"></div><div class="grid"></div>
__FX__
<div class="stage" style="z-index:2">
__BODY__
</div>
<div class="vig" style="z-index:3"></div>
__JS__
</body></html>"""

FX = """<canvas id="fx" style="position:absolute;inset:0;z-index:1;pointer-events:none"></canvas>
<script>
const cv=document.getElementById('fx');cv.width=1920;cv.height=1080;const cx=cv.getContext('2d');
const P=[];for(let i=0;i<80;i++){P.push({x:Math.random()*1920,y:Math.random()*1080,
 r:.8+Math.random()*2.6,s:.12+Math.random()*.5,o:.12+Math.random()*.4,
 hue:Math.random()<.6?'45,212,191':'167,139,250',ph:Math.random()*6.28});}
function draw(){const t=performance.now()/1000;cx.clearRect(0,0,1920,1080);
 for(const p of P){const y=(p.y-t*38*p.s)%1080,yy=y<0?y+1080:y;
  const x=p.x+Math.sin(t*.5+p.ph)*26;const tw=.55+.45*Math.sin(t*1.7+p.ph*3);
  cx.beginPath();cx.arc(x,yy,p.r,0,6.283);
  cx.fillStyle=`rgba(${p.hue},${(p.o*tw).toFixed(3)})`;cx.fill();}
 requestAnimationFrame(draw);}
requestAnimationFrame(draw);
</script>"""

# countUp helper: data-to on any .num element, starts at --d seconds
COUNTUP = """<script>
const els=[...document.querySelectorAll('.num')];
function tick(){const t=performance.now()/1000;
 for(const e of els){const d=parseFloat(e.dataset.d||'0'),dur=parseFloat(e.dataset.dur||'1.4');
  const to=parseFloat(e.dataset.to),p=Math.max(0,Math.min(1,(t-d)/dur));
  const ease=1-Math.pow(1-p,3);
  e.textContent=(to%1===0)?Math.round(to*ease):(to*ease).toFixed(1);}
 requestAnimationFrame(tick);}
requestAnimationFrame(tick);
</script>"""

SCENES = []


def scene(name, title, dur, c1, c2, body, css="", fx=False, js=""):
    SCENES.append(dict(name=name, title=title, dur=dur, c1=c1, c2=c2,
                       body=body, css=css, fx=fx, js=js))


# ══════════════════════════════════════════════════════════════════
# 開場章 — teal / violet
# ══════════════════════════════════════════════════════════════════

scene("scene01_hook", "Sensei — hook", 9, TEAL, VIOLET, fx=True, body="""
 <div class="kicker in" style="--d:.2s">ON-DEVICE AI CO-TEACHER</div>
 <div class="pop" style="--d:.55s;margin-top:26px;display:flex;align-items:baseline;gap:34px">
   <div class="h1" style="font-size:210px;line-height:1">Sensei</div>
   <div style="font-size:96px;font-weight:300;color:rgba(232,238,247,.42);letter-spacing:.22em">先生</div>
 </div>
 <div class="sub in" style="--d:1.35s;margin-top:44px;font-size:46px">
   把老師講的話，<span class="accent">即時</span>變成投影機上的結構化卡片
 </div>
 <div class="in" style="--d:2.1s;margin-top:56px;display:flex;gap:22px">
   <div class="badge">Faster-Whisper</div>
   <div class="badge">Gemma 4 e2b</div>
   <div class="badge">Ollama</div>
   <div class="badge">100% 本機</div>
 </div>
""")

scene("scene02_problem", "問題", 9, ORANGE, VIOLET, css="""
.split{display:flex;gap:70px;align-items:stretch}
.pane{width:720px;padding:44px 46px;border-radius:24px}
.pl{background:rgba(217,119,87,.10);border:1.5px solid rgba(217,119,87,.34)}
.pr{background:rgba(120,130,150,.08);border:1.5px solid rgba(150,165,190,.20)}
.ph{font-size:26px;font-weight:700;letter-spacing:.3em;margin-bottom:26px}
.line{font-size:33px;line-height:1.62;color:#eef3fa}
.bar{height:12px;border-radius:6px;background:rgba(150,165,190,.20);margin:20px 0}
""", body="""
 <div class="h2 in" style="--d:.15s;font-size:62px">每個課堂都有同一個落差</div>
 <div class="split" style="margin-top:56px">
   <div class="pane pl in" style="--d:.7s">
     <div class="ph" style="color:#f0a184">老師說出口的</div>
     <div class="line">「控制不是只有 PID，<br>還有最佳、類神經、<br>非線性、強健控制。」</div>
     <div style="margin-top:26px;display:flex;gap:12px;flex-wrap:wrap">
       <div class="badge" style="background:rgba(217,119,87,.16);border-color:rgba(217,119,87,.5);color:#f5b79f">有層次</div>
       <div class="badge" style="background:rgba(217,119,87,.16);border-color:rgba(217,119,87,.5);color:#f5b79f">有並列</div>
       <div class="badge" style="background:rgba(217,119,87,.16);border-color:rgba(217,119,87,.5);color:#f5b79f">有結構</div>
     </div>
   </div>
   <div class="pane pr in" style="--d:1.25s">
     <div class="ph" style="color:rgba(200,212,230,.62)">學生看見的</div>
     <div style="font-size:44px;font-weight:700;color:rgba(220,228,240,.5)">Lesson 5</div>
     <div class="bar" style="width:78%"></div>
     <div class="bar" style="width:56%"></div>
     <div class="bar" style="width:64%"></div>
     <div style="margin-top:30px;font-size:28px;color:rgba(200,212,230,.45)">一張靜止的投影片</div>
   </div>
 </div>
 <div class="sub in" style="--d:2.0s;margin-top:52px;font-size:38px">
   結構在<span style="color:#f0a184;font-weight:700">老師腦裡</span>，不在螢幕上
 </div>
""")

scene("scene03_position", "定位", 8, TEAL, VIOLET, css="""
.steps{display:flex;align-items:center;gap:34px;margin-top:64px}
.st{width:400px;padding:40px 34px;text-align:center;border-radius:24px;
 background:rgba(20,32,52,.72);border:1.5px solid rgba(150,200,255,.20)}
.si{font-size:76px;line-height:1}
.sn{font-size:44px;font-weight:800;margin-top:20px;color:#f4f8ff}
.sd{font-size:26px;color:rgba(232,238,247,.62);margin-top:12px;line-height:1.5}
.arw{font-size:56px;color:rgba(45,212,191,.6)}
""", body="""
 <div class="kicker in" style="--d:.15s">WHAT SENSEI DOES</div>
 <div class="h2 in" style="--d:.5s;margin-top:24px">Sensei 把那個結構搬到牆上</div>
 <div class="steps">
   <div class="st in" style="--d:1.0s"><div class="si">🎤</div><div class="sn">聽見</div>
     <div class="sd">教室麥克風<br>本機語音辨識</div></div>
   <div class="arw pop" style="--d:1.35s">→</div>
   <div class="st in" style="--d:1.6s"><div class="si">🧩</div><div class="sn">看出結構</div>
     <div class="sd">這是並列？比較？<br>還是流程？</div></div>
   <div class="arw pop" style="--d:1.95s">→</div>
   <div class="st in" style="--d:2.2s"><div class="si">🖥️</div><div class="sn">投影成卡</div>
     <div class="sd">第二螢幕自動換卡<br>老師不用碰滑鼠</div></div>
 </div>
""")

# ══════════════════════════════════════════════════════════════════
# 管線章 — teal forward
# ══════════════════════════════════════════════════════════════════

scene("scene04_pipeline", "管線", 10, TEAL, "56,189,248", css="""
.pipe{display:flex;align-items:center;gap:26px;margin-top:58px}
.nd{width:300px;padding:32px 26px;text-align:center;border-radius:22px;
 background:rgba(16,28,46,.88);border:1.5px solid rgba(45,212,191,.30)}
.ni{font-size:56px;line-height:1}
.nn{font-size:34px;font-weight:800;margin-top:14px;color:#f4f8ff;white-space:nowrap}
.nm{font-family:"Noto Sans Mono CJK TC",monospace;font-size:18px;color:#6fe3d2;margin-top:10px;letter-spacing:.06em}
.wire{width:74px;height:6px;border-radius:3px;background:rgba(45,212,191,.18);position:relative;overflow:hidden}
.wire i{position:absolute;inset:0;width:40%;border-radius:3px;background:linear-gradient(90deg,transparent,#2dd4bf,transparent);
 animation:flow 1.9s linear infinite;animation-delay:var(--wd,0s)}
@keyframes flow{from{transform:translateX(-100%)}to{transform:translateX(280%)}}
.encl{margin-top:44px;padding:20px 46px;border-radius:999px;font-size:31px;font-weight:700;white-space:nowrap;
 background:rgba(74,124,89,.16);border:1.5px solid rgba(74,124,89,.55);color:#9fe0b4}
""", body="""
 <div class="kicker in" style="--d:.15s">THE PIPELINE</div>
 <div class="h2 in" style="--d:.45s;margin-top:22px;font-size:64px">一秒之內，從聲音到版面</div>
 <div class="pipe">
   <div class="nd in" style="--d:.9s"><div class="ni">🎤</div><div class="nn">講課語音</div><div class="nm">16 kHz mono</div></div>
   <div class="wire fadein" style="--d:1.2s"><i style="--wd:0s"></i></div>
   <div class="nd in" style="--d:1.45s"><div class="ni">📝</div><div class="nn">Whisper</div><div class="nm">large-v3 · 3 GB</div></div>
   <div class="wire fadein" style="--d:1.75s"><i style="--wd:.5s"></i></div>
   <div class="nd in" style="--d:2.0s"><div class="ni">🧠</div><div class="nn">Gemma 4</div><div class="nm">e2b · 7 GB</div></div>
   <div class="wire fadein" style="--d:2.3s"><i style="--wd:1s"></i></div>
   <div class="nd in" style="--d:2.55s"><div class="ni">📇</div><div class="nn">結構化卡片</div><div class="nm">/display</div></div>
 </div>
 <div class="encl in" style="--d:3.2s">● &nbsp;以上每一步，都跑在老師這台筆電裡</div>
""")

scene("scene05_asr", "ASR", 9, TEAL, "56,189,248", css="""
.wv{display:flex;align-items:center;gap:7px;height:120px;margin-top:20px}
.wv i{width:9px;border-radius:5px;background:linear-gradient(180deg,#2dd4bf,#38bdf8);animation:wv 1.1s ease-in-out infinite alternate}
@keyframes wv{from{height:14px;opacity:.45}to{height:var(--h,70px);opacity:1}}
.tx{margin-top:34px;font-size:40px;line-height:1.6;color:#eef3fa;text-align:center;max-width:1340px}
.hl{color:#2dd4bf;font-weight:800;border-bottom:4px solid rgba(45,212,191,.5)}
.gl{margin-top:36px;display:flex;gap:14px;flex-wrap:wrap;justify-content:center;max-width:1400px}
.gt{padding:12px 26px;border-radius:10px;font-size:26px;font-weight:600;white-space:nowrap;
 background:rgba(45,212,191,.10);border:1px solid rgba(45,212,191,.35);color:#8fe9db}
.stat{margin-top:40px;font-size:34px;color:rgba(232,238,247,.8)}
""", body="""
 <div class="kicker in" style="--d:.15s">STEP 1 · 語音辨識</div>
 <div class="h2 in" style="--d:.45s;margin-top:20px;font-size:60px">聽得懂工程術語的耳朵</div>
 <div class="wv fadein" style="--d:.9s">
""" + "".join(
    f'<i style="--h:{h}px;animation-delay:{i*0.07:.2f}s"></i>'
    for i, h in enumerate([28,52,86,110,74,40,96,120,64,34,80,104,58,26,70,112,88,44,30,66,98,116,72,38,54,90,60,32,78,106,50,24])
) + """
 </div>
 <div class="tx in" style="--d:1.5s">「同學，<span class="hl">PID 控制</span>不是唯一，還有<span class="hl">最佳控制</span>、<span class="hl">強健控制</span>…」</div>
 <div class="gl">
   <div class="gt in" style="--d:2.0s">PID 控制</div>
   <div class="gt in" style="--d:2.1s">LQR</div>
   <div class="gt in" style="--d:2.2s">MPC</div>
   <div class="gt in" style="--d:2.3s">卡爾曼濾波</div>
   <div class="gt in" style="--d:2.4s">SCADA</div>
   <div class="gt in" style="--d:2.5s">Modbus</div>
   <div class="gt in" style="--d:2.6s">變槳</div>
   <div class="gt in" style="--d:2.7s">齒輪箱</div>
   <div class="gt in" style="--d:2.8s">IEC 61131</div>
 </div>
 <div class="stat in" style="--d:3.3s">課程詞彙表當作先驗 → 專有名詞辨識錯誤率 <span class="accent">降低 40–60%</span></div>
""")

scene("scene06_tools", "tool calling", 9, TEAL, VIOLET, css="""
.tools{display:flex;flex-wrap:wrap;gap:20px;margin-top:46px;justify-content:center;max-width:1360px}
.tl{width:300px}
.tl{padding:24px 20px;border-radius:16px;text-align:center;
 background:rgba(16,28,46,.82);border:1.5px solid rgba(150,200,255,.18)}
.tl .tn{font-family:"Noto Sans Mono CJK TC",monospace;font-size:23px;color:#a9bdd8;white-space:nowrap}
.tl.on{background:rgba(45,212,191,.16);border-color:rgba(45,212,191,.75);box-shadow:0 0 46px rgba(45,212,191,.35)}
.tl.on .tn{color:#7ff0df;font-weight:700}
.tl.skip{border-style:dashed;border-color:rgba(150,200,255,.30);background:rgba(16,28,46,.55)}
.tl.skip .tn{color:#7c8ba1}
.pick{margin-top:44px;font-size:36px;color:rgba(232,238,247,.82)}
""", body="""
 <div class="kicker in" style="--d:.15s">STEP 2 · 結構判斷</div>
 <div class="h2 in" style="--d:.45s;margin-top:20px;font-size:60px">八個模板 ＋ 一個「這句不用出卡」</div>
 <div class="sub in" style="--d:.85s;margin-top:22px;font-size:31px">Gemma 4 用原生 function calling 挑一個工具，把老師的話填進欄位</div>
 <div class="tools">
   <div class="tl in" style="--d:1.35s"><div class="tn">comparison_table</div></div>
   <div class="tl on pop" style="--d:2.15s"><div class="tn">enumeration_cards</div></div>
   <div class="tl in" style="--d:1.45s"><div class="tn">flow_diagram</div></div>
   <div class="tl in" style="--d:1.55s"><div class="tn">hierarchy_tree</div></div>
   <div class="tl in" style="--d:1.65s"><div class="tn">swot</div></div>
   <div class="tl in" style="--d:1.75s"><div class="tn">pyramid</div></div>
   <div class="tl in" style="--d:1.85s"><div class="tn">quiz_card</div></div>
   <div class="tl in" style="--d:1.90s"><div class="tn">key_fact</div></div>
   <div class="tl skip in" style="--d:2.0s"><div class="tn">no_card</div></div>
 </div>
 <div class="pick in" style="--d:2.7s">模型挑中 <span class="accent">enumeration_cards</span> — 因為這句話在「並列」</div>
""")

scene("scene07_layers", "四層防線", 8, TEAL, VIOLET, css="""
.lay{width:1240px;margin-top:44px;display:flex;flex-direction:column;gap:16px}
.lr{display:flex;align-items:center;gap:26px;padding:24px 34px;border-radius:16px;
 background:rgba(16,28,46,.84);border:1.5px solid rgba(150,200,255,.18)}
.lk{font-family:"Noto Sans Mono CJK TC",monospace;font-size:22px;color:#6fe3d2;width:56px;flex:none}
.ln{font-size:34px;font-weight:700;color:#f4f8ff;width:330px;flex:none;white-space:nowrap}
.ld{font-size:26px;color:rgba(232,238,247,.66);line-height:1.45}
.ok{margin-left:auto;font-size:34px;color:#4ade80;flex:none}
""", body="""
 <div class="kicker in" style="--d:.15s">STEP 3 · 結構保證</div>
 <div class="h2 in" style="--d:.45s;margin-top:18px;font-size:58px">四層防線，一層漏了還有下一層</div>
 <div class="lay">
   <div class="lr in" style="--d:.95s"><div class="lk">01</div><div class="ln">原生 tool calling</div>
     <div class="ld">主路徑：模型直接填工具參數</div><div class="ok">✓</div></div>
   <div class="lr in" style="--d:1.3s"><div class="lk">02</div><div class="ln">JSON mode 備援</div>
     <div class="ld">取樣層強制合法 JSON，無效輸出產不出來</div><div class="ok">✓</div></div>
   <div class="lr in" style="--d:1.65s"><div class="lk">03</div><div class="ln">Pydantic 嚴格驗證</div>
     <div class="ld">七個 schema，欄位對不上就不放行</div><div class="ok">✓</div></div>
   <div class="lr in" style="--d:2.0s"><div class="lk">04</div><div class="ln">寬鬆救援</div>
     <div class="ld">只補視覺欄位（icon、空白副標），絕不編造內容</div><div class="ok">✓</div></div>
 </div>
 <div class="sub in" style="--d:2.6s;margin-top:36px;font-size:30px">小模型偶爾漏欄位 — 投影機不該因此空白</div>
""")

# ══════════════════════════════════════════════════════════════════
# 模板章 — 暖琥珀
# ══════════════════════════════════════════════════════════════════

scene("scene08_templates", "八模板", 9, ORANGE, AMBER, css="""
.tg{display:flex;flex-wrap:wrap;gap:22px;margin-top:48px;justify-content:center;max-width:1510px}
.tc{width:340px}
.tc{padding:28px 24px;border-radius:18px;text-align:center;
 background:rgba(28,22,16,.78);border:1.5px solid rgba(217,119,87,.30)}
.tc .ic{font-size:52px;line-height:1}
.tc .nm{font-size:31px;font-weight:800;color:#f8ede6;margin-top:14px;white-space:nowrap}
.tc .ex{font-size:22px;color:rgba(240,215,200,.6);margin-top:10px;line-height:1.4}
""", body="""
 <div class="kicker in" style="--d:.15s;color:#f0a184">CURATED TEMPLATES</div>
 <div class="h2 in" style="--d:.45s;margin-top:20px;font-size:62px">八種說話方式，八種版面</div>
 <div class="tg">
   <div class="tc in" style="--d:.95s"><div class="ic">📇</div><div class="nm">列舉卡片</div><div class="ex">「有 A、B、C、D」</div></div>
   <div class="tc in" style="--d:1.05s"><div class="ic">⚖️</div><div class="nm">比較表</div><div class="ex">「A 跟 B 差在…」</div></div>
   <div class="tc in" style="--d:1.15s"><div class="ic">➡️</div><div class="nm">流程圖</div><div class="ex">「先…再…然後…」</div></div>
   <div class="tc in" style="--d:1.25s"><div class="ic">🌳</div><div class="nm">階層樹</div><div class="ex">「分成兩類，各有…」</div></div>
   <div class="tc in" style="--d:1.35s"><div class="ic">🎯</div><div class="nm">SWOT</div><div class="ex">優勢劣勢機會威脅</div></div>
   <div class="tc in" style="--d:1.45s"><div class="ic">🔺</div><div class="nm">金字塔</div><div class="ex">「從底層到頂層」</div></div>
   <div class="tc in" style="--d:1.55s"><div class="ic">📝</div><div class="nm">隨堂測驗</div><div class="ex">「來考一題」</div></div>
   <div class="tc in" style="--d:1.65s"><div class="ic">💡</div><div class="nm">關鍵事實</div><div class="ex">「就一個數字要記住」</div></div>
 </div>
 <div class="sub in" style="--d:2.3s;margin-top:44px;font-size:32px">
   版面是<span style="color:#f0a184;font-weight:700">固定的</span> — 不讓模型每句話發明一種新排版
 </div>
""")

scene("scene09_enum", "列舉卡片 mock", 8, ORANGE, AMBER, css="""
.say{font-size:34px;color:rgba(240,222,208,.78);font-style:italic;text-align:center}
.sheet{width:1500px;margin-top:34px}
.row{display:flex;gap:20px;margin-top:26px}
.row>div{flex:1}
""", body="""
 <div class="say in" style="--d:.15s">老師說：「控制不是只有 PID，還有最佳、類神經、非線性、強健、適應控制。」</div>
 <div class="paper sheet in" style="--d:.85s">
   <div class="pm">● &nbsp;ENUMERATION CARDS</div>
   <div class="pt" style="margin-top:14px">控制方法的全貌</div>
   <div style="font-size:26px;color:#7a6a52;margin-top:10px;font-style:italic">不是只有 PID</div>
   <div class="row">
     <div class="pcard pop" style="--d:1.5s;--ac:#D97757"><div class="n">PID 控制</div><div class="d">· 業界主流</div></div>
     <div class="pcard pop" style="--d:1.7s;--ac:#1F3A6E"><div class="n">最佳控制</div><div class="d">· LQR / MPC</div></div>
     <div class="pcard pop" style="--d:1.9s;--ac:#4A7C59"><div class="n">類神經控制</div><div class="d">· 資料驅動</div></div>
   </div>
   <div class="row">
     <div class="pcard pop" style="--d:2.1s;--ac:#C2741B"><div class="n">非線性控制</div><div class="d">· 滑模 / 回授線性化</div></div>
     <div class="pcard pop" style="--d:2.3s;--ac:#7D2E6E"><div class="n">強健控制</div><div class="d">· H∞ 穩定性保障</div></div>
     <div class="pcard pop" style="--d:2.5s;--ac:#C0392B"><div class="n">適應控制</div><div class="d">· 參數線上調整</div></div>
   </div>
 </div>
 <div class="in" style="--d:3.1s;margin-top:30px;font-size:28px;color:rgba(240,222,208,.62);font-family:'Noto Sans Mono CJK TC',monospace">
   卡片字級 ≥ 24 px · 標題 ≥ 36 px — 為教室最後一排設計
 </div>
""")

scene("scene10_compare", "比較表 mock", 8, ORANGE, AMBER, css="""
.say{font-size:34px;color:rgba(240,222,208,.78);font-style:italic;text-align:center}
.sheet{width:1480px;margin-top:34px}
table{width:100%;border-collapse:collapse;margin-top:24px}
th{font-family:"Noto Sans Mono CJK TC",monospace;font-size:20px;letter-spacing:.16em;text-transform:uppercase;
 text-align:left;padding:16px 18px;color:#7a6a52;background:rgba(122,106,82,.08)}
td{padding:20px 18px;border-bottom:1px solid rgba(122,106,82,.18);font-size:30px}
.ta{color:#D97757;font-weight:600}.tb{color:#1F3A6E;font-weight:600}.tk{color:#7a6a52;font-size:26px}
""", body="""
 <div class="say in" style="--d:.15s">老師說：「單迴路和雙迴路控制，差別在這幾個地方…」</div>
 <div class="paper sheet in" style="--d:.85s">
   <div class="pm">● &nbsp;COMPARISON TABLE</div>
   <div class="pt" style="margin-top:14px">單迴路 vs 雙迴路控制</div>
   <table>
     <tr><th style="width:26%">面向</th><th style="color:#D97757">單迴路</th><th style="color:#1F3A6E">雙迴路</th></tr>
     <tr class="fadein" style="--d:1.5s"><td class="tk">結構複雜度</td><td class="ta">簡單，單一回授</td><td class="tb">內外環串接</td></tr>
     <tr class="fadein" style="--d:1.75s"><td class="tk">抗擾能力</td><td class="ta">對內部擾動較弱</td><td class="tb">內環先吸收擾動</td></tr>
     <tr class="fadein" style="--d:2.0s"><td class="tk">感測器需求</td><td class="ta">一個</td><td class="tb">兩個</td></tr>
     <tr class="fadein" style="--d:2.25s"><td class="tk">調校難度</td><td class="ta">一組參數</td><td class="tb">內快外慢，需分開調</td></tr>
     <tr class="fadein" style="--d:2.5s"><td class="tk">成本</td><td class="ta">低</td><td class="tb">較高</td></tr>
   </table>
 </div>
""")

scene("scene11_flow", "流程圖 mock", 9, ORANGE, AMBER, css="""
.say{font-size:34px;color:rgba(240,222,208,.78);font-style:italic;text-align:center}
.sheet{width:1560px;margin-top:34px}
.fr{display:flex;align-items:stretch;gap:12px;margin-top:26px}
.fs{flex:1;background:#fffdf6;border:1px solid #d8cdb3;border-radius:12px;padding:22px 22px}
.fm{font-family:"Noto Sans Mono CJK TC",monospace;font-size:17px;letter-spacing:.16em;color:#7a6a52}
.fn{font-family:"Noto Serif CJK TC","Noto Sans CJK TC",serif;font-size:32px;font-weight:700;color:#0f0d0a;margin-top:8px;white-space:nowrap}
.fd{font-size:20px;color:#7a6a52;margin-top:8px;white-space:nowrap}
.fa{align-self:center;font-size:34px;color:#b3a181;flex:none}
""", body="""
 <div class="say in" style="--d:.15s">老師說：「先量測振動，再做特徵抽取，然後分類，最後報警。」</div>
 <div class="paper sheet in" style="--d:.85s">
   <div class="pm">● &nbsp;FLOW DIAGRAM</div>
   <div class="pt" style="margin-top:14px">風機狀態監控流程</div>
   <div class="fr">
     <div class="fs pop" style="--d:1.5s"><div class="fm"><span style="color:#D97757">●</span> STEP 01</div>
       <div class="fn">量測振動</div><div class="fd">加速規 · 8 kHz</div></div>
     <div class="fa pop" style="--d:1.65s">→</div>
     <div class="fs pop" style="--d:1.8s"><div class="fm"><span style="color:#1F3A6E">●</span> STEP 02</div>
       <div class="fn">特徵抽取</div><div class="fd">FFT 與峰度</div></div>
     <div class="fa pop" style="--d:1.95s">→</div>
     <div class="fs pop" style="--d:2.1s"><div class="fm"><span style="color:#4A7C59">●</span> STEP 03</div>
       <div class="fn">狀態分類</div><div class="fd">健康 / 劣化 / 故障</div></div>
     <div class="fa pop" style="--d:2.25s">→</div>
     <div class="fs pop" style="--d:2.4s"><div class="fm"><span style="color:#C0392B">●</span> STEP 04</div>
       <div class="fn">發出報警</div><div class="fd">SCADA 推播</div></div>
   </div>
 </div>
 <div class="in" style="--d:3.0s;margin-top:32px;font-size:30px;color:rgba(240,222,208,.7)">
   同一套管線，換一種語意 → 換一種版面
 </div>
""")

# ══════════════════════════════════════════════════════════════════
# 課堂章 — 黑板綠
# ══════════════════════════════════════════════════════════════════

scene("scene12_trigger", "語音觸發", 9, SAGE, "56,189,248", css="""
.tr{width:1440px;margin-top:44px;padding:34px 40px;border-radius:20px;
 background:rgba(14,30,22,.82);border:1.5px solid rgba(74,124,89,.42)}
.tm{font-family:"Noto Sans Mono CJK TC",monospace;font-size:20px;letter-spacing:.18em;color:#8fd3a5}
.tt{font-size:40px;line-height:1.6;color:#eef7f0;margin-top:16px}
.fire{color:#ffe08a;font-weight:900;background:rgba(255,224,138,.14);padding:2px 12px;border-radius:8px;
 border-bottom:4px solid rgba(255,224,138,.6)}
.log{margin-top:30px;display:flex;flex-direction:column;gap:12px;width:1440px}
.lg{font-family:"Noto Sans Mono CJK TC",monospace;font-size:25px;padding:14px 26px;border-radius:12px;
 background:rgba(10,20,14,.72);border-left:4px solid #4A7C59;color:#a8ddba;white-space:nowrap}
""", body="""
 <div class="kicker in" style="--d:.15s;color:#8fd3a5">SPOKEN TRIGGER</div>
 <div class="h2 in" style="--d:.45s;margin-top:18px;font-size:60px">老師說一句話，測驗就上牆</div>
 <div class="tr in" style="--d:.95s">
   <div class="tm">TRANSCRIPT</div>
   <div class="tt">「今天講了 PID 的三個分量。<span class="fire">來考一題</span>，下列哪一個不是控制方法？」</div>
 </div>
 <div class="log">
   <div class="lg fadein" style="--d:1.9s">[Pipeline] quiz trigger phrase detected → forcing template_hint=quiz_card</div>
   <div class="lg fadein" style="--d:2.35s">[Sensei LLM] path=tools template=quiz_card</div>
 </div>
 <div class="sub in" style="--d:2.9s;margin-top:36px;font-size:30px">
   字串命中就<span style="color:#8fd3a5;font-weight:700">硬鎖模板</span> — 不賭小模型的分類運氣
 </div>
""")

scene("scene13_quiz", "quiz 投影 mock", 9, SAGE, "56,189,248", css="""
.sheet{width:1520px}
.qq{font-family:"Noto Serif CJK TC","Noto Sans CJK TC",serif;font-size:54px;font-weight:700;color:#0f0d0a;line-height:1.3;margin-top:16px}
.og{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:30px}
.op{background:#fffdf6;border:1px solid #d8cdb3;border-radius:14px;padding:26px 30px;display:flex;align-items:center;gap:26px}
.ol{font-family:"Noto Serif CJK TC","Noto Sans CJK TC",serif;font-size:62px;font-style:italic;font-weight:600;line-height:1;min-width:56px;text-align:center}
.ot{font-size:34px;font-weight:600;color:#0f0d0a}
.note{margin-top:30px;font-size:30px;color:rgba(200,232,210,.78)}
""", body="""
 <div class="paper sheet in" style="--d:.2s">
   <div class="pm"><span style="color:#D97757">●</span> &nbsp;QUIZ · MEDIUM</div>
   <div class="qq">下列哪一個<span style="color:#C0392B">不是</span>控制方法？</div>
   <div class="og">
     <div class="op pop" style="--d:1.0s"><div class="ol" style="color:#D97757">A</div><div class="ot">PID 控制</div></div>
     <div class="op pop" style="--d:1.2s"><div class="ol" style="color:#1F3A6E">B</div><div class="ot">模糊控制</div></div>
     <div class="op pop" style="--d:1.4s"><div class="ol" style="color:#4A7C59">C</div><div class="ot">線性迴歸</div></div>
     <div class="op pop" style="--d:1.6s"><div class="ol" style="color:#C2741B">D</div><div class="ot">強健控制</div></div>
   </div>
 </div>
 <div class="note in" style="--d:2.4s">
   四個選項<span style="color:#8fd3a5;font-weight:700">長得一模一樣</span> — 答案留在老師的筆電上，由老師決定何時揭曉
 </div>
""")

scene("scene14_display", "SSE 推播", 9, SAGE, TEAL, css="""
.two{display:flex;align-items:center;gap:60px;margin-top:50px}
.dev{border-radius:20px;padding:26px;background:rgba(12,24,18,.86);border:1.5px solid rgba(74,124,89,.38)}
.dl{width:620px}.dp{width:820px}
.dh{font-family:"Noto Sans Mono CJK TC",monospace;font-size:19px;letter-spacing:.18em;color:#8fd3a5;margin-bottom:16px}
.scr{background:#0f1912;border:1px solid rgba(120,170,135,.24);border-radius:12px;padding:20px 22px}
.ui{display:flex;gap:10px;margin-bottom:14px}
.ui i{height:34px;border-radius:8px;background:rgba(150,200,170,.16);flex:1}
.ui i.hot{background:rgba(217,119,87,.5)}
.mini{background:#fffdf6;border-radius:8px;padding:16px 18px;color:#29261b}
.mt{font-family:"Noto Serif CJK TC","Noto Sans CJK TC",serif;font-size:26px;font-weight:700}
.mb{display:flex;gap:8px;margin-top:12px}
.mb i{flex:1;height:38px;border-radius:6px;background:#f2ece0;border-top:3px solid var(--a,#D97757)}
.arrw{position:relative;width:150px;height:8px;border-radius:4px;background:rgba(74,124,89,.22);overflow:hidden;flex:none}
.arrw i{position:absolute;inset:0;width:45%;border-radius:4px;background:linear-gradient(90deg,transparent,#7ff0df,transparent);
 animation:flow2 1.6s linear infinite}
@keyframes flow2{from{transform:translateX(-110%)}to{transform:translateX(260%)}}
.lbl{font-family:"Noto Sans Mono CJK TC",monospace;font-size:21px;color:#7ff0df;text-align:center;margin-top:14px;white-space:nowrap}
""", body="""
 <div class="kicker in" style="--d:.15s;color:#8fd3a5">TWO SCREENS</div>
 <div class="h2 in" style="--d:.45s;margin-top:18px;font-size:58px">操作在筆電，乾淨的那面給學生</div>
 <div class="two">
   <div class="dev dl in" style="--d:1.0s">
     <div class="dh">💻 &nbsp;OPERATOR CONSOLE · localhost:7860</div>
     <div class="scr">
       <div class="ui"><i></i><i></i><i class="hot"></i><i></i></div>
       <div class="ui"><i></i><i></i></div>
       <div class="mini"><div class="mt">控制方法的全貌</div>
         <div class="mb"><i style="--a:#D97757"></i><i style="--a:#1F3A6E"></i><i style="--a:#4A7C59"></i></div></div>
     </div>
   </div>
   <div style="display:flex;flex-direction:column;align-items:center">
     <div class="arrw fadein" style="--d:1.5s"><i></i></div>
     <div class="lbl fadein" style="--d:1.7s">SSE push</div>
   </div>
   <div class="dev dp in" style="--d:1.4s">
     <div class="dh">🖥️ &nbsp;PROJECTOR · /display · F11</div>
     <div class="scr" style="background:#f6f1e6;border-color:#d8cdb3">
       <div class="mini" style="padding:26px 28px">
         <div class="mt" style="font-size:38px">控制方法的全貌</div>
         <div class="mb" style="margin-top:18px"><i style="--a:#D97757;height:62px"></i><i style="--a:#1F3A6E;height:62px"></i><i style="--a:#4A7C59;height:62px"></i></div>
       </div>
     </div>
   </div>
 </div>
 <div class="sub in" style="--d:2.5s;margin-top:42px;font-size:30px">
   卡片一產生就推過去 — 不再每秒輪詢重算，投影機只負責淡入
 </div>
""")

scene("scene15_lang", "多語與主題", 8, SAGE, VIOLET, css="""
.lgs{display:flex;gap:14px;flex-wrap:wrap;justify-content:center;max-width:1500px;margin-top:40px}
.lc{padding:16px 32px;border-radius:999px;font-size:31px;font-weight:700;white-space:nowrap;
 background:rgba(20,36,28,.8);border:1.5px solid rgba(120,190,150,.34);color:#c8ebd4}
.th{display:flex;gap:24px;margin-top:44px}
.tsw{width:300px;border-radius:16px;overflow:hidden;border:1.5px solid rgba(150,200,255,.22)}
.tsw .top{height:96px;display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:700}
.tsw .bot{padding:14px;font-size:24px;text-align:center;background:rgba(12,20,32,.8);color:rgba(232,238,247,.72);white-space:nowrap}
""", body="""
 <div class="kicker in" style="--d:.15s;color:#8fd3a5">ONE MODEL, MANY ROOMS</div>
 <div class="h2 in" style="--d:.45s;margin-top:18px;font-size:58px">同一台筆電，八種投影語言</div>
 <div class="lgs">
   <div class="lc pop" style="--d:.95s">中文</div>
   <div class="lc pop" style="--d:1.03s">English</div>
   <div class="lc pop" style="--d:1.11s">日本語</div>
   <div class="lc pop" style="--d:1.19s">한국어</div>
   <div class="lc pop" style="--d:1.27s">Tiếng Việt</div>
   <div class="lc pop" style="--d:1.35s">Bahasa Indonesia</div>
   <div class="lc pop" style="--d:1.43s">Español</div>
   <div class="lc pop" style="--d:1.51s">Français</div>
 </div>
 <div class="th">
   <div class="tsw in" style="--d:2.0s"><div class="top" style="background:linear-gradient(135deg,#0f172a,#1e293b);color:#e2e8f0">Dark</div>
     <div class="bot">暗教室 / 投影機</div></div>
   <div class="tsw in" style="--d:2.15s"><div class="top" style="background:linear-gradient(135deg,#f8fafc,#e2e8f0);color:#1e293b">Light</div>
     <div class="bot">亮教室 / 螢幕分享</div></div>
   <div class="tsw in" style="--d:2.3s"><div class="top" style="background:linear-gradient(135deg,#f6f1e6,#efe7d3);color:#29261b">Paper</div>
     <div class="bot">米黃紙 / 黑板派</div></div>
 </div>
 <div class="sub in" style="--d:2.9s;margin-top:40px;font-size:30px">翻譯也是同一顆 Gemma 4 做的 — 一樣不出這台機器</div>
""")

# ══════════════════════════════════════════════════════════════════
# 戲劇景 — 全片唯一（前一刀 fadeblack）
# ══════════════════════════════════════════════════════════════════

scene("scene16_nocloud", "戲劇：沒有雲端", 10, TEAL, VIOLET, css="""
body{--c1:45,212,191;--c2:139,92,246}
.bg{background:radial-gradient(1400px 900px at 50% 44%,rgba(45,212,191,.10),transparent 66%),
 linear-gradient(160deg,#060a12 0%,#03050a 60%,#010204 100%)}
.aur{opacity:.28}
@keyframes shk{10%,90%{transform:translateX(-3px)}20%,80%{transform:translateX(6px)}
 30%,50%,70%{transform:translateX(-11px)}40%,60%{transform:translateX(11px)}100%{transform:none}}
/* Two animation shorthands on one element overwrite each other (the element would
   stay at opacity:0), so rise + shake are declared as a single animation list. */
.in.shk{animation:rise 1s cubic-bezier(.16,1,.3,1) var(--d,0s) both,
 shk .5s cubic-bezier(.36,.07,.19,.97) 2s both}
.mega{font-size:158px;font-weight:900;line-height:1.1;text-align:center;letter-spacing:.01em;color:#f4f8ff;
 text-shadow:0 0 90px rgba(45,212,191,.34)}
.strike{position:relative;display:inline-block;color:rgba(232,238,247,.34)}
.strike::after{content:"";position:absolute;left:-14px;right:-14px;top:52%;height:9px;border-radius:5px;background:#e0574f;
 transform:scaleX(0);transform-origin:left;animation:sx .6s cubic-bezier(.7,0,.3,1) both;animation-delay:2.5s;
 box-shadow:0 0 34px rgba(224,87,79,.6)}
@keyframes sx{to{transform:scaleX(1)}}
.byte{margin-top:52px;font-family:"Noto Sans Mono CJK TC",monospace;font-size:44px;letter-spacing:.2em;
 color:#7ff0df;white-space:nowrap}
""", body="""
 <div class="kicker in" style="--d:.3s">THE WHOLE POINT</div>
 <div class="mega in shk" style="--d:.8s;margin-top:40px">沒有<span class="strike">雲端</span></div>
 <div class="mega pop" style="--d:3.2s;margin-top:24px;font-size:96px;color:#7ff0df">一切都在這台筆電上</div>
 <div class="byte in" style="--d:4.2s">0 BYTES LEAVE THE ROOM</div>
""")

scene("scene17_why", "四個理由", 10, TEAL, BLUE, css="""
.rg{display:grid;grid-template-columns:repeat(2,660px);gap:24px;margin-top:48px;justify-content:center}
.rc{padding:34px 38px;border-radius:22px;text-align:left;
 background:rgba(14,26,44,.86);border:1.5px solid rgba(150,200,255,.20)}
.rn{font-family:"Noto Sans Mono CJK TC",monospace;font-size:22px;color:#6fe3d2;letter-spacing:.2em}
.rt{font-size:44px;font-weight:800;color:#f4f8ff;margin-top:12px;white-space:nowrap}
.rd{font-size:27px;color:rgba(232,238,247,.7);margin-top:14px;line-height:1.55}
""", body="""
 <div class="kicker in" style="--d:.15s">WHY NOT JUST USE A CLOUD LLM</div>
 <div class="h2 in" style="--d:.45s;margin-top:18px;font-size:58px">四個理由，順序不能換</div>
 <div class="rg">
   <div class="rc in" style="--d:1.0s"><div class="rn">01 · PRIVACY</div><div class="rt">🔒 隱私與法規</div>
     <div class="rd">很多學校的資安規範，根本不允許把含學生聲音的課堂錄音送到第三方伺服器。</div></div>
   <div class="rc in" style="--d:1.3s"><div class="rn">02 · COST</div><div class="rt">💰 成本公平</div>
     <div class="rd">預算緊的學校付不起「每堂課、每學期、每年」的 token 帳單。裝一次，之後邊際成本是零。</div></div>
   <div class="rc in" style="--d:1.6s"><div class="rn">03 · LATENCY</div><div class="rt">⚡ 延遲</div>
     <div class="rd">即時視覺化要在 2 秒內完成，光是雲端來回就吃掉 2–3 秒。</div></div>
   <div class="rc in" style="--d:1.9s"><div class="rn">04 · OFFLINE</div><div class="rt">📡 離線可用</div>
     <div class="rd">偏鄉教室、不穩的 Wi-Fi、臨時斷網 — Sensei 照常上課。</div></div>
 </div>
""")

# ══════════════════════════════════════════════════════════════════
# 成果章 — violet / deep
# ══════════════════════════════════════════════════════════════════

scene("scene18_stats", "數據", 7, VIOLET, BLUE, js=COUNTUP, css="""
.sg{display:flex;gap:34px;margin-top:56px}
.sc{width:380px;padding:40px 30px;border-radius:24px;text-align:center;
 background:rgba(20,26,50,.86);border:1.5px solid rgba(167,139,250,.28)}
.sv{font-size:118px;font-weight:900;line-height:1;
 background:linear-gradient(100deg,#f4f8ff,#c4b5fd);-webkit-background-clip:text;background-clip:text;color:transparent}
.su{font-size:30px;color:rgba(232,238,247,.7);margin-top:16px;white-space:nowrap}
.unit{font-size:52px;font-weight:800;color:#c4b5fd}
""", body="""
 <div class="kicker in" style="--d:.15s;color:#c4b5fd">BY THE NUMBERS</div>
 <div class="sg">
   <div class="sc in" style="--d:.7s"><div class="sv"><span class="num" data-to="7" data-d="1.0" data-dur="1.1">0</span></div>
     <div class="su">種視覺化模板</div></div>
   <div class="sc in" style="--d:.9s"><div class="sv"><span class="num" data-to="8" data-d="1.2" data-dur="1.1">0</span></div>
     <div class="su">種投影語言</div></div>
   <div class="sc in" style="--d:1.1s"><div class="sv"><span class="num" data-to="11" data-d="1.4" data-dur="1.2">0</span><span class="unit">GB</span></div>
     <div class="su">VRAM 全部用量</div></div>
   <div class="sc in" style="--d:1.3s"><div class="sv" style="background:linear-gradient(100deg,#f4f8ff,#7ff0df);-webkit-background-clip:text;background-clip:text">0</div>
     <div class="su">次雲端 API 呼叫</div></div>
 </div>
 <div class="sub in" style="--d:2.4s;margin-top:52px;font-size:32px">
   一台 RTX 4080 筆電，同時裝得下 Whisper large-v3 與 Gemma 4
 </div>
""")

scene("scene19_after", "課後", 8, VIOLET, PLUM, css="""
.fl{display:flex;align-items:center;gap:28px;margin-top:52px}
.fb{width:400px;padding:34px 30px;border-radius:22px;text-align:center;
 background:rgba(24,20,44,.86);border:1.5px solid rgba(167,139,250,.26)}
.fi{font-size:60px;line-height:1}
.ft{font-size:38px;font-weight:800;color:#f4f8ff;margin-top:16px;white-space:nowrap}
.fd{font-size:25px;color:rgba(232,238,247,.64);margin-top:12px;line-height:1.5}
.ar{font-size:50px;color:rgba(196,181,253,.6);flex:none}
""", body="""
 <div class="kicker in" style="--d:.15s;color:#c4b5fd">AFTER THE LECTURE</div>
 <div class="h2 in" style="--d:.45s;margin-top:18px;font-size:58px">下課之後，這堂課還留著</div>
 <div class="fl">
   <div class="fb in" style="--d:1.0s"><div class="fi">🗂️</div><div class="ft">自動存檔</div>
     <div class="fd">每張卡片存成 JSON<br>＋可直接開的 HTML</div></div>
   <div class="ar pop" style="--d:1.35s">→</div>
   <div class="fb in" style="--d:1.6s"><div class="fi">📑</div><div class="ft">今日總結</div>
     <div class="fd">整堂課的逐字稿<br>收斂成一張總結卡</div></div>
   <div class="ar pop" style="--d:1.95s">→</div>
   <div class="fb in" style="--d:2.2s"><div class="fi">🎓</div><div class="ft">學生講義</div>
     <div class="fd">一鍵輸出 handout.html<br>丟到教學平台就是筆記</div></div>
 </div>
 <div class="sub in" style="--d:2.9s;margin-top:44px;font-size:30px">
   老師本來就在講的內容，不用再花一個晚上重做一次投影片
 </div>
""")

scene("scene20_glossary", "換課不改碼", 7, VIOLET, PLUM, css="""
.fs2{width:1180px;margin-top:44px;padding:32px 40px;border-radius:20px;text-align:left;
 background:rgba(10,14,28,.9);border:1.5px solid rgba(167,139,250,.24);
 font-family:"Noto Sans Mono CJK TC",monospace}
.dir{font-size:29px;color:#c4b5fd;letter-spacing:.04em}
.fi2{font-size:27px;color:#dbe4f2;padding:9px 0 9px 40px;white-space:nowrap}
.fi2 b{color:#7ff0df;font-weight:600}
.cmt{color:#7c8aa5}
""", body="""
 <div class="kicker in" style="--d:.15s;color:#c4b5fd">NO CODE REQUIRED</div>
 <div class="h2 in" style="--d:.45s;margin-top:18px;font-size:56px">換一門課，不用改一行 Python</div>
 <div class="fs2 in" style="--d:1.0s">
   <div class="dir">glossaries/</div>
   <div class="fi2 fadein" style="--d:1.5s">├── <b>auto_control.zh.txt</b> <span class="cmt">— 自動控制 / 工業自動化</span></div>
   <div class="fi2 fadein" style="--d:1.7s">├── <b>machine_learning.zh.txt</b> <span class="cmt">— 機器學習 / 深度學習</span></div>
   <div class="fi2 fadein" style="--d:1.9s">├── <b>wind_energy.zh.txt</b> <span class="cmt">— 風力發電 / 風機監控</span></div>
   <div class="fi2 fadein" style="--d:2.1s">├── <b>general.en.txt</b> <span class="cmt">— English lectures</span></div>
   <div class="fi2 fadein" style="--d:2.3s">└── <b>_template.txt</b> <span class="cmt">← 複製這個，填上你的專有名詞</span></div>
 </div>
 <div class="sub in" style="--d:2.9s;margin-top:38px;font-size:30px">
   醫學、法律、財金 — 貢獻一門課，只要送一個<span style="color:#c4b5fd;font-weight:700">文字檔</span>
 </div>
""")

scene("scene21_stack", "開源", 9, VIOLET, TEAL, css="""
.sk{display:flex;gap:22px;margin-top:46px;flex-wrap:wrap;justify-content:center;max-width:1500px}
.sb{padding:26px 40px;border-radius:18px;text-align:center;
 background:rgba(18,26,46,.86);border:1.5px solid rgba(150,200,255,.22)}
.sn2{font-size:36px;font-weight:800;color:#f4f8ff;white-space:nowrap}
.sr{font-size:24px;color:rgba(232,238,247,.6);margin-top:8px;white-space:nowrap}
.lic{margin-top:46px;padding:20px 48px;border-radius:999px;font-size:33px;font-weight:700;white-space:nowrap;
 background:rgba(45,212,191,.12);border:1.5px solid rgba(45,212,191,.48);color:#7ff0df}
""", body="""
 <div class="kicker in" style="--d:.15s">BUILT ON OPEN WEIGHTS</div>
 <div class="h2 in" style="--d:.45s;margin-top:18px;font-size:58px">全部都是你裝得起的東西</div>
 <div class="sk">
   <div class="sb in" style="--d:1.0s"><div class="sn2">Gemma 4 e2b</div><div class="sr">結構化引擎 · 開放權重</div></div>
   <div class="sb in" style="--d:1.15s"><div class="sn2">Faster-Whisper</div><div class="sr">large-v3 · MIT</div></div>
   <div class="sb in" style="--d:1.3s"><div class="sn2">Ollama</div><div class="sr">本機推論 · 一行安裝</div></div>
   <div class="sb in" style="--d:1.45s"><div class="sn2">Pydantic v2</div><div class="sr">結構驗證</div></div>
   <div class="sb in" style="--d:1.6s"><div class="sn2">Gradio + FastAPI</div><div class="sr">操作台 + 投影頁</div></div>
 </div>
 <div class="lic in glow" style="--d:2.3s">CC-BY 4.0 · 拿去用，拿去改，拿去教你的課</div>
""")

scene("scene22_cta", "CTA", 10, TEAL, VIOLET, fx=True, css="""
.url{margin-top:44px;font-family:"Noto Sans Mono CJK TC",monospace;font-size:52px;font-weight:600;
 color:#7ff0df;letter-spacing:.02em;white-space:nowrap;
 padding:22px 54px;border-radius:18px;background:rgba(45,212,191,.10);border:1.5px solid rgba(45,212,191,.42)}
.tri{display:flex;gap:20px;margin-top:44px}
.tri .chip{font-size:32px;padding:18px 34px}
.sig{margin-top:52px;text-align:center;font-size:28px;line-height:1.7;color:rgba(232,238,247,.6)}
""", body="""
 <div class="pop" style="--d:.3s;display:flex;align-items:baseline;gap:30px">
   <div class="h1" style="font-size:158px;line-height:1">Sensei</div>
   <div style="font-size:74px;font-weight:300;color:rgba(232,238,247,.4);letter-spacing:.22em">先生</div>
 </div>
 <div class="sub in" style="--d:1.0s;margin-top:26px;font-size:42px">讓任何一位老師，都能有一位共同教學者</div>
 <div class="tri">
   <div class="chip in" style="--d:1.5s">🔒 不出教室</div>
   <div class="chip in" style="--d:1.65s">💰 零邊際成本</div>
   <div class="chip in" style="--d:1.8s">⚡ 一秒上牆</div>
 </div>
 <div class="url in glow" style="--d:2.4s">github.com/dofliu/Sensei</div>
 <div class="sig in" style="--d:3.1s">
   劉瑞弘 · 國立勤益科技大學 智慧自動化工程系 · DOF Lab<br>
   Whisper + Gemma 4 + Ollama &nbsp;·&nbsp; 100% on-device
 </div>
""")

# ══════════════════════════════════════════════════════════════════

TRANSITIONS = {
    "scene01_hook": "fade", "scene02_problem": "smoothup", "scene03_position": "circleopen",
    "scene04_pipeline": "smoothleft", "scene05_asr": "fade", "scene06_tools": "circleopen",
    "scene07_layers": "smoothup", "scene08_templates": "fade", "scene09_enum": "circleopen",
    "scene10_compare": "fade", "scene11_flow": "smoothleft", "scene12_trigger": "fade",
    "scene13_quiz": "circleopen", "scene14_display": "fade", "scene15_lang": "fadeblack",
    "scene16_nocloud": "fade", "scene17_why": "smoothup", "scene18_stats": "fade",
    "scene19_after": "circleopen", "scene20_glossary": "smoothleft", "scene21_stack": "fade",
}


def main() -> None:
    import json
    sb = {"fps": 30, "width": 1920, "height": 1080, "xfade": 0.6, "scenes": []}
    for i, s in enumerate(SCENES):
        html = (SHELL
                .replace("__TITLE__", s["title"])
                .replace("__C1__", s["c1"]).replace("__C2__", s["c2"])
                .replace("__DUR__", str(s["dur"]))
                .replace("__CSS__", s["css"])
                .replace("__FX__", FX if s["fx"] else "")
                .replace("__BODY__", s["body"])
                .replace("__JS__", s["js"]))
        (OUT / f"{s['name']}.html").write_text(html, encoding="utf-8")
        entry = {"file": f"{s['name']}.html", "duration": s["dur"]}
        if i < len(SCENES) - 1:
            entry["transition"] = TRANSITIONS[s["name"]]
        sb["scenes"].append(entry)
    (OUT / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(s["dur"] for s in SCENES) - (len(SCENES) - 1) * sb["xfade"]
    print(f"{len(SCENES)} scenes -> {total:.1f}s ({int(total//60)}:{total%60:04.1f})")


if __name__ == "__main__":
    main()
