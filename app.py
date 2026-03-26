import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import os
import re
import numpy as np
import math
import shutil

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

# --- 2. 核心数据：精确坐标库 (根据您提供的数据植入) ---
# 键：子公司名称 (对应您表格中的'子公司'列) -> 值：(经度, 纬度)
FARM_COORDS = {
    # --- 河南 ---
    '内乡': (111.974177, 33.026172),
    '卧龙': (112.451757, 32.904118),
    '邓州': (112.040009, 32.527833),
    '唐河': (113.098992, 32.680748),
    '扶沟': (114.476376, 34.156781),
    '通许': (114.600493, 34.376351),
    '杞县': (114.802569, 34.318349),
    '正阳': (114.310925, 32.410353),
    '滑县': (114.910323, 35.435523),
    '方城': (112.723136, 33.216503),
    '西华': (114.406725, 33.697725),
    '社旗': (113.044809, 32.992864),
    '太康': (114.858139, 34.225991),
    '商水': (114.391182, 33.522993),
    '鹿邑县': (115.107514, 33.906014),
    '睢阳区': (115.372991, 34.30589),
    '宁陵县': (115.204456, 34.399346),
    '范县': (115.433176, 35.701728),
    '上蔡县': (114.597094, 33.331728),
    '平舆县': (114.505587, 32.920675),
    '西平县': (113.878267, 33.41632),
    '项城市': (114.969351, 33.341667),
    '夏邑县': (116.021757, 34.37114),
    '安阳县': (114.742931, 36.149707),
    '清丰县': (115.013965, 35.930652),
    '鄢陵县': (114.278951, 34.211083),
    '汝州市': (112.745647, 34.111043),
    '固始县': (115.474146, 32.238077),
    '新野县': (112.425975, 32.364675),
    '内黄县': (114.676152, 35.859131),
    '柘城县': (115.479402, 34.050515),
    '淅川县': (111.790194, 32.761963),
    '民权县': (115.398268, 34.735022),
    '汝州综合体': (112.948383, 34.011989),
    '永城市': (116.304441, 33.801682),
    '长垣县': (114.766986, 35.339155),
    '延津县': (114.377132, 35.291432),
    '鹤壁牧原': (114.386975, 35.809994),
    '获嘉县': (113.66288, 35.2046),
    '桐柏县': (113.058334, 32.519104),
    
    # --- 吉林 ---
    '农安': (124.975026, 44.509817),
    '双辽': (123.51, 43.94),
    '通榆': (122.261505, 44.631419),
    '前郭': (124.276765, 44.594600),
    '双阳区': (125.781862, 43.667300),
    '大安市': (123.39, 45.38),
    
    # --- 河北 ---
    '广宗': (115.20, 37.19),
    '馆陶': (115.218494, 36.510758),
    '海兴': (117.377262, 38.030950),
    '新河': (115.281378, 37.434621),
    '冀州市': (115.54, 37.33),
    '辛集市': (115.30, 37.65),
    '宁晋县': (115.171980, 37.612749),
    '景县': (115.945897, 37.612491),
    '沽源县': (115.42, 41.62),
    '衡水': (115.82, 37.74),
    '枣强县': (115.83, 37.50),
    '南皮县': (116.943916, 38.064194),
    
    # --- 安徽 ---
    '颍泉区': (115.599268, 33.098624),
    '蒙城县': (116.609376, 33.394049),
    '濉溪县': (116.624214, 33.710737),
    '颍上县': (116.500112, 32.531886),
    '界首市': (115.444683, 33.376172),
    '泗县': (117.830689, 33.424762),
    '凤台县': (116.51289, 32.904951),
    '谯城区': (115.687302, 33.585384),
    '怀远县': (116.963973, 33.191138),
    '固镇县': (117.1621, 33.398033),
    '利辛县': (116.244545, 32.984365),
    '涡阳县': (116.311315, 33.687417),
    '埇桥区': (117.374351, 33.877565),
    '巢湖市': (117.736683, 31.868221),
    
    # --- 湖北 ---
    '钟祥': (112.47, 30.95),
    '老河口': (111.97, 32.44),
    '石首': (112.45, 29.85),
    '公安县': (112.22, 30.22),
    '江陵县': (112.416078, 30.213229),
    '枣阳市': (112.76, 32.33),
    '黄梅县': (115.986301, 30.198740),
    '沙洋县': (112.60, 30.55),
    '应城市': (113.42, 30.93),
    
    # --- 山东 ---
    '曹县': (115.311951, 34.982697),
    '垦利': (118.752705, 37.66242),
    '东明县': (115.13353, 35.107666),
    '单县': (116.379977, 34.774165),
    '牡丹区': (115.79993, 35.36729),
    '莘县': (115.661073, 36.094495),
    '平原县': (116.608758, 37.227159),
    '庆云县': (117.468609, 37.79133),
    '邹平县': (117.66476, 37.052593),
    '惠民县': (117.451905, 37.193405),
    '茌平县': (115.998245, 36.602007),
    '临邑县': (116.806591, 37.208431),
    '郯城县': (118.321426, 34.711822),
    '台儿庄区': (117.712099, 34.705999),
    '东阿县': (116.090552, 36.276555),
    '即墨市': (120.340184, 36.583618),
    '滕州市': (117.344359, 34.909827),
    '临清市': (115.751273, 36.724523),
    '高唐县': (116.199236, 36.731772),
    
    # --- 山西 ---
    '闻喜': (111.321350, 35.365287),
    '新绛': (111.24, 35.50),
    '万荣': (110.86, 35.37),
    '永济': (110.48, 34.93),
    '代县': (113.125732, 39.121769),
    '繁峙县': (113.379024, 39.179783),
    '夏县': (111.181768, 35.254032),
    '原平市': (112.680834, 38.665694),
    '洪洞县': (111.692355, 36.216551),
    '河津市': (110.654928, 35.574524),
    '神池县': (112.005175, 39.028321),
    
    # --- 陕西 ---
    '大荔': (110.091415, 34.721281),
    '白水': (109.45, 35.22),
    '蒲城县': (109.46, 35.02),
    '陈仓区': (107.49, 34.36),
    
    # --- 内蒙古 ---
    '奈曼': (120.927878, 43.064616),
    '开鲁': (121.632642, 43.598933),
    '敖汉': (119.98, 42.51),
    '翁牛特': (119.07, 42.87),
    '扎鲁特旗': (120.514915, 44.312293),
    '科尔沁左翼中旗': (122.728227, 43.976160),
    '扎赉特旗': (122.620878, 46.837922),
    '乌拉特前旗': (109.013417, 40.876159),
    '科尔沁右翼中旗': (121.78, 44.86),
    
    # --- 辽宁 ---
    '建平': (119.44, 42.03),
    '铁岭': (123.58, 42.33),
    '阜新': (122.15, 42.28),
    '义县': (121.320550, 41.533210),
    '黑山县': (122.367534, 41.821581),
    '台安县': (122.225035, 41.421804),
    '昌图县': (123.671174, 43.104225),
    '康平县': (123.273228, 42.856595),
    '开原市': (124.036026, 42.667296),
    '太子河区': (123.062166, 41.408947),
    
    # --- 江苏 ---
    '铜山': (117.622823, 34.257606),
    '灌南县': (119.549196, 34.074384),
    '新沂市': (118.216453, 34.351864),
    '沭阳县': (118.641929, 34.294331),
    '邳州市': (117.668994, 34.481481),
    '六合区': (118.87298, 32.535347),
    '溧水县': (119.150914, 31.470271),
    '江宁区': (118.545642, 31.7398),
    '海安县': (120.293852, 32.659334),
    '栖霞区': (119.178072, 32.219141),
    '睢宁县': (117.887315, 33.840061),
    '阜宁县': (119.587206, 33.829861),
    '洪泽县': (118.852251, 33.214594),
    '射阳县': (120.373813, 33.968139),
    '清江浦': (118.967096, 33.462627),
    '姜堰市': (120.034369, 32.677146),
    '高港区': (119.993463, 32.314677),
    '金湖县': (118.98806, 33.08724),
    '宝应县': (119.514705, 33.248707),
    '江都区': (119.814803, 32.404811),
    '吴江市': (120.715818, 31.07286),
    '海州区': (119.033589, 34.658202),
    '赣榆县': (119.003897, 34.776286),
    '涟水县': (119.082415, 33.910182),
    '宿豫区': (118.430718, 34.100119),
    '东海县': (118.556964, 34.431056),
    
    # --- 黑龙江 ---
    '龙江': (122.914668, 46.993156),
    '兰西': (126.02, 46.37),
    '林甸县': (124.561994, 46.959882),
    '望奎县': (126.57, 46.84),
    '克东县': (126.26, 47.80),
    '富裕县': (124.55, 47.91),
    '明水县': (125.662672, 47.206278),
    '甘南县': (124.066663, 47.845283),
    '克山县': (125.326714, 48.108026),
    '依安县': (125.55, 47.36),
    '木兰县': (127.871353, 46.265082),
    
    # --- 广西 ---
    '柳城县': (109.458396, 24.467501),
    '宾阳县': (108.89, 23.44),
    '银海区': (109.300157, 21.473149),
    '兴宾区': (109.375946, 23.818041),
    '武鸣县': (108.14, 23.37),
    '横县': (107.98, 22.83),
    '西乡塘区': (107.98, 22.83),
    '宁明县': (107.464169, 22.093841),
    '右江区': (106.576903, 23.863463),
    '江州': (107.353694, 22.40609),
    
    # --- 广东 ---
    '雷州市': (110.084601, 20.746093),
    '东源县': (114.7466, 23.790079),
    
    # --- 北京 ---
    '房山区': (115.816532, 39.544879),
    
    # --- 四川 ---
    '绵竹市': (104.10, 31.24),
    '邛崃市': (103.697539, 30.437545),
    '崇州市': (103.65, 30.69),
    
    # --- 湖南 ---
    '安乡县': (112.168104, 29.622921),
    
    # --- 江西 ---
    '南昌县': (115.916405, 28.321787),
    '袁州区': (114.074456, 27.799158),
    '新建县': (115.567059, 28.447897),
    '乐安县': (115.69333, 27.161043),
    
    # --- 浙江 ---
    '临海市': (121.676778, 28.825989)
}

# 保留城市坐标作为备用（主要用于屠宰场定位，如果屠宰场名字里没有农场名）
CITY_COORDS = {
    '南阳': (32.99, 112.53), '内乡': (33.05, 111.83), '郑州': (34.74, 113.65), '开封': (34.79, 114.31), 
    '周口': (33.63, 114.70), '济南': (36.65, 117.12), '临沂': (35.10, 118.35), '聊城': (36.45, 115.99), 
    '南京': (32.06, 118.79), '武汉': (30.58, 114.30), '襄阳': (32.01, 112.12),
    '合肥': (31.82, 117.23), '南昌': (28.68, 115.89), '广州': (23.13, 113.26)
}

# --- 3. 样式定义 ---
st.markdown("""
<style>
    .main .block-container { padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
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
</style>
""", unsafe_allow_html=True)

# --- 4. 核心计算函数 ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# 【核心更新】距离计算函数 - 优先使用精确坐标
def estimate_distance_auto(sub, mark):
    lat1, lon1 = None, None
    lat2, lon2 = None, None
    
    # 1. 获取发货地(子公司)坐标 - 优先查找精确库
    if sub in FARM_COORDS:
        lon1, lat1 = FARM_COORDS[sub]
    else:
        # 备用：查找城市库
        kw1 = find_keyword(sub)
        if kw1: lat1, lon1 = CITY_COORDS.get(kw1, (None, None))
        
    # 2. 获取目的地(屠宰场)坐标 - 通常只能用城市库
    kw2 = find_keyword(mark)
    if kw2: lat2, lon2 = CITY_COORDS.get(kw2, (None, None))
    
    if lat1 and lat2:
        return round(haversine(lat1, lon1, lat2, lon2), 1)
    return 0

def find_keyword(name):
    for city in CITY_COORDS.keys():
        if city in str(name): return city
    return None

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

# --- 5. 页面逻辑 (保持之前完善的逻辑不变) ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'

def go_to_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()

if st.session_state.current_page == 'home':
    st.markdown("""<div style="text-align: center; padding: 40px 0;"><h1 style="font-size: 3rem; color: #FF4B4B; margin-bottom: 10px;">🐷 猪猪侠全力冲杀！</h1><p style="font-size: 1.2rem; color: #666;">牧原生猪产业链智能决策系统 v20.0 (坐标植入版)</p><p style="color: #999;">""" + OCR_STATUS + """</p></div>""", unsafe_allow_html=True)
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

elif st.session_state.current_page == 'pricing':
    st.markdown("<div class='page-header'><h1>🛒 结算定价中心</h1></div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回首页", key="back_p"): go_to_page('home')
    st.markdown("### 📷 屠宰结算单智能识别")
    img_file = st.file_uploader("上传单据", type=['jpg', 'png'])
    if img_file and CAN_OCR:
        st.image(img_file, width=300)
        try:
            import pytesseract
            from PIL import Image
            text = pytesseract.image_to_string(Image.open(img_file).convert('L'), config='--psm 6 -l chi_sim+eng')
            st.text_area("识别结果", text, height=200)
        except: st.error("识别失败")

elif st.session_state.current_page == 'trend':
    st.markdown("<div class='page-header'><h1>📈 行情预测中心</h1></div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回首页", key="back_t"): go_to_page('home')
    st.markdown("#### 今日行情一览")
    df = st.session_state.get('auto_market_data', pd.DataFrame({'省份': ['河南'], '价格': [15.0]}))
    edited = st.data_editor(df, num_rows="dynamic", hide_index=True)
    st.line_chart(edited.set_index('省份'))

elif st.session_state.current_page == 'analysis':
    st.markdown("<div class='page-header'><h1>📊 销售全景中心</h1></div>", unsafe_allow_html=True)
    if st.button("⬅️ 返回首页", key="back_a"): go_to_page('home')
    
    st.markdown("### 数据上传与配置")
    uploaded_files = st.file_uploader("📤 上传明细 (支持多选)", type=["xlsx", "xls"], accept_multiple_files=True, key="sales_v21")
    
    if uploaded_files:
        try:
            df_list = [pd.read_excel(f) for f in uploaded_files]
            df = pd.concat(df_list, ignore_index=True)
            df['来源文件'] = df.get('来源文件', f.name)
            
            with st.expander("⚙️ 列名配置", expanded=False):
                df.columns = [str(col).strip().replace('\n', '') for col in df.columns]
                cols = df.columns.tolist()
                def guess(kw, cols): return next((c for c in cols if kw in c), None)
                c1, c2, c3, c4 = st.columns(4)
                with c1: sel_cust = st.selectbox("客户", cols, index=cols.index(guess('客户', cols)) if guess('客户', cols) else 0)
                with c2: sel_mark = st.selectbox("屠宰场", cols, index=cols.index(guess('屠宰', cols)) if guess('屠宰', cols) else 0)
                with c3: sel_heads = st.selectbox("头数", cols, index=cols.index(guess('头数', cols)) if guess('头数', cols) else 0)
                with c4: sel_sub = st.selectbox("子公司", cols, index=cols.index(guess('子公司', cols)) if guess('子公司', cols) else 0)
                c5, c6 = st.columns(2)
                with c5: sel_price = st.selectbox("单价", ["无"] + cols)
                with c6: sel_date = st.selectbox("日期", ["来源文件名"] + [c for c in cols if '日期' in c])

            df.rename(columns={sel_cust:'客户姓名', sel_mark:'屠宰场', sel_heads:'总头数', sel_sub:'子公司'}, inplace=True)
            if sel_price != "无": df.rename(columns={sel_price:'单价'}, inplace=True); has_price = True
            else: df['单价'] = 0; has_price = False
            if sel_date == "来源文件名": df['日期'] = df['来源文件']
            else: df['日期'] = df[sel_date]
            
            # 核心处理
            df.dropna(subset=['客户姓名', '屠宰场'], inplace=True)
            df['总头数'] = pd.to_numeric(df['总头数'], errors='coerce').fillna(0)
            if guess('体重', df.columns): df['体重段'] = df[guess('体重', df.columns)].apply(extract_weight_smart)
            else: df['体重段'] = '未知'
            # 使用新的距离计算函数
            df['运距'] = df.apply(lambda x: estimate_distance_auto(x.get('子公司',''), x['屠宰场']), axis=1)
            df['采购类型'] = df.apply(lambda x: '直采' if x['客户姓名']==x['屠宰场'] else '中间商', axis=1)
            df['客户分类'] = df['客户姓名'].apply(classify_customer)
            
            st.success("✅ 数据加载完成")
            
            # 筛选
            st.markdown("#### 🏭 屠宰场筛选")
            all_markets = df['屠宰场'].unique().tolist()
            is_select_all = st.checkbox("全选所有屠宰场", value=True, key="check_all_v5")
            if is_select_all: selected_markets = all_markets
            else: selected_markets = st.multiselect("选择特定屠宰场", all_markets, default=all_markets[:5], key="market_filter_v5")
            if not selected_markets: st.stop()
            df_view = df[df['屠宰场'].isin(selected_markets)]
            dates = sorted(df_view['日期'].unique())
            
            # 预警
            st.markdown("#### 🚨 核心市场智能预警")
            stats = df_view.groupby('屠宰场').agg(总量=('总头数', 'sum'), 日均=('总头数', 'mean')).reset_index()
            if len(dates) >= 3:
                t = df_view[df_view['日期'].isin(dates[-3:])].groupby(['屠宰场', '日期'])['总头数'].sum().unstack(fill_value=0)
                up, down = [], []
                for m in t.index:
                    v = t.loc[m].values
                    if len(v)==3:
                        if v[0] < v[1] < v[2]: up.append(m)
                        if v[0] > v[1] > v[2]: down.append(m)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("<div class='alert-box-up'><b>🚀 连涨机会</b><br>" + "<br>".join(up if up else ["暂无"]) + "</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown("<div class='alert-box-down'><b>📉 连跌风险</b><br>" + "<br>".join(down if down else ["暂无"]) + "</div>", unsafe_allow_html=True)
            
            # 图表
            st.markdown("#### 📊 趋势分析")
            fig = px.pie(stats, values='总量', names='屠宰场', title='市场份额', hole=0.4)
            st.plotly_chart(fig, use_container_width=True, key="pie_main")
            
            # 客户画像
            st.markdown("#### 🤝 重点客户画像")
            mid = df_view[df_view['采购类型'] == '中间商']
            if not mid.empty:
                cust = mid.groupby('客户姓名').agg(总量=('总头数', 'sum'), 天数=('日期', 'nunique'), 均价=('单价', 'mean')).reset_index()
                cust['距离'] = mid.groupby('客户姓名')['运距'].first().values # 简化处理取第一个
                st.dataframe(cust.nlargest(10, '总量'), hide_index=True, use_container_width=True)

            buf = BytesIO()
            df_view.to_excel(buf, index=False)
            st.download_button("📥 导出Excel", buf, "result.xlsx")
            
        except Exception as e:
            st.error(f"分析出错: {e}")