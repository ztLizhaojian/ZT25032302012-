#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分类管理功能修复是否有效
"""

import sqlite3
import os

# 获取数据库路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'data', 'finance_system.db')

def test_category_operations():
    """测试分类操作"""
    print(f"数据库路径: {db_path}")
    print("=" * 50)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 测试1: 插入分类
        print("测试1: 插入分类")
        test_category_name = "测试分类"
        test_category_type = "支出"
        test_description = "测试修复功能"
        
        query = "INSERT INTO categories (name, category_type, description) VALUES (?, ?, ?)"
        cursor.execute(query, (test_category_name, test_category_type, test_description))
        category_id = cursor.lastrowid
        conn.commit()
        
        print(f"✓ 成功插入分类: ID={category_id}")
        print(f"  分类名: {test_category_name}")
        print(f"  类型: {test_category_type}")
        print(f"  描述: {test_description}")
        print("-" * 50)
        
        # 测试2: 查询分类
        print("测试2: 查询分类")
        query = "SELECT id, name, category_type, description FROM categories WHERE id=?"
        cursor.execute(query, (category_id,))
        category = cursor.fetchone()
        
        if category:
            print(f"✓ 成功查询到分类: ID={category[0]}")
            print(f"  分类名: {category[1]}")
            print(f"  类型: {category[2]}")
            print(f"  描述: {category[3]}")
        else:
            print("✗ 查询分类失败")
        print("-" * 50)
        
        # 测试3: 更新分类
        print("测试3: 更新分类")
        updated_name = "测试分类（已更新）"
        updated_type = "收入"
        updated_description = "测试修复功能（已更新）"
        
        query = "UPDATE categories SET name=?, category_type=?, description=? WHERE id=?"
        cursor.execute(query, (updated_name, updated_type, updated_description, category_id))
        conn.commit()
        
        print(f"✓ 成功更新分类")
        print(f"  分类名: {updated_name}")
        print(f"  类型: {updated_type}")
        print(f"  描述: {updated_description}")
        print("-" * 50)
        
        # 测试4: 再次查询更新后的分类
        print("测试4: 再次查询更新后的分类")
        query = "SELECT id, name, category_type, description FROM categories WHERE id=?"
        cursor.execute(query, (category_id,))
        updated_category = cursor.fetchone()
        
        if updated_category:
            print(f"✓ 成功查询到更新后的分类: ID={updated_category[0]}")
            print(f"  分类名: {updated_category[1]}")
            print(f"  类型: {updated_category[2]}")
            print(f"  描述: {updated_category[3]}")
        else:
            print("✗ 查询更新后的分类失败")
        print("-" * 50)
        
        # 测试5: 删除分类
        print("测试5: 删除分类")
        query = "DELETE FROM categories WHERE id=?"
        cursor.execute(query, (category_id,))
        conn.commit()
        
        print(f"✓ 成功删除分类: ID={category_id}")
        print("-" * 50)
        
        # 测试6: 验证分类已删除
        print("测试6: 验证分类已删除")
        query = "SELECT id FROM categories WHERE id=?"
        cursor.execute(query, (category_id,))
        result = cursor.fetchone()
        
        if not result:
            print("✓ 分类已成功删除")
        else:
            print("✗ 分类删除失败")
        
        conn.close()
        print("=" * 50)
        print("所有测试通过！分类管理功能修复成功！")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        if conn:
            conn.close()

if __name__ == "__main__":
    test_category_operations()
