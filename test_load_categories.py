#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的分类数据加载逻辑
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from database.db_manager import execute_query

def test_load_categories_logic():
    """测试分类数据加载逻辑"""
    print("测试修复后的分类数据加载逻辑...")
    
    # 模拟修复后的load_categories方法逻辑
    query = "SELECT id, name, category_type, description FROM categories ORDER BY id"
    
    # 1. 使用修复后的fetch_all=True参数
    print("\n1. 使用fetch_all=True参数:")
    rows = execute_query(query, fetch_all=True)
    print(f"   查询结果类型: {type(rows).__name__}")
    print(f"   查询结果数量: {len(rows)}")
    
    if rows:
        print("\n   模拟表格填充逻辑:")
        print("   表格内容预览:")
        print("   +----+------------------+------------+-------------+")
        print("   | ID | 分类名           | 类型       | 备注        |")
        print("   +----+------------------+------------+-------------+")
        
        for row_data in rows:
            # 模拟原代码中的遍历逻辑
            items = []
            for i, data in enumerate(row_data):
                items.append(data)
            
            # 输出表格行
            print(f"   | {items[0]:<2} | {items[1]:<16} | {items[2]:<10} | {items[3]:<11} |")
        
        print("   +----+------------------+------------+-------------+")
    
    # 2. 对比不使用fetch_all=True的情况（原错误）
    print("\n2. 对比不使用fetch_all=True的情况（原错误）:")
    rows_without_fetchall = execute_query(query)
    print(f"   查询结果类型: {type(rows_without_fetchall).__name__}")
    
    if rows_without_fetchall:
        print("   原错误逻辑的表格填充预览:")
        print("   +----+------------------+------------+-------------+")
        print("   | ID | 分类名           | 类型       | 备注        |")
        print("   +----+------------------+------------+-------------+")
        
        # 模拟原错误代码中的遍历逻辑
        for row_data in rows_without_fetchall:
            items = []
            for i, data in enumerate(row_data):
                items.append(data)
            
            # 输出表格行
            print(f"   | {items[0]:<2} | {items[1]:<16} | {items[2]:<10} | {items[3]:<11} |")
        
        print("   +----+------------------+------------+-------------+")

if __name__ == "__main__":
    test_load_categories_logic()