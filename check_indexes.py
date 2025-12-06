#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查transactions表的索引是否已正确添加
"""

import sqlite3
import os

# 获取数据库路径
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'data', 'finance_system.db')

def check_transaction_indexes():
    """检查transactions表的索引"""
    print(f"检查数据库: {db_path}")
    print("=" * 50)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询transactions表的所有索引
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='transactions'")
        indexes = cursor.fetchall()
        
        print(f"transactions表的索引: {len(indexes)} 个")
        print("-" * 50)
        
        if indexes:
            for index_name, index_sql in indexes:
                print(f"索引名称: {index_name}")
                print(f"索引定义: {index_sql}")
                print("-" * 50)
        else:
            print("transactions表没有任何索引！")
        
        conn.close()
        print("检查完成")
        
    except Exception as e:
        print(f"检查失败: {str(e)}")

if __name__ == "__main__":
    check_transaction_indexes()
