#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 实现账务处理与账户信息的深度联动
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 获取数据库路径
db_path = os.path.join('data', 'finance_system.db')
db_path = os.path.abspath(db_path)

# 确保数据库目录存在
db_dir = os.path.dirname(db_path)
os.makedirs(db_dir, exist_ok=True)

def connect_db():
    """连接到数据库"""
    return sqlite3.connect(db_path)

def create_migration_table(conn):
    """创建迁移表（如果不存在）"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS migrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version INTEGER NOT NULL UNIQUE,
        name TEXT NOT NULL,
        applied_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

def check_migration_applied(conn, version):
    """检查指定版本的迁移是否已应用"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM migrations WHERE version = ?", (version,))
    return cursor.fetchone() is not None

def record_migration(conn, version, name):
    """记录迁移应用"""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO migrations (version, name) VALUES (?, ?)", (version, name))
    conn.commit()

def main():
    """执行迁移"""
    print("开始执行数据库迁移...")
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # 确保迁移表存在
    create_migration_table(conn)
    
    # 检查是否已应用此迁移
    if check_migration_applied(conn, 2):
        print("迁移版本 2 已应用，跳过执行")
        conn.close()
        return
    
    try:
        # 1. 更新账户表
        print("更新账户表...")
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(accounts);")
        account_cols = [col[1] for col in cursor.fetchall()]
        
        if 'user_dept_id' not in account_cols:
            cursor.execute("ALTER TABLE accounts ADD COLUMN user_dept_id INTEGER")
            print("  - 已添加 user_dept_id 字段")
        else:
            print("  - user_dept_id 字段已存在，跳过")
            
        if 'create_time' not in account_cols:
            cursor.execute("ALTER TABLE accounts ADD COLUMN create_time TEXT")
            # 更新现有记录的创建时间
            cursor.execute("UPDATE accounts SET create_time = CURRENT_TIMESTAMP WHERE create_time IS NULL")
            print("  - 已添加 create_time 字段")
        else:
            print("  - create_time 字段已存在，跳过")
        
        # 2. 更新交易表
        print("更新交易表...")
        cursor.execute("PRAGMA table_info(transactions);")
        transaction_cols = [col[1] for col in cursor.fetchall()]
        
        if 'trade_type' not in transaction_cols:
            cursor.execute("ALTER TABLE transactions ADD COLUMN trade_type TEXT")
            # 更新现有交易记录的trade_type
            cursor.execute("UPDATE transactions SET trade_type = transaction_type WHERE trade_type IS NULL")
            print("  - 已添加 trade_type 字段")
        else:
            print("  - trade_type 字段已存在，跳过")
            
        if 'trade_status' not in transaction_cols:
            cursor.execute("ALTER TABLE transactions ADD COLUMN trade_status TEXT")
            # 设置默认值
            cursor.execute("UPDATE transactions SET trade_status = 'completed' WHERE trade_status IS NULL")
            print("  - 已添加 trade_status 字段")
        else:
            print("  - trade_status 字段已存在，跳过")
            
        if 'reconciliation_flag' not in transaction_cols:
            cursor.execute("ALTER TABLE transactions ADD COLUMN reconciliation_flag TEXT")
            # 设置默认值
            cursor.execute("UPDATE transactions SET reconciliation_flag = 'unreconciled' WHERE reconciliation_flag IS NULL")
            print("  - 已添加 reconciliation_flag 字段")
        else:
            print("  - reconciliation_flag 字段已存在，跳过")
        
        # 3. 创建转账关联表
        print("创建转账关联表...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transfer_records';")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfer_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_record_id INTEGER NOT NULL,
                to_record_id INTEGER NOT NULL,
                transfer_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_record_id) REFERENCES transactions(id),
                FOREIGN KEY (to_record_id) REFERENCES transactions(id)
            )
            """)
            print("  - 已创建 transfer_records 表")
        else:
            print("  - transfer_records 表已存在，跳过")
        
        # 4. 创建对账日志表
        print("创建对账日志表...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reconciliation_logs';")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reconciliation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                reconciliation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                expected_balance REAL NOT NULL,
                actual_balance REAL NOT NULL,
                difference REAL NOT NULL,
                status TEXT DEFAULT 'completed',
                reconciled_by INTEGER,
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                FOREIGN KEY (reconciled_by) REFERENCES users(id)
            )
            """)
            print("  - 已创建 reconciliation_logs 表")
        else:
            print("  - reconciliation_logs 表已存在，跳过")
        
        # 5. 创建用户权限表
        print("创建用户权限表...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_permissions';")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id INTEGER,
                permission TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """)
            print("  - 已创建 user_permissions 表")
        else:
            print("  - user_permissions 表已存在，跳过")
        
        # 6. 创建索引
        print("创建索引...")
        # 检查索引是否已存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = [idx[0] for idx in cursor.fetchall()]
        
        if 'idx_transactions_trade_status' not in indexes:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_trade_status ON transactions(trade_status)")
            print("  - 已创建交易状态索引")
        else:
            print("  - 交易状态索引已存在，跳过")
            
        if 'idx_transactions_reconciliation_flag' not in indexes:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_reconciliation_flag ON transactions(reconciliation_flag)")
            print("  - 已创建对账标记索引")
        else:
            print("  - 对账标记索引已存在，跳过")
            
        if 'idx_accounts_user_dept' not in indexes:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_user_dept ON accounts(user_dept_id)")
            print("  - 已创建用户部门ID索引")
        else:
            print("  - 用户部门ID索引已存在，跳过")
        
        # 提交事务
        conn.commit()
        
        # 记录迁移
        record_migration(conn, 2, "实现账务处理与账户信息的深度联动")
        
        print("\n数据库迁移执行完成！")
        
    except Exception as e:
        print(f"\n迁移执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()