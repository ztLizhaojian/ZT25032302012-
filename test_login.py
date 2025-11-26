#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import sqlite3

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.security import verify_password, hash_password

def test_login():
    print("测试登录功能...")
    
    # 直接连接数据库文件
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'finance_system.db')
    
    if not os.path.exists(db_path):
        print(f'数据库文件不存在: {db_path}')
        return
    
    print(f'数据库文件存在: {db_path}')
    
    # 连接数据库并查询用户
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    cursor = conn.cursor()
    
    # 查询用户
    cursor.execute('SELECT id, username, password, fullname, role FROM users WHERE username = ?', ('admin',))
    user = cursor.fetchone()
    
    print('数据库中的用户信息:')
    if user:
        print(f'  ID: {user["id"]}')
        print(f'  用户名: {user["username"]}')
        print(f'  密码哈希: {user["password"]}')
        print(f'  全名: {user["fullname"]}')
        print(f'  角色: {user["role"]}')
        
        # 测试密码验证
        test_password = 'admin123'
        print(f'\n测试密码 "{test_password}" 验证:')
        hashed = hash_password(test_password)
        print(f'  输入密码的哈希: {hashed}')
        print(f'  数据库中的哈希: {user["password"]}')
        print(f'  哈希是否匹配: {hashed == user["password"]}')
        print(f'  verify_password结果: {verify_password(test_password, user["password"])}')
        
        # 反向测试参数
        print(f'  verify_password(反向参数): {verify_password(user["password"], test_password)}')
    else:
        print('  未找到用户')
    
    conn.close()

if __name__ == "__main__":
    test_login()