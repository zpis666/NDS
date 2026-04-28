#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化 patterns.py 中的 ADDRESS 正则表达式
"""
import re

# 读取文件
with open('src/matchers/patterns.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 使用正则表达式查找并替换 ADDRESS 部分
# 匹配从 'ADDRESS': [ 到 ], 的部分
pattern = r"('ADDRESS': \[)\n(.*?\n)(.*?\n)(.*?\])"
replacement = r"""\1
        # 完整地址：省/自治区 + 市 + 区/县 + 街道/路 + 号/室
        re.compile(r'[\u4e00-\u9fa5]{2,6}(?:省|自治区|市)[\u4e00-\u9fa5]{2,8}(?:市|区|县|镇|乡)[\u4e00-\u9fa5\d]{2,20}(?:路|街|道|巷|弄|号|室|栋|幢|楼|单元|小区|花园|大厦|广场|公寓|村|组|院|苑|城|府|庭|阁|坊|里|园|庄)[\u4e00-\u9fa5\d]{0,15}'),
        # 市级地址：市 + 区/县 + 街道/路 + 号/室
        re.compile(r'[\u4e00-\u9fa5]{2,8}(?:市|区|县|镇|乡)[\u4e00-\u9fa5\d]{2,20}(?:路|街|道|巷|弄|号|室|栋|幢|楼|单元|小区|花园|大厦|广场|公寓|村|组|院|苑|城|府|庭|阁|坊|里|园|庄)[\u4e00-\u9fa5\d]{0,15}'),
    ],"""

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    with open('src/matchers/patterns.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("ADDRESS 正则表达式已优化")
else:
    print("未找到匹配的内容")
