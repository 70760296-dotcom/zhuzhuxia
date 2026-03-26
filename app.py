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
        <p style="font-size: 1.2rem; color: #666;">牧原生猪产业链智能决策系统 v17.0</p>
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
# 页面 D: 销售全景 (修复预警阈值)
# ==========================================
elif st.session_state.current_page == 'analysis':
    st.markdown("<div class='page-header'><h1>📊 销售全景中心</h1></div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回首页", key="back_a"): go_to_page('home')
    
    st.markdown("### 数据上传与配置")
    uploaded_files = st.file_uploader("📤 上传明细 (支持多选)", type=["xlsx", "xls"], accept_multiple_files=True, key="sales_v21")
    
    if uploaded_files:
        try:
            df_list = []
            for f in uploaded_files:
                temp = pd.read_excel(f); temp['来源文件'] = f.name; df_list.append(temp)
            df_raw = pd.concat(df_list, ignore_index=True)
            
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
            if guess('体重', df.columns): df['体重段'] = df[guess('体重', df.columns)].apply(extract_weight_smart)
            else: df['体重段'] = '未知'
            if '运距' not in df.columns: df['运距'] = df.apply(lambda x: estimate_distance_auto(x.get('子公司',''), x['屠宰场']), axis=1)
            df['采购类型'] = df.apply(lambda x: '直采' if x['客户姓名']==x['屠宰场'] else '中间商', axis=1)
            df['客户分类'] = df['客户姓名'].apply(classify_customer)
            
            st.success("✅ 数据加载完成")
            
            # --- 筛选逻辑 ---
            st.markdown("#### 🏭 屠宰场筛选")
            all_markets = df['屠宰场'].unique().tolist()
            is_select_all = st.checkbox("全选所有屠宰场", value=True, key="check_all_v10")
            
            if is_select_all: selected_markets = all_markets
            else: selected_markets = st.multiselect("选择特定屠宰场", all_markets, default=all_markets[:5], key="market_filter_v11")
            
            if not selected_markets: st.stop()
            df_view = df[df['屠宰场'].isin(selected_markets)]
            dates = sorted(df_view['日期'].unique())
            
            # --- 智能预警 (修复阈值) ---
            st.markdown("#### 🚨 核心市场智能预警")
            
            market_stats_base = df_view.groupby('屠宰场').agg(
                总量=('总头数', 'sum'), 日均量=('总头数', 'mean'), 供应商数=('客户姓名', 'nunique')
            ).reset_index()
            
            # 【修复】只要日均量大于10头就纳入分析 (适合测试数据)
            # 或者按总量排序取前80%的核心市场
            core_markets = market_stats_base[market_stats_base['日均量'] > 10]['屠宰场'].tolist()
            
            # 如果没有日均>10的，就取所有市场
            if not core_markets:
                core_markets = all_markets
            
            alerts_up = []
            alerts_down = []
            
            if len(dates) >= 3 and core_markets:
                df_core = df_view[df_view['屠宰场'].isin(core_markets)]
                df_last3 = df_core[df_core['日期'].isin(dates[-3:])]
                trend_check = df_last3.groupby(['屠宰场', '日期'])['总头数'].sum().unstack(fill_value=0)
                
                for market in trend_check.index:
                    vals = trend_check.loc[market].values
                    if len(vals) == 3:
                        pct = (vals[2] - vals[0]) / vals[0] * 100 if vals[0] > 0 else 0
                        data_str = f"{int(vals[0])}→{int(vals[1])}→{int(vals[2])}"
                        
                        if vals[0] > vals[1] > vals[2]:
                            alerts_down.append({'屠宰场': market, 'pct': pct, 'data': data_str})
                        elif vals[0] < vals[1] < vals[2]:
                            alerts_up.append({'屠宰场': market, 'pct': pct, 'data': data_str})
            
            col_up, col_down = st.columns(2)
            
            with col_up:
                st.markdown("<div class='alert-box-up'>", unsafe_allow_html=True)
                st.markdown("<div class='alert-title'>🚀 连涨机会</div>", unsafe_allow_html=True)
                if alerts_up:
                    for item in alerts_up:
                        st.markdown(f"**{item['屠宰场']}** +{item['pct']:.1f}%")
                        st.caption(item['data'])
                else: st.caption("暂无明显连涨")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_down:
                st.markdown("<div class='alert-box-down'>", unsafe_allow_html=True)
                st.markdown("<div class='alert-title'>📉 连跌风险</div>", unsafe_allow_html=True)
                if alerts_down:
                    for item in alerts_down:
                        st.markdown(f"**{item['屠宰场']}** {item['pct']:.1f}%")
                        st.caption(item['data'])
                else: st.caption("暂无明显连跌")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")

            # --- 趋势图 ---
            st.markdown("#### 📊 趋势分析")
            
            if is_select_all:
                st.markdown("**市场份额分布 (核心市场)**")
                # 只显示有数据的市场
                valid_pie_data = market_stats_base[market_stats_base['总量'] > 0]
                if not valid_pie_data.empty:
                    fig_pie = px.pie(valid_pie_data, values='总量', names='屠宰场', hole=0.4)
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_size=14)
                    fig_pie.update_layout(height=350, showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig_pie, use_container_width=True, key="pie_v10")
                
                st.markdown("**Top 10 接收量走势**")
                top_10_list = market_stats_base.nlargest(10, '总量')['屠宰场'].tolist()
                line_data = df_view[df_view['屠宰场'].isin(top_10_list)].groupby(['日期', '屠宰场'])['总头数'].sum().reset_index()
                fig_line = px.line(line_data, x='日期', y='总头数', color='屠宰场', markers=True)
                st.plotly_chart(fig_line, use_container_width=True, key="line_v10")
            else:
                trend_detail = df_view.groupby(['日期', '屠宰场'])['总头数'].sum().reset_index()
                fig = px.line(trend_detail, x='日期', y='总头数', color='屠宰场', markers=True, title="单日详细走势")
                st.plotly_chart(fig, use_container_width=True, key="line_detail_v10")

            st.markdown("---")

            # --- 客户画像 ---
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
                    else: st.info("暂无公户数据")
                
                with tab_pri:
                    pri_data = df_focus[df_focus['客户分类'] == '👤 个人户'].nlargest(10, '总头数')
                    if not pri_data.empty:
                        disp_cols = ['客户姓名', '总头数', '出现天数', '主要流向', '运距区间']
                        if has_price: disp_cols.insert(3, '平均单价')
                        st.dataframe(pri_data[disp_cols].style.format({'平均单价': '{:.2f}'}), hide_index=True, use_container_width=True)
                    else: st.info("暂无个人户数据")

                with st.expander("🔍 查看详细画像图表"):
                    sel_name = st.selectbox("选择客户", top_cust_list)
                    if sel_name:
                        c_d = all_mid[all_mid['客户姓名'] == sel_name]
                        st.markdown(f"**选手类型**：{classify_behavior(c_d, dates)}")
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.markdown("**源头分布**")
                            fig_src = px.pie(c_d, values='总头数', names='子公司', hole=0.4)
                            st.plotly_chart(fig_src, use_container_width=True, key="det_src_v10")
                        with c2:
                            st.markdown("**体重偏好**")
                            fig_w = px.pie(c_d, values='总头数', names='体重段', hole=0.4)
                            st.plotly_chart(fig_w, use_container_width=True, key="det_w_v10")
                        with c3:
                            st.markdown("**流向分布**")
                            fig_flow = px.pie(c_d, values='总头数', names='屠宰场', hole=0.4)
                            st.plotly_chart(fig_flow, use_container_width=True, key="det_flow_v10")

                if not is_select_all:
                    st.markdown("---")
                    st.markdown("#### 📈 核心客户供货趋势")
                    st.caption(f"展示前10大客户向 **{', '.join(selected_markets)}** 的每日供货量变化")
                    
                    top_10_cust_data = df_mid_view[df_mid_view['客户姓名'].isin(top_cust_list[:10])]
                    if not top_10_cust_data.empty:
                        trend_cust = top_10_cust_data.groupby(['日期', '客户姓名'])['总头数'].sum().reset_index()
                        fig_cust_trend = px.line(trend_cust, x='日期', y='总头数', color='客户姓名', markers=True)
                        st.plotly_chart(fig_cust_trend, use_container_width=True, key="cust_trend_v5")

            # --- 综合建议 ---
            st.markdown("---")
            st.markdown("#### 💡 综合运营指导建议")
            if core_markets:
                top_market = market_stats_base[market_stats_base['屠宰场'].isin(core_markets)].nlargest(1, '总量').iloc[0]
                st.info(f"""
                **📋 核心结论**：
                1. **主力流向**：**{top_market['屠宰场']}** (总量 {int(top_market['总量'])} 头)，是当前绝对核心。
                2. **体重需求**：市场最欢迎 **{df_view.groupby('体重段')['总头数'].sum().idxmax()}** 的猪源。
                3. **客户建议**：请重点关注上方列表中的 **"👑 忠实选手"**。
                """)
            else: st.warning("数据较少，无法生成深度建议。")

            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_view.to_excel(writer, index=False)
            st.download_button("📥 导出Excel", buffer, "分析结果.xlsx")

        except Exception as e:
            st.error(f"分析出错: {e}")