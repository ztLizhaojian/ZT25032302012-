#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身份验证控制器模块
负责处理用户登录、注册和权限验证等功能
"""

import logging
from datetime import datetime
import os

try:
    # 导入用户模型
    from src.models.user_model import UserModel
    # 导入数据库管理器
    from src.database.db_manager import log_operation
    # 初始化用户模型实例
    user_model = UserModel()
    DATABASE_READY = True
except ImportError as e:
    logging.error(f"导入模块失败: {str(e)}")
    DATABASE_READY = False

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger("AuthController")


class AuthController:
    """
    身份验证控制器
    管理用户的身份验证流程和权限控制
    """
    
    def __init__(self):
        """
        初始化身份验证控制器
        """
        self.user_model = user_model
        self.current_user = None
        self.is_authenticated = False
        self.last_login_attempt = None
        self.failed_attempts = 0
    
    def login(self, username, password, remember_me=False, ip_address=None):
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            remember_me: 是否记住登录状态
            ip_address: IP地址（用于日志记录）
            
        Returns:
            dict: 包含登录结果的字典
                 {success: bool, message: str, user: dict or None}
        """
        # 记录登录尝试
        self.last_login_attempt = datetime.now()
        self.failed_attempts += 1
        
        # 验证输入
        if not username or not password:
            logger.warning(f"登录尝试失败: 用户名或密码为空")
            return {
                "success": False,
                "message": "用户名和密码不能为空",
                "user": None
            }
        
        try:
            # 调用用户模型进行身份验证
            auth_result = self.user_model.authenticate_user(username, password)
            
            if auth_result and auth_result.get('success'):
                # 登录成功，重置失败尝试计数
                self.failed_attempts = 0
                self.current_user = auth_result['user']
                self.is_authenticated = True
                
                # 记录登录日志
                if DATABASE_READY:
                    log_operation(
                        user_id=auth_result['user']['id'],
                        action="login",
                        details=f"用户登录成功，记住我: {remember_me}",
                        ip_address=ip_address
                    )
                
                logger.info(f"用户 {username} 登录成功")
                
                return {
                    "success": True,
                    "message": auth_result.get('message', "登录成功"),
                    "user": auth_result['user']
                }
            else:
                # 登录失败
                # 记录失败日志
                if DATABASE_READY:
                    log_operation(
                        user_id=None,
                        action="login_failed",
                        details=f"用户名或密码错误，尝试次数: {self.failed_attempts}",
                        ip_address=ip_address
                    )
                
                logger.warning(f"用户 {username} 登录失败")
                
                # 检查是否需要锁定账户
                if self.failed_attempts >= 5:
                    logger.warning(f"用户 {username} 连续登录失败5次，可能需要锁定账户")
                    
                return {
                    "success": False,
                    "message": auth_result.get('message', "用户名或密码错误") if auth_result else "用户名或密码错误",
                    "user": None
                }
                
        except Exception as e:
            logger.error(f"登录过程出错: {str(e)}")
            return {
                "success": False,
                "message": f"登录过程中发生错误: {str(e)}",
                "user": None
            }
    
    def logout(self, ip_address=None):
        """
        用户登出
        
        Args:
            ip_address: IP地址（用于日志记录）
            
        Returns:
            dict: 包含登出结果的字典
                 {success: bool, message: str}
        """
        try:
            # 获取当前用户信息用于日志记录
            user_id = None
            username = None
            if self.current_user:
                user_id = self.current_user['id']
                username = self.current_user['username']
            
            # 调用用户模型进行登出
            result = self.user_model.logout_user()
            
            if result:
                # 重置当前用户状态
                self.current_user = None
                self.is_authenticated = False
                
                # 记录登出日志
                if DATABASE_READY:
                    log_operation(
                        user_id=user_id,
                        action="logout",
                        details="用户登出成功",
                        ip_address=ip_address
                    )
                
                logger.info(f"用户 {username} 登出成功")
                
                return {
                    "success": True,
                    "message": "登出成功"
                }
            else:
                logger.error(f"用户 {username} 登出失败")
                
                return {
                    "success": False,
                    "message": "登出失败",
                }
                
        except Exception as e:
            logger.error(f"登出过程出错: {str(e)}")
            return {
                "success": False,
                "message": f"登出过程中发生错误: {str(e)}"
            }
    
    def register(self, username, password, confirm_password, fullname, email, role='user', ip_address=None):
        """
        用户注册
        
        Args:
            username: 用户名
            password: 密码
            confirm_password: 确认密码
            fullname: 全名
            email: 邮箱
            role: 角色
            ip_address: IP地址（用于日志记录）
            
        Returns:
            dict: 包含注册结果的字典
                 {success: bool, message: str, user_id: int or None}
        """
        # 验证输入
        if not all([username, password, confirm_password, fullname, email]):
            logger.warning("注册尝试失败: 缺少必要信息")
            return {
                "success": False,
                "message": "请填写所有必填信息",
                "user_id": None
            }
        
        # 验证密码一致性
        if password != confirm_password:
            logger.warning("注册尝试失败: 两次输入的密码不一致")
            return {
                "success": False,
                "message": "两次输入的密码不一致",
                "user_id": None
            }
        
        # 验证密码强度
        if len(password) < 6:
            logger.warning("注册尝试失败: 密码强度不足")
            return {
                "success": False,
                "message": "密码长度至少为6位",
                "user_id": None
            }
        
        try:
            # 调用用户模型创建用户
            user_id = self.user_model.create_user(
                username=username,
                password=password,
                fullname=fullname,
                email=email,
                role=role
            )
            
            if user_id:
                # 注册成功，记录日志
                if DATABASE_READY:
                    log_operation(
                        user_id=None,
                        action="register",
                        details=f"用户注册成功，ID: {user_id}, 角色: {role}",
                        ip_address=ip_address
                    )
                
                logger.info(f"用户 {username} 注册成功，ID: {user_id}")
                
                return {
                    "success": True,
                    "message": "注册成功",
                    "user_id": user_id
                }
            else:
                logger.warning(f"用户 {username} 注册失败")
                
                return {
                    "success": False,
                    "message": "用户名已存在",
                    "user_id": None
                }
                
        except Exception as e:
            logger.error(f"注册过程出错: {str(e)}")
            return {
                "success": False,
                "message": f"注册过程中发生错误: {str(e)}",
                "user_id": None
            }
    
    def change_password(self, user_id, old_password, new_password, confirm_password):
        """
        修改密码
        
        Args:
            user_id: 用户ID
            old_password: 原密码
            new_password: 新密码
            confirm_password: 确认新密码
            
        Returns:
            dict: 包含修改结果的字典
                 {success: bool, message: str}
        """
        # 验证输入
        if not all([old_password, new_password, confirm_password]):
            return {
                "success": False,
                "message": "请填写所有密码信息",
            }
        
        # 验证密码一致性
        if new_password != confirm_password:
            return {
                "success": False,
                "message": "两次输入的新密码不一致",
            }
        
        # 验证新密码强度
        if len(new_password) < 6:
            return {
                "success": False,
                "message": "新密码长度至少为6位",
            }
        
        try:
            # 调用用户模型修改密码
            result = self.user_model.change_password(user_id, old_password, new_password)
            
            if result:
                # 修改成功，记录日志
                if DATABASE_READY:
                    log_operation(
                        user_id=user_id,
                        action="change_password",
                        details="密码修改成功"
                    )
                
                logger.info(f"用户ID {user_id} 密码修改成功")
                
                return {
                    "success": True,
                    "message": "密码修改成功",
                }
            else:
                logger.warning(f"用户ID {user_id} 密码修改失败: 原密码错误")
                
                return {
                    "success": False,
                    "message": "原密码错误",
                }
                
        except Exception as e:
            logger.error(f"修改密码过程出错: {str(e)}")
            return {
                "success": False,
                "message": f"修改密码过程中发生错误: {str(e)}"
            }
    
    def reset_password(self, user_id, new_password, confirm_password):
        """
        重置密码（管理员功能，无需原密码）
        
        Args:
            user_id: 用户ID
            new_password: 新密码
            confirm_password: 确认新密码
            
        Returns:
            dict: 包含重置结果的字典
                 {success: bool, message: str}
        """
        # 验证输入
        if not all([new_password, confirm_password]):
            return {
                "success": False,
                "message": "请填写所有密码信息",
            }
        
        # 验证密码一致性
        if new_password != confirm_password:
            return {
                "success": False,
                "message": "两次输入的新密码不一致",
            }
        
        # 验证新密码强度
        if len(new_password) < 6:
            return {
                "success": False,
                "message": "新密码长度至少为6位",
            }
        
        try:
            # 调用用户模型重置密码
            result = self.user_model.reset_password(user_id, new_password)
            
            if result:
                # 重置成功，记录日志
                if DATABASE_READY:
                    log_operation(
                        user_id=self.current_user['id'] if self.current_user else None,
                        action="reset_password",
                        details=f"用户ID {user_id} 密码重置成功"
                    )
                
                logger.info(f"用户ID {user_id} 密码重置成功")
                
                return {
                    "success": True,
                    "message": "密码重置成功",
                }
            else:
                logger.warning(f"用户ID {user_id} 密码重置失败")
                
                return {
                    "success": False,
                    "message": "密码重置失败",
                }
                
        except Exception as e:
            logger.error(f"重置密码过程出错: {str(e)}")
            return {
                "success": False,
                "message": f"重置密码过程中发生错误: {str(e)}"
            }
    
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
    
    def check_permission(self, required_role):
        """
        检查用户是否具有指定权限
        
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
    
    def get_user_by_id(self, user_id):
        """
        通过ID获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict or None: 用户信息
        """
        try:
            return self.user_model.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"获取用户信息出错: {str(e)}")
            return None
    
    def get_all_users(self):
        """
        获取所有用户列表
        
        Returns:
            list: 用户列表
        """
        try:
            return self.user_model.get_all_users()
        except Exception as e:
            logger.error(f"获取用户列表出错: {str(e)}")
            return []
    
    def update_user_info(self, user_id, fullname=None, email=None, role=None):
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            fullname: 全名（可选）
            email: 邮箱（可选）
            role: 角色（可选）
            
        Returns:
            dict: 包含更新结果的字典
                 {success: bool, message: str}
        """
        try:
            # 调用用户模型更新用户信息
            result = self.user_model.update_user(user_id, fullname, email, role)
            
            if result:
                # 更新成功，记录日志
                if DATABASE_READY:
                    log_operation(
                        user_id=self.current_user['id'] if self.current_user else None,
                        action="update_user",
                        details=f"用户ID {user_id} 信息更新成功"
                    )
                
                logger.info(f"用户ID {user_id} 信息更新成功")
                
                # 如果更新的是当前用户，更新当前用户信息
                if self.current_user and self.current_user['id'] == user_id:
                    if fullname:
                        self.current_user['fullname'] = fullname
                    if email:
                        self.current_user['email'] = email
                    if role:
                        self.current_user['role'] = role
                
                return {
                    "success": True,
                    "message": "用户信息更新成功",
                }
            else:
                logger.warning(f"用户ID {user_id} 信息更新失败")
                
                return {
                    "success": False,
                    "message": "用户信息更新失败",
                }
                
        except Exception as e:
            logger.error(f"更新用户信息过程出错: {str(e)}")
            return {
                "success": False,
                "message": f"更新用户信息过程中发生错误: {str(e)}"
            }
    
    def delete_user(self, user_id):
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含删除结果的字典
                 {success: bool, message: str}
        """
        try:
            # 检查是否为当前登录用户
            if self.current_user and self.current_user['id'] == user_id:
                return {
                    "success": False,
                    "message": "无法删除当前登录用户",
                }
            
            # 调用用户模型删除用户
            result = self.user_model.delete_user(user_id)
            
            if result:
                # 删除成功，记录日志
                if DATABASE_READY:
                    log_operation(
                        user_id=self.current_user['id'] if self.current_user else None,
                        action="delete_user",
                        details=f"用户ID {user_id} 删除成功"
                    )
                
                logger.info(f"用户ID {user_id} 删除成功")
                
                return {
                    "success": True,
                    "message": "用户删除成功",
                }
            else:
                logger.warning(f"用户ID {user_id} 删除失败")
                
                return {
                    "success": False,
                    "message": "用户删除失败",
                }
                
        except Exception as e:
            logger.error(f"删除用户过程出错: {str(e)}")
            return {
                "success": False,
                "message": f"删除用户过程中发生错误: {str(e)}"
            }


# 创建全局身份验证控制器实例
auth_controller = AuthController()


if __name__ == "__main__":
    # 测试身份验证控制器功能
    print("身份验证控制器测试")
    
    # 测试登录
    # 注意：这只是一个基本测试，实际使用中应该通过UI进行交互
    if DATABASE_READY:
        # 假设有一个测试用户，用户名: admin, 密码: admin123
        login_result = auth_controller.login("admin", "admin123")
        print(f"登录测试结果: {login_result}")
    else:
        print("数据库未就绪，跳过测试")