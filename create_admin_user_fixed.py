#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员用户脚本（修复版）
用于创建用户名为admin，密码为123456的管理员账户
"""

import os
import sys
import sqlite3

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_admin_user():
    """创建管理员用户"""
    print("创建管理员用户（修复版）")
    print("=" * 30)
    
    try:
        # 导入必要的模块
        from src.utils.security import hash_password
        
        # 确保数据目录存在
        data_dir = os.path.join('src', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # 数据库路径
        db_path = os.path.join(data_dir, 'finance_system.db')
        print(f"1. 数据库路径: {db_path}")
        
        # 连接数据库
        print("2. 连接数据库...")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 创建用户表
        print("3. 创建用户表...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            fullname TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT
        )
        ''')
        
        # 检查admin用户是否已存在
        print("4. 检查admin用户是否已存在...")
        cursor.execute("SELECT id, username FROM users WHERE username = ?", ('admin',))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"   ⚠️  admin用户已存在 (ID: {existing_user['id']})")
        else:
            print("   ✅ 未找到admin用户，将创建新用户")
        
        # 创建或更新admin用户
        print("5. 创建/更新admin用户...")
        admin_password = "123456"
        hashed_password = hash_password(admin_password)
        
        if existing_user:
            # 更新现有用户的密码
            cursor.execute(
                "UPDATE users SET password = ?, fullname = ?, email = ?, role = ? WHERE username = ?",
                (hashed_password, "系统管理员", "admin@example.com", "admin", "admin")
            )
            print("   ✅ admin用户密码已更新")
        else:
            # 创建新用户
            cursor.execute(
                """INSERT INTO users (username, password, fullname, email, role)
                   VALUES (?, ?, ?, ?, ?)""",
                ('admin', hashed_password, "系统管理员", "admin@example.com", "admin")
            )
            print("   ✅ admin用户创建成功")
        
        # 提交事务
        conn.commit()
        
        # 验证用户创建/更新结果
        print("6. 验证用户信息...")
        cursor.execute("SELECT id, username, password FROM users WHERE username = ?", ('admin',))
        user = cursor.fetchone()
        
        if user:
            print(f"   用户ID: {user['id']}")
            print(f"   用户名: {user['username']}")
            print(f"   密码哈希: {user['password']}")
            
            # 验证密码
            verification = hash_password(admin_password) == user['password']
            print(f"   密码验证: {'✅ 通过' if verification else '❌ 失败'}")
            
            if verification:
                print("\n🎉 管理员用户创建/更新成功!")
                print(f"   用户名: admin")
                print(f"   密码: {admin_password}")
                conn.close()
                return True
            else:
                print("\n❌ 密码验证失败!")
                conn.close()
                return False
        else:
            print("\n❌ 未找到创建的用户!")
            conn.close()
            return False
            
    except Exception as e:
        print(f"\n❌ 创建管理员用户时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_admin_user()
    if success:
        print("\n✅ 脚本执行成功!")
        sys.exit(0)
    else:
        print("\n❌ 脚本执行失败!")
        sys.exit(1)