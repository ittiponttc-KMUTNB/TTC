import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import time

st.set_page_config(page_title="🏇 Horse Race Leaderboard", page_icon="🏇", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Kanit:wght@400;700;900&family=Sarabun:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
.main { background-color: #0d1b2a; }
[data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #0d1b2a 0%, #1a2f45 100%); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #0a1628; border-right: 1px solid #1e3a5f; }
h1,h2,h3 { color:#f0c040 !important; font-family:'Kanit',sans-serif !important; }
.stat-card { background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1); border-radius:12px; padding:16px; text-align:center; }
.stat-value { font-family:'Kanit',sans-serif; font-size:2rem; font-weight:900; color:#f0c040; }
.stat-label { font-family:'Sarabun',sans-serif; font-size:.82rem; color:#7ab3d4; }
.race-title { font-family:'Kanit',sans-serif; font-size:2.6rem; font-weight:900; color:#f0c040; text-align:center; text-shadow:0 0 30px rgba(240,192,64,.5); letter-spacing:2px; margin-bottom:.1rem; }
.race-subtitle { font-family:'Sarabun',sans-serif; font-size:1.05rem; color:#7ab3d4; text-align:center; margin-bottom:1.6rem; }
.section-header { font-family:'Kanit',sans-serif; font-size:1.15rem; font-weight:700; color:#f0c040; border-bottom:2px solid rgba(240,192,64,.3); padding-bottom:7px; margin-bottom:14px; }
.stButton>button { font-family:'Kanit',sans-serif !important; font-weight:700 !important; border-radius:10px !important; border:none !important; padding:.55rem 1.6rem !important; font-size:1rem !important; transition:all .2s !important; }
.stButton>button:hover { transform:translateY(-2px); }
</style>
""", unsafe_allow_html=True)

# ─── Constants ────────────────────────────────────────────────────────────────
MEDAL = {1:"🥇", 2:"🥈", 3:"🥉"}
HORSE = "🏇"   # ม้าทุกตัวเหมือนกัน (คนขี่ม้า)

DEFAULT_PLAYERS = [
    {"ชื่อทีม": "ทีมแดง",    "คะแนน": 85},
    {"ชื่อทีม": "ทีมน้ำเงิน","คะแนน": 72},
    {"ชื่อทีม": "ทีมเขียว",  "คะแนน": 91},
    {"ชื่อทีม": "ทีมเหลือง", "คะแนน": 68},
    {"ชื่อทีม": "ทีมม่วง",   "คะแนน": 77},
]

if "players"  not in st.session_state: st.session_state.players  = pd.DataFrame(DEFAULT_PLAYERS)
if "animate"  not in st.session_state: st.session_state.animate  = False
if "prev_pos" not in st.session_state: st.session_state.prev_pos = {}


# ─── Build HTML ───────────────────────────────────────────────────────────────
def build_full_html(df_sorted: pd.DataFrame, progress: dict) -> str:
    lanes_html = ""
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        rank      = i + 1
        name      = str(row["ชื่อทีม"])[:18]
        score     = int(row["คะแนน"])
        pct       = progress.get(name, 0)
        left      = max(4, min(86, pct * 0.82 + 4))
        dust_left = max(0, left - 7)

        rank_sym  = MEDAL.get(rank, str(rank))
        rank_col  = {1:"#FFD700", 2:"#C0C0C0", 3:"#CD7F32"}.get(rank, "#7ab3d4")
        ldr_bg    = "rgba(255,215,0,0.07)" if rank == 1 else "rgba(0,0,0,0.22)"
        ldr_bdr   = "rgba(255,215,0,0.35)" if rank == 1 else "rgba(255,255,255,0.07)"
        ldr_anim  = "leader-glow 1.8s ease-in-out infinite" if rank == 1 else "none"
        # ม้านำวิ่งเร็วกว่า ม้าตามช้ากว่า
        spd       = "0.28s" if rank == 1 else f"{0.34 + i*0.03:.2f}s"
        d_delay   = f"{i*0.08:.2f}s"

        lanes_html += f"""
        <div style="display:flex;align-items:center;
                    margin:7px 18px;
                    background:{ldr_bg};
                    border-radius:40px;
                    padding:6px 14px;
                    border:1px solid {ldr_bdr};
                    position:relative;
                    min-height:70px;
                    animation:{ldr_anim};">

            <!-- อันดับ -->
            <div style="font-family:'Kanit',sans-serif;font-size:1.3rem;font-weight:900;
                        width:36px;text-align:center;flex-shrink:0;
                        color:{rank_col};text-shadow:0 0 10px {rank_col};">
                {rank_sym}
            </div>

            <!-- ลู่วิ่ง -->
            <div style="flex:1;height:50px;
                        background:rgba(255,255,255,0.03);
                        border-radius:25px;
                        position:relative;overflow:visible;
                        margin:0 10px;">

                <!-- horse-wrap: ชื่อทีม(ด้านหลัง/ซ้าย) + ม้า(หันขวา) เคลื่อนที่พร้อมกัน -->
                <div style="position:absolute;
                            top:50%;
                            left:{left:.1f}%;
                            transform:translateY(-50%);
                            transition:left 0.75s cubic-bezier(0.22,1,0.36,1);
                            display:flex;
                            flex-direction:row;
                            align-items:center;
                            z-index:10;
                            gap:5px;">

                    <!-- ชื่อทีม: อยู่ด้านหลังม้า (ซ้าย) -->
                    <div style="white-space:nowrap;
                                font-family:'Kanit',sans-serif;
                                font-size:0.70rem;
                                font-weight:700;
                                color:#fff;
                                background:rgba(0,0,0,0.72);
                                border:1px solid rgba(255,255,255,0.28);
                                border-radius:20px;
                                padding:2px 8px;
                                line-height:1.5;">
                        {name}
                    </div>

                    <!-- ม้า: scaleX(-1) flip ให้หันขวา + gallop -->
                    <div style="font-size:2.4rem;
                                line-height:1;
                                display:inline-block;
                                filter:drop-shadow(2px 3px 5px rgba(0,0,0,0.85));
                                animation:gallop {spd} ease-in-out infinite;
                                transform-origin:center center;">
                        {HORSE}
                    </div>
                </div>

                <!-- ฝุ่นด้านหลัง -->
                <div style="position:absolute;top:62%;
                            left:{dust_left:.1f}%;
                            font-size:0.75rem;
                            animation:dust 0.5s ease-out infinite;
                            animation-delay:{d_delay};
                            pointer-events:none;z-index:5;">
                    💨
                </div>

                <!-- ธงปลายทาง -->
                <div style="position:absolute;right:14px;top:50%;
                            transform:translateY(-50%);
                            font-size:1.3rem;opacity:0.6;
                            animation:flag-wave 1.4s ease-in-out infinite;">
                    🏁
                </div>
            </div>

            <!-- คะแนน -->
            <div style="font-family:'Kanit',sans-serif;font-size:1.05rem;font-weight:700;
                        background:rgba(240,192,64,0.12);
                        border:1px solid rgba(240,192,64,0.4);
                        color:#f0c040;padding:4px 14px;border-radius:20px;
                        min-width:68px;text-align:center;flex-shrink:0;">
                {score}
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Kanit:wght@400;700;900&family=Sarabun:wght@400;600&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:transparent; padding:4px; }}

  /* ══ ม้า gallop: body โยนขึ้นลง + เอียง ══
     scaleX เป็นบวกตลอด → ม้าหันขวา (ทิศทางวิ่ง) */
  @keyframes gallop {{
    0%   {{ transform:scaleX(-1.00) translateY(-50%) rotate(-3deg); }}
    12%  {{ transform:scaleX(-1.05) translateY(-60%) rotate(-1deg); }}
    25%  {{ transform:scaleX(-0.95) translateY(-42%) rotate( 3deg); }}
    38%  {{ transform:scaleX(-1.04) translateY(-57%) rotate(-2deg); }}
    50%  {{ transform:scaleX(-0.96) translateY(-44%) rotate( 2deg); }}
    62%  {{ transform:scaleX(-1.03) translateY(-55%) rotate(-1deg); }}
    75%  {{ transform:scaleX(-0.97) translateY(-46%) rotate( 1deg); }}
    88%  {{ transform:scaleX(-1.02) translateY(-54%) rotate(-2deg); }}
    100% {{ transform:scaleX(-1.00) translateY(-50%) rotate(-3deg); }}
  }}

  @keyframes dust {{
    0%   {{ opacity:.8;  transform:scale(0.4) translateX(0);     }}
    60%  {{ opacity:.3;  transform:scale(1.4) translateX(-18px); }}
    100% {{ opacity:0;   transform:scale(2.2) translateX(-28px); }}
  }}

  @keyframes leader-glow {{
    0%,100% {{ box-shadow:0 0 10px rgba(255,215,0,.2); }}
    50%      {{ box-shadow:0 0 30px rgba(255,215,0,.6); }}
  }}

  @keyframes flag-wave {{
    0%,100% {{ transform:translateY(-50%) rotate( 0deg); }}
    40%      {{ transform:translateY(-55%) rotate(10deg); }}
    80%      {{ transform:translateY(-50%) rotate(-3deg); }}
  }}
</style>
</head>
<body>
<div style="background:linear-gradient(180deg,#174d17 0%,#2d7b2d 50%,#174d17 100%);
            border-radius:18px;
            padding:16px 0 12px 0;
            border:3px solid #3a7a3a;
            box-shadow:0 8px 40px rgba(0,0,0,.6);
            position:relative;overflow:hidden;">

  <!-- เส้นแนวตั้งตกแต่ง -->
  <div style="position:absolute;inset:0;
              background:repeating-linear-gradient(
                90deg,transparent 0,transparent 59px,
                rgba(255,255,255,.015) 59px,rgba(255,255,255,.015) 60px);
              pointer-events:none;border-radius:15px;"></div>

  <div style="text-align:center;font-family:'Kanit',sans-serif;
              font-size:.8rem;color:#4a8c4a;letter-spacing:3px;margin-bottom:6px;">
    ══ สนามแข่ง ══
  </div>

  {lanes_html}

  <div style="text-align:right;font-family:'Sarabun',sans-serif;
              font-size:.75rem;color:#4a8c4a;margin:4px 32px 0 0;">
    🏁 เส้นชัย
  </div>
</div>
</body>
</html>"""


# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-header">⚙️ จัดการข้อมูล</div>', unsafe_allow_html=True)
    st.markdown("**✏️ แก้ไขผู้เข้าแข่งขัน**")
    edited_df = st.data_editor(
        st.session_state.players, num_rows="dynamic", use_container_width=True,
        column_config={
            "ชื่อทีม": st.column_config.TextColumn("ชื่อทีม", width="medium"),
            "คะแนน":  st.column_config.NumberColumn("คะแนน", min_value=0, max_value=9999, step=1),
        }, key="player_editor",
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ อัปเดต", use_container_width=True, type="primary"):
            st.session_state.players = edited_df.dropna(subset=["ชื่อทีม"]).reset_index(drop=True)
            st.session_state.animate = True
            st.rerun()
    with c2:
        if st.button("🔄 รีเซ็ต", use_container_width=True):
            st.session_state.players = pd.DataFrame(DEFAULT_PLAYERS)
            st.session_state.animate = False
            st.session_state.prev_pos = {}
            st.rerun()

    st.divider()
    st.markdown("**➕ เพิ่มคะแนนรวดเร็ว**")
    qname = st.selectbox("เลือกทีม", options=st.session_state.players["ชื่อทีม"].tolist(), key="qname")
    qpts  = st.number_input("คะแนนที่เพิ่ม", 1, 100, 5, key="qpts")
    if st.button("➕ เพิ่มคะแนน", use_container_width=True, type="primary"):
        idx = st.session_state.players[st.session_state.players["ชื่อทีม"] == qname].index
        if len(idx) > 0:
            st.session_state.players.at[idx[0], "คะแนน"] += qpts
            st.session_state.animate = True
            st.rerun()

    st.divider()
    st.markdown('<div class="section-header">🎨 ตั้งค่า</div>', unsafe_allow_html=True)
    race_title  = st.text_input("ชื่อการแข่งขัน", value="🏆 การแข่งขันคะแนน", key="rtitle")
    max_display = st.slider("แสดงสูงสุด (ทีม)", 3, 10, 8, key="maxd")


# ─── Main ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="race-title">🏇 HORSE RACE LEADERBOARD 🏇</div>', unsafe_allow_html=True)
st.markdown(f'<div class="race-subtitle">{race_title}</div>', unsafe_allow_html=True)

df = st.session_state.players.copy()
df["คะแนน"] = pd.to_numeric(df["คะแนน"], errors="coerce").fillna(0).astype(int)
df_sorted = df.sort_values("คะแนน", ascending=False).head(max_display).reset_index(drop=True)

if len(df_sorted) > 0:
    ca, cb, cc, cd = st.columns(4)
    leader = df_sorted.iloc[0]["ชื่อทีม"]
    with ca: st.markdown(f'<div class="stat-card"><div class="stat-value">{len(df_sorted)}</div><div class="stat-label">ทีมเข้าแข่ง</div></div>', unsafe_allow_html=True)
    with cb: st.markdown(f'<div class="stat-card"><div class="stat-value">{df_sorted["คะแนน"].max()}</div><div class="stat-label">คะแนนสูงสุด</div></div>', unsafe_allow_html=True)
    with cc: st.markdown(f'<div class="stat-card"><div class="stat-value">{int(df_sorted["คะแนน"].mean())}</div><div class="stat-label">คะแนนเฉลี่ย</div></div>', unsafe_allow_html=True)
    with cd: st.markdown(f'<div class="stat-card"><div class="stat-value" style="font-size:1.05rem">{leader}</div><div class="stat-label">🥇 ผู้นำ</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
track_ph = st.empty()

def final_pos(df_s):
    mx = int(df_s["คะแนน"].max()) or 1
    return {r["ชื่อทีม"]: (r["คะแนน"] / mx * 100) for _, r in df_s.iterrows()}

def track_height(n):
    return n * 88 + 72

# ─── Animate ──────────────────────────────────────────────────────────────────
if st.session_state.animate and len(df_sorted) > 0:
    target = final_pos(df_sorted)
    start  = {n: st.session_state.prev_pos.get(n, 0) for n in target}
    h      = track_height(len(df_sorted))
    for step in range(41):
        t     = step / 40
        eased = 1 - (1 - t) ** 5
        curr  = {n: start[n] + (target[n] - start[n]) * eased for n in target}
        with track_ph:
            components.html(build_full_html(df_sorted, curr), height=h, scrolling=False)
        time.sleep(0.03)
    st.session_state.prev_pos = target
    st.session_state.animate  = False
else:
    if len(df_sorted) > 0:
        pos = final_pos(df_sorted)
        if not st.session_state.prev_pos:
            st.session_state.prev_pos = pos
        components.html(build_full_html(df_sorted, pos),
                        height=track_height(len(df_sorted)), scrolling=False)
    else:
        st.warning("ยังไม่มีทีม กรุณาเพิ่มข้อมูลใน Sidebar")

# Start button
st.markdown("<br>", unsafe_allow_html=True)
_, mid, _ = st.columns([2, 1, 2])
with mid:
    if st.button("🏇 เริ่มวิ่ง!", use_container_width=True, type="primary"):
        st.session_state.prev_pos = {}
        st.session_state.animate  = True
        st.rerun()

# ─── Podium ────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">🏆 โพเดียม</div>', unsafe_allow_html=True)
if len(df_sorted) >= 1:
    top3  = df_sorted.head(3)
    order = [1, 0, 2] if len(top3) >= 3 else list(range(len(top3)))
    cols  = st.columns(3)
    mts   = ["55px","80px","25px"]
    glows = ["none","0 0 28px rgba(255,215,0,.45)","none"]
    for ci, ri in enumerate(order):
        if ri < len(top3):
            row = top3.iloc[ri]
            with cols[ci]:
                st.markdown(f"""
                <div style="text-align:center;background:rgba(255,255,255,.05);
                            border-radius:16px;padding:18px 10px;
                            border:1px solid rgba(255,255,255,.1);
                            box-shadow:{glows[ci]};margin-top:{mts[ci]};">
                    <div style="font-size:2.3rem;">{HORSE}</div>
                    <div style="font-size:1.9rem">{MEDAL.get(ri+1,'')}</div>
                    <div style="font-family:'Kanit',sans-serif;font-weight:700;
                                color:white;font-size:1.05rem;margin:6px 0 3px">{row['ชื่อทีม']}</div>
                    <div style="font-family:'Kanit',sans-serif;font-weight:900;
                                color:#f0c040;font-size:1.7rem">{int(row['คะแนน'])}</div>
                    <div style="font-family:'Sarabun',sans-serif;color:#7ab3d4;font-size:.78rem">คะแนน</div>
                </div>""", unsafe_allow_html=True)

# ─── Full Table ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">📊 ตารางคะแนนเต็ม</div>', unsafe_allow_html=True)
disp = df_sorted.copy()
disp.insert(0, "อันดับ", [MEDAL.get(i+1, f"#{i+1}") for i in range(len(disp))])
st.dataframe(
    disp[["อันดับ","ชื่อทีม","คะแนน"]], use_container_width=True, hide_index=True,
    column_config={"คะแนน": st.column_config.ProgressColumn(
        "คะแนน", min_value=0,
        max_value=int(disp["คะแนน"].max()) if len(disp) > 0 else 100,
        format="%d")}
)
st.markdown("""<div style="text-align:center;margin-top:36px;font-family:'Sarabun',sans-serif;
font-size:.78rem;color:rgba(255,255,255,.18);">🏇 Horse Race Leaderboard — สร้างด้วย Streamlit</div>""",
unsafe_allow_html=True)
