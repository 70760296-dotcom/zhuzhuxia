import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import math

# --- 1. 核心数据：坐标库 ---
FARM_COORDS = {
    '内乡': (111.974177, 33.026172), '卧龙': (112.451757, 32.904118), '邓州': (112.040009, 32.527833),
    '唐河': (113.098992, 32.680748), '扶沟': (114.476376, 34.156781), '通许': (114.600493, 34.376351),
    '杞县': (114.802569, 34.318349), '正阳': (114.310925, 32.410353), '滑县': (114.910323, 35.435523),
    '方城': (112.723136, 33.216503), '西华': (114.406725, 33.697725), '社旗': (113.044809, 32.992864),
    '太康': (114.858139, 34.225991), '商水': (114.391182, 33.522993), '鹿邑县': (115.107514, 33.906014),
}
CITY_COORDS = {
    '南阳': (32.99, 112.53), '郑州': (34.74, 113.65), '济南': (36.65, 117.12), 
    '南京': (32.06, 118.79), '武汉': (30.58, 114.30), '广州': (23.13, 113.26)
}

# --- 2. 计算函数 ---
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

# --- 3. 样式 ---
st.markdown("""
<style>
    .main .block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }
    header, footer { visibility: hidden; }
    .stButton>button { background-color: #FF4B4B; color: white; border-radius: 8px; padding: 8px 20px; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

# --- 4. 页面路由 ---
if 'page' not in st.session_state: st.session_state.page = 'home'
def go(p): st.session_state.page = p; st.rerun()

# ==========================================
# 页面 A：指挥室
# ==========================================
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align:center; color:#FF4B4B'>🐷 生猪智能采购系统</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#888'>云端精简版 v1.0</p>", unsafe_allow_html=True)
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📥 采购情报", use_container_width=True): go('procurement')
    with c2:
        if st.button("📤 结算模拟", use_container_width=True): go('slaughter')
    with c3:
        if st.button("📉 运营复盘", use_container_width=True): go('analysis')

# ==========================================
# 页面 B：采购
# ==========================================
elif st.session_state.page == 'procurement':
    st.markdown("<h2>📥 采购情报中心</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): go('home')
    st.info("策略库：牧原延时30秒、温氏拼手速、中粮暗标盲投。")

# ==========================================
# 页面 C：结算模拟
# ==========================================
elif st.session_state.page == 'slaughter':
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
        
    if st.button("🚀 计算"):
        settle = s_base * (s_rate/100)
        profit = (settle - p_price) * p_weight * p_heads
        st.metric("预估利润", f"{profit:.0f} 元")

# ==========================================
# 页面 D：复盘
# ==========================================
elif st.session_state.page == 'analysis':
    st.markdown("<h2>📉 运营复盘</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回"): go('home')
    
    files = st.file_uploader("上传Excel", type=['xlsx'])
    if files:
        df = pd.read_excel(files)
        
        with st.expander("配置列名"):
            cols = df.columns.tolist()
            def guess(k): return next((c for c in cols if k in c), None)
            f_price_p = st.selectbox("采购单价", cols, index=cols.index(guess('采购')) if guess('采购') else 0)
            f_price_s = st.selectbox("结算单价", cols, index=cols.index(guess('结算')) if guess('结算') else 0)
            f_heads = st.selectbox("头数", cols, index=cols.index(guess('头数')) if guess('头数') else 0)
        
        # 强制转数字
        df[f_price_p] = pd.to_numeric(df[f_price_p], errors='coerce')
        df[f_price_s] = pd.to_numeric(df[f_price_s], errors='coerce')
        df[f_heads] = pd.to_numeric(df[f_heads], errors='coerce')
        
        # 计算
        df['利润'] = (df[f_price_s] - df[f_price_p]) * df[f_heads] * 110
        df['利润'] = df['利润'].fillna(0)
        
        st.metric("总利润", f"{df['利润'].sum():.0f} 元")
        st.dataframe(df[[f_price_p, f_price_s, '利润']].head(10))
