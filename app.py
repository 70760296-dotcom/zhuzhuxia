import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import math
import numpy as np

# --- 1. 核心数据：精确坐标库 (完整版) ---
FARM_COORDS = {
    # --- 河南 ---
    '内乡': (111.974177, 33.026172), '卧龙': (112.451757, 32.904118), '邓州': (112.040009, 32.527833),
    '唐河': (113.098992, 32.680748), '扶沟': (114.476376, 34.156781), '通许': (114.600493, 34.376351),
    '杞县': (114.802569, 34.318349), '正阳': (114.310925, 32.410353), '滑县': (114.910323, 35.435523),
    '方城': (112.723136, 33.216503), '西华': (114.406725, 33.697725), '社旗': (113.044809, 32.992864),
    '太康': (114.858139, 34.225991), '商水': (114.391182, 33.522993), '鹿邑县': (115.107514, 33.906014),
    '睢阳区': (115.372991, 34.30589), '宁陵县': (115.204456, 34.399346), '范县': (115.433176, 35.701728),
    '上蔡县': (114.597094, 33.331728), '平舆县': (114.505587, 32.920675), '西平县': (113.878267, 33.41632),
    '项城市': (114.969351, 33.341667), '夏邑县': (116.021757, 34.37114), '安阳县': (114.742931, 36.149707),
    '农安': (124.975026, 44.509817), '双辽': (123.51, 43.94), '广宗': (115.20, 37.19),
    '颍泉区': (115.599268, 33.098624), '钟祥': (112.47, 30.95), '曹县': (115.311951, 34.982697),
    '闻喜': (111.321350, 35.365287), '大荔': (110.091415, 34.721281), '奈曼': (120.927878, 43.064616),
    '建平': (119.44, 42.03), '铜山': (117.622823, 34.257606), '雷州市': (110.084601, 20.746093),
}
# 备用城市坐标
CITY_COORDS = {
    '南阳': (32.99, 112.53), '郑州': (34.74, 113.65), '济南': (36.65, 117.12), 
    '南京': (32.06, 118.79), '武汉': (30.58, 114.30), '广州': (23.13, 113.26)
}

# --- 2. 业务逻辑计算函数 ---
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

def calc_profit(purchase_price, settle_price, weight, heads, distance, loss_rate=0.002):
    purchase_cost = purchase_price * weight * heads
    freight = 800 + distance * 8 * (heads/120) 
    actual_weight = weight * heads * (1 - loss_rate)
    income = settle_price * actual_weight
    profit = income - purchase_cost - freight
    return profit, purchase_cost, freight, income

# --- 3. 样式定义 (完整版) ---
st.markdown("""
<style>
    .main .block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }
    header, footer { visibility: hidden; }
    .stButton>button { background-color: #FF4B4B; color: white; border-radius: 8px; padding: 8px 20px; font-weight:bold; }
    .stButton>button:hover { background-color: #e04343; }
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
    st.markdown("<p style='text-align:center; color:#888'>云端完整版 v2.0</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.info("📊 **今日行情**\n\n河南: 15.2")
    with c2: st.warning("📉 **风险预警**\n\n价格倒挂")
    with c3: st.success("💰 **机会**\n\n温氏降价")
    with c4: st.info("🚚 **在途**\n\n3车运输中")
    
    st.markdown("### 🚀 快速导航")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📥 采购情报中心", use_container_width=True): go('procurement')
        st.caption("竞拍策略 | 实时行情")
    with c2:
        if st.button("📤 屠宰结算模拟", use_container_width=True): go('slaughter')
        st.caption("结算价预估 | 利润试算")
    with c3:
        if st.button("📉 运营复盘分析", use_container_width=True): go('analysis')
        st.caption("历史盈亏 | 路线优化")

# ==========================================
# 页面 B：采购情报中心
# ==========================================
elif st.session_state.page == 'procurement':
    st.markdown("<h2>📥 采购情报中心</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回指挥室"): go('home')
    
    st.markdown("#### 📝 竞拍策略库")
    st.info("""
    **1. 牧原策略**：
    - 模式：明标，整车+零散两轮。
    - ⚠️ 延时机制：最后30秒有人出价，自动延时1分钟。
    - 💡 建议：不要过早亮底牌，预留最后10秒冲刺。
    
    **2. 中粮策略**：
    - 模式：暗标，仅能投标1次。
    - 💡 建议：依靠历史数据推算成本，避免“赢了标，亏了钱”。
    
    **3. 温氏/双胞胎**：
    - 模式：明标，无延时。
    - 💡 建议：必须在截止前最后1秒出价，拼手速。
    """)

# ==========================================
# 页面 C：屠宰结算模拟
# ==========================================
elif st.session_state.page == 'slaughter':
    st.markdown("<h2>📤 屠宰结算模拟器</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回指挥室"): go('home')
    
    with st.expander("📖 查看利润计算公式"):
        st.markdown("`利润 = (到场总重 × 结算价) - (采购总重 × 采购价) - 运费`")

    st.markdown("### 🧮 实时试算工具")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 🛒 采购端参数")
        p_price = st.number_input("采购单价 (元/公斤)", value=15.0)
        p_weight = st.number_input("预估均重 (公斤)", value=115)
        p_heads = st.number_input("采购头数", value=100)
        p_farm = st.selectbox("发货养殖场", list(FARM_COORDS.keys()))
        
    with c2:
        st.markdown("#### 🏭 屠宰端参数")
        s_base = st.number_input("屠宰基准肉价 (元/公斤)", value=18.0)
        s_rate = st.slider("预估出肉率 (%)", 70, 85, 76)
        s_level = st.select_slider("级别系数", options=[0.95, 0.98, 1.0, 1.02, 1.05], value=1.0)
        s_deduct = st.number_input("预估扣款 (元/公斤)", value=0.1)
        s_markets = st.multiselect("目标屠宰场", ['南京', '武汉', '广州', '郑州'], default=['南京'])
    
    if st.button("🚀 开始计算利润", type="primary"):
        settle_price = s_base * (s_rate/100) * s_level - s_deduct
        dist = 0
        if p_farm and s_markets:
            coord1 = get_coord(p_farm)
            coord2 = CITY_COORDS.get(s_markets[0])
            if coord1 and coord2: dist = haversine(coord1[1], coord1[0], coord2[1], coord2[0])
        
        profit, cost, freight, income = calc_profit(p_price, settle_price, p_weight, p_heads, dist)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("预估结算价", f"{settle_price:.2f} 元/kg")
        with c2: st.metric("预估总成本", f"{cost+freight:.0f} 元")
        with c3: st.metric("预估总利润", f"{profit:.0f} 元", delta=f"{profit/(cost+freight)*100:.1f}%")
            
        st.success(f"**详细账单**：运距约 {dist} 公里，单头利润 **{profit/p_heads:.1f} 元**")

# ==========================================
# 页面 D：运营复盘分析 (完整修复版)
# ==========================================
elif st.session_state.page == 'analysis':
    st.markdown("<h2>📉 运营复盘分析</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回指挥室"): go('home')
    
    st.markdown("### 📤 上传历史运营数据")
    files = st.file_uploader("上传Excel明细 (包含：采购价、结算价、体重、头数)", type=['xlsx'], accept_multiple_files=True)
    
    if files:
        try:
            df = pd.concat([pd.read_excel(f) for f in files])
            
            with st.expander("⚙️ 列名配置", expanded=True):
                cols = df.columns.tolist()
                def guess(k): return next((c for c in cols if k in c), None)
                
                c1, c2, c3 = st.columns(3)
                with c1: f_date = st.selectbox("日期", cols, index=cols.index(guess('日期')) if guess('日期') else 0)
                with c2: f_sub = st.selectbox("养殖场", cols, index=cols.index(guess('子公司')) if guess('子公司') else 0)
                with c3: f_mark = st.selectbox("屠宰场", cols, index=cols.index(guess('屠宰')) if guess('屠宰') else 0)
                
                c1, c2, c3 = st.columns(3)
                with c1: f_price_p = st.selectbox("采购单价", cols)
                with c2: f_price_s = st.selectbox("结算单价", cols)
                with c3: f_heads = st.selectbox("头数", cols)
                
                f_weight = st.selectbox("均重(公斤)", ["无"] + cols)

            # 核心修复：强制转数字
            df[f_price_p] = pd.to_numeric(df[f_price_p], errors='coerce')
            df[f_price_s] = pd.to_numeric(df[f_price_s], errors='coerce')
            df[f_heads] = pd.to_numeric(df[f_heads], errors='coerce')
            
            if f_weight != "无":
                df[f_weight] = pd.to_numeric(df[f_weight], errors='coerce')
                df['总重量'] = df[f_weight] * df[f_heads]
            else:
                df['总重量'] = df[f_heads] * 110
                
            df[[f_price_p, f_price_s, '总重量']] = df[[f_price_p, f_price_s, '总重量']].fillna(0)
            
            # 计算运距
            df['运距'] = df.apply(lambda x: haversine(*get_coord(x[f_sub]), *CITY_COORDS.get(x[f_mark], (0,0))) if get_coord(x[f_sub]) else 0, axis=1)
            
            # 计算利润
            df['总收入'] = df['总重量'] * df[f_price_s]
            df['总成本'] = df['总重量'] * df[f_price_p]
            df['利润'] = df['总收入'] - df['总成本']
            
            st.success("✅ 数据计算完成")
            
            st.markdown("#### 💰 利润趋势分析")
            trend = df.groupby(f_date).agg({'利润':'sum', '运距':'mean'}).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=trend[f_date], y=trend['利润'], name='日利润'))
            fig.update_layout(height=400, title="每日盈亏走势")
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("#### 📊 详细数据表")
            disp_cols = [f_date, f_sub, f_mark, '运距', f_price_p, f_price_s, '利润']
            st.dataframe(df[disp_cols].head(20).style.format({'利润': '{:.0f}', '运距': '{:.0f}'}))
            
            buf = BytesIO()
            df.to_excel(buf, index=False)
            st.download_button("📥 导出完整计算表", buf, "复盘结果.xlsx")

        except Exception as e:
            st.error(f"分析出错: {e}")