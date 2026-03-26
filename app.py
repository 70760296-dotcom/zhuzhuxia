import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# --- 核心数据 ---
FARM_COORDS = {'内乡': (111.97, 33.02), '卧龙': (112.45, 32.90), '邓州': (112.04, 32.52)}
CITY_COORDS = {'南阳': (32.99, 112.53), '郑州': (34.74, 113.65), '济南': (36.65, 117.12), '南京': (32.06, 118.79), '武汉': (30.58, 114.30)}

# --- 计算函数 ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_coord(name):
    if name in FARM_COORDS: return FARM_COORDS[name]
    for city, coord in CITY_COORDS.items():
        if city in str(name): return coord
    return None

# --- 样式 ---
st.markdown("""<style>header, footer {visibility: hidden;}</style>""", unsafe_allow_html=True)

# --- 页面路由 ---
if 'page' not in st.session_state: st.session_state.page = 'home'
def go(p): st.session_state.page = p; st.rerun()

# ==========================================
# 主页
# ==========================================
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align:center; color:#FF4B4B'>🐷 生猪智能采购系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888'>纯净版 v1.1</p>", unsafe_allow_html=True)
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("📥 结算模拟", use_container_width=True): go('calc')
    with c2: 
        if st.button("📉 运营复盘", use_container_width=True): go('data')

# ==========================================
# 结算模拟
# ==========================================
elif st.session_state.page == 'calc':
    st.markdown("<h2>📤 屠宰结算模拟器</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): go('home')
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🛒 采购端")
        p_price = st.number_input("采购单价(元/公斤)", value=15.0)
        p_weight = st.number_input("均重(公斤)", value=115)
        p_heads = st.number_input("头数", value=100)
        
    with c2:
        st.markdown("#### 🏭 屠宰端")
        s_base = st.number_input("基准肉价", value=18.0)
        s_rate = st.slider("出肉率(%)", 70, 85, 76)
        
    if st.button("🚀 计算利润"):
        settle = s_base * (s_rate/100)
        profit = (settle - p_price) * p_weight * p_heads
        st.metric("预估利润", f"{profit:.0f} 元")

# ==========================================
# 运营复盘
# ==========================================
elif st.session_state.page == 'data':
    st.markdown("<h2>📉 运营复盘</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): go('home')
    
    files = st.file_uploader("上传Excel", type=['xlsx'])
    if files:
        df = pd.read_excel(files)
        st.write("数据预览：", df.head())