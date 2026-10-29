"""BEYOND THE CRASH — Streamlit investigation dashboard.
Input: CAROL_Aviation_EDA.csv, exported by the completed analysis notebook.
All statistics are calculated at runtime from the selected analytical population.
"""
from pathlib import Path
import html
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Beyond the Crash | Investigation Files", page_icon="✈", layout="wide", initial_sidebar_state="expanded")
ROOT = Path(__file__).resolve().parent
ORANGE, RED, CYAN = "#FF6B2B", "#EF4444", "#38BDF8"
WHITE, MUTED, PANEL = "#FFFFFF", "#CBD5E1", "#171D29"
UNKNOWN = {"", "Unknown", "Not Reported"}
FACTORS = {
    "Personnel issues": "Human Factors",
    "Aircraft": "Aircraft-Related Factors",
    "Environmental issues": "Environmental Factors",
    "Organizational issues": "Organizational Factors",
    "Not determined": "Undetermined",
}
CASES = [
    ("01", "THE DEADLIEST MOMENT", "Is the most frequently reported flight phase also associated with the highest proportion of fatal accidents?"),
    ("02", "THE WEATHER PARADOX", "Are accidents recorded under VMC necessarily associated with less severe outcomes than accidents under IMC?"),
    ("03", "HUMAN ERROR OR MECHANICAL FAILURE?", "Which contributing-factor categories appear most frequently in official investigation findings?"),
    ("04", "DOES THE AIRCRAFT MATTER?", "How do recorded fatal-outcome proportions differ across aircraft categories and engine configurations?"),
    ("05", "THE SURVIVAL PARADOX", "Can an aircraft sustain substantial or destructive damage while recording zero fatalities?"),
    ("06", "THE HIDDEN PATTERN", "How do documented investigation findings differ between fatal and nonfatal aviation accidents?"),
]

FILTER_KEYS = ("wx", "air", "phase", "outcome")
def _filter_state_css(selected):
    """Selected value -> orange text + subtle orange border; empty -> grey 'Select option'.
    `selected` maps each filter key to its current value (None when empty)."""
    out = []
    for k in FILTER_KEYS:
        on = selected.get(k) is not None
        txt, bd = ("#FF6B2B", "rgba(255,107,43,.65)") if on else ("#94A3B8", "#303848")
        w = f'.st-key-{k}'
        out.append(f'{w} [data-baseweb="select"] > div {{border-color:{bd}!important}}')
        out.append(f'{w} [data-baseweb="select"] div, {w} [role="combobox"], {w} input {{color:{txt}!important;-webkit-text-fill-color:{txt}!important;caret-color:{txt}!important}}')
        out.append(f'{w} input::placeholder {{color:#94A3B8!important;-webkit-text-fill-color:#94A3B8!important;opacity:1!important}}')
        out.append(f'{w} svg {{color:#CBD5E1!important}}')
    return "\n".join(out)

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&family=DM+Sans:wght@400;500;600;700&display=swap');
:root { color-scheme:dark; }
html, body, [data-testid="stApp"], [data-testid="stMain"] {background:#07090E!important;color:#FFFFFF!important;font-family:'DM Sans',sans-serif!important}
[data-testid="stSidebar"] {background:#10141D!important;border-right:1px solid #303848!important}
[data-testid="stSidebar"] * {color:#F1F5F9!important}
[data-testid="stHeader"] {background:rgba(7,9,14,.6)!important}
[data-testid="stMarkdownContainer"],p,span,label,h1,h2,h3 {color:inherit}
h1,h2,h3 {font-family:'Barlow Condensed',sans-serif!important;letter-spacing:.04em!important}
.block-container {padding-top:1.3rem!important;max-width:1500px!important;padding-bottom:5rem!important}
[data-testid="stMetric"] {background:#171D29;border:1px solid #303848;border-top:2px solid #FF6B2B;border-radius:12px;padding:18px 20px}
[data-testid="stMetricLabel"] * {color:#CBD5E1!important;font-size:.88rem!important}
[data-testid="stMetricValue"] * {color:#fff!important;font-family:'Barlow Condensed',sans-serif!important;font-size:2rem!important}
[data-baseweb="select"]>div, [data-testid="stMultiSelect"] [data-baseweb="select"]>div, [data-testid="stSelectbox"] [data-baseweb="select"]>div {background:#171D29!important;color:#FFFFFF!important;border-color:#465063!important}
[data-baseweb="popover"], [role="listbox"], [role="option"] {background:#171D29!important;color:#fff!important}
[data-baseweb="tag"] {background:#303848!important;color:#fff!important}
.stButton>button, [data-testid="stBaseButton-secondary"] {background:#222B3B!important;color:#FFFFFF!important;border:1px solid #566278!important;border-radius:8px!important;font-weight:700!important}
.stButton>button:hover {background:#FF6B2B!important;color:#07090E!important;border-color:#FF6B2B!important}
[data-testid="stFileUploader"] {border:1px dashed #566278;background:#10141D;border-radius:10px;padding:12px}
[data-testid="stDataFrame"], [data-testid="stTable"] {background:#171D29}
hr {border-color:#303848!important}
.hero {position:relative;overflow:hidden;min-height:400px;border:1px solid #303848;border-radius:17px;background:radial-gradient(ellipse at 76% 65%,rgba(255,107,43,.14),transparent 40%),linear-gradient(120deg,#0B0E15,#111722 72%,#0D1016);margin-bottom:30px;padding:54px 5%;isolation:isolate}
.hero:before {content:'';position:absolute;inset:0;background:linear-gradient(transparent 97%,rgba(56,189,248,.09) 98%),linear-gradient(90deg,transparent 97%,rgba(56,189,248,.09) 98%);background-size:52px 52px;transform:perspective(550px) rotateX(37deg) scale(1.8);opacity:.33;z-index:-1}
.hero:after {content:'';position:absolute;bottom:0;left:0;right:0;height:70px;background:linear-gradient(transparent,#07090E);z-index:-1}
.eyebrow {font-size:.76rem;color:#FFAC83!important;letter-spacing:.23em;font-weight:700}
.hero h1 {font-size:clamp(3.8rem,8vw,7.5rem)!important;line-height:.86;margin:26px 0 20px;letter-spacing:.015em!important;max-width:740px;color:#FFFFFF!important}
.hero p {color:#CBD5E1!important;font-size:1.09rem;letter-spacing:.02em}
.record {font-size:.72rem;letter-spacing:.18em;color:#CBD5E1!important;margin-top:50px}
.dot {display:inline-block;width:8px;height:8px;background:#EF4444;border-radius:100%;box-shadow:0 0 12px #EF4444;margin-right:9px;animation:pulse 3s ease-in-out infinite}
.flightart {position:absolute;width:48%;right:0;top:5%;opacity:.88;pointer-events:none;filter:drop-shadow(0 0 30px rgba(255,107,43,.15))}
.flightart path.flighttrail {stroke-dasharray:12 10;animation:trail 22s linear infinite}
@keyframes pulse {50% {opacity:.4;box-shadow:0 0 3px #EF4444}}
@keyframes trail {to {stroke-dashoffset:-440}}
.sectionline {display:flex;align-items:center;gap:15px;margin:40px 0 15px;color:#FFAB87!important;font-size:.73rem;letter-spacing:.19em;font-weight:700}
.sectionline:after {content:'';height:1px;flex:1;background:linear-gradient(90deg,#FF6B2B55,transparent)}
.casehead {padding:20px 0 8px;border-top:1px solid #303848;margin-top:32px}
.casehead h2 {font-size:clamp(2.1rem,4vw,3.5rem)!important;margin:.25rem 0 .55rem;color:#FFFFFF!important;line-height:1}
.casehead p {color:#CBD5E1!important;max-width:840px}
.note {border-left:2px solid #38BDF8;background:#111824;border-radius:0 8px 8px 0;padding:13px 18px;margin:13px 0 21px;color:#CBD5E1!important;font-size:.87rem;line-height:1.65}
.note strong {color:#FFF!important}
.poster {border:1px solid #303848;border-radius:11px;padding:24px;background:linear-gradient(115deg,#171D29,#10141D);min-height:155px}
.poster .k {color:#CBD5E1!important;font-size:.77rem;letter-spacing:.16em}
.poster .v {color:#FFFFFF!important;font-family:'Barlow Condensed',sans-serif;font-size:3rem;font-weight:700;line-height:1.2}
.footer {margin-top:44px;border-top:1px solid #303848;padding-top:28px;color:#CBD5E1!important}
@media(max-width:850px){.flightart{width:100%;opacity:.2}.hero{padding:35px 7%;min-height:360px}.hero h1{font-size:3.7rem!important}.record{margin-top:35px}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}

/* Controls: see consolidated FILTER STYLES block below */
[data-baseweb="popover"] [role="option"]:hover {background:#313E52!important}
[data-baseweb="popover"] [role="option"] *{color:inherit!important}
[data-baseweb="popover"] [aria-selected="true"] {background:#42312B!important;color:#FF6B2B!important}
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul[role="listbox"] {background:#171D29!important}
[data-testid="stSidebar"] [data-testid="stButton"] button {border-color:#68788B!important;color:#E7ECF2!important}
.case-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));grid-auto-rows:1fr;gap:16px;margin-top:10px}
@media(max-width:700px){.case-grid{grid-template-columns:minmax(0,1fr)}}
.case-tile {box-sizing:border-box;height:100%;background:linear-gradient(140deg,#171D29,#10141D);border:1px solid #303848;border-top:2px solid #FF6B2B;border-radius:12px;padding:21px;min-height:185px;cursor:default}
.case-tile span{font-size:.72rem;color:#FFAB87;letter-spacing:.16em;font-weight:700}
.case-tile h3{font-size:1.7rem;color:white!important;margin:12px 0 8px}
.case-tile p{font-size:.9rem;color:#CBD5E1!important;line-height:1.5}


/* ===== FILTER STYLES (selectboxes) =====
   Selected / empty text colour is injected per widget by Python (filter_state_css). */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {color:#FFFFFF!important}
[data-testid="stSelectbox"] [data-baseweb="select"] div,
[data-testid="stSelectbox"] [data-baseweb="select"] input {background-color:transparent!important}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
  background-color:#171D29!important;border:1px solid #303848!important;border-radius:9px!important;min-height:43px!important;cursor:pointer!important;box-shadow:none!important}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div {
  background-color:#171D29!important;border-color:#FF6B2B!important}
[data-testid="stSelectbox"] input::placeholder {color:#94A3B8!important;-webkit-text-fill-color:#94A3B8!important;opacity:1!important}
[data-testid="stSelectbox"] svg {color:#CBD5E1!important}
[data-testid="stElementContainer"]:has(#fs-marker), .element-container:has(#fs-marker) {display:none!important}

/* ===== DATA PREVIEW toggle ===== */
.st-key-preview_open button, .st-key-preview_active button, .st-key-preview_close button {
  background:#171D29!important;color:#FFFFFF!important;border:1px solid #303848!important;border-radius:8px!important;font-weight:700!important;box-shadow:none!important}
.st-key-preview_open button *, .st-key-preview_active button *, .st-key-preview_close button * {color:inherit!important}
.st-key-preview_open button:hover, .st-key-preview_open button:focus, .st-key-preview_open button:focus-visible, .st-key-preview_open button:active,
.st-key-preview_close button:hover, .st-key-preview_close button:focus, .st-key-preview_close button:focus-visible, .st-key-preview_close button:active {
  background:#222B3B!important;color:#FFFFFF!important;border-color:#FF6B2B!important;outline:none!important}
.st-key-preview_active button, .st-key-preview_active button:hover, .st-key-preview_active button:focus, .st-key-preview_active button:focus-visible, .st-key-preview_active button:active {
  background:#FF6B2B!important;color:#07090E!important;border-color:#FF6B2B!important;outline:none!important}
</style>''', unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def read_csv(source):
    return pd.read_csv(source, low_memory=False)

@st.cache_data(show_spinner=False)
def prepare(df):
    out = df.copy()
    out["FatalInjuryCount"] = pd.to_numeric(out["FatalInjuryCount"], errors="coerce")
    out["NumberOfEngines"] = pd.to_numeric(out["NumberOfEngines"], errors="coerce")
    out["EventYear"] = pd.to_datetime(out["EventDate"], errors="coerce").dt.year
    return out

def split_unique(df, field):
    """One row per accident and label; does not change source dataframe."""
    a = df[["NtsbNo", field, "FatalInjuryCount"]].copy()
    a[field] = a[field].fillna("").astype(str).str.split(";")
    a = a.explode(field)
    a[field] = a[field].str.strip()
    return a.drop_duplicates(["NtsbNo", field])

def rates(a, col):
    a = a.copy()
    a["Fatal"] = a["FatalInjuryCount"].gt(0)
    res = a.groupby(col).agg(n=("NtsbNo", "nunique"), fatal=("Fatal", "sum")).reset_index()
    res["rate"] = (100 * res["fatal"] / res["n"]).round(2)
    return res

def chart(fig, height=400):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=WHITE, family="DM Sans"), margin=dict(l=10,r=15,t=40,b=25),
                      height=height, hoverlabel=dict(bgcolor="#253044",font_color="white"),
                      legend=dict(font=dict(color=WHITE)))
    fig.update_xaxes(gridcolor="rgba(203,213,225,.11)", zeroline=False, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor="rgba(203,213,225,.08)", zeroline=False, tickfont=dict(color=MUTED))
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False})

def horizontal(df, x, y, color=CYAN, label=None, height=400):
    if df.empty:
        st.info("No eligible combinations under the current filters.")
        return
    fig=px.bar(df.sort_values(x), x=x, y=y, orientation="h", text=label or x,
               custom_data=[c for c in ("n", "fatal") if c in df], color_discrete_sequence=[color])
    fig.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0, hovertemplate="%{y}<br>%{x:,.2f}<extra></extra>")
    fig.update_layout(xaxis_title="Accidents (%)" if x=="rate" else "Unique accidents", yaxis_title=None)
    fig.update_xaxes(range=[0, max(float(df[x].max())*1.23, 1)])
    chart(fig,height)

def section(k,title,q):
    st.markdown(f'<div class="casehead"><div class="eyebrow">INVESTIGATION FILE / {k}</div><h2>{html.escape(title)}</h2><p>{html.escape(q)}</p></div>', unsafe_allow_html=True)

def info(text):
    st.markdown(f'<div class="note">{text}</div>',unsafe_allow_html=True)

def factors(df):
    f=split_unique(df,"Findings")
    f["MainCategory"]=f["Findings"].str.split(" - ", regex=False).str[0].str.strip()
    f["FactorCategory"]=f["MainCategory"].map(FACTORS)
    return f.dropna(subset=["FactorCategory"]).drop_duplicates(["NtsbNo","FactorCategory"])

flight_svg='''<svg class="flightart" viewBox="0 0 660 470" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><defs><radialGradient id="burn"><stop stop-color="#FF6B2B" stop-opacity=".55"/><stop offset="1" stop-color="#FF6B2B" stop-opacity="0"/></radialGradient></defs><ellipse cx="450" cy="350" rx="260" ry="90" fill="url(#burn)"/><circle cx="385" cy="220" r="165" fill="none" stroke="#38BDF8" stroke-opacity=".14"/><circle cx="385" cy="220" r="105" fill="none" stroke="#38BDF8" stroke-opacity=".12"/><path class="flighttrail" d="M-20 383Q150 360 260 285 T640 140" fill="none" stroke="#FF6B2B" stroke-width="2.3"/><g transform="translate(360 213) rotate(-21)" fill="#C8D1DB"><path d="M0 -150 C11 -135 13 -98 13 -60 L19 -3 119 55 121 76 14 48 10 109 46 135 46 148 0 136 -46 148 -46 135 -10 109 -14 48 -121 76 -119 55 -19 -3 -13 -60 C-13 -98 -11 -135 0 -150Z"/><path d="M-4 -130 L-4 130" stroke="#1A202B" stroke-width="2"/></g><path d="M20 433L280 433M320 433L500 433" stroke="#A7B2BF" stroke-opacity=".25" stroke-width="3" stroke-dasharray="28 16"/></svg>'''
st.markdown('''<div class="hero">''' + flight_svg + '''<div class="eyebrow">AIR SAFETY INTELLIGENCE / ARCHIVE 001</div><h1>BEYOND<br>THE CRASH</h1><p><em>Every Accident Leaves a Story. Data Reveals the Truth.</em></p><div class="record"><span class="dot"></span> FLIGHT DATA RECOVERED &nbsp;•&nbsp; INVESTIGATION ACTIVE</div></div>''', unsafe_allow_html=True)

source = ROOT/"CAROL_Aviation_EDA.csv"
if not source.exists():
    st.warning("**Data file required.** The notebook was supplied, but its exported CSV was not. Place the notebook-exported **CAROL_Aviation_EDA.csv** beside `app.py`. No statistics have been invented.")
    st.markdown("### Ready for investigation")
    st.write("The six investigations, global filters and analytical methods are implemented. Actual plots and numeric findings will appear when the matching notebook export is loaded.")
    st.stop()

try:
    raw=read_csv(source)
except Exception as exc:
    st.error(f"Could not read CSV: {exc}")
    st.stop()
required=["NtsbNo","EventDate","BroadPhaseofFlight","WeatherCondition","Findings","ProbableCause","AirCraftCategory","EngineType","NumberOfEngines","AirCraftDamage","HighestInjuryLevel","FatalInjuryCount"]
missing=[c for c in required if c not in raw.columns]
if missing:
    st.error(f"Dataset columns do not match the analysis notebook. Missing: {', '.join(missing)}")
    st.stop()
if raw["NtsbNo"].isna().any() or raw["NtsbNo"].duplicated().any():
    st.error("The supplied dataset does not contain exactly one non-missing unique NtsbNo per accident. No records will be silently dropped or merged.")
    st.stop()
if raw[["Findings","ProbableCause"]].isna().any().any():
    st.error("This file is not the notebook's final EDA population: some Findings or ProbableCause are missing. Export CAROL_Aviation_EDA.csv from the completed notebook. The dashboard will not silently exclude records.")
    st.stop()
raw=prepare(raw)
if raw["FatalInjuryCount"].isna().any():
    st.warning("Some fatality counts are unreported or invalid. Those accidents are not classified as nonfatal, and are excluded only from metrics needing known fatality counts.")

with st.sidebar:
    st.markdown("**FILTERS**")
    def options(col):
        return sorted(set(x.strip() for s in raw[col].dropna().astype(str) for x in s.split(";") if x.strip()))
    wx=st.selectbox("Weather condition", options("WeatherCondition"), index=None, placeholder="Select option", key="wx")
    air=st.selectbox("Aircraft category", options("AirCraftCategory"), index=None, placeholder="Select option", key="air")
    phase=st.selectbox("Flight phase", options("BroadPhaseofFlight"), index=None, placeholder="Select option", key="phase")
    outcome=st.selectbox("Fatal-outcome status",["Fatal accidents","Zero recorded fatalities","Unreported fatality count"], index=None, placeholder="Select option",key="outcome")
    years=raw["EventYear"].dropna()
    if not years.empty:
        ymin,ymax=int(years.min()),int(years.max())
        if ymin<ymax:
            yr=st.slider("Event years",ymin,ymax,(ymin,ymax),key="years")
        else:
            yr=(ymin,ymax)
    else:yr=None
    def clear_filters():
        for key in ("wx","air","phase","outcome","years"):
            st.session_state.pop(key,None)
    st.button("✕ Clear filters",use_container_width=True,key="clear_filters",on_click=clear_filters)
    st.divider()
    st.markdown("**RESEARCH CASE NAVIGATION**")
    pages=["Dashboard"]+[f"{k} · {t.title()}" for k,t,_ in CASES]+["Final verdict"]
    if "page" not in st.session_state: st.session_state.page="Dashboard"
    selected_case=st.radio("Investigation file",pages,label_visibility="collapsed",key="page")
    st.caption("Choose a case to explore its findings. Filters update the results.")

st.markdown('<span id="fs-marker"></span><style>'+_filter_state_css({"wx":wx,"air":air,"phase":phase,"outcome":outcome})+'</style>',unsafe_allow_html=True)

filtered=raw.copy()
for col,val in [("WeatherCondition",wx),("AirCraftCategory",air),("BroadPhaseofFlight",phase)]:
    if val:
        filtered=filtered[filtered[col].fillna("").astype(str).map(lambda s: val in {p.strip() for p in s.split(";")}).astype(bool)]
if outcome=="Fatal accidents":filtered=filtered[filtered["FatalInjuryCount"]>0]
elif outcome=="Zero recorded fatalities":filtered=filtered[filtered["FatalInjuryCount"]==0]
elif outcome=="Unreported fatality count":filtered=filtered[filtered["FatalInjuryCount"].isna()]
if yr is not None:filtered=filtered[filtered["EventYear"].between(*yr)]
if filtered.empty:
    st.warning("No accident records match your current filters. Use Clear filters in the sidebar to reset them.")
    st.stop()

if selected_case=="Dashboard":
    st.markdown('<div class="sectionline" aria-hidden="true"></div>',unsafe_allow_html=True)
    known=filtered["FatalInjuryCount"].notna()
    fatal=int((filtered["FatalInjuryCount"]>0).sum())
    nonfatal=int((filtered["FatalInjuryCount"]==0).sum())
    metrics=st.columns(5)
    for col,(label,value) in zip(metrics,[("Recorded accidents",f"{len(filtered):,}"),("Fatal accidents",f"{fatal:,}"),("Zero-fatality accidents",f"{nonfatal:,}"),("Recorded fatalities",f"{filtered['FatalInjuryCount'].sum(min_count=1):,.0f}" if known.any() else "N/A"),("Fatal accident proportion",f"{fatal/known.sum()*100:.1f}%" if known.any() else "N/A")]):
        col.metric(label,value)
    st.caption(f"Current filters: {len(filtered):,} distinct accidents of {len(raw):,} in the loaded EDA CSV. Outcome denominator: {int(known.sum()):,} accidents with documented fatality counts. {int((~known).sum()):,} unreported.")
    if len(filtered)==0:
        st.info("No accidents match these filters. Use Clear filters in the sidebar to return to the full selected population.")
        st.stop()
    if len(raw)!=6701:
        st.warning(f"Notebook documentation reports 6,701 analysis records, but this input contains {len(raw):,}. Verify that you loaded its final export. Visuals use the provided file without deleting records.")

    st.markdown('<div class="sectionline" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown("### What do these records reveal?")
    st.caption("All panels below respond to the sidebar filters. Accident counts represent documented investigation records—not accident risk per flight.")
    a,b=st.columns(2)
    with a:
        yearly=filtered.groupby("EventYear",dropna=True).NtsbNo.nunique().reset_index(name="Accidents")
        if not yearly.empty:
            fig=px.area(yearly,x="EventYear",y="Accidents",markers=True,color_discrete_sequence=[CYAN])
            fig.update_layout(title="Recorded accidents by event year",xaxis_title="Event year",yaxis_title="Accidents")
            chart(fig,345)
    with b:
        conditions=filtered.WeatherCondition.fillna("Not Reported").value_counts().rename_axis("Condition").reset_index(name="Accidents")
        fig=px.bar(conditions,x="Condition",y="Accidents",color_discrete_sequence=[ORANGE])
        fig.update_layout(title="Weather conditions across records",xaxis_title=None,yaxis_title="Accidents")
        chart(fig,345)
    c,d=st.columns(2)
    with c:
        phases=split_unique(filtered,"BroadPhaseofFlight")
        phases=phases[~phases.BroadPhaseofFlight.isin(UNKNOWN)]
        phase_counts=rates(phases,"BroadPhaseofFlight").nlargest(9,"n")
        st.markdown("**Most reported flight phases**")
        horizontal(phase_counts,"n","BroadPhaseofFlight",CYAN,"n",385)
    with d:
        ac=split_unique(filtered,"AirCraftCategory")
        ac=ac[~ac.AirCraftCategory.isin(UNKNOWN)]
        counts=ac.AirCraftCategory.value_counts().head(9).rename_axis("Aircraft category").reset_index(name="Accidents")
        st.markdown("**Aircraft category distribution**")
        horizontal(counts,"Accidents","Aircraft category",ORANGE,"Accidents",385)
    e,fcol=st.columns(2)
    with e:
        damage=split_unique(filtered,"AirCraftDamage")
        dc=damage[~damage.AirCraftDamage.isin(UNKNOWN)].AirCraftDamage.value_counts().rename_axis("Damage category").reset_index(name="Accidents")
        st.markdown("**Documented aircraft damage**")
        horizontal(dc,"Accidents","Damage category",ORANGE,"Accidents",320)
    with fcol:
        fc=factors(filtered).FactorCategory.value_counts().rename_axis("Finding category").reset_index(name="Accidents")
        st.markdown("**Investigation finding categories**")
        horizontal(fc,"Accidents","Finding category",CYAN,"Accidents",320)
    st.markdown('<div class="sectionline" aria-hidden="true"></div>',unsafe_allow_html=True)
    st.markdown("### Explore the six research cases")
    st.caption("Choose a case using the sidebar navigation.")
    tiles="".join(f'<div class="case-tile"><span>CASE {k} / INVESTIGATION FILE</span><h3>{html.escape(t)}</h3><p>{html.escape(q)}</p></div>' for k,t,q in CASES)
    st.markdown(f'<div class="case-grid">{tiles}</div>',unsafe_allow_html=True)
    def set_preview(open_state):
        st.session_state["show_preview"]=open_state
    if "show_preview" not in st.session_state: st.session_state["show_preview"]=False
    if not st.session_state["show_preview"]:
        st.button("Data preview and dataset statistics",key="preview_open",use_container_width=True,on_click=set_preview,args=(True,))
    else:
        hdr,close=st.columns([5,1])
        with hdr:
            st.button("Data preview and dataset statistics",key="preview_active",use_container_width=True,on_click=set_preview,args=(False,))
        with close:
            st.button("× Close preview",key="preview_close",use_container_width=True,on_click=set_preview,args=(False,))
        st.dataframe(filtered.head(100),use_container_width=True,hide_index=True)
        st.dataframe(pd.DataFrame({"Missing values":filtered.isna().sum(),"Missing %":(filtered.isna().mean()*100).round(2)}).sort_values("Missing values",ascending=False),use_container_width=True)
        st.dataframe(filtered.select_dtypes(include="number").describe(),use_container_width=True)
    info("<strong>Population:</strong> This dashboard uses the six-case EDA export and preserves the notebook's analysis population. A phase, aircraft, damage type, or finding may be reported more than once in one accident, but each accident is counted once per category. These associations do not establish causality.")

elif selected_case.startswith("01"):
    k,t,q=CASES[0];section(k,t,q)
    ph=split_unique(filtered,"BroadPhaseofFlight")
    ph=ph[~ph["BroadPhaseofFlight"].isin(UNKNOWN)]
    s=rates(ph,"BroadPhaseofFlight")
    a,b=st.columns(2)
    with a:
        st.markdown("**REPORTED ACCIDENT FREQUENCY**")
        horizontal(s,"n","BroadPhaseofFlight",CYAN,"n",450)
    with b:
        st.markdown("**FATAL ACCIDENT PROPORTION · n ≥ 30**")
        horizontal(s[s.n>=30],"rate","BroadPhaseofFlight",ORANGE,"rate",450)
    if not s.empty:
        most=s.sort_values("n",ascending=False).iloc[0]
        eligible=s[s.n>=30]
        if len(eligible):
            high=eligible.sort_values("rate",ascending=False).iloc[0]
            info(f"<strong>Evidence:</strong> {html.escape(str(most.BroadPhaseofFlight))} has the most reported accidents (n={most.n:,}). Among phases with at least 30 records, {html.escape(str(high.BroadPhaseofFlight))} has the highest observed fatal-outcome proportion ({high.rate:.2f}%, n={high.n:,}).")
    st.caption("One accident counted once within each phase; multiple phases may apply. Rates = accidents with recorded fatalities > 0 / unique accidents in phase. Categories with n < 30 omitted only from rate chart.")

elif selected_case.startswith("02"):
    k,t,q=CASES[1];section(k,t,q)
    wxdf=filtered[filtered.WeatherCondition.isin(["Visual (VMC)","Instrument (IMC)"])].copy()
    summary=rates(wxdf,"WeatherCondition") if len(wxdf) else pd.DataFrame()
    a,b=st.columns(2)
    with a:
        st.markdown("**FATAL ACCIDENT PROPORTION / ALL VMC–IMC RECORDS**")
        if len(summary):horizontal(summary,"rate","WeatherCondition",RED,"rate",320)
        else:st.info("No VMC / IMC accidents selected.")
    with b:
        st.markdown("**DOCUMENTED INJURY SEVERITY (%)**")
        valid=wxdf[wxdf.HighestInjuryLevel.isin(["Fatal","Serious","Minor"])]
        if len(valid):
            cross=pd.crosstab(valid.WeatherCondition,valid.HighestInjuryLevel,normalize="index").mul(100)
            fig=go.Figure()
            for key,color in [("Fatal",RED),("Serious",ORANGE),("Minor",CYAN)]:
                if key in cross:fig.add_bar(y=cross.index,x=cross[key],orientation="h",name=key,marker_color=color)
            fig.update_layout(barmode="stack",xaxis_title="Share of documented severity (%)");chart(fig,320)
        else:st.info("No documented injury-severity records selected.")
    if len(wxdf):
        unknown=wxdf[~wxdf.HighestInjuryLevel.isin(["Fatal","Serious","Minor"])]
        st.caption(f"VMC / IMC accident records: {len(wxdf):,}. Excluded from the severity distribution (unknown, None or unreported): {len(unknown):,}. Fatal-accident rates and documented-severity shares have DIFFERENT denominators. Weather associations do not demonstrate causality.")

elif selected_case.startswith("03"):
    k,t,q=CASES[2];section(k,t,q)
    f=factors(filtered); cnt=f.FactorCategory.value_counts().rename_axis("Factor").reset_index(name="Accidents")
    horizontal(cnt,"Accidents","Factor",ORANGE,"Accidents",400)
    if not cnt.empty:
        top=cnt.iloc[0];info(f"<strong>Evidence tag:</strong> {html.escape(top.Factor)} appears in {top.Accidents:,} distinct accidents under current filters. Each investigation may contribute to several categories.")
    st.caption("Findings split at ';'; their original prefix before ' - ' mapped to the notebook's five groups. Aircraft-related findings are not synonymous with confirmed mechanical failure.")

elif selected_case.startswith("04"):
    k,t,q=CASES[3];section(k,t,q)
    ac=split_unique(filtered,"AirCraftCategory");ac=ac[~ac.AirCraftCategory.isin(UNKNOWN)]
    en=split_unique(filtered,"EngineType");en=en[~en.EngineType.isin(UNKNOWN)]
    a,b=st.columns(2)
    with a:
        st.markdown("**AIRCRAFT CATEGORY · n ≥ 30**")
        horizontal(rates(ac,"AirCraftCategory").query("n >= 30"),"rate","AirCraftCategory",CYAN,"rate",390)
    with b:
        st.markdown("**ENGINE TYPE · n ≥ 30**")
        horizontal(rates(en,"EngineType").query("n >= 30"),"rate","EngineType",ORANGE,"rate",390)
    ec=filtered.dropna(subset=["NumberOfEngines"]).copy()
    ec["Engine configuration"]=np.select([ec.NumberOfEngines.eq(0),ec.NumberOfEngines.eq(1),ec.NumberOfEngines.ge(2)], ["Zero engines","Single engine","Multi-engine"],default="Other")
    count=rates(ec,"Engine configuration") if len(ec) else pd.DataFrame()
    st.markdown("**ENGINE CONFIGURATION · DOCUMENTED ENGINE COUNTS**")
    if len(count):horizontal(count,"rate","Engine configuration",CYAN,"rate",260)
    st.caption(f"Missing engine counts excluded from engine-count comparisons only: {filtered.NumberOfEngines.isna().sum():,}. Zero-engine aircraft retained. Multiple engine types and aircraft categories are counted once per accident within each label. Charts show n ≥ 30 except configuration (all documented groups).")
    with st.expander("Show subgroup sample sizes"):
        for label,data in [("Aircraft category",rates(ac,"AirCraftCategory")),("Engine type",rates(en,"EngineType")),("Engine configuration",count)]:
            st.write(label)
            st.dataframe(data,use_container_width=True,hide_index=True)

elif selected_case.startswith("05"):
    k,t,q=CASES[4];section(k,t,q)
    dmg=split_unique(filtered,"AirCraftDamage")
    dmg=dmg[dmg.AirCraftDamage.isin(["Destroyed","Substantial","Minor","None"])].copy()
    summary=dmg.groupby("AirCraftDamage").agg(n=("NtsbNo","nunique"), zero=("FatalInjuryCount",lambda s:int(s.eq(0).sum()))).reset_index()
    summary["rate"]=100*summary.zero/summary.n
    a,b=st.columns(2)
    for col,cat in [(a,"Substantial"),(b,"Destroyed")]:
        match=summary[summary.AirCraftDamage.eq(cat)]
        r=match.iloc[0] if len(match) else None
        with col:
            st.markdown(f'<div class="poster"><div class="k">{cat.upper()} DAMAGE / ZERO RECORDED FATALITIES</div><div class="v">{int(r.zero):,} <span style="font-size:1.2rem;color:#FF6B2B">/ {int(r.n):,}</span></div><div style="color:#CBD5E1">{r.rate:.1f}% of {cat.lower()}-damage accidents</div></div>' if r is not None else f'<div class="poster">{cat}: no matching records</div>',unsafe_allow_html=True)
    st.markdown("**AIRCRAFT DAMAGE · DISTINCT ACCIDENTS**")
    horizontal(summary.rename(columns={"AirCraftDamage":"Damage"}),"n","Damage",ORANGE,"n",280)
    info("<strong>Interpretation safeguard.</strong> Zero recorded fatalities is not equivalent to zero injuries. Multiple damage categories may apply to the same accident. Unknown damage is excluded from this damage-specific comparison, not from the dashboard.")

elif selected_case.startswith("06"):
    k,t,q=CASES[5];section(k,t,q)
    f=factors(filtered)
    f=f.merge(filtered[["NtsbNo","FatalInjuryCount"]].rename(columns={"FatalInjuryCount":"outcome_count"}),on="NtsbNo",how="left")
    known=filtered[filtered.FatalInjuryCount.notna()]
    totals={"Fatal":int(known.FatalInjuryCount.gt(0).sum()),"Nonfatal":int(known.FatalInjuryCount.eq(0).sum())}
    f=f[f.outcome_count.notna()].copy();f["Outcome"]=np.where(f.outcome_count.gt(0),"Fatal","Nonfatal")
    counts=f.groupby(["FactorCategory","Outcome"]).NtsbNo.nunique().reset_index(name="Accidents")
    counts["Percent"]=counts.apply(lambda r:100*r.Accidents/totals[r.Outcome] if totals[r.Outcome] else np.nan,axis=1)
    if len(counts):
        fig=px.bar(counts,x="Percent",y="FactorCategory",color="Outcome",orientation="h",barmode="group",text="Percent",color_discrete_map={"Fatal":RED,"Nonfatal":CYAN},custom_data=["Accidents","Outcome"])
        fig.update_traces(texttemplate="%{x:.1f}%",textposition="outside",cliponaxis=False)
        fig.update_layout(xaxis_title="Documented factor prevalence within outcome group (%)",yaxis_title=None)
        chart(fig,430)
    else:st.info("No eligible investigation findings.")
    st.caption(f"Denominators: fatal accidents n={totals['Fatal']:,}, zero-fatality accidents n={totals['Nonfatal']:,}; exclude {filtered.FatalInjuryCount.isna().sum():,} unreported counts. Factors overlap; sum of percentages need not equal 100%.")


else:
    st.markdown('<div class="sectionline" aria-hidden="true"></div>',unsafe_allow_html=True)
    st.markdown("# THE FINAL VERDICT")
    st.markdown("*The numbers tell a story. The investigation reveals its limits.*")
    st.markdown("### What the currently selected records show")
    ph=split_unique(filtered,"BroadPhaseofFlight");ph=ph[~ph.BroadPhaseofFlight.isin(UNKNOWN)]
    r=rates(ph,"BroadPhaseofFlight")
    if not r.empty:
        common=r.loc[r.n.idxmax()];st.markdown(f"**Most frequently reported phase:** {common.BroadPhaseofFlight} — {common.n:,} accidents. Frequency alone does not establish outcome severity.")
    d=split_unique(filtered,"AirCraftDamage"); severe=d[d.AirCraftDamage.isin(["Destroyed","Substantial"])]
    if len(severe):st.markdown(f"**Damage vs fatality:** {int(severe.FatalInjuryCount.eq(0).sum()):,} distinct accident–damage-category observations of severe damage recorded zero fatalities. This is not necessarily a count of distinct accidents across both categories.")
    f=factors(filtered)
    if len(f):st.markdown(f"**Most documented factor grouping:** {f.FactorCategory.value_counts().index[0]} (not necessarily a sole or proven cause).")
    st.markdown("### Evidence limitations")
    info("<strong>Missing records and selection:</strong> The notebook retained accidents with Findings and ProbableCause; this can bias observed patterns. <strong>Overlapping labels:</strong> One accident can belong to several flight, aircraft, damage or findings categories. <strong>Unequal sample sizes:</strong> Small groups have less stable rates. <strong>Exposure:</strong> No denominators for total flights or flight hours; accident frequency is not accident risk. <strong>Causality:</strong> These are descriptive observational associations, not causal effects.")
    st.markdown('<div class="footer">✈ &nbsp; BEYOND THE CRASH &nbsp; / &nbsp; END OF INVESTIGATION FILE &nbsp; · &nbsp; DATA CAN REVEAL PATTERNS, NOT REPLACE AN INVESTIGATION.</div>',unsafe_allow_html=True)
