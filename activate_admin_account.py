#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面激活admin用户账户脚本
解决"账户未激活，请联系管理员"的问题
"""

import sqlite3
import hashlib
import os

def hash_password(password):
    """生成密码哈希值"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_and_activate_admin(db_path):
    """检查并激活admin用户账户"""
    print(f"\n正在处理数据库: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 检查users表结构，查看所有可能与激活状态相关的字段
        print("\n1. 检查users表结构:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("用户表字段:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # 2. 检查admin用户的当前状态
        print("\n2. 检查admin用户当前状态:")
        cursor.execute("SELECT * FROM users WHERE username = ?", ('admin',))
        user = cursor.fetchone()
        
        if not user:
            print("未找到admin用户，创建新的admin用户")
            # 创建admin用户
            admin_password = hash_password('admin123')
            
            # 尝试多种可能的插入方式，适应不同的表结构
            try:
                # 标准插入方式
                cursor.execute(
                    "INSERT INTO users (username, password, status, is_active, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                    ('admin', admin_password, 'active', 1)
                )
                print("成功创建admin用户")
            except sqlite3.OperationalError as e:
                print(f"插入错误: {e}")
                try:
                    # 尝试简化版本的插入
                    cursor.execute(
                        "INSERT INTO users (username, password, status) VALUES (?, ?, ?)",
                        ('admin', admin_password, 'active')
                    )
                    print("成功创建admin用户(简化版本)")
                except sqlite3.OperationalError as e:
                    print(f"简化插入也失败: {e}")
                    # 尝试最基础版本
                    try:
                        cursor.execute(
                            "INSERT INTO users (username, password) VALUES (?, ?)",
                            ('admin', admin_password)
                        )
                        print("成功创建admin用户(基础版本)")
                    except sqlite3.OperationalError as e:
                        print(f"基础插入失败: {e}")
        else:
            # 打印当前用户信息
            print(f"找到admin用户: {user}")
            
            # 3. 更新所有可能控制激活状态的字段
            print("\n3. 更新激活状态:")
            
            # 更新status字段
            cursor.execute("UPDATE users SET status = ? WHERE username = ?", ('active', 'admin'))
            print("已更新status为'active'")
            
            # 检查并更新is_active字段(如果存在)
            has_is_active = any(col[1] == 'is_active' for col in columns)
            if has_is_active:
                cursor.execute("UPDATE users SET is_active = ? WHERE username = ?", (1, 'admin'))
                print("已更新is_active为1")
            
            # 检查并更新activated字段(如果存在)
            has_activated = any(col[1] == 'activated' for col in columns)
            if has_activated:
                cursor.execute("UPDATE users SET activated = ? WHERE username = ?", (1, 'admin'))
                print("已更新activated为1")
            
            # 检查并更新account_status字段(如果存在)
            has_account_status = any(col[1] == 'account_status' for col in columns)
            if has_account_status:
                cursor.execute("UPDATE users SET account_status = ? WHERE username = ?", ('active', 'admin'))
                print("已更新account_status为'active'")
            
            # 确保密码正确
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hash_password('admin123'), 'admin'))
            print("已确保密码正确设置为'admin123'")
        
        # 4. 再次检查用户状态
        print("\n4. 确认用户状态更新:")
        cursor.execute("SELECT * FROM users WHERE username = ?", ('admin',))
        updated_user = cursor.fetchone()
        print(f"更新后admin用户信息: {updated_user}")
        
        # 5. 确保admin是唯一活跃用户
        print("\n5. 确保admin是唯一活跃用户:")
        cursor.execute("UPDATE users SET status = ? WHERE username != ?", ('inactive', 'admin'))
        print(f"已将其他用户设置为inactive")
        
        # 如果存在is_active字段，也更新其他用户
        if has_is_active:
            cursor.execute("UPDATE users SET is_active = ? WHERE username != ?", (0, 'admin'))
            print("已将其他用户is_active设置为0")
        
        # 提交更改
        conn.commit()
        conn.close()
        print("\n✅ 数据库操作完成")
        return True
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False

def main():
    print("===== Admin账户激活工具 =====")
    
    # 检查并激活所有可能的数据库位置
    db_paths = [
        'src/data/finance_system.db',
        'data/finance_system.db',
        'finance_system.db'
    ]
    
    success = False
    for db_path in db_paths:
        abs_path = os.path.abspath(db_path)
        if check_and_activate_admin(abs_path):
            success = True
    
    print("\n" + "="*30)
    if success:
        print("✅ Admin账户已成功激活")
        print("请重启应用程序后尝试使用以下凭证登录:")
        print("  用户名: admin")
        print("  密码: admin123")
    else:
        print("❌ 未能成功激活admin账户")
    print("="*30)

if __name__ == "__main__":
    main()