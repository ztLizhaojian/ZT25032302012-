# -*- coding: utf-8 -*-
"""
信号管理器模块
用于定义和管理应用程序中的全局信号
"""
from PyQt5.QtCore import QObject, pyqtSignal


class SignalManager(QObject):
    """
    信号管理器类
    用于定义和发射应用程序中的全局信号
    """
    # 交易数据变化信号
    transaction_data_changed = pyqtSignal()
    
    # 账户数据变化信号
    account_data_changed = pyqtSignal()
    
    # 分类数据变化信号
    category_data_changed = pyqtSignal()
    
    # 用户数据变化信号
    user_data_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()


# 创建全局信号管理器实例
signal_manager = SignalManager()
