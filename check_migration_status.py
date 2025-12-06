#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库迁移状态
"""

import os
import sys
import sqlite3

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 获取数据库路径
db_path = os.path.join('data', 'finance_system.db')
db_path = os.path.abspath(db_path)

def connect_db():
    """连接到数据库"""
    return sqlite3.connect(db_path)

def main():
    """检查迁移状态"""
    print("检查数据库迁移状态...")
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # 检查迁移表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migrations';")
        if cursor.fetchone():
            print("迁移表存在，查看已应用的迁移：")
            cursor.execute("SELECT * FROM migrations ORDER BY version;")
            migrations = cursor.fetchall()
            for migration in migrations:
                print(f"- 版本: {migration[1]}, 名称: {migration[2]}, 应用时间: {migration[3]}")
        else:
            print("迁移表不存在")
        
        # 检查账户表结构
        print("\n账户表结构：")
        cursor.execute("PRAGMA table_info(accounts);")
        for col in cursor.fetchall():
            print(f"- {col[1]} ({col[2]})")
        
        # 检查交易表结构
        print("\n交易表结构：")
        cursor.execute("PRAGMA table_info(transactions);")
        for col in cursor.fetchall():
            print(f"- {col[1]} ({col[2]})")
            
        # 检查新增的表
        print("\n新增表：")
        new_tables = ['transfer_records', 'reconciliation_logs', 'user_permissions']
        for table in new_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
            if cursor.fetchone():
                print(f"- {table} 存在")
            else:
                print(f"- {table} 不存在")
                
    except Exception as e:
        print(f"检查失败: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()