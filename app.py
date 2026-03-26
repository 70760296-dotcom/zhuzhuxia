import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import os
import re
import numpy as np
import math

# --- 1. 核心配置 ---
TESSERACT_PATH = '/opt/homebrew/bin/tesseract'
try:
    import pytesseract
    from PIL import Image
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        OCR_STATUS = "✅ 系统就绪"
        CAN_OCR = True
    else:
        OCR_STATUS = "❌ 未检测到引擎"
        CAN_OCR = False
except Exception as e:
    OCR_STATUS = f"❌ 错误: {e}"
    CAN_OCR = False

# --- 2. 样式定义 (舒适宽屏版) ---
st.markdown("""
<style>
    /* 【优化布局】左右留出舒适边距，撑满但不拥挤 */
    [data-testid="stMainBlockContainer"] {
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 100% !important;
    }
    /* 隐藏页眉页脚 */
    header, footer { visibility: hidden; height: 0px !important; }
    
    :root { --primary-color: #FF4B4B; --bg-color: #f4f6f9; --card-bg: #ffffff; }
    body { background-color: var(--bg-color); }
    
    .home-card-container {
        background-color: var(--card-bg); border-radius: 20px; padding: 40px 30px; text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; height: 100%; transition: all 0.3s ease;
    }
    .home-card-container:hover { transform: translateY(-5px); border-color: var(--primary-color); }
    
    .stButton { text-align: center; margin-top: 20px; }
    .stButton>button { background-color: var(--primary-color); color: white; border-radius: 10px; border: none; padding: 10px 24px; font-weight: bold; min-width: 120px; }
    .stButton>button:hover { background-color: #e04343; }

    .page-header { background: linear-gradient(135deg, #FF4B4B 0%, #FF7E5F 100%); padding: 30px; border-radius: 0px 0px 20px 20px; margin-top: -2rem; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(255, 75, 75, 0.3); color: white; }
    
    .alert-box-up { background-color: #e8f5e9; border-left: 5px solid #00C853; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .alert-box-down { background-color: #ffebee; border-left: 5px solid #FF4B4B; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .alert-title { font-weight: bold; font-size: 1.1rem; margin-bottom: 5px; }
    
    /* 文字总结卡片样式 */
    .insight-card {
        background-color: #f8f9fa; border-left: 4px solid #2196F3; padding: 12px 15px;
        border-radius: 8px; margin-top: 10px; margin-bottom: 20px; font-size: 0.95rem;
        color: #333; line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 核心计算函数 ---
CITY_COORDS = {
    '南阳': (32.99, 112.53), '内乡': (33.05, 111.83), '郑州': (34.74, 113.65), '开封': (34.79, 114.31), 
    '周口': (33.63, 114.70), '济南': (36.65, 117.12), '临沂': (35.10, 118.35), '聊城': (36.45, 115.99), 
    '南京': (32.06, 118.79), '武汉': (30.58, 114.30), '襄阳': (32.01, 112.12),
    '合肥': (31.82, 117.23), '南昌': (28.68, 115.89), '广州': (23.13, 113.26)
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def find_keyword(name):
    for city in CITY_COORDS.keys():
        if city in str(name): return city
    return None

def estimate_distance_auto(sub, mark):
    kw1, kw2 = find_keyword(sub), find_keyword(mark)
    if kw1 and kw2: return round(haversine(*CITY_COORDS[kw1], *CITY_COORDS[kw2]), 1)
    return 0

def extract_weight_smart(text):
    if pd.isna(text): return "未知"
    matches = re.findall(r'(\d+)-(\d+)', str(text))
    if matches:
        valid = [(int(m[0]), int(m[1])) for m in matches if int(m[0]) > 90]
        if valid: return f"{valid[-1][0]}-{valid[-1][1]}kg"
    return "未知"

def classify_customer(name):
    if pd.isna(name): return '未知'
    if any(kw in str(name) for kw in ['公司', '有限', '集团', '合作社']): return '🏢 公户'
    return '👤 个人户'

def classify_behavior(cust_data, total_dates):
    days = cust_data['日期'].nunique()
    if len(total_dates) == 0: return "未知"
    ratio = days / len(total_dates)
    if ratio > 0.8: return "👑 忠实选手"
    if ratio < 0.2:
        if cust_data['日期'].max() == max(total_dates): return "🚀 猛然闯入选手"
        return "⚠️ 消极选手"
    return "🛡️ 稳定选手"

def process_ocr(image_file):
    try:
        img = Image.open(image_file).convert('L')
        text = pytesseract.image_to_string(img, config='--psm 6 -l chi_sim+eng')
        return text
    except: return "识别失败"

# --- 4. 页面状态管理 ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

def go_to_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# ==========================================
# 页面 A: 官网首页
# ==========================================
if st.session_state.current_page == 'home':
    st.markdown("""
    <div style="text-align: center; padding: 40px 0;">
        <h1 style="font-size: 3rem; color: #FF4B4B; margin-bottom: 10px;">🐷 猪猪侠全力冲杀！</h1>
        <p style="font-size: 1.2rem; color: #666;">牧原生猪产业链智能决策系统 v18.0</p>
        <p style="color: #999;">""" + OCR_STATUS + """</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown('<div class="home-card-container">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 3.5rem; margin-bottom:15px;">🛒</div>', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#333;">结算定价</h3>', unsafe_allow_html=True)
        st.markdown('<p style="color:#888; font-size:0.95rem;">屠宰结算单智能识别<br>自动计算最优采购策略</p>', unsafe_allow_html=True)
        if st.button("进入模块", key="btn_home_1"): go_to_page('pricing')
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="home-card-container">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 3.5rem; margin-bottom:15px;">📈</div>', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#333;">行情预测</h3>', unsafe_allow_html=True)
        st.markdown('<p style="color:#888; font-size:0.95rem;">多维度价格趋势分析<br>未来五日行情推演</p>', unsafe_allow_html=True)
        if st.button("进入模块", key="btn_home_2"): go_to_page('trend')
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="home-card-container">', unsafe_allow_html=True)
        st.markdown('<div style="font-size: 3.5rem; margin-bottom:15px;">📊</div>', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#333;">销售全景</h3>', unsafe_allow_html=True)
        st.markdown('<p style="color:#888; font-size:0.95rem;">客户画像与物流洞察<br>多日趋势深度挖掘</p>', unsafe_allow_html=True)
        if st.button("进入模块", key="btn_home_3"): go_to_page('analysis')
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 页面 B: 结算定价
# ==========================================
elif st.session_state.current_page == 'pricing':
    st.markdown("<div class='page-header'><h1>🛒 结算定价中心</h1></div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回首页", key="back_p"): go_to_page('home')
    st.markdown("### 📷 屠宰结算单智能识别")
    img_file = st.file_uploader("上传单据", type=['jpg', 'png'])
    if img_file and CAN_OCR:
        st.image(img_file, width=300)
        text = process_ocr(img_file)
        st.text_area("识别结果", text, height=200)
        st.data_editor(pd.DataFrame({'体重段': ['', ''], '单价': [0, 0]}), num_rows="dynamic", hide_index=True)

# ==========================================
# 页面 C: 行情预测
# ==========================================
elif st.session_state.current_page == 'trend':
    st.markdown("<div class='page-header'><h1>📈 行情预测中心</h1></div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回首页", key="back_t"): go_to_page('home')
    auto_data = st.session_state.get('auto_market_data', None)
    if auto_data is not None: df_market = auto_data
    else: df_market = pd.DataFrame({'省份': ['河南'], '价格': [15.0]})
    st.markdown("#### 今日行情一览")
    edited = st.data_editor(df_market, num_rows="dynamic", hide_index=True)
    st.line_chart(edited.set_index('省份'))

# ==========================================
# 页面 D: 销售全景 (优化版 v18.0)
# ==========================================
elif st.session_state.current_page == 'analysis':
    st.markdown("<div class='page-header'><h1>📊 销售全景中心</h1></div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回首页", key="back_a"): go_to_page('home')
    
    st.markdown("### 数据上传与配置")
    uploaded_files = st.file_uploader("📤 上传明细 (支持多选)", type=["xlsx", "xls"], accept_multiple_files=True, key="sales_v22")
    
    if uploaded_files:
        try:
            df_list = []
            for f in uploaded_files:
                temp = pd.read_excel(f); temp['来源文件'] = f.name; df_list.append(temp)
            df_raw = pd.concat(df_list, ignore_index=True)
            
            # 列名配置逻辑
            with st.expander("⚙️ 列名配置", expanded=False):
                df_raw.columns = [str(col).strip().replace('\n', '') for col in df_raw.columns]
                cols = df_raw.columns.tolist()
                def guess(kw, cols): return next((c for c in cols if kw in c), None)
                
                c1, c2, c3, c4 = st.columns(4)
                with c1: sel_cust = st.selectbox("客户", cols, index=cols.index(guess('客户', cols)) if guess('客户', cols) else 0)
                with c2: sel_mark = st.selectbox("屠宰场", cols, index=cols.index(guess('屠宰', cols)) if guess('屠宰', cols) else 0)
                with c3: sel_heads = st.selectbox("头数", cols, index=cols.index(guess('头数', cols)) if guess('头数', cols) else 0)
                with c4: sel_sub = st.selectbox("子公司", ["无"] + cols, index=cols.index(guess('子公司', cols))+1 if guess('子公司', cols) else 0)
                c5, c6 = st.columns(2)
                with c5: sel_price = st.selectbox("单价", ["无"] + cols)
                with c6: sel_date = st.selectbox("日期", ["来源文件名"] + [c for c in cols if '日期' in c])

            # 数据清洗
            df = df_raw.copy()
            df.rename(columns={sel_cust:'客户姓名', sel_mark:'屠宰场', sel_heads:'总头数'}, inplace=True)
            if sel_sub != "无": df.rename(columns={sel_sub:'子公司'}, inplace=True)
            else: df['子公司'] = '未知'
            if sel_price != "无": df.rename(columns={sel_price:'单价'}, inplace=True); has_price = True
            else: df['单价'] = 0; has_price = False
            if sel_date == "来源文件名": df['日期'] = df['来源文件']
            else: df['日期'] = df[sel_date]
            
            df.dropna(subset=['客户姓名', '屠宰场'], inplace=True)
            df['总头数'] = pd.to_numeric(df['总头数'], errors='coerce').fillna(0)
            
            # 体重段处理
            weight_col = guess('体重', df.columns)
            if weight_col: df['体重段'] = df[weight_col].apply(extract_weight_smart)
            else: df['体重段'] = '未知'
            
            if '运距' not in df.columns: df['运距'] = df.apply(lambda x: estimate_distance_auto(x.get('子公司',''), x['屠宰场']), axis=1)
            df['采购类型'] = df.apply(lambda x: '直采' if x['客户姓名']==x['屠宰场'] else '中间商', axis=1)
            df['客户分类'] = df['客户姓名'].apply(classify_customer)
            
            st.success("✅ 数据加载完成")
            
            # --- 筛选逻辑 ---
            st.markdown("#### 🏭 屠宰场筛选")
            all_markets = df['屠宰场'].unique().tolist()
            is_select_all = st.checkbox("全选所有屠宰场", value=True, key="check_all_v12")
            
            if is_select_all: selected_markets = all_markets
            else: selected_markets = st.multiselect("选择特定屠宰场", all_markets, default=all_markets[:1] if all_markets else [], key="market_filter_v12")
            
            if not selected_markets: st.stop()
            df_view = df[df['屠宰场'].isin(selected_markets)]
            dates = sorted(df_view['日期'].unique())
            
            # ==========================================
            # 1. 核心市场智能预警 (Top 10 排名版)
            # ==========================================
            st.markdown("#### 🚨 核心市场智能预警")
            st.caption("基于所有选定市场的最新日环比变化计算涨跌幅")
            
            alerts_up = []
            alerts_down = []
            
            # 计算每个市场的涨跌幅
            market_pivot = df_view.groupby(['屠宰场', '日期'])['总头数'].sum().unstack(fill_value=0)
            
            # 至少需要两天数据才能计算涨跌
            if len(dates) >= 2:
                last_date = dates[-1]
                prev_date = dates[-2]
                
                # 计算环比
                for market in market_pivot.index:
                    last_val = market_pivot.loc[market, last_date] if last_date in market_pivot.columns else 0
                    prev_val = market_pivot.loc[market, prev_date] if prev_date in market_pivot.columns else 0
                    
                    if prev_val > 0:
                        pct = (last_val - prev_val) / prev_val * 100
                        data = {'屠宰场': market, 'pct': pct, 'last': last_val, 'prev': prev_val}
                        if pct > 0: alerts_up.append(data)
                        elif pct < 0: alerts_down.append(data)
            
            # 排序取前10
            top_up = sorted(alerts_up, key=lambda x: x['pct'], reverse=True)[:10]
            top_down = sorted(alerts_down, key=lambda x: x['pct'])[:10] # 负数越小跌得越狠
            
            col_up, col_down = st.columns(2)
            
            with col_up:
                st.markdown("<div class='alert-box-up'>", unsafe_allow_html=True)
                st.markdown("<div class='alert-title'>🚀 涨幅 Top 10 排行</div>", unsafe_allow_html=True)
                if top_up:
                    for i, item in enumerate(top_up, 1):
                        st.markdown(f"**{i}. {item['屠宰场']}**  ⬆️ **{item['pct']:.1f}%**")
                        st.caption(f"昨日 {int(item['prev'])} → 今日 {int(item['last'])} (增量 {int(item['last']-item['prev'])})")
                else: st.caption("暂无明显增长市场")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_down:
                st.markdown("<div class='alert-box-down'>", unsafe_allow_html=True)
                st.markdown("<div class='alert-title'>📉 跌幅 Top 10 排行</div>", unsafe_allow_html=True)
                if top_down:
                    for i, item in enumerate(top_down, 1):
                        st.markdown(f"**{i}. {item['屠宰场']}**  ⬇️ **{abs(item['pct']):.1f}%**")
                        st.caption(f"昨日 {int(item['prev'])} → 今日 {int(item['last'])} (减量 {abs(int(item['last']-item['prev']))})")
                else: st.caption("暂无明显下跌市场")
                st.markdown("</div>", unsafe_allow_html=True)

            # 预警文字总结
            summary_text = ""
            if top_up:
                summary_text += f"📈 **增长方面**：{top_up[0]['屠宰场']} 增长势头最猛，环比激增 {top_up[0]['pct']:.1f}%。"
            if top_down:
                summary_text += f" 📉 **下滑方面**：{top_down[0]['屠宰场']} 下滑最严重，跌幅达 {abs(top_down[0]['pct']):.1f}%，需关注是否存在客户流失。"
            if not summary_text: summary_text = "当前市场波动平稳，无显著涨跌异常。"
            
            st.markdown(f"<div class='insight-card'>💡 <b>智能解读：</b>{summary_text}</div>", unsafe_allow_html=True)
            st.markdown("---")

            # ==========================================
            # 2. 体重段趋势分析 (针对单一屠宰场)
            # ==========================================
            if not is_select_all and len(selected_markets) == 1:
                st.markdown("#### ⚖️ 屠宰场体重需求分析")
                target_market = selected_markets[0]
                df_single = df_view[df_view['屠宰场'] == target_market]
                
                # 按日期和体重段汇总
                weight_trend = df_single.groupby(['日期', '体重段'])['总头数'].sum().reset_index()
                
                # 绘制柱状图
                fig_weight = px.bar(weight_trend, x='日期', y='总头数', color='体重段', 
                                    barmode='group', title=f"{target_market} 每日体重段收购情况")
                fig_weight.update_layout(xaxis_title="日期", yaxis_title="头数", legend_title="体重段")
                st.plotly_chart(fig_weight, use_container_width=True, key="weight_bar_v1")
                
                # 文字总结
                if not weight_trend.empty:
                    top_weight = weight_trend.groupby('体重段')['总头数'].sum().idxmax()
                    top_weight_count = weight_trend.groupby('体重段')['总头数'].sum().max()
                    st.markdown(f"""
                    <div class='insight-card'>
                        💡 <b>需求洞察：</b>该屠宰场偏好 <b>{top_weight}</b> 的猪源，累计收购 <b>{int(top_weight_count)}</b> 头。<br>
                        建议子公司在向该市场调猪时，优先匹配此体重区间的猪群。
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("---")

            # ==========================================
            # 3. 整体趋势分析 (饼图+折线图)
            # ==========================================
            st.markdown("#### 📊 整体趋势分析")
            
            market_stats_base = df_view.groupby('屠宰场').agg(总量=('总头数', 'sum')).reset_index()
            
            if is_select_all:
                st.markdown("**市场份额分布**")
                valid_pie_data = market_stats_base[market_stats_base['总量'] > 0]
                if not valid_pie_data.empty:
                    fig_pie = px.pie(valid_pie_data, values='总量', names='屠宰场', hole=0.4)
                    st.plotly_chart(fig_pie, use_container_width=True, key="pie_v12")
                    
                    # 饼图总结
                    top_m = valid_pie_data.nlargest(1, '总量').iloc[0]
                    st.markdown(f"<div class='insight-card'>💡 <b>格局解读：</b>目前 <b>{top_m['屠宰场']}</b> 占据绝对主导地位，市场份额达到 <b>{top_m['总量']/valid_pie_data['总量'].sum()*100:.1f}%</b>。</div>", unsafe_allow_html=True)
                
                st.markdown("**Top 10 接收量走势**")
                top_10_list = market_stats_base.nlargest(10, '总量')['屠宰场'].tolist()
                line_data = df_view[df_view['屠宰场'].isin(top_10_list)].groupby(['日期', '屠宰场'])['总头数'].sum().reset_index()
                fig_line = px.line(line_data, x='日期', y='总头数', color='屠宰场', markers=True)
                st.plotly_chart(fig_line, use_container_width=True, key="line_v12")
            else:
                trend_detail = df_view.groupby(['日期', '屠宰场'])['总头数'].sum().reset_index()
                fig = px.line(trend_detail, x='日期', y='总头数', color='屠宰场', markers=True, title="单日详细走势")
                st.plotly_chart(fig, use_container_width=True, key="line_detail_v12")
                # 多选时的简单总结
                st.markdown(f"<div class='insight-card'>💡 <b>趋势解读：</b>展示了 {len(selected_markets)} 个选定屠宰场的采购走势，请结合折线波动判断市场活跃度。</div>", unsafe_allow_html=True)

            st.markdown("---")

            # ==========================================
            # 4. 客户画像分析
            # ==========================================
            st.markdown("#### 🤝 重点客户画像")
            
            df_mid_view = df_view[df_view['采购类型'] == '中间商']
            if not df_mid_view.empty:
                all_mid = df[df['采购类型'] == '中间商']
                
                cust_stats = all_mid.groupby('客户姓名').agg(
                    总头数=('总头数', 'sum'), 平均单价=('单价', 'mean'), 出现天数=('日期', 'nunique'),
                    客户分类=('客户分类', 'first'), 主要流向=('屠宰场', lambda x: x.mode()[0] if not x.mode().empty else '未知'),
                    最小运距=('运距', 'min'), 最大运距=('运距', 'max')
                ).reset_index()
                
                cust_stats['运距区间'] = cust_stats.apply(lambda x: f"{x['最小运距']:.0f}-{x['最大运距']:.0f}km", axis=1)
                
                active_customers = df_mid_view['客户姓名'].unique()
                cust_stats_active = cust_stats[cust_stats['客户姓名'].isin(active_customers)]
                
                top_cust_list = cust_stats_active.nlargest(20, '总头数')['客户姓名'].tolist()
                df_focus = cust_stats_active[cust_stats_active['客户姓名'].isin(top_cust_list)]
                
                tab_pub, tab_pri = st.tabs(["🏢 公户分析", "👤 个人户分析"])
                
                with tab_pub:
                    pub_data = df_focus[df_focus['客户分类'] == '🏢 公户'].nlargest(10, '总头数')
                    if not pub_data.empty:
                        disp_cols = ['客户姓名', '总头数', '出现天数', '主要流向', '运距区间']
                        if has_price: disp_cols.insert(3, '平均单价')
                        st.dataframe(pub_data[disp_cols].style.format({'平均单价': '{:.2f}'}), hide_index=True, use_container_width=True)
                        st.markdown(f"<div class='insight-card'>💡 <b>洞察：</b>公户群体供货量大且稳定，平均合作时长较长，是核心稳定盘。</div>", unsafe_allow_html=True)
                    else: st.info("暂无公户数据")
                
                with tab_pri:
                    pri_data = df_focus[df_focus['客户分类'] == '👤 个人户'].nlargest(10, '总头数')
                    if not pri_data.empty:
                        disp_cols = ['客户姓名', '总头数', '出现天数', '主要流向', '运距区间']
                        if has_price: disp_cols.insert(3, '平均单价')
                        st.dataframe(pri_data[disp_cols].style.format({'平均单价': '{:.2f}'}), hide_index=True, use_container_width=True)
                        st.markdown(f"<div class='insight-card'>💡 <b>洞察：</b>个人户通常更敏感，运距分布较广，建议关注其流向变化以捕捉市场机会。</div>", unsafe_allow_html=True)
                    else: st.info("暂无个人户数据")

                with st.expander("🔍 查看详细画像图表"):
                    sel_name = st.selectbox("选择客户", top_cust_list, key="sel_cust_detail_v2")
                    if sel_name:
                        c_d = all_mid[all_mid['客户姓名'] == sel_name]
                        st.markdown(f"**选手类型**：{classify_behavior(c_d, dates)}")
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.markdown("**源头分布**")
                            fig_src = px.pie(c_d, values='总头数', names='子公司', hole=0.4)
                            st.plotly_chart(fig_src, use_container_width=True, key="det_src_v12")
                        with c2:
                            st.markdown("**体重偏好**")
                            fig_w = px.pie(c_d, values='总头数', names='体重段', hole=0.4)
                            st.plotly_chart(fig_w, use_container_width=True, key="det_w_v12")
                        with c3:
                            st.markdown("**流向分布**")
                            fig_flow = px.pie(c_d, values='总头数', names='屠宰场', hole=0.4)
                            st.plotly_chart(fig_flow, use_container_width=True, key="det_flow_v12")
                        
                        st.markdown(f"<div class='insight-card'>💡 <b>客户画像总结：</b>{sel_name} 主要从 {c_d['子公司'].mode()[0]} 调货，偏好体重段 {c_d['体重段'].mode()[0]}，核心销往 {c_d['屠宰场'].mode()[0]}。</div>", unsafe_allow_html=True)

            # --- 综合建议 ---
            st.markdown("---")
            st.markdown("#### 💡 综合运营指导建议")
            valid_stats = market_stats_base[market_stats_base['总量'] > 0]
            if not valid_stats.empty:
                top_market = valid_stats.nlargest(1, '总量').iloc[0]
                
                # 动态建议逻辑
                advice_1 = f"**主力流向**：**{top_market['屠宰场']}** (总量 {int(top_market['总量'])} 头)，是当前绝对核心。"
                
                weight_pref = df_view.groupby('体重段')['总头数'].sum()
                if not weight_pref.empty:
                    advice_2 = f"**体重需求**：市场最欢迎 **{weight_pref.idxmax()}** 的猪源。"
                else: advice_2 = ""
                
                # 简单的预警建议
                if top_down:
                    advice_3 = f"**风险提示**：{top_down[0]['屠宰场']} 出现大幅下跌，建议销售部门核实该市场情况。"
                else: advice_3 = "目前各市场走势平稳，无异常下跌风险。"

                st.info(f"📋 **核心结论**：\n1. {advice_1}\n2. {advice_2}\n3. {advice_3}")
            else: st.warning("数据较少，无法生成深度建议。")

            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_view.to_excel(writer, index=False)
            st.download_button("📥 导出Excel", buffer, "分析结果.xlsx")

        except Exception as e:
            st.error(f"分析出错: {e}")
            st.error("请检查数据格式是否符合要求，或联系管理员。")
