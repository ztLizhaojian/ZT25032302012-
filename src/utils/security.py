#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全工具模块
提供密码哈希、验证、令牌管理等安全相关功能
"""

import hashlib
import os
import secrets
from typing import Tuple, Optional
from datetime import datetime, timedelta

from src.utils.logger import get_logger, log_error, handle_errors

logger = get_logger('security')


@handle_errors('security', fallback_return=None)
def hash_password(password: str) -> str:
    """
    对密码进行哈希处理（使用PBKDF2算法）
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码（包含盐值）
    """
    try:
        # 生成随机盐值
        salt = secrets.token_bytes(16)
        
        # 使用PBKDF2算法进行哈希
        iterations = 100000
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',  # 哈希算法
            password.encode('utf-8'),  # 密码
            salt,  # 盐值
            iterations  # 迭代次数
        )
        
        # 将盐值和哈希值组合并编码为十六进制字符串
        salt_hex = salt.hex()
        hash_hex = password_hash.hex()
        
        # 返回格式: 迭代次数$盐值$哈希值
        return f"{iterations}${salt_hex}${hash_hex}"
        
    except Exception as e:
        log_error('security', f"密码哈希失败: {str(e)}")
        raise


@handle_errors('security', fallback_return=False)
def verify_password(password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配
    
    Args:
        password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    try:
        # 兼容旧版本哈希格式（静态盐值）
        if hashed_password and len(hashed_password) == 64 and '$' not in hashed_password:
            # 使用旧的验证方式
            return hashlib.sha256((password + "finance_system_salt").encode()).hexdigest() == hashed_password
        
        # 解析新的哈希密码格式
        parts = hashed_password.split('$')
        if len(parts) != 3:
            log_error('security', "无效的密码哈希格式")
            return False
        
        iterations, salt_hex, hash_hex = parts
        iterations = int(iterations)
        
        # 解码盐值
        salt = bytes.fromhex(salt_hex)
        
        # 重新计算密码哈希
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            iterations
        )
        
        # 比较哈希值
        return password_hash.hex() == hash_hex
        
    except Exception as e:
        log_error('security', f"密码验证失败: {str(e)}")
        return False


@handle_errors('security')
def generate_token(token_length: int = 32) -> str:
    """
    生成安全的随机令牌
    
    Args:
        token_length: 令牌长度
        
    Returns:
        str: 随机令牌
    """
    return secrets.token_hex(token_length)


@handle_errors('security')
def generate_session_token(user_id: int) -> str:
    """
    生成会话令牌
    
    Args:
        user_id: 用户ID
        
    Returns:
        str: 会话令牌
    """
    # 组合用户ID、时间戳和随机值生成会话令牌
    timestamp = datetime.now().timestamp()
    random_value = secrets.token_hex(16)
    
    # 创建会话数据
    session_data = f"{user_id}:{timestamp}:{random_value}"
    
    # 哈希处理
    return hashlib.sha256(session_data.encode()).hexdigest()


class TokenManager:
    """
    令牌管理器，用于生成和验证临时令牌（如密码重置令牌）
    """
    
    def __init__(self):
        self.token_ttl = timedelta(hours=24)  # 默认令牌有效期24小时
    
    def generate_token(self, user_id: int) -> Tuple[str, str]:
        """
        生成令牌和过期时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            tuple: (令牌, 过期时间字符串)
        """
        # 生成随机令牌
        token = generate_token(16)
        
        # 计算过期时间
        expires_at = datetime.now() + self.token_ttl
        expires_str = expires_at.strftime('%Y-%m-%d %H:%M:%S')
        
        return token, expires_str
    
    def is_token_valid(self, expires_str: str) -> bool:
        """
        检查令牌是否过期
        
        Args:
            expires_str: 过期时间字符串
            
        Returns:
            bool: 是否有效
        """
        try:
            expires_at = datetime.strptime(expires_str, '%Y-%m-%d %H:%M:%S')
            return datetime.now() <= expires_at
        except Exception as e:
            log_error('security', f"令牌有效性检查失败: {str(e)}")
            return False


# 密码策略验证函数
def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    验证密码强度
    
    Args:
        password: 待验证的密码
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    # 长度检查
    if len(password) < 8:
        return False, "密码长度至少需要8个字符"
    
    # 包含数字检查
    if not any(char.isdigit() for char in password):
        return False, "密码必须包含至少一个数字"
    
    # 包含小写字母检查
    if not any(char.islower() for char in password):
        return False, "密码必须包含至少一个小写字母"
    
    # 包含大写字母检查
    if not any(char.isupper() for char in password):
        return False, "密码必须包含至少一个大写字母"
    
    # 包含特殊字符检查
    special_chars = "!@#$%^&*()-_=+[]{}|;:,.<>?/"
    if not any(char in special_chars for char in password):
        return False, "密码必须包含至少一个特殊字符"
    
    # 密码通过验证
    return True, ""


# 输入验证工具函数
def sanitize_input(input_str: str, max_length: Optional[int] = None) -> str:
    """
    清理和验证输入字符串
    
    Args:
        input_str: 输入字符串
        max_length: 最大长度限制
        
    Returns:
        str: 清理后的字符串
    """
    # 转换为字符串并去除首尾空白
    if input_str is None:
        return ""
    
    sanitized = str(input_str).strip()
    
    # 长度限制
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        log_error('security', f"输入长度超过限制，已截断")
    
    return sanitized


# 创建全局实例
token_manager = TokenManager()
