{\rtf1\ansi\ansicpg936\cocoartf2869
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
import plotly.express as px\
import plotly.graph_objects as go\
from io import BytesIO\
import os\
import re\
import numpy as np\
import math\
import shutil\
\
# --- 1. \uc0\u26680 \u24515 \u37197 \u32622  ---\
TESSERACT_PATH = '/usr/bin/tesseract' # \uc0\u20113 \u31471 \u40664 \u35748 \u36335 \u24452 \
try:\
    import pytesseract\
    from PIL import Image\
    # \uc0\u20113 \u31471 \u19981 \u38656 \u35201 \u25351 \u23450 \u36335 \u24452 \u65292 \u26412 \u22320 \u27979 \u35797 \u21487 \u33021 \u38656 \u35201 \
    OCR_STATUS = "\uc0\u9989  \u31995 \u32479 \u23601 \u32490 "\
    CAN_OCR = True\
except Exception as e:\
    OCR_STATUS = f"\uc0\u10060  \u38169 \u35823 : \{e\}"\
    CAN_OCR = False\
\
# --- 2. \uc0\u26680 \u24515 \u25968 \u25454 \u65306 \u31934 \u30830 \u22352 \u26631 \u24211  ---\
FARM_COORDS = \{\
    '\uc0\u20869 \u20065 ': (111.974177, 33.026172), '\u21351 \u40857 ': (112.451757, 32.904118), '\u37011 \u24030 ': (112.040009, 32.527833),\
    '\uc0\u21776 \u27827 ': (113.098992, 32.680748), '\u25206 \u27807 ': (114.476376, 34.156781), '\u36890 \u35768 ': (114.600493, 34.376351),\
    '\uc0\u26462 \u21439 ': (114.802569, 34.318349), '\u27491 \u38451 ': (114.310925, 32.410353), '\u28369 \u21439 ': (114.910323, 35.435523),\
    '\uc0\u26041 \u22478 ': (112.723136, 33.216503), '\u35199 \u21326 ': (114.406725, 33.697725), '\u31038 \u26071 ': (113.044809, 32.992864),\
    '\uc0\u22826 \u24247 ': (114.858139, 34.225991), '\u21830 \u27700 ': (114.391182, 33.522993), '\u40575 \u37009 \u21439 ': (115.107514, 33.906014),\
    '\uc0\u20892 \u23433 ': (124.975026, 44.509817), '\u21452 \u36797 ': (123.51, 43.94), '\u24191 \u23447 ': (115.20, 37.19),\
    '\uc0\u39053 \u27849 \u21306 ': (115.599268, 33.098624), '\u38047 \u31077 ': (112.47, 30.95), '\u26361 \u21439 ': (115.311951, 34.982697),\
\}\
CITY_COORDS = \{\
    '\uc0\u21335 \u38451 ': (32.99, 112.53), '\u37073 \u24030 ': (34.74, 113.65), '\u27982 \u21335 ': (36.65, 117.12), \
    '\uc0\u21335 \u20140 ': (32.06, 118.79), '\u27494 \u27721 ': (30.58, 114.30), '\u24191 \u24030 ': (23.13, 113.26)\
\}\
\
# --- 3. \uc0\u35745 \u31639 \u20989 \u25968  ---\
def haversine(lat1, lon1, lat2, lon2):\
    R = 6371.0\
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)\
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2\
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))\
\
def get_coord(name):\
    if name in FARM_COORDS: return FARM_COORDS[name]\
    for city, coord in CITY_COORDS.items():\
        if city in str(name): return coord\
    return None\
\
# --- 4. \uc0\u26679 \u24335  ---\
st.markdown("""\
<style>\
    .main .block-container \{ padding: 2rem 2.5rem !important; max-width: 100% !important; \}\
    header, footer \{ visibility: hidden; \}\
    .stButton>button \{ background-color: #FF4B4B; color: white; border-radius: 8px; padding: 8px 20px; font-weight:bold; \}\
</style>\
""", unsafe_allow_html=True)\
\
# --- 5. \uc0\u39029 \u38754 \u36335 \u30001  ---\
if 'page' not in st.session_state: st.session_state.page = 'home'\
def go(p): st.session_state.page = p; st.rerun()\
\
# ==========================================\
# \uc0\u39029 \u38754  A\u65306 \u25351 \u25381 \u23460 \
# ==========================================\
if st.session_state.page == 'home':\
    st.markdown("<h1 style='text-align:center; color:#FF4B4B'>\uc0\u55357 \u56375  \u29983 \u29482 \u26234 \u33021 \u37319 \u36141 \u31995 \u32479 </h1>", unsafe_allow_html=True)\
    st.markdown("<p style='text-align:center; color:#888'>\uc0\u20113 \u31471 \u29256  v22.0</p>", unsafe_allow_html=True)\
    st.markdown("---")\
    c1, c2, c3 = st.columns(3)\
    with c1:\
        if st.button("\uc0\u55357 \u56549  \u37319 \u36141 \u24773 \u25253 ", use_container_width=True): go('procurement')\
    with c2:\
        if st.button("\uc0\u55357 \u56548  \u32467 \u31639 \u27169 \u25311 ", use_container_width=True): go('slaughter')\
    with c3:\
        if st.button("\uc0\u55357 \u56521  \u36816 \u33829 \u22797 \u30424 ", use_container_width=True): go('analysis')\
\
# ==========================================\
# \uc0\u39029 \u38754  B\u65306 \u37319 \u36141 \
# ==========================================\
elif st.session_state.page == 'procurement':\
    st.markdown("<h2>\uc0\u55357 \u56549  \u37319 \u36141 \u24773 \u25253 \u20013 \u24515 </h2>", unsafe_allow_html=True)\
    if st.button("\uc0\u11013 \u65039  \u36820 \u22238 "): go('home')\
    st.info("\uc0\u31574 \u30053 \u24211 \u65306 \u29287 \u21407 \u24310 \u26102 30\u31186 \u12289 \u28201 \u27663 \u25340 \u25163 \u36895 \u12289 \u20013 \u31918 \u26263 \u26631 \u30450 \u25237 \u12290 ")\
\
# ==========================================\
# \uc0\u39029 \u38754  C\u65306 \u32467 \u31639 \u27169 \u25311 \
# ==========================================\
elif st.session_state.page == 'slaughter':\
    st.markdown("<h2>\uc0\u55357 \u56548  \u23648 \u23472 \u32467 \u31639 \u27169 \u25311 \u22120 </h2>", unsafe_allow_html=True)\
    if st.button("\uc0\u11013 \u65039  \u36820 \u22238 "): go('home')\
    \
    c1, c2 = st.columns(2)\
    with c1:\
        st.markdown("#### \uc0\u55357 \u57042  \u37319 \u36141 \u31471 ")\
        p_price = st.number_input("\uc0\u37319 \u36141 \u21333 \u20215 (\u20803 /\u20844 \u26020 )", value=15.0)\
        p_weight = st.number_input("\uc0\u22343 \u37325 (\u20844 \u26020 )", value=115)\
        p_heads = st.number_input("\uc0\u22836 \u25968 ", value=100)\
        \
    with c2:\
        st.markdown("#### \uc0\u55356 \u57325  \u23648 \u23472 \u31471 ")\
        s_base = st.number_input("\uc0\u22522 \u20934 \u32905 \u20215 ", value=18.0)\
        s_rate = st.slider("\uc0\u20986 \u32905 \u29575 (%)", 70, 85, 76)\
        \
    if st.button("\uc0\u55357 \u56960  \u35745 \u31639 "):\
        settle = s_base * (s_rate/100)\
        profit = (settle - p_price) * p_weight * p_heads\
        st.metric("\uc0\u39044 \u20272 \u21033 \u28070 ", f"\{profit:.0f\} \u20803 ")\
\
# ==========================================\
# \uc0\u39029 \u38754  D\u65306 \u22797 \u30424  (\u20462 \u22797 \u29256 )\
# ==========================================\
elif st.session_state.page == 'analysis':\
    st.markdown("<h2>\uc0\u55357 \u56521  \u36816 \u33829 \u22797 \u30424 </h2>", unsafe_allow_html=True)\
    if st.button("\uc0\u11013 \u65039  \u36820 \u22238 "): go('home')\
    \
    files = st.file_uploader("\uc0\u19978 \u20256 Excel", type=['xlsx'])\
    if files:\
        df = pd.read_excel(files)\
        \
        # \uc0\u37197 \u32622 \
        with st.expander("\uc0\u37197 \u32622 \u21015 \u21517 "):\
            cols = df.columns.tolist()\
            def guess(k): return next((c for c in cols if k in c), None)\
            f_price_p = st.selectbox("\uc0\u37319 \u36141 \u21333 \u20215 ", cols, index=cols.index(guess('\u37319 \u36141 ')) if guess('\u37319 \u36141 ') else 0)\
            f_price_s = st.selectbox("\uc0\u32467 \u31639 \u21333 \u20215 ", cols, index=cols.index(guess('\u32467 \u31639 ')) if guess('\u32467 \u31639 ') else 0)\
            f_heads = st.selectbox("\uc0\u22836 \u25968 ", cols, index=cols.index(guess('\u22836 \u25968 ')) if guess('\u22836 \u25968 ') else 0)\
        \
        # \uc0\u24378 \u21046 \u36716 \u25968 \u23383 \
        df[f_price_p] = pd.to_numeric(df[f_price_p], errors='coerce')\
        df[f_price_s] = pd.to_numeric(df[f_price_s], errors='coerce')\
        df[f_heads] = pd.to_numeric(df[f_heads], errors='coerce')\
        \
        # \uc0\u35745 \u31639 \
        df['\uc0\u21033 \u28070 '] = (df[f_price_s] - df[f_price_p]) * df[f_heads] * 110 # \u20551 \u35774 \u22343 \u37325 110\
        df['\uc0\u21033 \u28070 '] = df['\u21033 \u28070 '].fillna(0)\
        \
        st.metric("\uc0\u24635 \u21033 \u28070 ", f"\{df['\u21033 \u28070 '].sum():.0f\} \u20803 ")\
        st.dataframe(df[[f_price_p, f_price_s, '\uc0\u21033 \u28070 ']].head(10))}