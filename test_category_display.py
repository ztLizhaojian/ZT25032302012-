#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分类数据显示修复效果
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from database.db_access import DBAccess
from database.db_manager import execute_query

def test_category_query():
    """测试分类数据查询"""
    print("测试分类数据查询...")
    
    # 测试1: 使用execute_query函数
    print("\n1. 使用execute_query函数:")
    query = "SELECT id, name, category_type, description FROM categories ORDER BY id"
    
    # 不使用fetch_all=True (应该返回单条记录)
    single_row = execute_query(query)
    print(f"   不使用fetch_all=True的结果: {type(single_row).__name__}")
    if single_row:
        print(f"   单条记录示例: {single_row}")
    
    # 使用fetch_all=True (应该返回所有记录列表)
    all_rows = execute_query(query, fetch_all=True)
    print(f"   使用fetch_all=True的结果: {type(all_rows).__name__}")
    if all_rows:
        print(f"   总记录数: {len(all_rows)}")
        print(f"   前3条记录:")
        for i, row in enumerate(all_rows[:3]):
            print(f"     {i+1}. {row}")
    
    # 测试2: 直接使用DBAccess类
    print("\n2. 使用DBAccess类:")
    from database.db_manager import DBManager
    db_manager = DBManager()
    categories = db_manager.get_all_categories()
    print(f"   分类列表: {type(categories).__name__}")
    if categories:
        print(f"   总分类数: {len(categories)}")
        print(f"   前3个分类:")
        for i, category in enumerate(categories[:3]):
            print(f"     {i+1}. {category}")

if __name__ == "__main__":
    test_category_query()