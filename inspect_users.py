#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的用户数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.db_manager import init_db, execute_query
from src.utils.security import hash_password

print("初始化数据库...")
init_db()

print("\n查询所有用户:")
try:
    users = execute_query("SELECT * FROM users", fetch_all=True)
    if users:
        for user in users:
            print(user)
    else:
        print("未找到用户")

    print("\n特别查询admin用户:")
    admin_user = execute_query("SELECT * FROM users WHERE username = 'admin'", fetch=True)
    if admin_user:
        print(f"ID: {admin_user['id']}")
        print(f"Username: {admin_user['username']}")
        print(f"Password (hashed): {admin_user['password']}")
        print(f"Fullname: {admin_user['fullname']}")
        print(f"Email: {admin_user['email']}")
        print(f"Role: {admin_user['role']}")
        
        # 验证密码
        test_password = "admin123"
        hashed_test = hash_password(test_password)
        print(f"\n测试密码 '{test_password}' 的哈希值: {hashed_test}")
        print(f"数据库中存储的哈希值: {admin_user['password']}")
        print(f"密码匹配结果: {hashed_test == admin_user['password']}")
    else:
        print("未找到admin用户")
        
except Exception as e:
    print(f"查询出错: {e}")
    import traceback
    traceback.print_exc()