#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为accounts表添加user_id字段的脚本
用于修复账户加载失败问题
"""

import os
import sqlite3
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据库路径
from src.database.db_manager import DB_PATH
from src.utils.logger import get_logger

logger = get_logger('add_user_id_migration')

def add_user_id_column():
    """为accounts表添加user_id字段"""
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print(f"连接数据库: {DB_PATH}")
        logger.info(f"开始为accounts表添加user_id字段")
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("accounts表中未找到user_id字段，正在添加...")
            # 添加字段
            cursor.execute("ALTER TABLE accounts ADD COLUMN user_id INTEGER")
            
            # 添加外键约束
            # SQLite限制：需要重新创建表才能添加外键约束
            # 所以我们使用触发器来模拟外键约束
            cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS accounts_user_id_fk
            BEFORE INSERT ON accounts
            FOR EACH ROW
            WHEN NEW.user_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM users WHERE id = NEW.user_id)
            BEGIN
                SELECT RAISE(ABORT, '外键约束失败：用户不存在');
            END
            ''')
            
            # 为现有记录设置默认值（系统账户）
            cursor.execute("UPDATE accounts SET user_id = NULL")
            
            conn.commit()
            print("成功为accounts表添加user_id字段，并设置现有账户为系统账户")
            logger.info("成功为accounts表添加user_id字段")
        else:
            print("user_id字段已存在，无需添加")
            logger.info("user_id字段已存在")
            
        # 添加索引以提高查询性能
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id)")
            print("成功创建user_id索引")
        except Exception as e:
            print(f"创建索引时出错，但不影响主功能: {str(e)}")
            
    except sqlite3.Error as e:
        error_msg = f"数据库操作失败: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        if conn:
            conn.rollback()
        sys.exit(1)
    except Exception as e:
        error_msg = f"执行脚本时出错: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()

def check_database_structure():
    """检查数据库结构"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("\n检查数据库结构:")
        cursor.execute("PRAGMA table_info(accounts)")
        columns = cursor.fetchall()
        
        print("accounts表结构:")
        for column in columns:
            print(f"  {column[1]} ({column[2]})")
            
        # 检查是否有账户数据
        cursor.execute("SELECT COUNT(*) FROM accounts")
        account_count = cursor.fetchone()[0]
        print(f"\n账户总数: {account_count}")
        
        # 检查用户表
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"用户总数: {user_count}")
        
    except Exception as e:
        print(f"检查数据库结构时出错: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("开始执行数据库迁移脚本...")
    add_user_id_column()
    check_database_structure()
    print("\n数据库迁移完成！现在可以重新启动应用程序。")
