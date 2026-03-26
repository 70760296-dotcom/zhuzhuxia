import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import math
import numpy as np
import os
import re

# --- 1. OCR 配置 ---
try:
    import pytesseract
    from PIL import Image
    if os.path.exists('/usr/bin/tesseract'):
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    OCR_STATUS = "✅ OCR可用"
    CAN_OCR = True
except Exception as e:
    OCR_STATUS = f"⚠️ OCR不可用 ({e})"
    CAN_OCR = False

# --- 2. 核心数据：坐标库 ---
FARM_COORDS = {
    '内乡': (111.974177, 33.026172), '卧龙': (112.451757, 32.904118), '邓州': (112.040009, 32.527833),
    '唐河': (113.098992, 32.680748), '扶沟': (114.476376, 34.156781), '通许': (114.600493, 34.376351),
    '杞县': (114.802569, 34.318349), '正阳': (114.310925, 32.410353), '滑县': (114.910323, 35.435523),
    '方城': (112.723136, 33.216503), '西华': (114.406725, 33.697725), '社旗': (113.044809, 32.992864),
    '太康': (114.858139, 34.225991), '商水': (114.391182, 33.522993), '鹿邑县': (115.107514, 33.906014),
    '农安': (124.975026, 44.509817), '双辽': (123.51, 43.94), '广宗': (115.20, 37.19),
}
CITY_COORDS = {
    '南阳': (32.99, 112.53), '郑州': (34.74, 113.65), '济南': (36.65, 117.12), 
    '南京': (32.06, 118.79), '武汉': (30.58, 114.30), '广州': (23.13, 113.26),
    '临沂': (35.10, 118.35), '成都': (104.06, 30.67), '杭州': (120.16, 30.25)
}

# --- 3. 计算函数 ---
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

# --- 4. 样式 ---
st.markdown("""
<style>
    .main .block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }
    header, footer { visibility: hidden; }
    .stButton>button { background-color: #FF4B4B; color: white; border-radius: 8px; padding: 8px 20px; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

# --- 5. 页面路由 ---
if 'page' not in st.session_state: st.session_state.page = 'home'
def go(p): st.session_state.page = p; st.rerun()

# ==========================================
# 页面 A：指挥室
# ==========================================
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align:center; color:#FF4B4B'>🐷 生猪智能采购系统</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#888'>商业智能版 v5.0 | {OCR_STATUS}</p>", unsafe_allow_html=True)
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📊 行情分析预测", use_container_width=True): go('trend')
    with c2:
        if st.button("📤 屠宰结算模拟", use_container_width=True): go('slaughter')
    with c3:
        if st.button("📉 运营复盘分析", use_container_width=True): go('analysis')

# ==========================================
# 页面 B：行情分析预测 (恢复版)
# ==========================================
elif st.session_state.page == 'trend':
    st.markdown("<h2>📊 行情分析预测</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回指挥室"): go('home')
    
    st.markdown("#### 数据来源")
    st.caption("此页面会自动读取【运营复盘】中上传的历史成交数据。")
    
    # 读取全局数据
    df_history = st.session_state.get('global_df', None)
    
    if df_history is not None:
        st.success(f"已检测到 {len(df_history)} 条历史数据")
        
        with st.expander("⚙️ 配置分析列"):
            cols = df_history.columns.tolist()
            def guess(k): return next((c for c in cols if k in c), cols[0])
            c1, c2 = st.columns(2)
            with c1: f_date = st.selectbox("日期列", cols, index=cols.index(guess('日期')))
            with c2: f_price = st.selectbox("价格列", cols, index=cols.index(guess('结算')))
        
        # 绘制趋势图
        df_trend = df_history.groupby(f_date)[f_price].mean().reset_index()
        fig = px.line(df_trend, x=f_date, y=f_price, markers=True, title="历史价格走势")
        st.plotly_chart(fig, use_container_width=True)
        
        # 简单预测
        avg_price = df_trend[f_price].mean()
        last_price = df_trend[f_price].iloc[-1]
        st.metric("最近成交均价", f"{last_price:.2f}", f"较平均 {'↑' if last_price > avg_price else '↓'} {abs(last_price-avg_price):.2f}")
        
    else:
        st.warning("暂无数据。请先在【运营复盘分析】页面上传 Excel 数据。")

# ==========================================
# 页面 C：结算模拟 (含OCR关联)
# ==========================================
elif st.session_state.page == 'slaughter':
    st.markdown("<h2>📤 屠宰结算模拟器</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回指挥室"): go('home')
    
    # --- OCR 模块 ---
    st.markdown("#### 📷 结算单智能识别")
    img_file = st.file_uploader("上传单据", type=['jpg', 'png'])
    
    # 初始化 session state 用于存储识别结果
    if 'ocr_p_price' not in st.session_state: st.session_state.ocr_p_price = 15.0
    if 'ocr_s_price' not in st.session_state: st.session_state.ocr_s_price = 18.0
    if 'ocr_weight' not in st.session_state: st.session_state.ocr_weight = 115

    if img_file:
        st.image(img_file, width=300)
        if CAN_OCR:
            if st.button("🤖 开始识别并填入"):
                try:
                    img = Image.open(img_file).convert('L')
                    text = pytesseract.image_to_string(img, config='--psm 6 -l chi_sim+eng')
                    st.text_area("识别原始文本", text, height=100)
                    
                    # 智能解析逻辑
                    nums = re.findall(r'\d+\.?\d*', text)
                    if len(nums) >= 2:
                        # 简单假设：较大的数可能是价格，中间的可能是体重
                        # 这里您可以后续优化解析规则
                        floats = [float(n) for n in nums if float(n) > 10] # 过滤小数字
                        if len(floats) >= 2:
                            # 按数值排序，取中间值作为体重，大值作为价格（极简逻辑，可调整）
                            floats.sort()
                            st.session_state.ocr_weight = floats[len(floats)//2] # 取中位数
                            st.session_state.ocr_s_price = floats[-1] # 取最大值假设为结算价
                            # 假设采购价略低，这里不自动填，仅填识别到的
                            st.success(f"✅ 解析成功！已自动填入下方：体重 {st.session_state.ocr_weight}kg, 结算价 {st.session_state.ocr_s_price}元")
                        else:
                            st.warning("识别到的数字较少，请手动核对。")
                    else:
                        st.warning("未识别到有效数字，请手动输入。")
                except Exception as e:
                    st.error(f"识别出错: {e}")
        else:
            st.warning("云端 OCR 功能暂未启用")
            
    st.markdown("---")

    # --- 计算模块 (自动关联) ---
    st.markdown("#### 🧮 利润试算")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🛒 采购端")
        # value 参数关联 session_state
        p_price = st.number_input("采购单价 (元/公斤)", value=st.session_state.ocr_p_price)
        p_weight = st.number_input("预估均重 (公斤)", value=st.session_state.ocr_weight)
        p_heads = st.number_input("采购头数", value=100)
        p_farm = st.selectbox("发货养殖场", list(FARM_COORDS.keys()))
        
    with c2:
        st.markdown("#### 🏭 屠宰端")
        s_base = st.number_input("屠宰基准肉价 (元/公斤)", value=st.session_state.ocr_s_price)
        s_rate = st.slider("预估出肉率 (%)", 70, 85, 76)
        s_level = st.select_slider("级别系数", options=[0.95, 0.98, 1.0, 1.02, 1.05], value=1.0)
        s_deduct = st.number_input("预估扣款 (元/公斤)", value=0.1)
        
        s_market_input = st.text_input("目标屠宰场名称", value="临沂")
    
    if st.button("🚀 开始计算利润", type="primary"):
        settle_price = s_base * (s_rate/100) * s_level - s_deduct
        dist = 0
        coord1 = get_coord(p_farm)
        coord2 = get_coord(s_market_input)
        if coord1 and coord2: dist = haversine(coord1[1], coord1[0], coord2[1], coord2[0])
        
        profit, cost, freight, income = calc_profit(p_price, settle_price, p_weight, p_heads, dist)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("预估结算价", f"{settle_price:.2f} 元/kg")
        with c2: st.metric("预估总成本", f"{cost+freight:.0f} 元")
        with c3: st.metric("预估总利润", f"{profit:.0f} 元", delta=f"{profit/(cost+freight)*100:.1f}%")
        st.success(f"**单头利润**：**{profit/p_heads:.1f} 元/头**")

# ==========================================
# 页面 D：运营复盘 (稳健修复 + 数据共享)
# ==========================================
elif st.session_state.page == 'analysis':
    st.markdown("<h2>📉 运营复盘分析</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回指挥室"): go('home')
    
    files = st.file_uploader("上传Excel明细", type=['xlsx'], accept_multiple_files=True)
    
    if files:
        try:
            df = pd.concat([pd.read_excel(f) for f in files])
            
            # 存入全局 Session State，供【行情分析】使用
            st.session_state['global_df'] = df
            
            with st.expander("⚙️ 列名配置", expanded=True):
                cols = df.columns.tolist()
                def guess(k): return next((c for c in cols if k in c), cols[0])
                
                c1, c2, c3 = st.columns(3)
                with c1: f_date = st.selectbox("日期", cols, index=cols.index(guess('日期')))
                with c2: f_sub = st.selectbox("养殖场", cols, index=cols.index(guess('子公司')))
                with c3: f_mark = st.selectbox("屠宰场", cols, index=cols.index(guess('屠宰')))
                
                c1, c2, c3 = st.columns(3)
                with c1: f_price_p = st.selectbox("采购单价", cols)
                with c2: f_price_s = st.selectbox("结算单价", cols)
                with c3: f_heads = st.selectbox("头数", cols)
                
                f_weight = st.selectbox("均重(公斤)", ["无"] + cols)

            # 数据清洗
            df[f_price_p] = pd.to_numeric(df[f_price_p], errors='coerce').fillna(0)
            df[f_price_s] = pd.to_numeric(df[f_price_s], errors='coerce').fillna(0)
            df[f_heads] = pd.to_numeric(df[f_heads], errors='coerce').fillna(0)
            
            if f_weight != "无":
                df[f_weight] = pd.to_numeric(df[f_weight], errors='coerce').fillna(110)
                df['总重量'] = df[f_weight] * df[f_heads]
            else:
                df['总重量'] = df[f_heads] * 110
            
            df['运距'] = df.apply(lambda x: haversine(*get_coord(x[f_sub]), *CITY_COORDS.get(x[f_mark], (0,0))) if get_coord(x[f_sub]) else 0, axis=1)
            
            # 利润计算
            df['总收入'] = df['总重量'] * df[f_price_s]
            df['总成本'] = df['总重量'] * df[f_price_p]
            df['利润'] = df['总收入'] - df['总成本']
            
            st.success("✅ 数据计算完成 (已同步至【行情分析】)")
            
            # 【修复】使用 px.bar 替代 go.Figure，绝对不报错
            st.markdown("#### 💰 利润趋势分析")
            trend = df.groupby(f_date).agg({'利润':'sum', '运距':'mean'}).reset_index()
            
            # 使用 px 绘图
            fig = px.bar(trend, x=f_date, y='利润', text='利润', title="每日盈亏走势")
            fig.update_traces(textposition='outside')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # 详情表
            disp_cols = [f_date, f_sub, f_mark, '运距', f_price_p, f_price_s, '利润']
            st.dataframe(df[disp_cols].head(20).style.format({'利润': '{:.0f}', '运距': '{:.0f}'}))
            
            buf = BytesIO()
            df.to_excel(buf, index=False)
            st.download_button("📥 导出完整计算表", buf, "复盘结果.xlsx")

        except Exception as e:
            st.error(f"分析出错: {e}")