#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员用户
"""

import sys
import os
import traceback

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_admin_user():
    """创建管理员用户"""
    print("=== 创建管理员用户 ===")
    
    try:
        # 1. 初始化数据库
        print("1. 初始化数据库...")
        from src.database.db_manager import init_db
        init_db()
        print("✅ 数据库初始化成功")
        
        # 2. 导入安全模块
        print("\n2. 导入安全模块...")
        from src.utils.security import hash_password
        print("✅ 安全模块导入成功")
        
        # 3. 创建管理员用户
        print("\n3. 创建管理员用户...")
        from src.database.db_manager import execute_query
        
        # 检查是否已有管理员用户
        admin_exists = execute_query(
            "SELECT COUNT(*) as count FROM users WHERE role = 'admin'",
            fetch=True
        )
        
        if admin_exists and admin_exists['count'] > 0:
            print("⚠️  管理员用户已存在")
            # 查询现有管理员用户
            existing_admin = execute_query(
                "SELECT id, username, fullname, role FROM users WHERE role = 'admin'",
                fetch=True
            )
            if existing_admin:
                print(f"   用户名: {existing_admin['username']}")
                print(f"   全名: {existing_admin['fullname']}")
                print(f"   角色: {existing_admin['role']}")
        else:
            # 创建默认管理员用户
            admin_password = 'admin123'
            hashed_password = hash_password(admin_password)
            
            result = execute_query(
                "INSERT INTO users (username, password, fullname, email, role) VALUES (?, ?, ?, ?, ?)",
                ('admin', hashed_password, '系统管理员', 'admin@example.com', 'admin')
            )
            
            print("✅ 管理员用户创建成功")
            print(f"   用户名: admin")
            print(f"   密码: {admin_password}")
            print(f"   全名: 系统管理员")
            print(f"   角色: admin")
        
        # 4. 验证用户创建
        print("\n4. 验证用户创建...")
        users = execute_query(
            "SELECT id, username, password, fullname, role FROM users",
            fetch_all=True
        )
        
        if users:
            print(f"✅ 数据库中共有 {len(users)} 个用户:")
            for i, user in enumerate(users, 1):
                print(f"\n   用户 {i}:")
                print(f"     ID: {user['id']}")
                print(f"     用户名: {user['username']}")
                print(f"     全名: {user['fullname']}")
                print(f"     角色: {user['role']}")
        else:
            print("❌ 数据库中仍然没有用户")
            
    except Exception as e:
        print(f"❌ 创建过程中发生错误: {str(e)}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = create_admin_user()
    sys.exit(0 if success else 1)