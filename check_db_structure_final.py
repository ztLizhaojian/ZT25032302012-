#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构的脚本
"""

import sys
import os
import sqlite3

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_database_structure():
    """检查数据库表结构"""
    print("=== 检查数据库表结构 ===")
    
    try:
        # 1. 确定数据库路径
        from src.database.db_manager import DB_PATH
        print(f"数据库路径: {DB_PATH}")
        
        # 2. 检查数据库文件是否存在
        if not os.path.exists(DB_PATH):
            print("❌ 数据库文件不存在")
            return False
        
        print("✅ 数据库文件存在")
        
        # 3. 连接到数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 4. 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\n数据库中的表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 5. 检查users表结构
        print("\nusers表结构:")
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
        # 6. 检查其他重要表结构
        print("\naccounts表结构:")
        cursor.execute("PRAGMA table_info(accounts);")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_database_structure()