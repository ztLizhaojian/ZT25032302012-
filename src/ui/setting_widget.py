#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置组件
实现系统设置功能
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox, 
    QCheckBox, QSpinBox, QVBoxLayout, QHBoxLayout, 
    QFormLayout, QGroupBox, QMessageBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据库操作
from src.database.db_manager import execute_query, log_operation


class SettingWidget(QWidget):
    """设置组件类"""
    
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建常规设置组
        general_group = QGroupBox("常规设置")
        general_layout = QFormLayout(general_group)
        general_layout.setContentsMargins(15, 15, 15, 15)
        general_layout.setSpacing(10)
        
        # 默认账户设置
        self.default_account_combo = QComboBox()
        self.load_accounts()
        general_layout.addRow("默认账户:", self.default_account_combo)
        
        # 默认分类设置
        self.default_category_combo = QComboBox()
        self.load_categories()
        general_layout.addRow("默认分类:", self.default_category_combo)
        
        # 创建安全设置组
        security_group = QGroupBox("安全设置")
        security_layout = QFormLayout(security_group)
        security_layout.setContentsMargins(15, 15, 15, 15)
        security_layout.setSpacing(10)
        
        # 自动登出时间设置
        self.auto_logout_spin = QSpinBox()
        self.auto_logout_spin.setRange(1, 120)
        self.auto_logout_spin.setSuffix(" 分钟")
        security_layout.addRow("自动登出时间:", self.auto_logout_spin)
        
        # 密码复杂度要求
        self.password_complexity_check = QCheckBox("启用密码复杂度要求")
        security_layout.addRow("", self.password_complexity_check)
        
        # 创建备份设置组
        backup_group = QGroupBox("备份设置")
        backup_layout = QFormLayout(backup_group)
        backup_layout.setContentsMargins(15, 15, 15, 15)
        backup_layout.setSpacing(10)
        
        # 自动备份间隔
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 30)
        self.backup_interval_spin.setSuffix(" 天")
        backup_layout.addRow("自动备份间隔:", self.backup_interval_spin)
        
        # 备份保留数量
        self.backup_keep_spin = QSpinBox()
        self.backup_keep_spin.setRange(1, 100)
        self.backup_keep_spin.setSuffix(" 个")
        backup_layout.addRow("备份保留数量:", self.backup_keep_spin)
        
        # 操作按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 保存按钮
        self.save_button = QPushButton("保存设置")
        self.save_button.setFixedHeight(36)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
        """)
        self.save_button.clicked.connect(self.save_settings)
        
        # 重置按钮
        self.reset_button = QPushButton("重置")
        self.reset_button.setFixedHeight(36)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.reset_button.clicked.connect(self.reset_settings)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(general_group)
        main_layout.addWidget(security_group)
        main_layout.addWidget(backup_group)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
    
    def load_accounts(self):
        """加载账户列表"""
        try:
            # 查询账户数据
            query = "SELECT name FROM accounts ORDER BY id"
            rows = execute_query(query)
            
            # 填充账户下拉框
            for row in rows:
                self.default_account_combo.addItem(row[0])
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载账户数据失败: {str(e)}")
    
    def load_categories(self):
        """加载分类列表"""
        try:
            # 查询分类数据
            query = "SELECT name FROM categories ORDER BY id"
            rows = execute_query(query)
            
            # 填充分类下拉框
            for row in rows:
                self.default_category_combo.addItem(row[0])
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载分类数据失败: {str(e)}")
    
    def load_settings(self):
        """加载设置"""
        try:
            # 这里应该从数据库或配置文件加载实际设置
            # 目前使用默认值
            self.auto_logout_spin.setValue(30)
            self.backup_interval_spin.setValue(7)
            self.backup_keep_spin.setValue(10)
            self.password_complexity_check.setChecked(True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载设置失败: {str(e)}")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 这里应该将设置保存到数据库或配置文件
            # 目前只是显示消息
            QMessageBox.information(self, "成功", "设置已保存!")
            
            # 记录操作日志
            log_operation(self.user_info['id'], "保存系统设置")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
    
    def reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(self, "确认", "确定要重置所有设置为默认值吗?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # 重置为默认值
                self.load_settings()
                QMessageBox.information(self, "成功", "设置已重置为默认值!")
                
                # 记录操作日志
                log_operation(self.user_info['id'], "重置系统设置")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重置设置失败: {str(e)}")