#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全工具模块
提供密码哈希、验证等安全相关功能
"""

import hashlib

# 密码哈希盐值
PASSWORD_SALT = "finance_system_salt"

def hash_password(password):
    """
    对密码进行哈希处理
    
    Args:
        password: 原始密码
        
    Returns:
        str: 哈希后的密码
    """
    return hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest()

def verify_password(password, hashed_password):
    """
    验证密码是否匹配
    
    Args:
        password: 原始密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    return hash_password(password) == hashed_password
