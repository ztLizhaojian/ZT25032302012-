#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插入admin用户脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.db_manager import init_db, execute_query
from src.utils.security import hash_password

def insert_admin_user():
    """插入admin用户"""
    try:
        # 初始化数据库
        init_db()
        print("数据库初始化完成")
        
        # 检查是否已存在admin用户
        existing_admin = execute_query(
            "SELECT id FROM users WHERE username = ?", 
            ('admin',), 
            fetch=True
        )
        
        if existing_admin:
            print("Admin用户已存在，无需重复插入")
            return True
            
        # 哈希密码
        password = "admin123"
        hashed_password = hash_password(password)
        
        # 插入admin用户
        execute_query(
            "INSERT INTO users (username, password, fullname, email, role, status, created_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
            ('admin', hashed_password, '系统管理员', 'admin@example.com', 'admin', 'active')
        )
        
        # 验证用户是否插入成功
        user = execute_query(
            "SELECT * FROM users WHERE username = ?", 
            ('admin',), 
            fetch=True
        )
        
        if user:
            print("Admin用户插入成功!")
            print(f"用户信息: ID={user['id']}, Username={user['username']}, Role={user['role']}")
            
            # 验证密码哈希
            if user['password'] == hashed_password:
                print("密码哈希验证通过")
                return True
            else:
                print("密码哈希验证失败")
                return False
        else:
            print("Admin用户插入失败，未找到插入的用户")
            return False
            
    except Exception as e:
        print(f"插入admin用户时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = insert_admin_user()
    if success:
        print("Admin用户创建成功!")
    else:
        print("Admin用户创建失败!")
        sys.exit(1)