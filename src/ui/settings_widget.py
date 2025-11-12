#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置和管理组件
实现系统配置、账户管理、分类管理、用户管理等功能
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox, 
    QDateEdit, QTextEdit, QTableView, QHeaderView, QVBoxLayout, 
    QHBoxLayout, QGridLayout, QGroupBox, QTabWidget, QMessageBox,
    QDialog, QFormLayout, QInputDialog, QSpinBox, QDoubleSpinBox,
    QFileDialog, QListWidget, QListWidgetItem, QCheckBox, QTreeWidget,
    QTreeWidgetItem, QSplitter
)
from PyQt5.QtGui import QFont, QColor, QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtCore import Qt, QDate, QSortFilterProxyModel

import sys
import os
import json
import shutil
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据库操作
from src.database.db_manager import execute_query, log_operation


class SettingsWidget(QWidget):
    """设置和管理组件类"""
    
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建标签页部件
        self.tab_widget = QTabWidget()
        
        # 创建各个设置标签页
        self.create_accounts_tab()      # 账户管理
        self.create_categories_tab()    # 分类管理
        self.create_users_tab()         # 用户管理（仅管理员可见）
        self.create_system_tab()        # 系统设置
        self.create_backup_tab()        # 备份恢复
        
        # 添加标签页
        self.tab_widget.addTab(self.accounts_widget, "账户管理")
        self.tab_widget.addTab(self.categories_widget, "分类管理")
        if self.user_info['role'] == 'admin':
            self.tab_widget.addTab(self.users_widget, "用户管理")
        self.tab_widget.addTab(self.system_widget, "系统设置")
        self.tab_widget.addTab(self.backup_widget, "备份恢复")
        
        # 添加标签页到主布局
        main_layout.addWidget(self.tab_widget)
    
    def create_accounts_tab(self):
        """创建账户管理标签页"""
        self.accounts_widget = QWidget()
        accounts_layout = QVBoxLayout(self.accounts_widget)
        accounts_layout.setSpacing(15)
        
        # 创建表单组
        form_group = QGroupBox("账户信息")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)
        
        # 账户名称
        form_layout.addRow("账户名称:", QLabel(""))  # 占位，将被替换
        self.account_name_edit = QLineEdit()
        self.account_name_edit.setPlaceholderText("请输入账户名称")
        form_layout.setWidget(0, QFormLayout.FieldRole, self.account_name_edit)
        
        # 账户类型
        form_layout.addRow("账户类型:", QLabel(""))  # 占位
        self.account_type_combo = QComboBox()
        self.account_type_combo.addItems(["现金", "银行存款", "信用卡", "支付宝", "微信", "其他"])
        form_layout.setWidget(1, QFormLayout.FieldRole, self.account_type_combo)
        
        # 期初余额
        form_layout.addRow("期初余额:", QLabel(""))  # 占位
        self.opening_balance_edit = QLineEdit()
        self.opening_balance_edit.setPlaceholderText("请输入期初余额")
        self.opening_balance_edit.setText("0.00")
        form_layout.setWidget(2, QFormLayout.FieldRole, self.opening_balance_edit)
        
        # 备注
        form_layout.addRow("备注:", QLabel(""))  # 占位
        self.account_note_edit = QTextEdit()
        self.account_note_edit.setPlaceholderText("请输入备注信息")
        self.account_note_edit.setMaximumHeight(80)
        form_layout.setWidget(3, QFormLayout.FieldRole, self.account_note_edit)
        
        # 创建操作按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.add_account_button = QPushButton("添加账户")
        self.add_account_button.setFixedHeight(36)
        self.add_account_button.setStyleSheet("""
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
        self.add_account_button.clicked.connect(self.add_account)
        
        self.update_account_button = QPushButton("更新账户")
        self.update_account_button.setFixedHeight(36)
        self.update_account_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)
        self.update_account_button.clicked.connect(self.update_account)
        self.update_account_button.setEnabled(False)
        
        self.delete_account_button = QPushButton("删除账户")
        self.delete_account_button.setFixedHeight(36)
        self.delete_account_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)
        self.delete_account_button.clicked.connect(self.delete_account)
        self.delete_account_button.setEnabled(False)
        
        self.reset_account_button = QPushButton("重置")
        self.reset_account_button.setFixedHeight(36)
        self.reset_account_button.setStyleSheet("""
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
        self.reset_account_button.clicked.connect(self.reset_account_form)
        
        button_layout.addWidget(self.add_account_button)
        button_layout.addWidget(self.update_account_button)
        button_layout.addWidget(self.delete_account_button)
        button_layout.addWidget(self.reset_account_button)
        
        # 创建账户表格
        self.account_table = QTableView()
        self.account_table.setAlternatingRowColors(True)
        self.account_table.setSortingEnabled(True)
        self.account_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.account_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 5px;
                font-family: SimHei;
                font-weight: bold;
            }
        """)
        self.account_table.clicked.connect(self.on_account_selected)
        
        # 创建表格模型
        self.account_model = QStandardItemModel(0, 5)
        self.account_model.setHorizontalHeaderLabels([
            "ID", "账户名称", "账户类型", "期初余额", "备注"
        ])
        self.account_table.setModel(self.account_model)
        self.account_table.hideColumn(0)  # 隐藏ID列
        
        # 添加到布局
        accounts_layout.addWidget(form_group)
        accounts_layout.addLayout(button_layout)
        accounts_layout.addWidget(self.account_table)
        
        # 加载账户数据
        self.load_accounts()
    
    def create_categories_tab(self):
        """创建分类管理标签页"""
        self.categories_widget = QWidget()
        categories_layout = QVBoxLayout(self.categories_widget)
        categories_layout.setSpacing(15)
        
        # 创建分类类型选择
        type_select_layout = QHBoxLayout()
        type_select_layout.addWidget(QLabel("分类类型:"))
        self.category_type_combo = QComboBox()
        self.category_type_combo.addItems(["收入分类", "支出分类"])
        self.category_type_combo.currentTextChanged.connect(self.load_categories)
        type_select_layout.addWidget(self.category_type_combo)
        type_select_layout.addStretch(1)
        
        # 创建表单组
        form_group = QGroupBox("分类信息")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)
        
        # 分类名称
        form_layout.addRow("分类名称:", QLabel(""))  # 占位
        self.category_name_edit = QLineEdit()
        self.category_name_edit.setPlaceholderText("请输入分类名称")
        form_layout.setWidget(0, QFormLayout.FieldRole, self.category_name_edit)
        
        # 分类代码
        form_layout.addRow("分类代码:", QLabel(""))  # 占位
        self.category_code_edit = QLineEdit()
        self.category_code_edit.setPlaceholderText("请输入分类代码")
        form_layout.setWidget(1, QFormLayout.FieldRole, self.category_code_edit)
        
        # 父分类
        form_layout.addRow("父分类:", QLabel(""))  # 占位
        self.parent_category_combo = QComboBox()
        self.parent_category_combo.addItem("无")
        form_layout.setWidget(2, QFormLayout.FieldRole, self.parent_category_combo)
        
        # 备注
        form_layout.addRow("备注:", QLabel(""))  # 占位
        self.category_note_edit = QTextEdit()
        self.category_note_edit.setPlaceholderText("请输入备注信息")
        self.category_note_edit.setMaximumHeight(80)
        form_layout.setWidget(3, QFormLayout.FieldRole, self.category_note_edit)
        
        # 创建操作按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.add_category_button = QPushButton("添加分类")
        self.add_category_button.setFixedHeight(36)
        self.add_category_button.setStyleSheet("""
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
        self.add_category_button.clicked.connect(self.add_category)
        
        self.update_category_button = QPushButton("更新分类")
        self.update_category_button.setFixedHeight(36)
        self.update_category_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)
        self.update_category_button.clicked.connect(self.update_category)
        self.update_category_button.setEnabled(False)
        
        self.delete_category_button = QPushButton("删除分类")
        self.delete_category_button.setFixedHeight(36)
        self.delete_category_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)
        self.delete_category_button.clicked.connect(self.delete_category)
        self.delete_category_button.setEnabled(False)
        
        self.reset_category_button = QPushButton("重置")
        self.reset_category_button.setFixedHeight(36)
        self.reset_category_button.setStyleSheet("""
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
        self.reset_category_button.clicked.connect(self.reset_category_form)
        
        button_layout.addWidget(self.add_category_button)
        button_layout.addWidget(self.update_category_button)
        button_layout.addWidget(self.delete_category_button)
        button_layout.addWidget(self.reset_category_button)
        
        # 创建分类表格
        self.category_table = QTableView()
        self.category_table.setAlternatingRowColors(True)
        self.category_table.setSortingEnabled(True)
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.category_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 5px;
                font-family: SimHei;
                font-weight: bold;
            }
        """)
        self.category_table.clicked.connect(self.on_category_selected)
        
        # 创建表格模型
        self.category_model = QStandardItemModel(0, 6)
        self.category_model.setHorizontalHeaderLabels([
            "ID", "分类名称", "分类代码", "分类类型", "父分类", "备注"
        ])
        self.category_table.setModel(self.category_model)
        self.category_table.hideColumn(0)  # 隐藏ID列
        
        # 添加到布局
        categories_layout.addLayout(type_select_layout)
        categories_layout.addWidget(form_group)
        categories_layout.addLayout(button_layout)
        categories_layout.addWidget(self.category_table)
        
        # 加载分类数据
        self.load_categories()
    
    def create_users_tab(self):
        """创建用户管理标签页（仅管理员可见）"""
        self.users_widget = QWidget()
        users_layout = QVBoxLayout(self.users_widget)
        users_layout.setSpacing(15)
        
        # 创建表单组
        form_group = QGroupBox("用户信息")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(10)
        
        # 用户名
        form_layout.addRow("用户名:", QLabel(""))  # 占位
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        form_layout.setWidget(0, QFormLayout.FieldRole, self.username_edit)
        
        # 密码
        form_layout.addRow("密码:", QLabel(""))  # 占位
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("请输入密码")
        form_layout.setWidget(1, QFormLayout.FieldRole, self.password_edit)
        
        # 确认密码
        form_layout.addRow("确认密码:", QLabel(""))  # 占位
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        self.confirm_password_edit.setPlaceholderText("请再次输入密码")
        form_layout.setWidget(2, QFormLayout.FieldRole, self.confirm_password_edit)
        
        # 全名
        form_layout.addRow("全名:", QLabel(""))  # 占位
        self.fullname_edit = QLineEdit()
        self.fullname_edit.setPlaceholderText("请输入用户全名")
        form_layout.setWidget(3, QFormLayout.FieldRole, self.fullname_edit)
        
        # 用户角色
        form_layout.addRow("角色:", QLabel(""))  # 占位
        self.role_combo = QComboBox()
        self.role_combo.addItems(["管理员", "普通用户"])
        form_layout.setWidget(4, QFormLayout.FieldRole, self.role_combo)
        
        # 状态
        form_layout.addRow("状态:", QLabel(""))  # 占位
        self.status_combo = QComboBox()
        self.status_combo.addItems(["启用", "禁用"])
        form_layout.setWidget(5, QFormLayout.FieldRole, self.status_combo)
        
        # 创建操作按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.add_user_button = QPushButton("添加用户")
        self.add_user_button.setFixedHeight(36)
        self.add_user_button.setStyleSheet("""
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
        self.add_user_button.clicked.connect(self.add_user)
        
        self.update_user_button = QPushButton("更新用户")
        self.update_user_button.setFixedHeight(36)
        self.update_user_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)
        self.update_user_button.clicked.connect(self.update_user)
        self.update_user_button.setEnabled(False)
        
        self.delete_user_button = QPushButton("删除用户")
        self.delete_user_button.setFixedHeight(36)
        self.delete_user_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """)
        self.delete_user_button.clicked.connect(self.delete_user)
        self.delete_user_button.setEnabled(False)
        
        self.reset_user_button = QPushButton("重置")
        self.reset_user_button.setFixedHeight(36)
        self.reset_user_button.setStyleSheet("""
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
        self.reset_user_button.clicked.connect(self.reset_user_form)
        
        button_layout.addWidget(self.add_user_button)
        button_layout.addWidget(self.update_user_button)
        button_layout.addWidget(self.delete_user_button)
        button_layout.addWidget(self.reset_user_button)
        
        # 创建用户表格
        self.user_table = QTableView()
        self.user_table.setAlternatingRowColors(True)
        self.user_table.setSortingEnabled(True)
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 5px;
                font-family: SimHei;
                font-weight: bold;
            }
        """)
        self.user_table.clicked.connect(self.on_user_selected)
        
        # 创建表格模型
        self.user_model = QStandardItemModel(0, 6)
        self.user_model.setHorizontalHeaderLabels([
            "ID", "用户名", "全名", "角色", "状态", "创建时间"
        ])
        self.user_table.setModel(self.user_model)
        self.user_table.hideColumn(0)  # 隐藏ID列
        
        # 添加到布局
        users_layout.addWidget(form_group)
        users_layout.addLayout(button_layout)
        users_layout.addWidget(self.user_table)
        
        # 加载用户数据
        self.load_users()
    
    def create_system_tab(self):
        """创建系统设置标签页"""
        self.system_widget = QWidget()
        system_layout = QVBoxLayout(self.system_widget)
        system_layout.setSpacing(15)
        
        # 创建基本设置组
        basic_group = QGroupBox("基本设置")
        basic_layout = QGridLayout(basic_group)
        basic_layout.setContentsMargins(15, 15, 15, 15)
        basic_layout.setSpacing(15)
        
        # 公司名称
        basic_layout.addWidget(QLabel("公司名称:"), 0, 0)
        self.company_name_edit = QLineEdit()
        self.company_name_edit.setPlaceholderText("请输入公司名称")
        basic_layout.addWidget(self.company_name_edit, 0, 1)
        
        # 会计期间起始月份
        basic_layout.addWidget(QLabel("会计期间起始月份:"), 1, 0)
        self.fiscal_start_month_combo = QComboBox()
        for i in range(1, 13):
            self.fiscal_start_month_combo.addItem(f"{i}月")
        basic_layout.addWidget(self.fiscal_start_month_combo, 1, 1)
        
        # 小数位数
        basic_layout.addWidget(QLabel("金额小数位数:"), 2, 0)
        self.decimal_places_combo = QComboBox()
        self.decimal_places_combo.addItems(["0", "1", "2", "3", "4"])
        self.decimal_places_combo.setCurrentText("2")
        basic_layout.addWidget(self.decimal_places_combo, 2, 1)
        
        # 自动保存
        basic_layout.addWidget(QLabel("自动保存:"), 3, 0)
        self.auto_save_check = QCheckBox()
        self.auto_save_check.setChecked(True)
        basic_layout.addWidget(self.auto_save_check, 3, 1)
        
        # 创建颜色设置组
        color_group = QGroupBox("颜色设置")
        color_layout = QGridLayout(color_group)
        color_layout.setContentsMargins(15, 15, 15, 15)
        color_layout.setSpacing(15)
        
        # 收入颜色
        color_layout.addWidget(QLabel("收入颜色:"), 0, 0)
        self.income_color_button = QPushButton()
        self.income_color_button.setStyleSheet("background-color: #28a745")
        self.income_color_button.clicked.connect(lambda: self.select_color(self.income_color_button))
        color_layout.addWidget(self.income_color_button, 0, 1)
        
        # 支出颜色
        color_layout.addWidget(QLabel("支出颜色:"), 1, 0)
        self.expense_color_button = QPushButton()
        self.expense_color_button.setStyleSheet("background-color: #dc3545")
        self.expense_color_button.clicked.connect(lambda: self.select_color(self.expense_color_button))
        color_layout.addWidget(self.expense_color_button, 1, 1)
        
        # 利润颜色
        color_layout.addWidget(QLabel("利润颜色:"), 2, 0)
        self.profit_color_button = QPushButton()
        self.profit_color_button.setStyleSheet("background-color: #17a2b8")
        self.profit_color_button.clicked.connect(lambda: self.select_color(self.profit_color_button))
        color_layout.addWidget(self.profit_color_button, 2, 1)
        
        # 创建保存按钮
        save_button_layout = QHBoxLayout()
        self.save_settings_button = QPushButton("保存设置")
        self.save_settings_button.setFixedHeight(40)
        self.save_settings_button.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
        """)
        self.save_settings_button.clicked.connect(self.save_settings)
        save_button_layout.addWidget(self.save_settings_button)
        save_button_layout.addStretch(1)
        
        # 添加到布局
        system_layout.addWidget(basic_group)
        system_layout.addWidget(color_group)
        system_layout.addLayout(save_button_layout)
        
        # 加载设置
        self.load_settings()
    
    def create_backup_tab(self):
        """创建备份恢复标签页"""
        self.backup_widget = QWidget()
        backup_layout = QVBoxLayout(self.backup_widget)
        backup_layout.setSpacing(15)
        
        # 创建备份设置组
        backup_setting_group = QGroupBox("备份设置")
        backup_setting_layout = QGridLayout(backup_setting_group)
        backup_setting_layout.setContentsMargins(15, 15, 15, 15)
        backup_setting_layout.setSpacing(15)
        
        # 备份目录
        backup_setting_layout.addWidget(QLabel("备份目录:"), 0, 0)
        backup_dir_layout = QHBoxLayout()
        self.backup_dir_edit = QLineEdit()
        self.backup_dir_edit.setPlaceholderText("请选择备份目录")
        backup_dir_layout.addWidget(self.backup_dir_edit, 1)
        
        self.select_backup_dir_button = QPushButton("浏览...")
        self.select_backup_dir_button.clicked.connect(self.select_backup_directory)
        backup_dir_layout.addWidget(self.select_backup_dir_button)
        
        backup_setting_layout.addLayout(backup_dir_layout, 0, 1)
        
        # 自动备份频率
        backup_setting_layout.addWidget(QLabel("自动备份频率:"), 1, 0)
        self.auto_backup_combo = QComboBox()
        self.auto_backup_combo.addItems(["不自动备份", "每天", "每周", "每月"])
        backup_setting_layout.addWidget(self.auto_backup_combo, 1, 1)
        
        # 最大备份文件数
        backup_setting_layout.addWidget(QLabel("最大备份文件数:"), 2, 0)
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setRange(1, 100)
        self.max_backups_spin.setValue(10)
        backup_setting_layout.addWidget(self.max_backups_spin, 2, 1)
        
        # 创建操作按钮布局
        action_layout = QHBoxLayout()
        action_layout.setSpacing(15)
        
        self.backup_now_button = QPushButton("立即备份")
        self.backup_now_button.setFixedHeight(40)
        self.backup_now_button.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
        """)
        self.backup_now_button.clicked.connect(self.backup_now)
        
        self.restore_button = QPushButton("恢复备份")
        self.restore_button.setFixedHeight(40)
        self.restore_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.restore_button.clicked.connect(self.restore_backup)
        
        self.clean_backups_button = QPushButton("清理备份")
        self.clean_backups_button.setFixedHeight(40)
        self.clean_backups_button.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.clean_backups_button.clicked.connect(self.clean_backups)
        
        action_layout.addWidget(self.backup_now_button)
        action_layout.addWidget(self.restore_button)
        action_layout.addWidget(self.clean_backups_button)
        
        # 创建备份列表
        self.backup_list = QListWidget()
        self.backup_list.setAlternatingRowColors(True)
        
        # 添加到布局
        backup_layout.addWidget(backup_setting_group)
        backup_layout.addLayout(action_layout)
        backup_layout.addWidget(QLabel("备份文件列表:"))
        backup_layout.addWidget(self.backup_list)
        
        # 加载备份设置和列表
        self.load_backup_settings()
        self.refresh_backup_list()
    
    # 账户管理相关方法
    def load_accounts(self):
        """加载账户数据"""
        try:
            accounts = execute_query("SELECT * FROM accounts ORDER BY name", fetchall=True)
            
            # 清空表格
            self.account_model.setRowCount(0)
            
            # 添加数据到表格
            for account in accounts:
                row_items = []
                
                # ID
                row_items.append(QStandardItem(str(account['id'])))
                row_items[-1].setEditable(False)
                
                # 账户名称
                row_items.append(QStandardItem(account['name']))
                row_items[-1].setEditable(False)
                
                # 账户类型
                row_items.append(QStandardItem(account['type']))
                row_items[-1].setEditable(False)
                
                # 期初余额
                balance_item = QStandardItem(f"¥{account['opening_balance']:.2f}")
                balance_item.setEditable(False)
                balance_item.setTextAlignment(Qt.AlignRight)
                row_items.append(balance_item)
                
                # 备注
                note = account['note'] if account['note'] else ""
                row_items.append(QStandardItem(note))
                row_items[-1].setEditable(False)
                
                # 添加行到模型
                self.account_model.appendRow(row_items)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载账户失败: {str(e)}")
    
    def add_account(self):
        """添加账户"""
        try:
            # 获取表单数据
            name = self.account_name_edit.text().strip()
            account_type = self.account_type_combo.currentText()
            opening_balance_text = self.opening_balance_edit.text().strip()
            note = self.account_note_edit.toPlainText().strip()
            
            # 验证输入
            if not name:
                QMessageBox.warning(self, "输入错误", "请输入账户名称")
                self.account_name_edit.setFocus()
                return
            
            try:
                opening_balance = float(opening_balance_text)
            except ValueError:
                QMessageBox.warning(self, "输入错误", "期初余额必须是数字")
                self.opening_balance_edit.setFocus()
                return
            
            # 检查账户是否已存在
            existing_account = execute_query(
                "SELECT id FROM accounts WHERE name = ?", 
                (name,), 
                fetch=True
            )
            
            if existing_account:
                QMessageBox.warning(self, "错误", "账户名称已存在")
                self.account_name_edit.setFocus()
                return
            
            # 添加账户
            execute_query(
                "INSERT INTO accounts (name, type, opening_balance, note) VALUES (?, ?, ?, ?)",
                (name, account_type, opening_balance, note)
            )
            
            # 记录操作日志
            log_operation(
                self.user_info['id'], 
                'add_account', 
                f"添加了账户: {name}"
            )
            
            # 显示成功消息
            QMessageBox.information(self, "添加成功", "账户已成功添加")
            
            # 重置表单
            self.reset_account_form()
            
            # 刷新数据
            self.load_accounts()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加账户失败: {str(e)}")
    
    def update_account(self):
        """更新账户"""
        try:
            # 获取选中的行
            selected_rows = self.account_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "操作错误", "请先选择要更新的账户")
                return
            
            # 获取账户ID
            account_id = self.account_model.data(self.account_model.index(selected_rows[0].row(), 0))
            
            # 获取表单数据
            name = self.account_name_edit.text().strip()
            account_type = self.account_type_combo.currentText()
            opening_balance_text = self.opening_balance_edit.text().strip()
            note = self.account_note_edit.toPlainText().strip()
            
            # 验证输入
            if not name:
                QMessageBox.warning(self, "输入错误", "请输入账户名称")
                self.account_name_edit.setFocus()
                return
            
            try:
                opening_balance = float(opening_balance_text)
            except ValueError:
                QMessageBox.warning(self, "输入错误", "期初余额必须是数字")
                self.opening_balance_edit.setFocus()
                return
            
            # 检查账户名称是否与其他账户重复
            existing_account = execute_query(
                "SELECT id FROM accounts WHERE name = ? AND id != ?", 
                (name, account_id), 
                fetch=True
            )
            
            if existing_account:
                QMessageBox.warning(self, "错误", "账户名称已存在")
                self.account_name_edit.setFocus()
                return
            
            # 更新账户
            execute_query(
                "UPDATE accounts SET name = ?, type = ?, opening_balance = ?, note = ? WHERE id = ?",
                (name, account_type, opening_balance, note, account_id)
            )
            
            # 记录操作日志
            log_operation(
                self.user_info['id'], 
                'update_account', 
                f"更新了账户: {name}"
            )
            
            # 显示成功消息
            QMessageBox.information(self, "更新成功", "账户已成功更新")
            
            # 重置表单
            self.reset_account_form()
            
            # 刷新数据
            self.load_accounts()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新账户失败: {str(e)}")
    
    def delete_account(self):
        """删除账户"""
        try:
            # 获取选中的行
            selected_rows = self.account_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "操作错误", "请先选择要删除的账户")
                return
            
            # 获取账户ID和名称
            account_id = self.account_model.data(self.account_model.index(selected_rows[0].row(), 0))
            account_name = self.account_model.data(self.account_model.index(selected_rows[0].row(), 1))
            
            # 检查是否有交易记录关联
            transaction_count = execute_query(
                "SELECT COUNT(*) as count FROM transactions WHERE account_id = ?", 
                (account_id,), 
                fetch=True
            )
            
            if transaction_count['count'] > 0:
                QMessageBox.warning(
                    self, 
                    "无法删除", 
                    f"账户 '{account_name}' 已有交易记录，无法删除。\n请先删除相关的交易记录。"
                )
                return
            
            # 确认删除
            reply = QMessageBox.question(
                self, 
                "确认删除", 
                f"确定要删除账户 '{account_name}' 吗？\n此操作不可恢复。",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 删除账户
                execute_query("DELETE FROM accounts WHERE id = ?", (account_id,))
                
                # 记录操作日志
                log_operation(
                    self.user_info['id'], 
                    'delete_account', 
                    f"删除了账户: {account_name}"
                )
                
                # 显示成功消息
                QMessageBox.information(self, "删除成功", "账户已成功删除")
                
                # 重置表单
                self.reset_account_form()
                
                # 刷新数据
                self.load_accounts()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除账户失败: {str(e)}")
    
    def reset_account_form(self):
        """重置账户表单"""
        self.account_name_edit.clear()
        self.account_type_combo.setCurrentIndex(0)
        self.opening_balance_edit.setText("0.00")
        self.account_note_edit.clear()
        
        # 取消选中
        self.account_table.clearSelection()
        
        # 启用/禁用按钮
        self.add_account_button.setEnabled(True)
        self.update_account_button.setEnabled(False)
        self.delete_account_button.setEnabled(False)
    
    def on_account_selected(self, index):
        """账户选中事件"""
        # 获取选中行的数据
        account_id = self.account_model.data(self.account_model.index(index.row(), 0))
        name = self.account_model.data(self.account_model.index(index.row(), 1))
        account_type = self.account_model.data(self.account_model.index(index.row(), 2))
        opening_balance_text = self.account_model.data(self.account_model.index(index.row(), 3))
        note = self.account_model.data(self.account_model.index(index.row(), 4))
        
        # 更新表单
        self.account_name_edit.setText(name)
        
        # 设置账户类型
        type_index = self.account_type_combo.findText(account_type)
        if type_index >= 0:
            self.account_type_combo.setCurrentIndex(type_index)
        
        # 设置期初余额（去掉货币符号和格式）
        if opening_balance_text.startswith('¥'):
            opening_balance_text = opening_balance_text[1:]
        self.opening_balance_edit.setText(opening_balance_text)
        
        # 设置备注
        if note:
            self.account_note_edit.setText(note)
        else:
            self.account_note_edit.clear()
        
        # 启用/禁用按钮
        self.add_account_button.setEnabled(False)
        self.update_account_button.setEnabled(True)
        self.delete_account_button.setEnabled(True)
    
    # 分类管理相关方法
    def load_categories(self):
        """加载分类数据"""
        try:
            # 获取分类类型
            category_type_text = self.category_type_combo.currentText()
            db_type = "income" if category_type_text == "收入分类" else "expense"
            
            # 查询分类数据
            categories = execute_query(
                "SELECT c.*, p.name as parent_name FROM categories c LEFT JOIN categories p ON c.parent_id = p.id WHERE c.type = ? ORDER BY c.name",
                (db_type,),
                fetchall=True
            )
            
            # 清空表格
            self.category_model.setRowCount(0)
            
            # 更新父分类下拉框
            self.parent_category_combo.clear()
            self.parent_category_combo.addItem("无")
            for category in categories:
                self.parent_category_combo.addItem(category['name'])
            
            # 添加数据到表格
            for category in categories:
                row_items = []
                
                # ID
                row_items.append(QStandardItem(str(category['id'])))
                row_items[-1].setEditable(False)
                
                # 分类名称
                row_items.append(QStandardItem(category['name']))
                row_items[-1].setEditable(False)
                
                # 分类代码
                code = category['code'] if category['code'] else ""
                row_items.append(QStandardItem(code))
                row_items[-1].setEditable(False)
                
                # 分类类型
                row_items.append(QStandardItem(category_type_text))
                row_items[-1].setEditable(False)
                
                # 父分类
                parent_name = category['parent_name'] if category['parent_name'] else "无"
                row_items.append(QStandardItem(parent_name))
                row_items[-1].setEditable(False)
                
                # 备注
                note = category['note'] if category['note'] else ""
                row_items.append(QStandardItem(note))
                row_items[-1].setEditable(False)
                
                # 添加行到模型
                self.category_model.appendRow(row_items)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载分类失败: {str(e)}")
    
    def add_category(self):
        """添加分类"""
        try:
            # 获取表单数据
            name = self.category_name_edit.text().strip()
            code = self.category_code_edit.text().strip()
            parent_name = self.parent_category_combo.currentText()
            note = self.category_note_edit.toPlainText().strip()
            
            # 获取分类类型
            category_type_text = self.category_type_combo.currentText()
            db_type = "income" if category_type_text == "收入分类" else "expense"
            
            # 验证输入
            if not name:
                QMessageBox.warning(self, "输入错误", "请输入分类名称")
                self.category_name_edit.setFocus()
                return
            
            # 检查分类是否已存在
            existing_category = execute_query(
                "SELECT id FROM categories WHERE name = ? AND type = ?", 
                (name, db_type), 
                fetch=True
            )
            
            if existing_category:
                QMessageBox.warning(self, "错误", "分类名称已存在")
                self.category_name_edit.setFocus()
                return
            
            # 获取父分类ID
            parent_id = None
            if parent_name != "无":
                parent_category = execute_query(
                    "SELECT id FROM categories WHERE name = ? AND type = ?", 
                    (parent_name, db_type), 
                    fetch=True
                )
                if parent_category:
                    parent_id = parent_category['id']
            
            # 添加分类
            execute_query(
                "INSERT INTO categories (name, code, type, parent_id, note) VALUES (?, ?, ?, ?, ?)",
                (name, code, db_type, parent_id, note)
            )
            
            # 记录操作日志
            log_operation(
                self.user_info['id'], 
                'add_category', 
                f"添加了分类: {name}"
            )
            
            # 显示成功消息
            QMessageBox.information(self, "添加成功", "分类已成功添加")
            
            # 重置表单
            self.reset_category_form()
            
            # 刷新数据
            self.load_categories()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加分类失败: {str(e)}")
    
    def update_category(self):
        """更新分类"""
        try:
            # 获取选中的行
            selected_rows = self.category_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "操作错误", "请先选择要更新的分类")
                return
            
            # 获取分类ID
            category_id = self.category_model.data(self.category_model.index(selected_rows[0].row(), 0))
            
            # 获取表单数据
            name = self.category_name_edit.text().strip()
            code = self.category_code_edit.text().strip()
            parent_name = self.parent_category_combo.currentText()
            note = self.category_note_edit.toPlainText().strip()
            
            # 获取分类类型
            category_type_text = self.category_type_combo.currentText()
            db_type = "income" if category_type_text == "收入分类" else "expense"
            
            # 验证输入
            if not name:
                QMessageBox.warning(self, "输入错误", "请输入分类名称")
                self.category_name_edit.setFocus()
                return
            
            # 检查分类名称是否与其他分类重复
            existing_category = execute_query(
                "SELECT id FROM categories WHERE name = ? AND type = ? AND id != ?", 
                (name, db_type, category_id), 
                fetch=True
            )
            
            if existing_category:
                QMessageBox.warning(self, "错误", "分类名称已存在")
                self.category_name_edit.setFocus()
                return
            
            # 获取父分类ID
            parent_id = None
            if parent_name != "无":
                parent_category = execute_query(
                    "SELECT id FROM categories WHERE name = ? AND type = ?", 
                    (parent_name, db_type), 
                    fetch=True
                )
                if parent_category:
                    parent_id = parent_category['id']
                    
                    # 避免循环引用
                    if parent_id == category_id:
                        QMessageBox.warning(self, "错误", "分类不能作为自己的父分类")
                        return
            
            # 更新分类
            execute_query(
                "UPDATE categories SET name = ?, code = ?, parent_id = ?, note = ? WHERE id = ?",
                (name, code, parent_id, note, category_id)
            )
            
            # 记录操作日志
            log_operation(
                self.user_info['id'], 
                'update_category', 
                f"更新了分类: {name}"
            )
            
            # 显示成功消息
            QMessageBox.information(self, "更新成功", "分类已成功更新")
            
            # 重置表单
            self.reset_category_form()
            
            # 刷新数据
            self.load_categories()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新分类失败: {str(e)}")
    
    def delete_category(self):
        """删除分类"""
        try:
            # 获取选中的行
            selected_rows = self.category_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "操作错误", "请先选择要删除的分类")
                return
            
            # 获取分类ID和名称
            category_id = self.category_model.data(self.category_model.index(selected_rows[0].row(), 0))
            category_name = self.category_model.data(self.category_model.index(selected_rows[0].row(), 1))
            
            # 检查是否有子分类
            child_count = execute_query(
                "SELECT COUNT(*) as count FROM categories WHERE parent_id = ?", 
                (category_id,), 
                fetch=True
            )
            
            if child_count['count'] > 0:
                QMessageBox.warning(
                    self, 
                    "无法删除", 
                    f"分类 '{category_name}' 下有子分类，无法删除。\n请先删除或移动子分类。"
                )
                return
            
            # 检查是否有交易记录关联
            transaction_count = execute_query(
                "SELECT COUNT(*) as count FROM transactions WHERE category_id = ?", 
                (category_id,), 
                fetch=True
            )
            
            if transaction_count['count'] > 0:
                QMessageBox.warning(
                    self, 
                    "无法删除", 
                    f"分类 '{category_name}' 已有交易记录，无法删除。\n请先删除相关的交易记录。"
                )
                return
            
            # 确认删除
            reply = QMessageBox.question(
                self, 
                "确认删除", 
                f"确定要删除分类 '{category_name}' 吗？\n此操作不可恢复。",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 删除分类
                execute_query("DELETE FROM categories WHERE id = ?", (category_id,))
                
                # 记录操作日志
                log_operation(
                    self.user_info['id'], 
                    'delete_category', 
                    f"删除了分类: {category_name}"
                )
                
                # 显示成功消息
                QMessageBox.information(self, "删除成功", "分类已成功删除")
                
                # 重置表单
                self.reset_category_form()
                
                # 刷新数据
                self.load_categories()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除分类失败: {str(e)}")
    
    def reset_category_form(self):
        """重置分类表单"""
        self.category_name_edit.clear()
        self.category_code_edit.clear()
        self.parent_category_combo.setCurrentIndex(0)
        self.category_note_edit.clear()
        
        # 取消选中
        self.category_table.clearSelection()
        
        # 启用/禁用按钮
        self.add_category_button.setEnabled(True)
        self.update_category_button.setEnabled(False)
        self.delete_category_button.setEnabled(False)
    
    def on_category_selected(self, index):
        """分类选中事件"""
        # 获取选中行的数据
        category_id = self.category_model.data(self.category_model.index(index.row(), 0))
        name = self.category_model.data(self.category_model.index(index.row(), 1))
        code = self.category_model.data(self.category_model.index(index.row(), 2))
        parent_name = self.category_model.data(self.category_model.index(index.row(), 4))
        note = self.category_model.data(self.category_model.index(index.row(), 5))
        
        # 更新表单
        self.category_name_edit.setText(name)
        
        if code:
            self.category_code_edit.setText(code)
        else:
            self.category_code_edit.clear()
        
        # 设置父分类
        parent_index = self.parent_category_combo.findText(parent_name)
        if parent_index >= 0:
            self.parent_category_combo.setCurrentIndex(parent_index)
        
        # 设置备注
        if note:
            self.category_note_edit.setText(note)
        else:
            self.category_note_edit.clear()
        
        # 启用/禁用按钮
        self.add_category_button.setEnabled(False)
        self.update_category_button.setEnabled(True)
        self.delete_category_button.setEnabled(True)
    
    # 用户管理相关方法
    def load_users(self):
        """加载用户数据"""
        try:
            users = execute_query("SELECT * FROM users ORDER BY id", fetchall=True)
            
            # 清空表格
            self.user_model.setRowCount(0)
            
            # 添加数据到表格
            for user in users:
                row_items = []
                
                # ID
                row_items.append(QStandardItem(str(user['id'])))
                row_items[-1].setEditable(False)
                
                # 用户名
                row_items.append(QStandardItem(user['username']))
                row_items[-1].setEditable(False)
                
                # 全名
                fullname = user['fullname'] if user['fullname'] else ""
                row_items.append(QStandardItem(fullname))
                row_items[-1].setEditable(False)
                
                # 角色
                role = "管理员" if user['role'] == 'admin' else "普通用户"
                row_items.append(QStandardItem(role))
                row_items[-1].setEditable(False)
                
                # 状态
                status = "启用" if user['status'] == 'active' else "禁用"
                status_item = QStandardItem(status)
                status_item.setEditable(False)
                # 根据状态设置颜色
                if user['status'] == 'active':
                    status_item.setForeground(QColor("#28a745"))
                else:
                    status_item.setForeground(QColor("#6c757d"))
                row_items.append(status_item)
                
                # 创建时间
                row_items.append(QStandardItem(user['created_at']))
                row_items[-1].setEditable(False)
                
                # 添加行到模型
                self.user_model.appendRow(row_items)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载用户失败: {str(e)}")
    
    def add_user(self):
        """添加用户"""
        try:
            # 获取表单数据
            username = self.username_edit.text().strip()
            password = self.password_edit.text().strip()
            confirm_password = self.confirm_password_edit.text().strip()
            fullname = self.fullname_edit.text().strip()
            role_text = self.role_combo.currentText()
            status_text = self.status_combo.currentText()
            
            # 验证输入
            if not username:
                QMessageBox.warning(self, "输入错误", "请输入用户名")
                self.username_edit.setFocus()
                return
            
            if not password:
                QMessageBox.warning(self, "输入错误", "请输入密码")
                self.password_edit.setFocus()
                return
            
            if password != confirm_password:
                QMessageBox.warning(self, "输入错误", "两次输入的密码不一致")
                self.confirm_password_edit.setFocus()
                return
            
            # 检查用户是否已存在
            existing_user = execute_query(
                "SELECT id FROM users WHERE username = ?", 
                (username,), 
                fetch=True
            )
            
            if existing_user:
                QMessageBox.warning(self, "错误", "用户名已存在")
                self.username_edit.setFocus()
                return
            
            # 转换角色和状态
            role = "admin" if role_text == "管理员" else "user"
            status = "active" if status_text == "启用" else "inactive"
            
            # 添加用户
            execute_query(
                "INSERT INTO users (username, password, fullname, role, status) VALUES (?, ?, ?, ?, ?)",
                (username, password, fullname, role, status)
            )
            
            # 记录操作日志
            log_operation(
                self.user_info['id'], 
                'add_user', 
                f"添加了用户: {username}"
            )
            
            # 显示成功消息
            QMessageBox.information(self, "添加成功", "用户已成功添加")
            
            # 重置表单
            self.reset_user_form()
            
            # 刷新数据
            self.load_users()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加用户失败: {str(e)}")
    
    def update_user(self):
        """更新用户"""
        try:
            # 获取选中的行
            selected_rows = self.user_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "操作错误", "请先选择要更新的用户")
                return
            
            # 获取用户ID
            user_id = self.user_model.data(self.user_model.index(selected_rows[0].row(), 0))
            current_username = self.user_model.data(self.user_model.index(selected_rows[0].row(), 1))
            
            # 不允许修改自己的角色（管理员）
            if str(user_id) == str(self.user_info['id']) and self.role_combo.currentText() != "管理员":
                QMessageBox.warning(self, "操作错误", "不允许修改自己的管理员角色")
                return
            
            # 获取表单数据
            username = self.username_edit.text().strip()
            password = self.password_edit.text().strip()
            confirm_password = self.confirm_password_edit.text().strip()
            fullname = self.fullname_edit.text().strip()
            role_text = self.role_combo.currentText()
            status_text = self.status_combo.currentText()
            
            # 验证输入
            if not username:
                QMessageBox.warning(self, "输入错误", "请输入用户名")
                self.username_edit.setFocus()
                return
            
            if password != confirm_password:
                QMessageBox.warning(self, "输入错误", "两次输入的密码不一致")
                self.confirm_password_edit.setFocus()
                return
            
            # 检查用户名是否与其他用户重复
            existing_user = execute_query(
                "SELECT id FROM users WHERE username = ? AND id != ?", 
                (username, user_id), 
                fetch=True
            )
            
            if existing_user:
                QMessageBox.warning(self, "错误", "用户名已存在")
                self.username_edit.setFocus()
                return
            
            # 转换角色和状态
            role = "admin" if role_text == "管理员" else "user"
            status = "active" if status_text == "启用" else "inactive"
            
            # 更新用户
            if password:
                # 如果输入了密码，则更新密码
                execute_query(
                    "UPDATE users SET username = ?, password = ?, fullname = ?, role = ?, status = ? WHERE id = ?",
                    (username, password, fullname, role, status, user_id)
                )
            else:
                # 否则不更新密码
                execute_query(
                    "UPDATE users SET username = ?, fullname = ?, role = ?, status = ? WHERE id = ?",
                    (username, fullname, role, status, user_id)
                )
            
            # 记录操作日志
            log_operation(
                self.user_info['id'], 
                'update_user', 
                f"更新了用户: {current_username} -> {username}"
            )
            
            # 显示成功消息
            QMessageBox.information(self, "更新成功", "用户已成功更新")
            
            # 重置表单
            self.reset_user_form()
            
            # 刷新数据
            self.load_users()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新用户失败: {str(e)}")
    
    def delete_user(self):
        """删除用户"""
        try:
            # 获取选中的行
            selected_rows = self.user_table.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "操作错误", "请先选择要删除的用户")
                return
            
            # 获取用户ID和名称
            user_id = self.user_model.data(self.user_model.index(selected_rows[0].row(), 0))
            username = self.user_model.data(self.user_model.index(selected_rows[0].row(), 1))
            
            # 不允许删除自己
            if str(user_id) == str(self.user_info['id']):
                QMessageBox.warning(self, "操作错误", "不允许删除当前登录用户")
                return
            
            # 检查是否有交易记录关联
            transaction_count = execute_query(
                "SELECT COUNT(*) as count FROM transactions WHERE created_by = ?", 
                (user_id,), 
                fetch=True
            )
            
            if transaction_count['count'] > 0:
                QMessageBox.warning(
                    self, 
                    "无法删除", 
                    f"用户 '{username}' 已有操作记录，无法删除。\n请先删除相关的操作记录。"
                )
                return
            
            # 确认删除
            reply = QMessageBox.question(
                self, 
                "确认删除", 
                f"确定要删除用户 '{username}' 吗？\n此操作不可恢复。",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 删除用户
                execute_query("DELETE FROM users WHERE id = ?", (user_id,))
                
                # 记录操作日志
                log_operation(
                    self.user_info['id'], 
                    'delete_user', 
                    f"删除了用户: {username}"
                )
                
                # 显示成功消息
                QMessageBox.information(self, "删除成功", "用户已成功删除")
                
                # 重置表单
                self.reset_user_form()
                
                # 刷新数据
                self.load_users()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除用户失败: {str(e)}")
    
    def reset_user_form(self):
        """重置用户表单"""
        self.username_edit.clear()
        self.password_edit.clear()
        self.confirm_password_edit.clear()
        self.fullname_edit.clear()
        self.role_combo.setCurrentIndex(1)  # 默认为普通用户
        self.status_combo.setCurrentIndex(0)  # 默认为启用
        
        # 取消选中
        self.user_table.clearSelection()
        
        # 启用/禁用按钮
        self.add_user_button.setEnabled(True)
        self.update_user_button.setEnabled(False)
        self.delete_user_button.setEnabled(False)
    
    def on_user_selected(self, index):
        """用户选中事件"""
        # 获取选中行的数据
        user_id = self.user_model.data(self.user_model.index(index.row(), 0))
        username = self.user_model.data(self.user_model.index(index.row(), 1))
        fullname = self.user_model.data(self.user_model.index(index.row(), 2))
        role_text = self.user_model.data(self.user_model.index(index.row(), 3))
        status_text = self.user_model.data(self.user_model.index(index.row(), 4))
        
        # 更新表单
        self.username_edit.setText(username)
        self.password_edit.clear()
        self.confirm_password_edit.clear()
        
        if fullname:
            self.fullname_edit.setText(fullname)
        else:
            self.fullname_edit.clear()
        
        # 设置角色
        role_index = self.role_combo.findText(role_text)
        if role_index >= 0:
            self.role_combo.setCurrentIndex(role_index)
        
        # 设置状态
        status_index = self.status_combo.findText(status_text)
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)
        
        # 启用/禁用按钮
        self.add_user_button.setEnabled(False)
        self.update_user_button.setEnabled(True)
        self.delete_user_button.setEnabled(True)
    
    # 系统设置相关方法
    def load_settings(self):
        """加载系统设置"""
        try:
            # 尝试从数据库加载设置
            settings = execute_query("SELECT * FROM system_settings WHERE id = 1", fetch=True)
            
            if settings:
                # 公司名称
                if settings['company_name']:
                    self.company_name_edit.setText(settings['company_name'])
                
                # 会计期间起始月份
                if settings['fiscal_start_month']:
                    start_month = int(settings['fiscal_start_month'])
                    self.fiscal_start_month_combo.setCurrentIndex(start_month - 1)
                
                # 小数位数
                if settings['decimal_places']:
                    decimal_places = int(settings['decimal_places'])
                    self.decimal_places_combo.setCurrentIndex(decimal_places)
                
                # 自动保存
                self.auto_save_check.setChecked(settings['auto_save'] == 1)
                
                # 颜色设置
                if settings['income_color']:
                    self.income_color_button.setStyleSheet(f"background-color: {settings['income_color']}")
                if settings['expense_color']:
                    self.expense_color_button.setStyleSheet(f"background-color: {settings['expense_color']}")
                if settings['profit_color']:
                    self.profit_color_button.setStyleSheet(f"background-color: {settings['profit_color']}")
                    
        except Exception as e:
            print(f"加载系统设置失败: {str(e)}")
    
    def save_settings(self):
        """保存系统设置"""
        try:
            # 获取表单数据
            company_name = self.company_name_edit.text().strip()
            fiscal_start_month = self.fiscal_start_month_combo.currentIndex() + 1
            decimal_places = int(self.decimal_places_combo.currentText())
            auto_save = 1 if self.auto_save_check.isChecked() else 0
            
            # 获取颜色
            income_color = self.income_color_button.styleSheet().split(':')[-1].strip()
            expense_color = self.expense_color_button.styleSheet().split(':')[-1].strip()
            profit_color = self.profit_color_button.styleSheet().split(':')[-1].strip()
            
            # 检查设置是否存在
            existing_settings = execute_query("SELECT id FROM system_settings WHERE id = 1", fetch=True)
            
            if existing_settings:
                # 更新设置
                execute_query(
                    "UPDATE system_settings SET company_name = ?, fiscal_start_month = ?, decimal_places = ?, auto_save = ?, income_color = ?, expense_color = ?, profit_color = ? WHERE id = 1",
                    (company_name, fiscal_start_month, decimal_places, auto_save, income_color, expense_color, profit_color)
                )
            else:
                # 插入设置
                execute_query(
                    "INSERT INTO system_settings (id, company_name, fiscal_start_month, decimal_places, auto_save, income_color, expense_color, profit_color) VALUES (1, ?, ?, ?, ?, ?, ?, ?)",
                    (company_name, fiscal_start_month, decimal_places, auto_save, income_color, expense_color, profit_color)
                )
            
            # 记录操作日志
            log_operation(
                self.user_info['id'], 
                'save_settings', 
                "更新了系统设置"
            )
            
            # 显示成功消息
            QMessageBox.information(self, "保存成功", "系统设置已成功保存")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
    
    def select_color(self, button):
        """选择颜色"""
        from PyQt5.QtWidgets import QColorDialog
        
        # 获取当前颜色
        current_color = button.styleSheet().split(':')[-1].strip()
        
        # 打开颜色选择器
        color = QColorDialog.getColor(QColor(current_color), self, "选择颜色")
        
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()}")
    
    # 备份恢复相关方法
    def load_backup_settings(self):
        """加载备份设置"""
        try:
            # 尝试从数据库加载设置
            settings = execute_query("SELECT * FROM system_settings WHERE id = 1", fetch=True)
            
            if settings:
                # 备份目录
                if settings['backup_directory']:
                    self.backup_dir_edit.setText(settings['backup_directory'])
                else:
                    # 默认备份目录
                    default_backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backups")
                    self.backup_dir_edit.setText(default_backup_dir)
                    # 创建默认备份目录
                    if not os.path.exists(default_backup_dir):
                        os.makedirs(default_backup_dir)
                
                # 自动备份频率
                if settings['auto_backup_frequency']:
                    frequency = settings['auto_backup_frequency']
                    if frequency == 'daily':
                        self.auto_backup_combo.setCurrentIndex(1)
                    elif frequency == 'weekly':
                        self.auto_backup_combo.setCurrentIndex(2)
                    elif frequency == 'monthly':
                        self.auto_backup_combo.setCurrentIndex(3)
                
                # 最大备份文件数
                if settings['max_backup_files']:
                    self.max_backups_spin.setValue(int(settings['max_backup_files']))
                    
        except Exception as e:
            print(f"加载备份设置失败: {str(e)}")
            # 使用默认值
            default_backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backups")
            self.backup_dir_edit.setText(default_backup_dir)
    
    def refresh_backup_list(self):
        """刷新备份文件列表"""
        try:
            backup_dir = self.backup_dir_edit.text().strip()
            
            # 清空列表
            self.backup_list.clear()
            
            # 检查备份目录是否存在
            if not os.path.exists(backup_dir):
                return
            
            # 获取所有备份文件
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.endswith('.sqlite') or filename.endswith('.db'):
                    file_path = os.path.join(backup_dir, filename)
                    try:
                        # 获取文件创建时间
                        created_time = os.path.getctime(file_path)
                        backup_files.append((created_time, filename, file_path))
                    except Exception:
                        continue
            
            # 按创建时间排序（最新的在前）
            backup_files.sort(reverse=True)
            
            # 添加到列表
            for created_time, filename, file_path in backup_files:
                # 格式化时间
                time_str = datetime.fromtimestamp(created_time).strftime('%Y-%m-%d %H:%M:%S')
                
                # 获取文件大小
                file_size = os.path.getsize(file_path) / 1024  # KB
                size_str = f"{file_size:.2f} KB"
                
                # 创建列表项
                item = QListWidgetItem(f"{filename}  ({time_str}) - {size_str}")
                item.setData(Qt.UserRole, file_path)  # 存储文件路径
                self.backup_list.addItem(item)
                
        except Exception as e:
            print(f"刷新备份列表失败: {str(e)}")
    
    def select_backup_directory(self):
        """选择备份目录"""
        from PyQt5.QtWidgets import QFileDialog
        
        # 打开目录选择器
        directory = QFileDialog.getExistingDirectory(self, "选择备份目录", self.backup_dir_edit.text())
        
        if directory:
            self.backup_dir_edit.setText(directory)
            # 保存备份目录设置
            self.save_backup_settings()
            # 刷新备份列表
            self.refresh_backup_list()
    
    def save_backup_settings(self):
        """保存备份设置"""
        try:
            # 获取表单数据
            backup_directory = self.backup_dir_edit.text().strip()
            auto_backup_index = self.auto_backup_combo.currentIndex()
            max_backups = self.max_backups_spin.value()
            
            # 转换自动备份频率
            auto_backup_frequency = 'none'
            if auto_backup_index == 1:
                auto_backup_frequency = 'daily'
            elif auto_backup_index == 2:
                auto_backup_frequency = 'weekly'
            elif auto_backup_index == 3:
                auto_backup_frequency = 'monthly'
            
            # 创建备份目录
            if not os.path.exists(backup_directory):
                os.makedirs(backup_directory)
            
            # 检查设置是否存在
            existing_settings = execute_query("SELECT id FROM system_settings WHERE id = 1", fetch=True)
            
            if existing_settings:
                # 更新设置
                execute_query(
                    "UPDATE system_settings SET backup_directory = ?, auto_backup_frequency = ?, max_backup_files = ? WHERE id = 1",
                    (backup_directory, auto_backup_frequency, max_backups)
                )
            else:
                # 插入设置
                execute_query(
                    "INSERT INTO system_settings (id, backup_directory, auto_backup_frequency, max_backup_files) VALUES (1, ?, ?, ?)",
                    (backup_directory, auto_backup_frequency, max_backups)
                )
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存备份设置失败: {str(e)}")
    
    def backup_now(self):
        """立即备份"""
        try:
            # 获取备份目录
            backup_dir = self.backup_dir_edit.text().strip()
            
            # 检查备份目录
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # 创建备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"financial_backup_{timestamp}.sqlite"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # 获取当前数据库路径
            from src.database.db_manager import DATABASE_PATH
            
            # 复制数据库文件
            shutil.copy2(DATABASE_PATH, backup_path)
            
            # 记录操作日志
            log_operation(
                self.user_info['id'], 
                'backup_database', 
                f"创建了数据库备份: {backup_filename}"
            )
            
            # 清理旧备份
            self.clean_old_backups()
            
            # 显示成功消息
            QMessageBox.information(self, "备份成功", f"数据库已成功备份到:\n{backup_path}")
            
            # 刷新备份列表
            self.refresh_backup_list()
            
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"数据库备份失败: {str(e)}")
    
    def restore_backup(self):
        """恢复备份"""
        try:
            # 获取选中的备份文件
            selected_items = self.backup_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "操作错误", "请先选择要恢复的备份文件")
                return
            
            # 获取备份文件路径
            backup_path = selected_items[0].data(Qt.UserRole)
            
            # 确认恢复
            reply = QMessageBox.question(
                self, 
                "确认恢复", 
                "恢复备份将覆盖当前数据库，所有未备份的数据将丢失。\n确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 关闭当前应用并恢复数据库
                # 这里简化处理，实际应用可能需要更复杂的逻辑
                # 比如先关闭数据库连接，再恢复文件，然后重启应用
                
                # 显示提示
                QMessageBox.information(
                    self, 
                    "恢复提示", 
                    "请关闭应用并手动将备份文件复制到数据库位置。\n当前数据库位置:",
                )
                
                # 记录操作日志
                log_operation(
                    self.user_info['id'], 
                    'restore_database', 
                    f"恢复了数据库备份: {os.path.basename(backup_path)}"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "恢复失败", f"数据库恢复失败: {str(e)}")
    
    def clean_backups(self):
        """清理备份"""
        try:
            # 获取备份目录和最大备份数
            backup_dir = self.backup_dir_edit.text().strip()
            max_backups = self.max_backups_spin.value()
            
            # 检查备份目录是否存在
            if not os.path.exists(backup_dir):
                return
            
            # 获取所有备份文件
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.endswith('.sqlite') or filename.endswith('.db'):
                    file_path = os.path.join(backup_dir, filename)
                    try:
                        # 获取文件创建时间
                        created_time = os.path.getctime(file_path)
                        backup_files.append((created_time, file_path))
                    except Exception:
                        continue
            
            # 按创建时间排序（最新的在前）
            backup_files.sort(reverse=True)
            
            # 删除超出数量的备份文件
            files_to_delete = backup_files[max_backups:]
            deleted_count = 0
            
            for _, file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception:
                    continue
            
            # 显示结果
            if deleted_count > 0:
                QMessageBox.information(self, "清理完成", f"已清理 {deleted_count} 个旧备份文件")
            else:
                QMessageBox.information(self, "清理完成", "没有需要清理的旧备份文件")
            
            # 刷新备份列表
            self.refresh_backup_list()
            
        except Exception as e:
            QMessageBox.critical(self, "清理失败", f"备份清理失败: {str(e)}")
    
    def clean_old_backups(self):
        """自动清理旧备份（内部方法）"""
        try:
            # 获取备份目录和最大备份数
            backup_dir = self.backup_dir_edit.text().strip()
            max_backups = self.max_backups_spin.value()
            
            # 检查备份目录是否存在
            if not os.path.exists(backup_dir):
                return
            
            # 获取所有备份文件
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.endswith('.sqlite') or filename.endswith('.db'):
                    file_path = os.path.join(backup_dir, filename)
                    try:
                        # 获取文件创建时间
                        created_time = os.path.getctime(file_path)
                        backup_files.append((created_time, file_path))
                    except Exception:
                        continue
            
            # 按创建时间排序（最新的在前）
            backup_files.sort(reverse=True)
            
            # 删除超出数量的备份文件
            files_to_delete = backup_files[max_backups:]
            for _, file_path in files_to_delete:
                try:
                    os.remove(file_path)
                except Exception:
                    continue
                    
        except Exception:
            # 静默失败，不影响主流程
            pass


if __name__ == "__main__":
    # 测试代码
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    user_info = {'id': 1, 'username': 'admin', 'role': 'admin'}
    settings_widget = SettingsWidget(user_info)
    settings_widget.show()
    sys.exit(app.exec_())