# 读取文件
with open('patterns.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到 ADDRESS 部分的行号
address_start = None
for i, line in enumerate(lines):
    if "'ADDRESS': [" in line:
        address_start = i
        break

if address_start is None:
    print("未找到 ADDRESS 部分")
    exit(1)

# 找到 ADDRESS 部分的结束行
address_end = address_start + 1
while address_end < len(lines) and "]," not in lines[address_end]:
    address_end += 1

# 创建新的 ADDRESS 部分
new_address_lines = [
    "    'ADDRESS': [\n",
    "        # 完整地址：省/自治区 + 市 + 区/县 + 街道/路 + 号/室\n",
    "        re.compile(r'[\u4e00-\u9fa5]{2,6}(?:省|自治区|市)[\u4e00-\u9fa5]{2,8}(?:市|区|县|镇|乡)[\u4e00-\u9fa5\d]{2,20}(?:路|街|道|巷|弄|号|室|栋|幢|楼|单元|小区|花园|大厦|广场|公寓|村|组|院|苑|城|府|庭|阁|坊|里|园|庄)[\u4e00-\u9fa5\d]{0,15}'),\n",
    "        # 市级地址：市 + 区/县 + 街道/路 + 号/室\n",
    "        re.compile(r'[\u4e00-\u9fa5]{2,8}(?:市|区|县|镇|乡)[\u4e00-\u9fa5\d]{2,20}(?:路|街|道|巷|弄|号|室|栋|幢|楼|单元|小区|花园|大厦|广场|公寓|村|组|院|苑|城|府|庭|阁|坊|里|园|庄)[\u4e00-\u9fa5\d]{0,15}'),\n",
    "    ],\n",
]

# 替换原来的 ADDRESS 部分
lines[address_start:address_end+1] = new_address_lines

# 写入文件
with open('patterns.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("ADDRESS 正则表达式已优化")
