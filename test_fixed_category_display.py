#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的分类数据显示逻辑
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from database.db_manager import execute_query

def test_fixed_load_categories_logic():
    """测试修复后的load_categories方法逻辑"""
    print("测试修复后的分类数据加载逻辑...")
    
    # 1. 获取分类数据
    query = "SELECT id, name, category_type, description FROM categories ORDER BY id"
    rows = execute_query(query, fetch_all=True)
    
    print(f"\n查询结果: {type(rows).__name__}, 共{len(rows)}条记录")
    
    # 2. 模拟修复后的填充逻辑
    print("\n模拟修复后的表格填充逻辑:")
    print("表格内容预览:")
    print("+----+------------------+------------+-------------+")
    print("| ID | 分类名           | 类型       | 备注        |")
    print("+----+------------------+------------+-------------+")
    
    for row_data in rows:
        # 修复后的逻辑：直接按字段名获取值
        items = []
        items.append(str(row_data['id']))
        items.append(str(row_data['name']))
        items.append(str(row_data['category_type']))
        items.append(str(row_data['description']))
        
        # 输出表格行
        print(f"| {items[0]:<2} | {items[1]:<16} | {items[2]:<10} | {items[3]:<11} |")
    
    print("+----+------------------+------------+-------------+")
    
    # 3. 验证数据完整性
    print("\n数据完整性验证:")
    for i, row in enumerate(rows):
        print(f"记录 {i+1}: ID={row['id']}, 分类名={row['name']}, 类型={row['category_type']}, 备注={row['description']}")

if __name__ == "__main__":
    test_fixed_load_categories_logic()