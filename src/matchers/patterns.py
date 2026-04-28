import re

SENSITIVE_PATTERNS = {
    'PHONE_NUMBER': [
        re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)'),
    ],
    'EMAIL': [
        re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    ],
    'ADDRESS': [
        # 完整地址：省/自治区 + 市 + 区/县 + 街道/路 + 号/室
        re.compile(r'[一-龥]{2,6}(?:省|自治区|市)[一-龥]{2,8}(?:市|区|县|镇|乡)[一-龥\d]{2,20}(?:路|街|道|巷|弄|号|室|栋|幢|楼|单元|小区|花园|大厦|广场|公寓|村|组|院|苑|城|府|庭|阁|坊|里|园|庄)[一-龥\d]{0,15}'),
        # 市级地址：市 + 区/县 + 街道/路 + 号/室
        re.compile(r'[一-龥]{2,8}(?:市|区|县|镇|乡)[一-龥\d]{2,20}(?:路|街|道|巷|弄|号|室|栋|幢|楼|单元|小区|花园|大厦|广场|公寓|村|组|院|苑|城|府|庭|阁|坊|里|园|庄)[一-龥\d]{0,15}'),
    ],
    'LICENSE_PLATE': [
        re.compile(r'[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-Z][A-Z0-9]{5,6}(?!\d)'),
    ],
    'SOCIAL_SECURITY_NO': [
        re.compile(r'(?<![A-Z0-9\u4e00-\u9fa5])[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-Z]{2}\d{8,12}(?!\d)'),
    ],
    'HOUSING_FUND_NO': [
        re.compile(r'(?<![A-Z0-9])[A-Z]{2}(?<!MR)(?<!YB)\d{9,15}(?!\d)'),
    ],
    'MEDICAL_INSURANCE_NO': [
        re.compile(r'(?<![A-Z0-9])YB\d{12,16}(?!\d)'),
    ],
    'VIN_CODE': [
        re.compile(r'(?<![A-Z0-9])[A-HJ-NPR-Z0-9]{17}(?![A-Z0-9])'),
    ],
    'MEDICAL_RECORD_NO': [
        re.compile(r'(?<![A-Z0-9])MR\d{7,12}(?!\d)'),
    ],
    'USCC': [
        re.compile(r'(?<![A-Z0-9])[1-9A-N][0-9A-HJ-NP-RTUW-Y]\d{6}[0-9A-HJ-NP-RTUW-Y]{10}(?![A-Z0-9])'),
    ],
    'BUSINESS_LICENSE_NO': [
        re.compile(r'(?<!\d)[1-9]\d{14}(?!\d)'),
    ],
    'GPS_COORDINATE': [
        re.compile(r'-?\d{1,3}\.\d{2,},\s*-?\d{1,3}\.\d{2,}'),
    ],
    'IP_ADDRESS': [
        re.compile(r'\b(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\b'),
    ],
    'MAC_ADDRESS': [
        re.compile(r'(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}'),
    ],
    'ID_CARD': [
        re.compile(r'(?<!\d)\d{17}[\dXx](?!\d)'),
    ],
    'BANK_CARD': [
        re.compile(r'(?<!\d)\d{16,19}(?!\d)'),
    ],
    'PASSPORT': [
        re.compile(r'(?<![A-Z0-9])[EGDSPCMH]\d{8}(?!\d)'),
    ],
    'MILITARY_ID': [
        re.compile(r'军字第\d{8,12}号'),
        re.compile(r'[\u4e00-\u9fa5]字第\d{6,10}号'),
    ],
    'PASSWORD_OR_SECRET': [
        re.compile(r'sk-[a-zA-Z0-9]{20,}'),
        re.compile(r'\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}'),
        re.compile(r'(?i)(?:password|passwd|pwd|secret|token|key|api_key)\s*[=:]\s*[^\s,;]{6,}'),
        re.compile(r'(?i)(?:bearer|authorization)\s+[a-zA-Z0-9_\-\.]{20,}'),
        # 匹配变量名包含 key/secret/password 的赋值
        re.compile(r'(?i)(?:v_|var_|@)?(?:key|secret|password|token|api_key)[^\s]*\s+(?:VARCHAR|TEXT|CHAR)\s*(?:\(\d+\))?\s+(?:DEFAULT\s+)?[\'\"]([^\'\"]{6,})[\'\"]'),
        # 匹配 DECLARE v_password := 'value' 格式
        re.compile(r'(?i)(?:v_|var_|@)?(?:key|secret|password|token|api_key)[^\s]*\s+(?:TEXT|VARCHAR|CHAR)\s*(?:\(\d+\))?\s*:=\s*[\'\"]([^\'\"]{6,})[\'\"]'),
    ],
}

NOISE_PATTERNS = [
    re.compile(r'^\d{1,2}$'),
    re.compile(r'^[a-zA-Z]{1,3}$'),
    re.compile(r'^(?:test|demo|example|null|none|undefined|N/A|nan|None)$', re.IGNORECASE),
    re.compile(r'^[0]+$'),
    re.compile(r'^[1]+$'),
]

CHINESE_SURNAMES_SINGLE = set(
    '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜'
    '谢邹苏潘葛范彭鲁韦马苗方俞任袁柳史唐费薛雷贺倪汤滕殷罗毕郝邬安常'
    '乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵汪祁毛禹狄米贝明臧计伏'
    '成戴宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁'
    '钟徐邱骆高夏蔡田樊胡凌霍虞万柯管卢莫经房裘干解应宗丁宣邓郁单杭洪包'
    '诸左石崔吉钮龚程裴陆荀羊甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧'
    '隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸'
    '司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙乔阴郁胥能苍双闻莘党翟'
    '谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴'
    '瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄'
    '阙东殴殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须'
    '丰巢关蒯相查后荆红游竺权逯盖益昂仝花公佘操禹'
)

CHINESE_SURNAMES_COMPOUND = {
    '欧阳', '太史', '端木', '上官', '司马', '东方', '独孤', '南宫', '万俟',
    '闻人', '夏侯', '诸葛', '尉迟', '公羊', '赫连', '澹台', '皇甫', '宗政',
    '濮阳', '公冶', '太叔', '申屠', '公孙', '慕容', '仲孙', '钟离', '长孙',
    '宇文', '司徒', '鲜于', '司空', '闾丘', '子车', '亓官', '司寇', '巫马',
    '公西', '颛孙', '壤驷', '公良', '漆雕', '乐正', '宰父', '谷梁', '拓跋',
    '夹谷', '轩辕', '令狐', '段干', '百里', '呼延', '东郭', '南门', '羊舌',
    '微生', '梁丘', '左丘', '东门', '西门', '第五', '公甲', '公山', '公伯',
    '公坚', '公沙', '公皙', '公祖', '公输', '公仪', '公玉', '公仲', '公上',
    '公丘', '公晰', '公胜', '公索', '公慎', '公荆', '公襄',
}

CHINESE_NAME_COMMON_WORDS = {
    '管理', '安全', '系统', '测试', '数据', '信息', '公司', '部门', '项目',
    '产品', '服务', '客户', '北京', '上海', '广州', '深圳', '中国', '美国',
    '医院', '学校', '银行', '保险', '基金', '门诊', '住院', '急诊',
    '患者', '病人', '医生', '护士', '主任', '院长', '经理', '总裁', '总监',
    '申请', '审批', '登记', '注册', '注销', '变更', '备案', '查询', '统计',
    '报告', '报表', '汇总', '明细', '详情', '概况', '简介', '说明', '备注',
    '成功', '失败', '正常', '异常', '有效', '无效', '启用', '禁用', '删除',
    '待审', '已审', '通过', '拒绝', '完成', '进行', '取消', '延期', '加急',
    '男', '女', '是', '否', '有', '无', '可', '不可', '已', '未',
    '上午', '下午', '晚上', '今天', '明天', '昨天', '本周', '下周', '本月',
    '总分', '合计', '总计', '小计', '平均', '最高', '最低', '排名', '评分',
    '姓名', '名称', '标题', '主题', '类型', '类别', '状态', '阶段', '级别',
    '地址', '位置', '地点', '场所', '区域', '范围', '边界', '中心', '总部',
    '文件', '图片', '照片', '视频', '音频', '附件', '资料', '材料', '文档',
    '密码', '账号', '账户', '用户名', '手机号', '邮箱', '电话', '座机',
    '诊断', '处方', '住院', '手术', '检查', '化验', '护理', '治疗', '康复',
    '出院', '入院', '转院', '会诊', '抢救', '观察', '复查', '随访', '体检',
    '发票', '收据', '报销', '付款', '转账', '充值', '提现', '退款', '结算',
    '库存', '出库', '入库', '盘点', '调拨', '采购', '销售', '退货', '发货',
    '签收', '派送', '快递', '物流', '运输', '仓储', '配送', '分拣', '包装',
    '代码', '编号', '序列', '批次', '版本', '日期', '时间', '数量', '金额',
    '价格', '折扣', '优惠', '积分', '余额', '信用', '额度', '利率', '汇率',
    '城市', '省份', '国家', '区县', '街道', '乡镇', '社区', '园区', '校区',
    '民族', '国籍', '籍贯', '学历', '学位', '专业', '职称', '职务', '工号',
    '入职', '离职', '调动', '晋升', '降级', '考核', '培训', '考勤', '请假',
    '加班', '出差', '福利', '薪资', '奖金', '补贴', '津贴', '社保', '公积',
    '本科', '硕士', '博士', '博士后', '院士', '教授', '副教授', '讲师', '助教',
    '编译', '运行', '部署', '配置', '接口', '数据库', '服务器', '网络', '程序',
    '算法', '模型', '指标', '参数', '变量', '常量', '函数', '方法', '属性',
    '对象', '数组', '字符串', '整数', '浮点', '布尔', '空值', '异常', '错误',
    '警告', '日志', '记录', '消息', '通知', '公告', '新闻', '动态', '资讯',
    '法律法规', '政策', '制度', '条例', '规定', '办法', '细则', '标准', '规范',
    '方案', '计划', '规划', '策略', '目标', '任务', '进度', '结果', '效果',
    '原因', '分析', '结论', '建议', '意见', '措施', '对策', '办法', '途径',
    '通知邮箱', '经核查', '申请理由', '宗例地址', '变更理由', '原登记', '登记住所', '准予',
    '通知', '邮箱', '经核', '核查', '理由', '宗例', '变更', '住所', '准予', '原登',
    '登记', '申请', '审批', '受理', '不予', '准许', '驳回', '退回', '补正',
    '告知', '送达', '公示', '公告', '声明', '承诺', '授权', '委托', '代理',
    '原告', '被告', '上诉', '申诉', '仲裁', '调解', '执行', '判决', '裁定',
    '立案', '结案', '撤诉', '和解', '调解', '开庭', '庭审', '质证', '举证',
    '家庭住址', '案件地址', '谢谢', '住址', '案件', '家庭', '案件编号',
    '案由', '案号', '庭审笔录', '裁判文书', '起诉状', '答辩状',
    '家属', '周期', '全麻', '麻醉', '高血压', '查体', '关系', '钱包',
    '家庭往址', '家属手机', '家属联系', '申请人', '家庭地址', '申请事项',
    '通知邮件', '家长证件', '申请业务', '申请补贴', '劳动争议',
    '能不能退', '居民纠纷', '麻醉方式', '单位地址', '满意', '申诉理由',
    '蒙脱石散', '通知电话', '申请人签', '申方', '金穗网购', '娄托方',
    '家庭住班', '单方', '蒙庭住址', '白期', '通户', '方签字', '申方签字',
    '家庭往班', '贝街道', '薄网购', '包核对',
}

SENSITIVE_KEYWORDS = {
    'CHINESE_NAME': ['姓名', '名字', 'name', 'real_name', 'patient_name', 'holder_name', 'consignee', 'owner_name', 'full_name', 'contact_name', 'person_name', 'delegate_name', 'rep_name', '法人', '代表', '联系人', 'operator', 'creator', 'author', 'sender', 'payer', 'payee', 'applicant', 'signer', 'party_a', 'party_b', 'doctor_name', 'nurse_name', 'handler', 'created_by', 'officer', 'judge', 'prosecutor', 'clerk', 'plaintiff', 'defendant', 'presiding_judge'],
    'PHONE_NUMBER': ['手机', '电话', 'phone', 'mobile', 'tel', 'contact_phone', '联系电话', 'cellphone', 'telephone', '移动电话'],
    'EMAIL': ['邮箱', '邮件', 'email', 'mail', 'e_mail', '电子邮箱'],
    'ADDRESS': ['地址', '住址', 'address', 'addr', 'domicile', 'home_address', 'full_address', 'shipping_address', '居住地', '通讯地址', '户籍'],
    'ID_CARD': ['身份证', 'id_card', 'identity', 'id_number', 'id_verify', 'sfz', '身份证号', '证件号'],
    'BANK_CARD': ['银行卡', 'bank_card', 'card_no', 'account_no', 'bank_account', '卡号'],
    'PASSWORD_OR_SECRET': ['密码', 'password', 'passwd', 'secret', 'token', 'key', 'api_key', 'passphrase', '密钥'],
    'PASSPORT': ['护照', 'passport', '护照号'],
    'VIN_CODE': ['车架号', 'vin', 'vehicle_id', 'vin_code', '车辆识别号'],
    'USCC': ['信用代码', 'uscc', 'credit_code', 'unified_code', '统一社会信用代码'],
    'MEDICAL_RECORD_NO': ['病历', 'medical_record', 'record_no', '就诊号', '病历号'],
    'MEDICAL_INSURANCE_NO': ['医保', 'medical_insurance', 'insurance_no', '医保卡', 'medical_insurance_no', 'encoded_rx'],
    'HOUSING_FUND_NO': ['公积金', 'housing_fund', 'hf_no', '住房公积金'],
    'SOCIAL_SECURITY_NO': ['社保', 'social_security', 'ss_no', 'ssn', '社保号', '社保账号'],
    'LICENSE_PLATE': ['车牌', 'license_plate', 'plate_no', '车牌号'],
    'IP_ADDRESS': ['IP', 'ip_address', 'ip_addr'],
    'MAC_ADDRESS': ['MAC', 'mac_address', '物理地址'],
    'GPS_COORDINATE': ['经纬度', '坐标', 'gps', 'latitude', 'longitude', 'lat', 'lng', 'lon'],
    'MILITARY_ID': ['军官证', '军人证', 'military'],
}

FIELD_NAME_LEVEL_MAP = {
    'id_card': 'L4',
    'id_number': 'L4',
    'identity': 'L4',
    'bank_card': 'L4',
    'card_no': 'L4',
    'password': 'L4',
    'secret': 'L4',
    'token': 'L4',
    'passport': 'L4',
    'military_id': 'L4',
}

ID_CARD_AREA_CODES = {
    11, 12, 13, 14, 15, 21, 22, 23, 31, 32, 33, 34, 35, 36, 37,
    41, 42, 43, 44, 45, 46, 50, 51, 52, 53, 54, 61, 62, 63, 64, 65,
    71, 81, 82, 91,
}


def validate_id_card(value):
    if len(value) != 18:
        return False
    if not re.match(r'^\d{17}[\dX]$', value):
        return False
    if int(value[:2]) not in ID_CARD_AREA_CODES:
        return False
    try:
        import datetime
        year = int(value[6:10])
        month = int(value[10:12])
        day = int(value[12:14])
        if year < 1900 or year > 2026:
            return False
        datetime.datetime(year, month, day)
    except (ValueError, TypeError):
        return False
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_chars = '10X98765432'
    total = sum(int(value[i]) * weights[i] for i in range(17))
    expected = check_chars[total % 11]
    return value[17].upper() == expected


def validate_bank_card(value):
    if not value.isdigit():
        return False
    if len(value) < 16 or len(value) > 19:
        return False
    if len(set(value)) == 1:
        return False
    digits = [int(d) for d in value]
    checksum = 0
    for i in range(len(digits) - 1, -1, -1):
        d = digits[i]
        if (len(digits) - i) % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def validate_vin(value):
    if len(value) != 17:
        return False
    if re.search(r'[IOQ]', value):
        return False
    if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', value):
        return False
    if len(set(value)) < 4:
        return False
    letter_count = sum(1 for c in value if c.isalpha())
    digit_count = sum(1 for c in value if c.isdigit())
    if letter_count < 3 or digit_count < 3:
        return False
    return True


def validate_uscc(value):
    if len(value) != 18:
        return False
    if not any(c.isalpha() for c in value):
        return False
    if value[:6].isdigit() and int(value[:2]) in ID_CARD_AREA_CODES:
        year_str = value[6:10]
        if year_str.isdigit() and 1900 <= int(year_str) <= 2026:
            return False
    chars = '0123456789ABCDEFGHJKLMNPQRTUWXY'
    if not all(c in chars for c in value):
        return False
    weights = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]
    total = 0
    for i in range(17):
        total += chars.index(value[i]) * weights[i]
    check = (31 - total % 31) % 31
    return chars[check] == value[17]


def is_chinese_name(value):
    if not re.match(r'^[\u4e00-\u9fa5·]{2,4}$', value):
        return False
    if value in CHINESE_NAME_COMMON_WORDS:
        return False
    if value[0] in CHINESE_SURNAMES_SINGLE:
        return True
    if value[:2] in CHINESE_SURNAMES_COMPOUND:
        return True
    return False


def is_likely_id_card(value):
    if len(value) == 18:
        core = value[:17]
        if not core.isdigit():
            return False
        if int(core[:2]) not in ID_CARD_AREA_CODES:
            return False
        year_prefix = int(core[6:8])
        if year_prefix not in (19, 20):
            return False
        month = int(core[10:12])
        if month < 1 or month > 12:
            return False
        return True
    if len(value) == 17:
        if not value.isdigit():
            return False
        if int(value[:2]) not in ID_CARD_AREA_CODES:
            return False
        year_prefix = int(value[6:8])
        if year_prefix not in (19, 20):
            return False
        month = int(value[10:12])
        if month < 1 or month > 12:
            return False
        return True
    return False


def validate_sensitive_value(sensitive_type, value):
    if sensitive_type == 'ID_CARD':
        return validate_id_card(value)
    elif sensitive_type == 'BANK_CARD':
        if not validate_bank_card(value):
            return False
        if is_likely_id_card(value):
            return False
        return True
    elif sensitive_type == 'VIN_CODE':
        return validate_vin(value)
    elif sensitive_type == 'USCC':
        return validate_uscc(value)
    elif sensitive_type == 'PHONE_NUMBER':
        return bool(re.match(r'^1[3-9]\d{9}$', value))
    elif sensitive_type == 'EMAIL':
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value))
    elif sensitive_type == 'IP_ADDRESS':
        if '.' not in value:
            return False
        parts = value.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(p) <= 255 for p in parts)
        except ValueError:
            return False
    elif sensitive_type == 'LICENSE_PLATE':
        return bool(re.match(r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-Z][A-Z0-9]{5,6}$', value))
    elif sensitive_type == 'MAC_ADDRESS':
        return bool(re.match(r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$', value))
    elif sensitive_type == 'PASSPORT':
        return bool(re.match(r'^[EGDSPCMH]\d{8}$', value))
    elif sensitive_type == 'BUSINESS_LICENSE_NO':
        if not re.match(r'^[1-9]\d{14}$', value):
            return False
        if int(value[:2]) in ID_CARD_AREA_CODES:
            year_prefix = int(value[6:8])
            if year_prefix in (19, 20):
                month = int(value[10:12])
                if 1 <= month <= 12:
                    return False
        weights = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13]
        total = 0
        for i in range(14):
            total += int(value[i]) * weights[i % 12]
        check = (11 - total % 11) % 11
        return check == int(value[14])
    elif sensitive_type == 'HOUSING_FUND_NO':
        return bool(re.match(r'^[A-Z]{2}(?!MR)(?!YB)\d{9,15}$', value))
    elif sensitive_type == 'MEDICAL_INSURANCE_NO':
        return bool(re.match(r'^YB\d{12,16}$', value))
    elif sensitive_type == 'MEDICAL_RECORD_NO':
        return bool(re.match(r'^MR\d{7,12}$', value))
    elif sensitive_type == 'SOCIAL_SECURITY_NO':
        return bool(re.match(r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-Z]{2}\d{8,12}$', value))
    elif sensitive_type == 'CHINESE_NAME':
        return is_chinese_name(value)
    elif sensitive_type == 'ADDRESS':
        return bool(re.search(r'(?:省|市|区|县)', value) and len(value) >= 6)
    elif sensitive_type == 'GPS_COORDINATE':
        return bool(re.match(r'^-?\d{1,3}\.\d{2,},\s*-?\d{1,3}\.\d{2,}$', value))
    elif sensitive_type == 'MILITARY_ID':
        return bool(re.search(r'字第.*号', value))
    elif sensitive_type == 'PASSWORD_OR_SECRET':
        return len(value) >= 6
    return True
