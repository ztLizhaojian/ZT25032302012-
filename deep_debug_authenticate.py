#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度调试用户认证过程
直接模拟authenticate_user方法的执行，检查实际使用的数据库和用户状态
"""

import sqlite3
import hashlib
import os
import sys
from datetime import datetime

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 定义测试凭据
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'

def hash_password(password):
    """模拟系统使用的密码哈希函数"""
    return hashlib.sha256(password.encode()).hexdigest()

def debug_database_connection():
    """调试数据库连接，检查实际使用的数据库路径"""
    print("\n=== 调试数据库连接 ===")
    
    # 尝试导入实际的数据库模块
    try:
        from src.database.db_manager import DB_PATH, get_db_path
        print(f"从db_manager导入的DB_PATH: {DB_PATH}")
        
        # 测试get_db_path函数
        dynamic_path = get_db_path()
        print(f"通过get_db_path()获取的路径: {dynamic_path}")
        
        # 检查路径是否存在
        if os.path.exists(dynamic_path):
            print(f"数据库文件存在: {dynamic_path}")
            return dynamic_path
        else:
            print(f"警告: 数据库文件不存在: {dynamic_path}")
    except Exception as e:
        print(f"导入数据库模块失败: {str(e)}")
    
    # 返回可能的数据库路径列表进行尝试
    return [
        'src/data/finance_system.db',
        'data/finance_system.db',
        'finance_system.db'
    ]

def directly_check_user_status(db_path):
    """直接检查数据库中的用户状态"""
    print(f"\n=== 直接检查数据库: {db_path} ===")
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查users表结构
        print("检查users表结构:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  列: {col[1]} (类型: {col[2]})")
        
        # 查询admin用户的所有信息
        print(f"\n查询admin用户的完整信息:")
        cursor.execute("SELECT * FROM users WHERE username = ?", (ADMIN_USERNAME,))
        user_data = cursor.fetchone()
        
        if user_data:
            # 获取列名
            cursor.execute("PRAGMA table_info(users)")
            column_names = [col[1] for col in cursor.fetchall()]
            
            # 打印用户详细信息
            print("Admin用户信息:")
            for i, value in enumerate(user_data):
                col_name = column_names[i] if i < len(column_names) else f"未知列{i}"
                print(f"  {col_name}: {value}")
            
            # 特别检查status列
            status_index = None
            for i, col in enumerate(column_names):
                if col.lower() == 'status':
                    status_index = i
                    break
            
            if status_index is not None:
                current_status = user_data[status_index]
                print(f"\n发现status列，当前值: '{current_status}'")
                
                # 检查其他可能的状态相关列
                print("\n检查其他可能的状态相关列:")
                for i, col in enumerate(column_names):
                    if col.lower() in ['active', 'activated', 'is_active', 'account_status']:
                        print(f"  {col}: {user_data[i]}")
                
                # 检查密码是否匹配
                password_index = None
                for i, col in enumerate(column_names):
                    if col.lower() == 'password':
                        password_index = i
                        break
                
                if password_index is not None:
                    stored_password = user_data[password_index]
                    expected_hash = hash_password(ADMIN_PASSWORD)
                    print(f"\n密码哈希检查:")
                    print(f"  存储的哈希: {stored_password[:20]}...")
                    print(f"  期望的哈希: {expected_hash[:20]}...")
                    print(f"  哈希匹配: {stored_password == expected_hash}")
            else:
                print("警告: 未找到status列")
            
            conn.close()
            return True
        else:
            print("未找到admin用户")
            conn.close()
            return False
    except Exception as e:
        print(f"检查数据库时出错: {str(e)}")
        return False

def simulate_authentication(db_path):
    """模拟authenticate_user方法的执行"""
    print(f"\n=== 模拟认证过程: {db_path} ===")
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 查询用户信息
        print("1. 查询用户信息...")
        cursor.execute(
            "SELECT id, username, password, fullname, email, role, status, last_login "
            "FROM users WHERE username = ?", 
            (ADMIN_USERNAME,)
        )
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ 失败: 用户不存在: {ADMIN_USERNAME}")
            conn.close()
            return False
        
        user_id, db_username, password_hash, fullname, email, role, status, last_login = result
        print(f"✅ 找到用户: {db_username} (ID: {user_id})")
        print(f"   状态: '{status}'")
        
        # 2. 检查用户状态
        print("\n2. 检查用户状态...")
        if status != 'active':
            print(f"❌ 失败: 账户未激活，请联系管理员 (当前状态: '{status}')")
            print("   这就是登录失败的原因！")
            
            # 尝试修复状态
            print("\n尝试修复用户状态...")
            cursor.execute("UPDATE users SET status = 'active' WHERE username = ?", (ADMIN_USERNAME,))
            conn.commit()
            
            # 验证修复
            cursor.execute("SELECT status FROM users WHERE username = ?", (ADMIN_USERNAME,))
            new_status = cursor.fetchone()[0]
            print(f"   修复后状态: '{new_status}'")
            
            if new_status == 'active':
                print("✅ 修复成功")
            else:
                print("❌ 修复失败")
            
            conn.close()
            return False
        else:
            print(f"✅ 状态检查通过: '{status}'")
        
        # 3. 验证密码
        print("\n3. 验证密码...")
        expected_hash = hash_password(ADMIN_PASSWORD)
        if password_hash != expected_hash:
            print(f"❌ 失败: 密码不匹配")
            print(f"   存储的哈希: {password_hash[:20]}...")
            print(f"   期望的哈希: {expected_hash[:20]}...")
            
            # 尝试修复密码
            print("\n尝试修复密码...")
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (expected_hash, ADMIN_USERNAME))
            conn.commit()
            print("✅ 密码已更新")
        else:
            print("✅ 密码验证通过")
        
        # 4. 模拟登录成功
        print("\n4. 登录成功模拟...")
        print("✅ 认证过程模拟成功！")
        
        conn.close()
        return True
    
    except Exception as e:
        print(f"模拟认证过程中出错: {str(e)}")
        return False

def main():
    print("=== 深度认证调试工具 ===")
    print(f"目标: 诊断并修复admin用户登录问题")
    
    # 调试数据库连接
    db_paths = debug_database_connection()
    
    # 确保db_paths是列表
    if isinstance(db_paths, str):
        db_paths = [db_paths]
    
    # 检查所有可能的数据库
    for db_path in db_paths:
        print(f"\n\n=== 处理数据库: {db_path} ===")
        
        # 直接检查用户状态
        directly_check_user_status(db_path)
        
        # 模拟认证过程
        simulate_authentication(db_path)
    
    print("\n\n=== 调试完成 ===")
    print("请重启应用程序后再次尝试登录。")

if __name__ == "__main__":
    main()
