#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查categories表的结构
"""

import sqlite3
import os

def check_categories_table():
    """检查categories表的结构"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'data', 'finance_system.db')
    print(f"数据库路径: {db_path}")
    print("=" * 50)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询表结构
        cursor.execute("PRAGMA table_info(categories)")
        columns = cursor.fetchall()
        
        print("categories表结构:")
        print("ID | 列名 | 数据类型 | 是否可为空 | 默认值 | 主键")
        print("-" * 50)
        
        for col in columns:
            print("{0} | {1} | {2} | {3} | {4} | {5}".format(
                col[0], col[1], col[2], col[3], col[4], col[5]
            ))
        
        conn.close()
        print("检查完成")
        
    except Exception as e:
        print(f"检查失败: {str(e)}")

if __name__ == "__main__":
    check_categories_table()
