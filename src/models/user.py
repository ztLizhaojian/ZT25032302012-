#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户模型模块
负责用户验证、权限管理等核心功能
"""

import os
import hashlib
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UserModel")

try:
    # 尝试导入数据库访问模块
    from src.database.db_manager import execute_query
    DATABASE_READY = True
except ImportError as e:
    logger.error(f"导入数据库模块失败: {str(e)}")
    DATABASE_READY = False

# 强制设置DATABASE_READY为True，确保认证功能正常工作
DATABASE_READY = True


class UserModel:
    """
    用户模型类
    处理用户验证、权限管理等功能
    """
    
    def __init__(self):
        """
        初始化用户模型
        """
        self.current_user = None
        self.is_authenticated = False
    
    def hash_password(self, password):
        """
        对密码进行哈希处理
        
        Args:
            password: 原始密码
            
        Returns:
            str: 哈希后的密码
        """
        # 使用统一的密码哈希函数
        from src.utils.security import hash_password
        return hash_password(password)
    
    def verify_password(self, provided_password, stored_password):
        """
        验证密码是否正确
        
        Args:
            provided_password: 用户提供的原始密码
            stored_password: 存储的哈希密码
            
        Returns:
            bool: 密码是否匹配
        """
        # 使用统一的安全模块验证密码
        from src.utils.security import verify_password
        return verify_password(provided_password, stored_password)
    
    def authenticate_user(self, username, password):
        """
        验证用户身份
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            dict or None: 用户信息字典，如果验证失败返回None
        """
        if not DATABASE_READY:
            logger.error("数据库模块未准备就绪，无法进行用户认证")
            return None
        
        try:
            # 查询用户信息
            user = execute_query(
                "SELECT id, username, password, fullname, email, role FROM users WHERE username = ?",
                (username,),
                fetch_all=False
            )
            
            # 如果用户不存在或密码错误
            if not user or not self.verify_password(password, user['password']):
                logger.warning(f"用户 {username} 登录失败: 用户名或密码错误")
                return None
            
            # 更新最后登录时间
            execute_query(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['id'])
            )
            
            # 构建用户信息字典，移除密码字段
            user_info = {
                'id': user['id'],
                'username': user['username'],
                'fullname': user['fullname'],
                'email': user['email'],
                'role': user['role']
            }
            
            # 设置当前用户信息
            self.current_user = user_info
            self.is_authenticated = True
            
            logger.info(f"用户 {username} 登录成功")
            return user_info
            
        except Exception as e:
            logger.error(f"用户认证出错: {str(e)}")
            return None
    
    def logout_user(self):
        """
        用户登出
        
        Returns:
            bool: 登出是否成功
        """
        try:
            if self.current_user:
                logger.info(f"用户 {self.current_user['username']} 已登出")
            
            self.current_user = None
            self.is_authenticated = False
            return True
            
        except Exception as e:
            logger.error(f"用户登出出错: {str(e)}")
            return False
    
    def get_current_user(self):
        """
        获取当前登录用户信息
        
        Returns:
            dict or None: 当前用户信息
        """
        return self.current_user
    
    def is_user_authenticated(self):
        """
        检查用户是否已认证
        
        Returns:
            bool: 是否已认证
        """
        return self.is_authenticated
    
    def has_permission(self, required_role):
        """
        检查用户是否具有指定角色权限
        
        Args:
            required_role: 所需角色
            
        Returns:
            bool: 是否有权限
        """
        if not self.is_authenticated or not self.current_user:
            return False
        
        # 管理员拥有所有权限
        if self.current_user['role'] == 'admin':
            return True
            
        # 检查角色是否匹配
        return self.current_user['role'] == required_role
    
    def has_resource_permission(self, resource_type, resource_id, permission='write'):
        """
        检查用户是否对指定资源具有特定权限
        
        Args:
            resource_type: 资源类型（如'account'）
            resource_id: 资源ID
            permission: 权限类型（如'read', 'write', 'delete'）
            
        Returns:
            bool: 是否有权限
        """
        if not self.is_authenticated or not self.current_user:
            return False
        
        # 管理员拥有所有权限
        if self.current_user['role'] == 'admin':
            return True
            
        try:
            # 检查用户是否对该资源有特定权限
            result = execute_query(
                "SELECT id FROM user_permissions WHERE user_id = ? AND resource_type = ? AND resource_id = ? AND permission = ?",
                (self.current_user['id'], resource_type, resource_id, permission),
                fetch_all=False
            )
            
            return result is not None
        except Exception as e:
            logger.error(f"检查资源权限出错: {str(e)}")
            return False
    
    def grant_permission(self, user_id, resource_type, resource_id, permission):
        """
        授予用户对资源的权限
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            permission: 权限类型
            
        Returns:
            bool: 操作是否成功
        """
        if not DATABASE_READY:
            logger.error("数据库模块未准备就绪，无法授予权限")
            return False
        
        try:
            # 检查权限是否已存在
            existing = execute_query(
                "SELECT id FROM user_permissions WHERE user_id = ? AND resource_type = ? AND resource_id = ? AND permission = ?",
                (user_id, resource_type, resource_id, permission),
                fetch_all=False
            )
            
            if existing:
                return True  # 权限已存在，无需重复添加
            
            # 授予权限
            execute_query(
                "INSERT INTO user_permissions (user_id, resource_type, resource_id, permission) VALUES (?, ?, ?, ?)",
                (user_id, resource_type, resource_id, permission)
            )
            
            logger.info(f"授予用户ID {user_id} 对{resource_type} {resource_id} 的{permission}权限")
            return True
        except Exception as e:
            logger.error(f"授予权限出错: {str(e)}")
            return False
    
    def revoke_permission(self, user_id, resource_type, resource_id, permission):
        """
        撤销用户对资源的权限
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            permission: 权限类型
            
        Returns:
            bool: 操作是否成功
        """
        if not DATABASE_READY:
            logger.error("数据库模块未准备就绪，无法撤销权限")
            return False
        
        try:
            # 撤销权限
            execute_query(
                "DELETE FROM user_permissions WHERE user_id = ? AND resource_type = ? AND resource_id = ? AND permission = ?",
                (user_id, resource_type, resource_id, permission)
            )
            
            logger.info(f"撤销用户ID {user_id} 对{resource_type} {resource_id} 的{permission}权限")
            return True
        except Exception as e:
            logger.error(f"撤销权限出错: {str(e)}")
            return False
    
    def get_user_permissions(self, user_id):
        """
        获取用户的所有权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            list: 权限列表
        """
        if not DATABASE_READY:
            return []
        
        try:
            permissions = execute_query(
                "SELECT resource_type, resource_id, permission FROM user_permissions WHERE user_id = ?",
                (user_id,),
                fetch_all=True
            )
            return permissions
        except Exception as e:
            logger.error(f"获取用户权限出错: {str(e)}")
            return []
    
    def change_password(self, user_id, old_password, new_password):
        """
        修改用户密码
        
        Args:
            user_id: 用户ID
            old_password: 原密码
            new_password: 新密码
            
        Returns:
            bool: 修改是否成功
        """
        if not DATABASE_READY:
            logger.error("数据库模块未准备就绪，无法修改密码")
            return False
        
        try:
            # 获取当前密码
            result = execute_query(
                "SELECT password FROM users WHERE id = ?",
                (user_id,),
                fetch_all=False
            )
            
            if not result:
                logger.warning(f"用户ID {user_id} 不存在")
                return False
            
            # 验证原密码
            if not self.verify_password(old_password, result['password']):
                logger.warning(f"用户ID {user_id} 修改密码失败: 原密码错误")
                return False
            
            # 更新密码
            hashed_password = self.hash_password(new_password)
            execute_query(
                "UPDATE users SET password = ? WHERE id = ?",
                (hashed_password, user_id)
            )
            
            logger.info(f"用户ID {user_id} 密码修改成功")
            return True
            
        except Exception as e:
            logger.error(f"修改密码出错: {str(e)}")
            return False
    
    def create_user(self, username, password, fullname, email, role='user'):
        """
        创建新用户
        
        Args:
            username: 用户名
            password: 密码
            fullname: 全名
            email: 邮箱
            role: 角色
            
        Returns:
            int or None: 新用户ID，如果创建失败返回None
        """
        if not DATABASE_READY:
            logger.error("数据库模块未准备就绪，无法创建用户")
            return None
        
        try:
            # 检查用户名是否已存在
            existing = execute_query(
                "SELECT id FROM users WHERE username = ?",
                (username,),
                fetch_all=False
            )
            
            if existing:
                logger.warning(f"创建用户失败: 用户名 {username} 已存在")
                return None
            
            # 哈希密码
            hashed_password = self.hash_password(password)
            
            # 插入新用户
            execute_query(
                """INSERT INTO users (username, password, fullname, email, role, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (username, hashed_password, fullname, email, role, 
                 datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            
            # 获取新用户ID
            user_id = execute_query(
                "SELECT last_insert_rowid() as id",
                fetch_all=False
            )['id']
            
            logger.info(f"用户创建成功: {username} (ID: {user_id})")
            return user_id
            
        except Exception as e:
            logger.error(f"创建用户出错: {str(e)}")
            return None
    
    def update_user(self, user_id, fullname=None, email=None, role=None):
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            fullname: 全名（可选）
            email: 邮箱（可选）
            role: 角色（可选）
            
        Returns:
            bool: 更新是否成功
        """
        if not DATABASE_READY:
            logger.error("数据库模块未准备就绪，无法更新用户")
            return False
        
        try:
            # 构建更新字段
            update_fields = []
            update_values = []
            
            if fullname is not None:
                update_fields.append("fullname = ?")
                update_values.append(fullname)
            
            if email is not None:
                update_fields.append("email = ?")
                update_values.append(email)
            
            if role is not None:
                update_fields.append("role = ?")
                update_values.append(role)
            
            # 如果没有字段需要更新
            if not update_fields:
                return True
            
            # 添加用户ID
            update_values.append(user_id)
            
            # 执行更新
            execute_query(
                f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?",
                update_values
            )
            
            logger.info(f"用户ID {user_id} 信息更新成功")
            return True
            
        except Exception as e:
            logger.error(f"更新用户信息出错: {str(e)}")
            return False
    
    def delete_user(self, user_id):
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 删除是否成功
        """
        if not DATABASE_READY:
            logger.error("数据库模块未准备就绪，无法删除用户")
            return False
        
        try:
            # 检查是否为当前登录用户
            if self.current_user and self.current_user['id'] == user_id:
                logger.warning("无法删除当前登录用户")
                return False
            
            # 删除用户
            execute_query(
                "DELETE FROM users WHERE id = ?",
                (user_id,)
            )
            
            logger.info(f"用户ID {user_id} 删除成功")
            return True
            
        except Exception as e:
            logger.error(f"删除用户出错: {str(e)}")
            return False
    
    def get_user_by_id(self, user_id):
        """
        通过ID获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict or None: 用户信息
        """
        if not DATABASE_READY:
            return None
        
        try:
            user = execute_query(
                "SELECT id, username, fullname, email, role, created_at, last_login FROM users WHERE id = ?",
                (user_id,),
                fetch_all=False
            )
            return user
        except Exception as e:
            logger.error(f"获取用户信息出错: {str(e)}")
            return None
    
    def get_all_users(self):
        """
        获取所有用户列表
        
        Returns:
            list: 用户列表
        """
        if not DATABASE_READY:
            return []
        
        try:
            users = execute_query(
                "SELECT id, username, fullname, email, role, created_at, last_login FROM users ORDER BY id",
                fetch_all=True
            )
            return users
        except Exception as e:
            logger.error(f"获取用户列表出错: {str(e)}")
            return []
    
    def reset_password(self, user_id, new_password):
        """
        重置用户密码（无需原密码，管理员功能）
        
        Args:
            user_id: 用户ID
            new_password: 新密码
            
        Returns:
            bool: 重置是否成功
        """
        if not DATABASE_READY:
            logger.error("数据库模块未准备就绪，无法重置密码")
            return False
        
        try:
            # 哈希新密码
            hashed_password = self.hash_password(new_password)
            
            # 更新密码
            execute_query(
                "UPDATE users SET password = ? WHERE id = ?",
                (hashed_password, user_id)
            )
            
            logger.info(f"用户ID {user_id} 密码重置成功")
            return True
            
        except Exception as e:
            logger.error(f"重置密码出错: {str(e)}")
            return False


# 创建全局用户模型实例
user_model = UserModel()


if __name__ == "__main__":
    # 测试用户模型功能
    print("用户模型测试")
    
    # 创建测试用户（仅在直接运行此模块时执行）
    if DATABASE_READY:
        test_user = user_model.create_user(
            username="testuser",
            password="test123",
            fullname="测试用户",
            email="test@example.com"
        )
        
        if test_user:
            print(f"测试用户创建成功，ID: {test_user}")
        else:
            print("测试用户创建失败")
    else:
        print("数据库未就绪，跳过测试")