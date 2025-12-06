#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐步调试认证过程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.user import UserModel
from src.controllers.auth_controller import AuthController
from src.database.db_manager import init_db
from src.utils.security import verify_password, hash_password
import sqlite3

def debug_database():
    """调试数据库状态"""
    print("=== 调试数据库状态 ===")
    
    # 初始化数据库
    init_db()
    
    # 直接连接数据库检查
    db_path = "data/finance_system.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查询所有用户
    print("\n查询所有用户...")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    if users:
        print(f"找到 {len(users)} 个用户:")
        for user in users:
            print(f"  - ID: {user['id']}, Username: {user['username']}, Role: {user['role']}")
    else:
        print("未找到任何用户!")
    
    # 查询admin用户
    print("\n查询admin用户...")
    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    admin_user = cursor.fetchone()
    
    if admin_user:
        print("找到admin用户:")
        print(f"  ID: {admin_user['id']}")
        print(f"  Username: {admin_user['username']}")
        print(f"  Password hash: {admin_user['password']}")
        print(f"  Fullname: {admin_user['fullname']}")
        print(f"  Role: {admin_user['role']}")
        
        # 验证密码
        plain_password = "admin123"
        is_valid = verify_password(plain_password, admin_user['password'])
        print(f"\n密码验证结果: {'✅ 正确' if is_valid else '❌ 错误'}")
    else:
        print("未找到admin用户!")
    
    conn.close()

def debug_user_model():
    """调试用户模型"""
    print("\n=== 调试用户模型 ===")
    
    # 初始化数据库
    init_db()
    
    # 创建用户模型实例
    user_model = UserModel()
    print("✅ UserModel创建成功")
    
    # 测试用户认证
    username = "admin"
    password = "admin123"
    
    print(f"\n尝试认证用户: {username}")
    print(f"使用密码: {password}")
    
    # 直接调用用户模型的认证方法
    user_info = user_model.authenticate_user(username, password)
    
    if user_info:
        print("✅ 用户模型认证成功!")
        print(f"用户信息: {user_info}")
        return True
    else:
        print("❌ 用户模型认证失败!")
        return False

def debug_auth_controller():
    """调试认证控制器"""
    print("\n=== 调试认证控制器 ===")
    
    # 初始化数据库
    init_db()
    
    # 创建认证控制器实例
    auth_controller = AuthController()
    print("✅ AuthController创建成功")
    
    # 测试登录
    username = "admin"
    password = "admin123"
    
    print(f"\n尝试登录用户: {username}")
    print(f"使用密码: {password}")
    
    # 调用登录方法
    result = auth_controller.login(username, password)
    
    if result["success"]:
        print("✅ 认证控制器登录成功!")
        print(f"消息: {result['message']}")
        user = result["user"]
        print(f"用户信息: {user}")
        return True
    else:
        print("❌ 认证控制器登录失败!")
        print(f"消息: {result['message']}")
        return False

def main():
    print("逐步调试认证过程")
    print("=" * 30)
    
    # 调试数据库
    debug_database()
    
    # 调试用户模型
    user_model_success = debug_user_model()
    
    # 调试认证控制器
    auth_controller_success = debug_auth_controller()
    
    print("\n" + "=" * 30)
    print("总结:")
    print(f"  用户模型测试: {'通过' if user_model_success else '失败'}")
    print(f"  认证控制器测试: {'通过' if auth_controller_success else '失败'}")
    
    if user_model_success and auth_controller_success:
        print("\n🎉 所有测试通过!")
        return True
    else:
        print("\n💥 测试失败!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)