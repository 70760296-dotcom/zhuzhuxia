import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    OCR_STATUS = f"⚠️ OCR不可用"
    CAN_OCR = False

# --- 2. 核心数据：养殖场坐标 ---
FARM_COORDS = {
    '内乡': (111.974177, 33.026172), '卧龙': (112.451757, 32.904118), '邓州': (112.040009, 32.527833),
    '唐河': (113.098992, 32.680748), '扶沟': (114.476376, 34.156781), '通许': (114.600493, 34.376351),
    '杞县': (114.802569, 34.318349), '正阳': (114.310925, 32.410353), '滑县': (114.910323, 35.435523),
    '方城': (112.723136, 33.216503), '西华': (114.406725, 33.697725), '社旗': (113.044809, 32.992864),
    '太康': (114.858139, 34.225991), '商水': (114.391182, 33.522993), '鹿邑县': (115.107514, 33.906014),
    '农安': (124.975026, 44.509817), '双辽': (123.51, 43.94), '广宗': (115.20, 37.19),
}

# --- 3. 核心数据：屠宰场精确坐标 (根据您提供的数据录入) ---
SLAUGHTER_HOUSE_COORDS = {
    # 安徽
    "泗县鑫汇屠宰场": (117.891702, 33.428263),
    "铜陵市润知味食品有限公司": (117.953444, 30.934191),
    "安徽省大别山食品有限公司": (116.449608, 31.747634),
    "安徽省福润肉类加工有限公司": (115.874200, 32.926127),
    "河池市宜州区顺佳食品贸易有限公司": (108.668039, 24.469325), # 注：此条坐标在广西，原表归类可能有误，按坐标归位
    "安徽天贝食品有限公司": (116.797014, 33.886605),
    "安徽神华肉制品有限公司": (116.683894, 33.790518),
    "安徽易太肉类食品有限公司": (118.489792, 31.303101),
    "安徽联润食品集团有限公司": (118.555539, 31.716886),
    "安徽永洁肉类有限公司": (115.290824, 33.053962),
    "安徽信德恒肉类食品有限公司": (116.976715, 30.597157),
    "安徽省东升食品有限公司": (116.581293, 33.248560),
    "黄山漫城香食品有限公司": (118.343068, 29.809437),
    "安徽新安食品有限公司": (117.490188, 31.916995),
    "安徽和润肉食品有限公司": (115.462665, 33.350360),
    "合肥春然肉食品有限公司": (117.286870, 32.002653),
    "阜阳市海利食品有限公司": (115.874310, 32.837136),
    "宿州福润肉类食品有限公司": (117.024609, 33.612400),
    "亳州市万邦食品有限公司": (115.804722, 33.889667),
    "安徽中和食品有限公司": (118.377854, 31.766165),
    
    # 江苏
    "扬州市盛康畜禽有限公司": (119.636586, 32.613291),
    "淮安温氏晶诚食品有限公司": (118.603400, 33.018535),
    "徐州凯佳食品有限公司": (116.672111, 34.738334),
    "苏州市华统食品有限公司": (120.676454, 31.190864),
    "淮安市金源肉品有限公司": (119.001619, 33.550982),
    "南通市通州区合鑫畜禽屠宰有限公司": (120.817978, 32.142123),
    "徐州安邦食品有限公司": (116.815421, 34.696057),
    "昆山市定点屠宰加工中心有限公司": (120.907039, 31.298923),
    "太仓市中溪食品有限公司": (121.091405, 31.576792),
    "江苏冠全食品有限公司": (120.293889, 33.085264),
    "江苏天宝食品有限公司": (119.988700, 32.800039),
    "太仓市青田食品有限公司": (121.073805, 31.467347),
    "江苏富康食品有限公司": (119.811643, 32.263285),
    "淮安拾分味道食品有限公司": (118.582975, 32.988819),
    "南京元润食品有限公司": (119.052242, 31.925219),
    "江苏润通食品有限公司": (119.062845, 33.651534),
    "高淳县食品有限公司淳溪分公司": (118.858974, 31.335588),
    "中粮家佳康（江苏）有限公司": (120.455351, 32.753951),
    "镇江市润江屠宰有限公司": (119.551143, 32.120392),
    "江苏优平食品有限公司": (119.717174, 32.489441),
    "江苏淮安苏食肉品有限公司": (119.044177, 33.567945),
    "连云港苏海肉食品有限公司": (119.224658, 34.663438),
    "盐城众恒食品有限公司": (119.777828, 34.012204),
    "徐州优特农牧有限公司": (117.240479, 34.097713),
    
    # 山东
    "日照市康信食品有限公司": (119.494150, 35.385771),
    "临沂新程金锣肉制品集团有限公司": (118.275438, 35.228216),
    "临沂顺发食品有限公司": (118.526724, 35.460035),
    "山东融跃肉制品有限公司": (117.415522, 35.110358),
    "凯佳食品集团有限公司": (118.424653, 35.105648),
    "聊城维尔康食品有限公司": (115.998945, 36.456489),
    "山东郯润生态食品有限公司": (118.342587, 34.740271),
    "青州凯佳食品有限公司": (118.527768, 36.729458),
    "山东汇融肉制品有限公司": (118.436659, 35.281693),
    "山东故乡食品有限公司": (118.582419, 34.953529),
    "临沂鑫盛源食品有限公司": (118.364410, 35.485587),
    "德州金锣肉制品有限公司": (116.878258, 37.13627),
    "山东千喜鹤食品有限公司": (115.980610, 36.987839),
    "聊城龙大肉食品有限公司": (115.946691, 36.511326),
    "泰安大福食品有限公司": (117.076086, 35.879883),
    "山东卓然食品有限公司": (115.518351, 35.581234),
    "山东成润肉类食品有限公司": (116.027105, 35.084920),
    "临沂市民康肉制品有限公司": (118.356953, 34.947830),
    "山东青山食品有限公司": (118.222660, 35.078680),
    "山东利洋食品有限公司": (117.994173, 34.852400),
    "山东子扬食品加工有限公司": (118.006274, 34.827429),
    "潍坊益康宝食品有限公司": (118.963664, 36.725928),
    "临沂市泽润肉制品加工有限公司": (118.390521, 35.161832),
    "齐河宏康肉类加工有限公司": (116.648215, 36.736261),
    "山东新农生态农业有限公司": (118.759185, 35.324728),
    "山东泗水泉林肉类加工有限公司": (117.401208, 35.651068),
    "山东恒昌源肉制品有限公司": (118.925276, 36.398908),
    "山东郓城华宝食品有限公司": (115.986700, 35.564373),
    "曲阜市圣利食品有限公司": (117.007254, 35.587214),
    "济宁三益食品有限公司": (116.203086, 35.609484),
    "山东利洋食品有限公司": (117.994173, 34.852400),
    
    # 河南
    "河南中润新程食品有限公司": (116.43904, 33.89636),
    "开封市福生祥食业有限公司": (114.332789, 34.754068),
    "河南上农实业有限公司": (114.212407, 33.309615),
    "西华县豫龙食品有限公司": (114.527715, 33.792054),
    "虞城县鑫虹食品有限公司": (115.886526, 34.402158),
    "郑州双汇食品有限公司": (113.841663, 34.718244),
    "商丘市缘源食品有限公司": (115.653927, 34.469351),
    "河南凯佳食品有限公司": (114.046096, 32.835376),
    "洛阳正大食品有限公司": (112.353606, 34.710513),
    "济源双汇食品有限公司": (112.630478, 35.086548),
    "河南唐人神肉类食品有限公司": (115.235812, 36.068087),
    "河南天康宏展食品有限公司": (113.789326, 34.485552),
    "新乡市高金食品有限公司": (114.093576, 35.280608),
    "原阳县天天食品有限公司": (113.909043, 35.042218),
    "辉县市兴桥食品有限公司": (113.690644, 35.372091),
    "南阳育阳食品有限公司": (112.649821, 32.892604),
    "邓州市渠首肉食品有限公司": (112.060287, 32.658489),
    "平顶山市爱鑫肉食品有限公司": (113.299395, 33.495645),
    "镇平县汇鑫肉联有限公司": (112.219162, 33.030893),
    "唐河豫龙肉制品有限公司": (112.822707, 32.661141),
    "社旗璟润肉食品有限公司": (111.899088, 33.030262),
    "新野县瑞发肉联有限公司": (112.375164, 32.505094),
    "固始县信佳食品有限公司": (115.701179, 32.192755),
    "河南双汇投资发展股份有限公司": (114.074586, 33.555256),
    
    # 河北
    "河北双杰肉类食品有限公司": (114.848683, 38.328007),
    "泊头市恒祥冷鲜肉有限公司": (116.549811, 38.122938),
    "秦皇岛宏泰生猪屠宰有限公司": (119.416356, 39.931754),
    "定州市福源食品有限公司": (114.848295, 38.457516),
    "涿州市宇东生猪屠宰有限公司": (116.013135, 39.451349),
    "饶阳县盈信屠宰有限公司": (115.745293, 38.222173),
    "河北千喜鹤肉类产业有限公司": (115.418535, 37.365442),
    "石家庄双鸽圣蕴食品有限公司": (114.981637, 38.032202),
    "邯郸市金都食品有限公司": (114.662263, 36.469504),
    "河北安平大红门食品有限公司": (115.562347, 38.236086),
    "保定市清苑区润发食品制造有限公司": (115.441068, 38.654472),
    "涿州市汪记生猪屠宰有限公司": (115.975274, 39.541514),
    "石家庄市双雨食品有限公司": (114.437042, 38.300437),
    "武强县鑫龙食品有限公司": (116.004733, 38.051391),
    "邯郸市民爱食品有限公司": (114.957247, 36.500666),
    "怀安宏都食品有限公司": (114.497613, 40.456153),
    "河北宏都实业集团有限公司": (119.270690, 39.879721),
    "承德二商大红门肉类食品有限公司": (117.419030, 40.994123),
    
    # 浙江
    "台州华统食品有限公司": (121.519050, 28.632285),
    "浙江云谷肉类食品有限公司": (120.137571, 28.659472),
    "丽水市华统食品有限公司": (119.804555, 28.342713),
    "宁波方兴食品有限公司": (121.423981, 29.743980),
    "杭州萧山临浦肉类加工有限公司": (120.241332, 30.004221),
    "杭州萧山红垦肉类加工有限公司": (120.395311, 30.223722),
    "绍兴市天天肉食品有限公司": (120.649181, 30.095899),
    "浙江诸暨力天食品有限公司": (120.241554, 29.713098),
    "浙江青莲食品股份有限公司新兴屠宰场": (120.932152, 30.584858),
    "桐乡市食品有限公司": (120.549282, 30.617008),
    "平湖市明大食品有限公司": (121.056330, 30.796711),
    "安吉交投食品有限公司递铺生猪定点屠宰场": (119.716677, 30.664660),
    "东阳康优食品有限公司": (120.215142, 29.277776),
    "金华紫兰食品有限公司": (119.527021, 29.087992),
    "慈溪市西部畜禽屠宰加工中心有限公司": (121.191484, 30.232652),
    "海盐县天康肉类食品有限公司通元中心屠宰厂": (120.849475, 30.428674),
    "建德市三弟兄农业开发有限公司": (119.489341, 29.518548),
    "桐乡市金瑞食品有限公司": (120.48714, 30.609612),
    
    # 广东/广西
    "广西邕之泰实业有限公司五合屠宰场": (108.533802, 22.824101),
    "深圳市中龙食品有限公司": (114.347148, 22.757307),
    "桂林肉类联合加工有限公司屠宰肉制品分公司": (110.288504, 25.296603),
    "广州孔旺记食品有限公司": (113.213203, 23.303661),
    "广州市番禺食品有限公司大石分公司": (113.298673, 22.998747),
    "广西新又鲜畜禽有限公司": (108.176411, 22.776216),
    "广西壮美那食品有限公司": (107.912645, 23.071412),
    "清远双汇食品有限公司": (112.996661, 23.720991),
    "东莞南联食品股份有限公司": (114.106018, 22.780957),
    "深圳农牧美益肉业有限公司": (113.888369, 22.721588),
    "粤海食品（佛山）有限公司": (113.050503, 23.125655),
    "广西贵港市盈康食品有限公司": (109.650205, 23.043856),
    
    # 黑龙江/辽宁/吉林
    "望奎双汇北大荒食品有限公司": (126.416244, 46.818139),
    "沈阳双汇食品有限公司": (123.585019, 41.957426),
    "大庆金锣肉制品有限公司": (124.925798, 46.631251),
    "铁岭九星食品集团有限公司": (123.970825, 42.776788),
    "吉林华正农牧业开发股份有限公司": (125.219401, 44.033824),
    "松原市三义肉食品有限公司": (124.855400, 45.252510),
    "梨树县华统食品有限公司": (124.374461, 43.306059),
    "四平市宏平肉业有限公司": (124.397409, 43.206316),
    "辽宁诚信味邦肉类加工有限公司": (122.963736, 41.064636),
    "阜新大红门肉类食品有限公司": (121.579253, 41.959430),
    "辽宁春晓肉食品有限公司": (122.026165, 41.765371),
    "沈阳市中邦食品有限公司": (122.872958, 41.501800),
    "辽宁千喜鹤食品有限公司": (123.570818, 41.920813),
    "辽宁国美农牧集团有限公司": (124.087789, 42.745916),
    "大连成三础明食品加工有限公司": (121.932453, 39.599800),
    "哈尔滨高金食品有限公司": (126.556556, 45.920705),
    "黑龙江北旺食品有限公司": (126.670668, 45.623798),
    "黑龙江龙大肉食品有限公司": (125.362052, 46.469672),
    "大庆一口猪食品有限公司": (125.269291, 45.882794),
    "克东县裕新畜禽食品加工有限公司": (126.256761, 48.015039),
    "兰西县丰达东北民猪产业开发有限公司": (126.264571, 46.241270),
    "巴彦万润肉类加工有限公司": (127.409098, 46.057320),
    "黑龙江宾西肉业有限公司": (127.154913, 45.774196),
    
    # 湖北/湖南
    "湖南湘食食品有限公司": (113.593537, 28.691424),
    "武汉恒源盛肉类食品有限公司": (114.332781, 30.231576),
    "天门鑫福食品有限公司": (113.114094, 30.602179),
    "襄阳市康福达肉食品有限公司": (112.171905, 32.083611),
    "荆门市康顺食品有限公司": (112.224996, 30.938424),
    "湖北湘康食品发展有限公司": (112.201065, 30.095190),
    "湖北佳农食品有限公司": (114.968086, 30.440207),
    "钟祥市盘龙肉类加工有限公司": (112.596988, 31.141641),
    "湖北高金食品有限公司": (113.743645, 31.005237),
    "宜昌市联海食品有限公司": (111.426920, 29.585569), # Approx
    "湖北心连心畜牧实业有限公司": (112.594075, 31.145083),
    "湖北升康食品有限公司": (112.576024, 29.899133),
    "湖北虹美食品有限公司": (112.305812, 31.056098),
    "湖北联鑫畜禽屠宰有限公司": (113.993246, 31.009821),
    "湖南红星盛业食品股份有限公司": (113.054170, 28.065139),
    "湖南颐丰食品有限公司": (112.309997, 28.701469),
    "湖南海泰食品有限公司": (113.194956, 29.415010),
    "岳阳汇康食品有限公司": (113.194082, 29.413272),
    "湖南惠源农牧发展股份有限公司": (111.678820, 28.971070),
    "张家界双安肉类食品有限公司牲猪定点屠宰场": (110.524336, 29.128940),
    
    # 四川/重庆/云南/贵州/陕西/甘肃/山西/内蒙古等
    "山西泽榆畜牧业开发有限公司": (112.696376, 37.642906),
    "运城市宏盛源食品有限公司生猪定点屠宰厂": (110.962712, 35.013007),
    "长治市上党区司马泓发肉业有限公司": (113.040283, 36.125587),
    "文水县双德食品有限公司": (112.035099, 37.467260),
    "山西晋润肉类食品有限公司": (112.269340, 37.308364),
    "晋中市太谷区开源肉业股份有限公司": (112.535761, 37.442594),
    "山西灵润肉食品有限公司": (111.883663, 36.867046),
    "山西裕盛肉业有限公司": (112.646110, 37.633610),
    "陕西双汇食品有限公司": (108.613393, 34.306172),
    "西安笨笨畜牧有限公司": (109.053979, 34.500529),
    "陕西蒲城大红门肉类食品有限公司": (109.630877, 34.954876),
    "咸阳市大地食品有限公司": (108.623870, 34.302596),
    "汉中市汉森食品有限公司": (107.039482, 33.092454),
    "重庆万州蓝希络食品有限公司": (108.467503, 30.776106),
    "重庆市兴发新实业有限公司": (107.011136, 29.847386),
    "重庆市垫江蓝星实业有限公司": (107.364652, 30.335564),
    "四川盛龙食品有限公司": (104.251618, 30.959432),
    "什邡市瑞祥肉食品有限公司": (104.064849, 31.144044),
    "什邡市远达食品有限公司": (104.090073, 31.210905),
    "甘肃西泰食品工业有限公司": (104.440614, 35.538555),
    "榆中瑞丰食品有限公司": (103.901048, 36.033743),
    "兰州高金食品有限公司": (103.858525, 36.030772),
    "甘肃品高食品有限公司": (103.627597, 36.120050),
    "内蒙古蒙德润食品有限公司": (110.526768, 40.574396),
    "包头市金锁生猪屠宰有限公司": (109.797720, 40.638154),
}

# --- 通用城市坐标 (备用) ---
CITY_COORDS = {
    '南阳': (32.99, 112.53), '郑州': (34.74, 113.65), '济南': (36.65, 117.12), 
    '南京': (32.06, 118.79), '武汉': (30.58, 114.30), '广州': (23.13, 113.26),
    '临沂': (35.10, 118.35), '成都': (104.06, 30.67), '杭州': (120.16, 30.25)
}

# --- 4. 计算函数 ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_coord(name):
    # 优先匹配精确屠宰场库
    if name in SLAUGHTER_HOUSE_COORDS: return SLAUGHTER_HOUSE_COORDS[name]
    # 其次匹配养殖场库
    if name in FARM_COORDS: return FARM_COORDS[name]
    # 最后模糊匹配城市
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

# 行为分类函数 (花期)
def classify_behavior(cust_data, total_dates):
    days = cust_data['日期'].nunique()
    if len(total_dates) == 0: return "未知"
    ratio = days / len(total_dates)
    if ratio > 0.8: return "👑 忠实选手"
    if ratio < 0.2:
        if cust_data['日期'].max() == max(total_dates): return "🚀 猛然闯入"
        return "⚠️ 消极选手"
    return "🛡️ 稳定选手"

# --- 5. 样式 ---
st.markdown("""
<style>
    .main .block-container { padding: 2rem 2.5rem !important; max-width: 100% !important; }
    header, footer { visibility: hidden; }
    .stButton>button { background-color: #FF4B4B; color: white; border-radius: 8px; padding: 8px 20px; font-weight:bold; }
    .stButton>button:hover { background-color: #e04343; }
    .alert-box-up { background-color: #e8f5e9; border-left: 5px solid #00C853; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
    .alert-box-down { background-color: #ffebee; border-left: 5px solid #FF4B4B; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 6. 页面路由 ---
if 'page' not in st.session_state: st.session_state.page = 'home'
def go(p): st.session_state.page = p; st.rerun()

# ==========================================
# 页面 A：指挥室
# ==========================================
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align:center; color:#FF4B4B'>🐷 生猪智能采购系统</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#888'>商业智能版 v6.0 | {OCR_STATUS}</p>", unsafe_allow_html=True)
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📊 行情分析预测", use_container_width=True): go('trend')
    with c2:
        if st.button("📤 屠宰结算模拟", use_container_width=True): go('slaughter')
    with c3:
        if st.button("📉 运营复盘分析", use_container_width=True): go('analysis')

# ==========================================
# 页面 B：行情分析 (关联复盘数据)
# ==========================================
elif st.session_state.page == 'trend':
    st.markdown("<h2>📊 行情分析预测</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回指挥室"): go('home')
    
    df_history = st.session_state.get('global_df', None)
    
    if df_history is not None:
        st.success(f"已检测到 {len(df_history)} 条历史数据")
        with st.expander("⚙️ 配置分析列"):
            cols = df_history.columns.tolist()
            def guess(k): return next((c for c in cols if k in c), cols[0])
            c1, c2 = st.columns(2)
            with c1: f_date = st.selectbox("日期列", cols, index=cols.index(guess('日期')))
            with c2: f_price = st.selectbox("价格列", cols, index=cols.index(guess('结算')))
        
        fig = px.line(df_history.groupby(f_date)[f_price].mean().reset_index(), x=f_date, y=f_price, title="价格走势")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("暂无数据。请先在【运营复盘分析】页面上传 Excel 数据。")

# ==========================================
# 页面 C：结算模拟 (OCR + 精确距离)
# ==========================================
elif st.session_state.page == 'slaughter':
    st.markdown("<h2>📤 屠宰结算模拟器</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回指挥室"): go('home')
    
    # --- OCR 模块 ---
    st.markdown("#### 📷 结算单智能识别")
    img_file = st.file_uploader("上传单据", type=['jpg', 'png'])
    
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
                    nums = re.findall(r'\d+\.?\d*', text)
                    if len(nums) >= 2:
                        floats = [float(n) for n in nums if float(n) > 10]
                        if len(floats) >= 2:
                            floats.sort()
                            st.session_state.ocr_weight = floats[len(floats)//2]
                            st.session_state.ocr_s_price = floats[-1]
                            st.success(f"✅ 已自动填入：体重 {st.session_state.ocr_weight}kg, 结算价 {st.session_state.ocr_s_price}元")
                except Exception as e:
                    st.error(f"识别出错: {e}")
        else:
            st.warning("云端 OCR 功能暂未启用")
            
    st.markdown("---")

    # --- 计算模块 ---
    st.markdown("#### 🧮 利润试算")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🛒 采购端")
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
        
        # 手动输入屠宰场名称，系统会自动查找精确坐标
        s_market_input = st.text_input("目标屠宰场名称", value="临沂新程金锣")
    
    if st.button("🚀 开始计算利润", type="primary"):
        settle_price = s_base * (s_rate/100) * s_level - s_deduct
        dist = 0
        coord1 = get_coord(p_farm)
        coord2 = get_coord(s_market_input) # 自动查找精确坐标
        
        if coord1 and coord2:
            dist = haversine(coord1[1], coord1[0], coord2[1], coord2[0])
            st.caption(f"📌 精确距离: {dist:.1f} 公里 (基于坐标库)")
        else:
            st.caption("⚠️ 未找到精确坐标，运距按0计算")
        
        profit, cost, freight, income = calc_profit(p_price, settle_price, p_weight, p_heads, dist)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("预估结算价", f"{settle_price:.2f} 元/kg")
        with c2: st.metric("预估总成本", f"{cost+freight:.0f} 元")
        with c3: st.metric("预估总利润", f"{profit:.0f} 元", delta=f"{profit/(cost+freight)*100:.1f}%")
        st.success(f"**单头利润**：**{profit/p_heads:.1f} 元/头**")

# ==========================================
# 页面 D：运营复盘 (高级版：预警+花期+份额)
# ==========================================
elif st.session_state.page == 'analysis':
    st.markdown("<h2>📉 运营复盘分析</h2>", unsafe_allow_html=True)
    if st.button("⬅️ 返回指挥室"): go('home')
    
    files = st.file_uploader("上传Excel明细", type=['xlsx'], accept_multiple_files=True)
    
    if files:
        try:
            df = pd.concat([pd.read_excel(f) for f in files])
            st.session_state['global_df'] = df # 同步数据
            
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
                df['总重量'] = pd.to_numeric(df[f_weight], errors='coerce').fillna(110) * df[f_heads]
            else:
                df['总重量'] = df[f_heads] * 110
            
            # 计算利润
            df['总收入'] = df['总重量'] * df[f_price_s]
            df['总成本'] = df['总重量'] * df[f_price_p]
            df['利润'] = df['总收入'] - df['总成本']
            
            st.success("✅ 数据计算完成")

            # --- 核心功能恢复：智能预警 ---
            st.markdown("#### 🚨 核心市场智能预警")
            # 统计连涨连跌
            trend_check = df.groupby([f_mark, f_date])['总头数'].sum().unstack(fill_value=0)
            up_markets, down_markets = [], []
            
            # 简单检查最近三天趋势
            if trend_check.shape[1] >= 3:
                last_3_days = trend_check.columns[-3:]
                for market in trend_check.index:
                    vals = trend_check.loc[market, last_3_days].values
                    if vals[0] < vals[1] < vals[2]: up_markets.append(market)
                    if vals[0] > vals[1] > vals[2]: down_markets.append(market)
                    
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='alert-box-up'><b>🚀 连涨机会</b><br>" + "<br>".join(up_markets[:5] if up_markets else ["暂无"]) + "</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='alert-box-down'><b>📉 连跌风险</b><br>" + "<br>".join(down_markets[:5] if down_markets else ["暂无"]) + "</div>", unsafe_allow_html=True)

            # --- 核心功能恢复：市场份额 ---
            st.markdown("#### 📊 屠宰场市场份额")
            share_df = df.groupby(f_mark)['总头数'].sum().reset_index()
            fig_pie = px.pie(share_df, values='总头数', names=f_mark, title='市场份额', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

            # --- 核心功能恢复：客户行为分析 (花期) ---
            st.markdown("#### 🤝 客户行为画像 (花期)")
            # 假设客户姓名列
            f_cust = guess('客户')
            if f_cust in cols:
                behavior_df = df.groupby(f_cust).apply(lambda x: classify_behavior(x, df[f_date].unique())).reset_index()
                behavior_df.columns = [f_cust, '行为画像']
                st.dataframe(behavior_df.head(10), use_container_width=True)
            
            # --- 详细数据表 ---
            with st.expander("📄 查看详细数据"):
                st.dataframe(df[[f_date, f_sub, f_mark, '利润']].head(20))

        except Exception as e:
            st.error(f"分析出错: {e}")