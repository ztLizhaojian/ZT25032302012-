#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查admin用户密码的脚本
"""

import sqlite3
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.security import hash_password, verify_password

def check_admin_password():
    """检查admin用户密码"""
    print("检查admin用户密码")
    print("=" * 30)
    
    try:
        # 连接数据库
        db_path = 'src/data/finance_system.db'
        print(f"数据库路径: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"❌ 数据库文件不存在: {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询admin用户
        cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
        user = cursor.fetchone()
        
        if user:
            print("✅ 找到admin用户:")
            print(f"   用户名: {user['username']}")
            print(f"   当前密码哈希: {user['password']}")
            
            # 生成期望的密码哈希
            expected_hash = hash_password("admin123")
            print(f"   期望的密码哈希: {expected_hash}")
            
            # 验证密码
            verification_result = verify_password("admin123", user['password'])
            print(f"   密码验证结果: {verification_result}")
            
            if verification_result:
                print("✅ admin123密码验证成功!")
            else:
                print("❌ admin123密码验证失败!")
                print("需要重新设置密码...")
                
                # 更新密码
                print("正在更新密码...")
                cursor.execute(
                    "UPDATE users SET password = ? WHERE username = ?",
                    (expected_hash, 'admin')
                )
                conn.commit()
                
                # 再次验证
                cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
                updated_user = cursor.fetchone()
                new_verification = verify_password("admin123", updated_user['password'])
                
                if new_verification:
                    print("✅ 密码更新并验证成功!")
                else:
                    print("❌ 密码更新失败!")
        else:
            print("❌ 未找到admin用户")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 检查过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_admin_password()
    if success:
        print("\n✅ 检查完成!")
    else:
        print("\n❌ 检查失败!")
        sys.exit(1)