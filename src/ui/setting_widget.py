#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置组件
实现系统设置功能
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox, 
    QCheckBox, QSpinBox, QVBoxLayout, QHBoxLayout, 
    QFormLayout, QGroupBox, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

import sys
import os
import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据库操作
from src.database.db_manager import execute_query, log_operation

# 导入设置控制器
from src.controllers.settings_controller import settings_controller


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
        
        # 应用主题
        general_layout.addRow("应用主题:", QLabel(""))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题"])
        general_layout.setWidget(0, QFormLayout.FieldRole, self.theme_combo)
        
        # 界面语言
        general_layout.addRow("界面语言:", QLabel(""))
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        general_layout.setWidget(1, QFormLayout.FieldRole, self.language_combo)
        
        # 默认账户设置
        general_layout.addRow("默认账户:", QLabel(""))
        self.default_account_combo = QComboBox()
        self.load_accounts()
        general_layout.setWidget(2, QFormLayout.FieldRole, self.default_account_combo)
        
        # 货币符号
        general_layout.addRow("货币符号:", QLabel(""))
        self.currency_edit = QLineEdit()
        general_layout.setWidget(3, QFormLayout.FieldRole, self.currency_edit)
        
        # 小数位数
        general_layout.addRow("小数位数:", QLabel(""))
        self.decimal_spin = QSpinBox()
        self.decimal_spin.setRange(0, 4)
        general_layout.setWidget(4, QFormLayout.FieldRole, self.decimal_spin)
        
        # 创建安全设置组
        security_group = QGroupBox("安全设置")
        security_layout = QFormLayout(security_group)
        security_layout.setContentsMargins(15, 15, 15, 15)
        security_layout.setSpacing(10)
        
        # 自动登出时间设置
        security_layout.addRow("自动登出时间:", QLabel(""))
        self.auto_logout_spin = QSpinBox()
        self.auto_logout_spin.setRange(1, 120)
        self.auto_logout_spin.setSuffix(" 分钟")
        security_layout.setWidget(0, QFormLayout.FieldRole, self.auto_logout_spin)
        
        # 密码复杂度要求
        security_layout.addRow("密码复杂度要求:", QLabel(""))
        self.password_complexity_check = QCheckBox("启用强密码要求")
        security_layout.setWidget(1, QFormLayout.FieldRole, self.password_complexity_check)
        
        # 密码最小长度
        security_layout.addRow("密码最小长度:", QLabel(""))
        self.password_min_length_spin = QSpinBox()
        self.password_min_length_spin.setRange(4, 20)
        security_layout.setWidget(2, QFormLayout.FieldRole, self.password_min_length_spin)
        
        # 创建备份设置组
        backup_group = QGroupBox("备份设置")
        backup_layout = QFormLayout(backup_group)
        backup_layout.setContentsMargins(15, 15, 15, 15)
        backup_layout.setSpacing(10)
        
        # 自动备份
        backup_layout.addRow("自动备份:", QLabel(""))
        self.auto_backup_check = QCheckBox("启用自动备份")
        backup_layout.setWidget(0, QFormLayout.FieldRole, self.auto_backup_check)
        
        # 自动备份间隔
        backup_layout.addRow("自动备份间隔:", QLabel(""))
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 30)
        self.backup_interval_spin.setSuffix(" 天")
        backup_layout.setWidget(1, QFormLayout.FieldRole, self.backup_interval_spin)
        
        # 备份保留数量
        backup_layout.addRow("备份保留数量:", QLabel(""))
        self.backup_keep_spin = QSpinBox()
        self.backup_keep_spin.setRange(1, 100)
        self.backup_keep_spin.setSuffix(" 个")
        backup_layout.setWidget(2, QFormLayout.FieldRole, self.backup_keep_spin)
        
        # 备份路径
        backup_layout.addRow("备份路径:", QLabel(""))
        backup_path_layout = QHBoxLayout()
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setReadOnly(True)
        self.browse_backup_button = QPushButton("浏览...")
        self.browse_backup_button.clicked.connect(self.browse_backup_path)
        backup_path_layout.addWidget(self.backup_path_edit)
        backup_path_layout.addWidget(self.browse_backup_button)
        backup_layout.setWidget(3, QFormLayout.FieldRole, backup_path_layout)
        
        # 创建财务设置组
        finance_group = QGroupBox("财务设置")
        finance_layout = QFormLayout(finance_group)
        finance_layout.setContentsMargins(15, 15, 15, 15)
        finance_layout.setSpacing(10)
        
        # 税率设置
        finance_layout.addRow("默认税率:", QLabel(""))
        self.tax_rate_edit = QLineEdit()
        self.tax_rate_edit.setPlaceholderText("例如: 0.13")
        finance_layout.setWidget(0, QFormLayout.FieldRole, self.tax_rate_edit)
        
        # 财年开始日期
        finance_layout.addRow("财年开始日期:", QLabel(""))
        self.fiscal_year_edit = QLineEdit()
        self.fiscal_year_edit.setPlaceholderText("MM-DD 格式，例如: 01-01")
        finance_layout.setWidget(1, QFormLayout.FieldRole, self.fiscal_year_edit)
        
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
        
        # 导出设置按钮
        self.export_button = QPushButton("导出设置")
        self.export_button.setFixedHeight(36)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.export_button.clicked.connect(self.export_settings)
        
        # 导入设置按钮
        self.import_button = QPushButton("导入设置")
        self.import_button.setFixedHeight(36)
        self.import_button.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.import_button.clicked.connect(self.import_settings)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.import_button)
        button_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(general_group)
        main_layout.addWidget(security_group)
        main_layout.addWidget(backup_group)
        main_layout.addWidget(finance_group)
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
    
    def load_settings(self):
        """从settings_controller加载设置"""
        try:
            # 应用主题
            theme = settings_controller.get_setting('app.theme', 'light')
            self.theme_combo.setCurrentIndex(0 if theme == 'light' else 1)
            
            # 界面语言
            language = settings_controller.get_setting('app.language', 'zh_CN')
            self.language_combo.setCurrentIndex(0 if language == 'zh_CN' else 1)
            
            # 默认账户
            default_account_id = settings_controller.get_setting('finance.default_account_id')
            if default_account_id:
                # 这里需要根据ID查找账户名称的索引
                pass
            
            # 货币符号
            currency = settings_controller.get_setting('finance.currency_symbol', '¥')
            self.currency_edit.setText(currency)
            
            # 小数位数
            decimals = settings_controller.get_setting('finance.decimal_places', 2)
            self.decimal_spin.setValue(decimals)
            
            # 自动登出时间
            logout_timeout = settings_controller.get_setting('security.session_timeout', 30)
            self.auto_logout_spin.setValue(logout_timeout)
            
            # 密码复杂度要求
            strong_password = settings_controller.get_setting('security.require_strong_password', False)
            self.password_complexity_check.setChecked(strong_password)
            
            # 密码最小长度
            min_length = settings_controller.get_setting('security.password_min_length', 6)
            self.password_min_length_spin.setValue(min_length)
            
            # 自动备份
            auto_backup = settings_controller.get_setting('app.auto_backup', True)
            self.auto_backup_check.setChecked(auto_backup)
            
            # 自动备份间隔
            backup_interval = settings_controller.get_setting('app.backup_interval', 7)
            self.backup_interval_spin.setValue(backup_interval)
            
            # 备份保留数量
            max_backups = settings_controller.get_setting('database.max_backups', 10)
            self.backup_keep_spin.setValue(max_backups)
            
            # 备份路径
            backup_path = settings_controller.get_setting('database.backup_path')
            self.backup_path_edit.setText(backup_path)
            
            # 税率
            tax_rate = settings_controller.get_setting('finance.tax_rate', 0.13)
            self.tax_rate_edit.setText(str(tax_rate))
            
            # 财年开始日期
            fiscal_start = settings_controller.get_setting('finance.financial_year_start', '01-01')
            self.fiscal_year_edit.setText(fiscal_start)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载设置失败: {str(e)}")
    
    def save_settings(self):
        """将设置保存到settings_controller"""
        try:
            # 应用主题
            theme = 'light' if self.theme_combo.currentIndex() == 0 else 'dark'
            settings_controller.set_setting('app.theme', theme)
            
            # 界面语言
            language = 'zh_CN' if self.language_combo.currentIndex() == 0 else 'en_US'
            settings_controller.set_setting('app.language', language)
            
            # 默认账户
            # 这里需要获取选中账户的ID
            # default_account_id = ...
            # settings_controller.set_setting('finance.default_account_id', default_account_id)
            
            # 货币符号
            currency = self.currency_edit.text()
            settings_controller.set_setting('finance.currency_symbol', currency)
            
            # 小数位数
            decimals = self.decimal_spin.value()
            settings_controller.set_setting('finance.decimal_places', decimals)
            
            # 自动登出时间
            logout_timeout = self.auto_logout_spin.value()
            settings_controller.set_setting('security.session_timeout', logout_timeout)
            
            # 密码复杂度要求
            strong_password = self.password_complexity_check.isChecked()
            settings_controller.set_setting('security.require_strong_password', strong_password)
            
            # 密码最小长度
            min_length = self.password_min_length_spin.value()
            settings_controller.set_setting('security.password_min_length', min_length)
            
            # 自动备份
            auto_backup = self.auto_backup_check.isChecked()
            settings_controller.set_setting('app.auto_backup', auto_backup)
            
            # 自动备份间隔
            backup_interval = self.backup_interval_spin.value()
            settings_controller.set_setting('app.backup_interval', backup_interval)
            
            # 备份保留数量
            max_backups = self.backup_keep_spin.value()
            settings_controller.set_setting('database.max_backups', max_backups)
            
            # 税率
            try:
                tax_rate = float(self.tax_rate_edit.text())
                settings_controller.set_setting('finance.tax_rate', tax_rate)
            except ValueError:
                QMessageBox.warning(self, "警告", "税率必须是有效的数字")
                return
            
            # 财年开始日期
            fiscal_start = self.fiscal_year_edit.text()
            settings_controller.set_setting('finance.financial_year_start', fiscal_start)
            
            QMessageBox.information(self, "成功", "设置已保存!")
            
            # 记录操作日志
            log_operation(self.user_info['id'], "保存系统设置", "用户更新了系统设置")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
    
    def reset_settings(self):
        """重置设置为默认值"""
        reply = QMessageBox.question(self, "确认", "确定要重置所有设置为默认值吗?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # 使用settings_controller重置设置
                settings_controller.reset_settings()
                
                # 重新加载设置
                self.load_settings()
                
                QMessageBox.information(self, "成功", "设置已重置为默认值!")
                
                # 记录操作日志
                log_operation(self.user_info['id'], "重置系统设置", "用户重置了系统设置")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重置设置失败: {str(e)}")
    
    def browse_backup_path(self):
        """浏览备份路径"""
        try:
            dir_path = QFileDialog.getExistingDirectory(self, "选择备份目录")
            if dir_path:
                self.backup_path_edit.setText(dir_path)
                settings_controller.set_setting('database.backup_path', dir_path)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"选择备份路径失败: {str(e)}")
    
    def export_settings(self):
        """导出设置"""
        try:
            # 显示文件对话框选择导出路径
            default_filename = f"settings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出设置", default_filename, "JSON文件 (*.json);;所有文件 (*)"
            )
            
            if file_path:
                # 使用settings_controller导出设置
                success = settings_controller.export_settings(file_path)
                if success:
                    QMessageBox.information(self, "成功", f"设置已成功导出到:\n{file_path}")
                else:
                    QMessageBox.error(self, "错误", "导出设置失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出设置失败: {str(e)}")
    
    def import_settings(self):
        """导入设置"""
        try:
            # 显示文件对话框选择导入文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "导入设置", "", "JSON文件 (*.json);;所有文件 (*)"
            )
            
            if file_path:
                # 确认导入操作
                reply = QMessageBox.question(
                    self, "确认导入", 
                    "导入设置将覆盖当前所有设置，确定要继续吗？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 使用settings_controller导入设置
                    success = settings_controller.import_settings(file_path)
                    if success:
                        # 重新加载设置
                        self.load_settings()
                        QMessageBox.information(self, "成功", "设置已成功导入")
                    else:
                        QMessageBox.error(self, "错误", "导入设置失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入设置失败: {str(e)}")