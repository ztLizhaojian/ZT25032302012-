#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账务处理组件
实现财务账目录入、查询、修改和删除功能
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox, 
    QDateEdit, QTextEdit, QTableView, QHeaderView, QVBoxLayout, 
    QHBoxLayout, QGridLayout, QGroupBox, QTabWidget, QMessageBox,
    QDialog, QFormLayout, QInputDialog, QSpinBox, QDoubleSpinBox
)
from PyQt5.QtGui import QFont, QColor, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QDate, QSortFilterProxyModel

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据库操作
from src.database.db_manager import execute_query, log_operation


class TransactionWidget(QWidget):
    """账务处理组件类"""
    
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.init_ui()
        self.load_transactions()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建标签页部件
        self.tab_widget = QTabWidget()
        
        # 创建录入标签页
        self.create_entry_tab()
        
        # 创建查询标签页
        self.create_query_tab()
        
        # 添加标签页
        self.tab_widget.addTab(self.entry_widget, "账目录入")
        self.tab_widget.addTab(self.query_widget, "账务查询")
        
        # 添加到主布局
        main_layout.addWidget(self.tab_widget)
    
    def create_entry_tab(self):
        """创建账目录入标签页"""
        self.entry_widget = QWidget()
        entry_layout = QVBoxLayout(self.entry_widget)
        entry_layout.setSpacing(15)
        
        # 创建录入表单
        form_group = QGroupBox("账务信息录入")
        form_layout = QGridLayout(form_group)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)
        form_layout.setColumnStretch(0, 1)
        form_layout.setColumnStretch(1, 2)
        
        # 交易类型
        form_layout.addWidget(QLabel("交易类型:"), 0, 0)
        self.transaction_type_combo = QComboBox()
        self.transaction_type_combo.addItems(["收入", "支出", "转账", "借贷"])
        self.transaction_type_combo.currentTextChanged.connect(self.on_transaction_type_changed)
        form_layout.addWidget(self.transaction_type_combo, 0, 1)
        
        # 账户
        form_layout.addWidget(QLabel("账户:"), 1, 0)
        self.account_combo = QComboBox()
        self.load_accounts()
        form_layout.addWidget(self.account_combo, 1, 1)
        
        # 对方账户（仅转账类型显示）
        form_layout.addWidget(QLabel("对方账户:"), 2, 0)
        self.target_account_combo = QComboBox()
        self.target_account_combo.addItems([account for account in self.get_account_names()])
        form_layout.addWidget(self.target_account_combo, 2, 1)
        
        # 分类
        form_layout.addWidget(QLabel("分类:"), 3, 0)
        self.category_combo = QComboBox()
        self.load_categories()
        form_layout.addWidget(self.category_combo, 3, 1)
        
        # 金额
        form_layout.addWidget(QLabel("金额:"), 4, 0)
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("请输入金额")
        form_layout.addWidget(self.amount_edit, 4, 1)
        
        # 交易日期
        form_layout.addWidget(QLabel("交易日期:"), 5, 0)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addWidget(self.date_edit, 5, 1)
        
        # 描述
        form_layout.addWidget(QLabel("描述:"), 6, 0, Qt.AlignTop)
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("请输入交易描述")
        self.description_edit.setMaximumHeight(80)
        form_layout.addWidget(self.description_edit, 6, 1)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_button = QPushButton("保存")
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
        self.save_button.clicked.connect(self.save_transaction)
        
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
        self.reset_button.clicked.connect(self.reset_form)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reset_button)
        
        # 添加到表单布局
        form_layout.addLayout(button_layout, 7, 0, 1, 2)
        
        # 添加到录入标签页布局
        entry_layout.addWidget(form_group)
        
        # 初始化时根据交易类型显示/隐藏控件
        self.on_transaction_type_changed(self.transaction_type_combo.currentText())
    
    def create_query_tab(self):
        """创建账务查询标签页"""
        self.query_widget = QWidget()
        query_layout = QVBoxLayout(self.query_widget)
        query_layout.setSpacing(15)
        
        # 创建查询条件组
        filter_group = QGroupBox("查询条件")
        filter_layout = QGridLayout(filter_group)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(10)
        
        # 账户筛选
        filter_layout.addWidget(QLabel("账户:"), 0, 0)
        self.filter_account_combo = QComboBox()
        self.filter_account_combo.addItem("全部")
        self.filter_account_combo.addItems(self.get_account_names())
        filter_layout.addWidget(self.filter_account_combo, 0, 1)
        
        # 类型筛选
        filter_layout.addWidget(QLabel("类型:"), 0, 2)
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(["全部", "收入", "支出", "转账", "借贷"])
        filter_layout.addWidget(self.filter_type_combo, 0, 3)
        
        # 分类筛选
        filter_layout.addWidget(QLabel("分类:"), 1, 0)
        self.filter_category_combo = QComboBox()
        self.filter_category_combo.addItem("全部")
        self.filter_category_combo.addItems(self.get_category_names())
        filter_layout.addWidget(self.filter_category_combo, 1, 1)
        
        # 日期范围筛选
        filter_layout.addWidget(QLabel("开始日期:"), 1, 2)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.start_date_edit, 1, 3)
        
        filter_layout.addWidget(QLabel("结束日期:"), 2, 0)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        filter_layout.addWidget(self.end_date_edit, 2, 1)
        
        # 查询按钮
        self.search_button = QPushButton("查询")
        self.search_button.setFixedHeight(36)
        self.search_button.setStyleSheet("""
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
        self.search_button.clicked.connect(self.search_transactions)
        
        self.clear_filter_button = QPushButton("清除筛选")
        self.clear_filter_button.setFixedHeight(36)
        self.clear_filter_button.setStyleSheet("""
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
        self.clear_filter_button.clicked.connect(self.clear_filters)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.clear_filter_button)
        
        filter_layout.addLayout(button_layout, 2, 2, 1, 2)
        
        # 创建表格视图
        self.transaction_table = QTableView()
        self.transaction_table.setAlternatingRowColors(True)
        self.transaction_table.setSortingEnabled(True)
        self.transaction_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transaction_table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 5px;
                font-family: SimHei;
                font-weight: bold;
            }
        """)
        
        # 创建表格模型
        self.create_table_model()
        
        # 创建操作按钮
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)
        
        self.edit_button = QPushButton("修改")
        self.edit_button.setFixedHeight(36)
        self.edit_button.setStyleSheet("""
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
        """)
        self.edit_button.clicked.connect(self.edit_transaction)
        
        self.delete_button = QPushButton("删除")
        self.delete_button.setFixedHeight(36)
        self.delete_button.setStyleSheet("""
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
        """)
        self.delete_button.clicked.connect(self.delete_transaction)
        
        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.delete_button)
        action_layout.addStretch(1)
        
        # 添加到查询标签页布局
        query_layout.addWidget(filter_group)
        query_layout.addWidget(self.transaction_table)
        query_layout.addLayout(action_layout)
    
    def create_table_model(self):
        """创建表格模型"""
        # 创建模型
        self.model = QStandardItemModel(0, 8)
        self.model.setHorizontalHeaderLabels([
            "ID", "交易类型", "账户", "分类", 
            "金额", "交易日期", "描述", "创建时间"
        ])
        
        # 创建代理模型用于排序和筛选
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setDynamicSortFilter(True)
        
        # 设置表格视图的模型
        self.transaction_table.setModel(self.proxy_model)
        
        # 隐藏ID列
        self.transaction_table.hideColumn(0)
    
    def load_accounts(self):
        """加载账户列表"""
        try:
            accounts = execute_query("SELECT name FROM accounts ORDER BY name", fetchall=True)
            self.account_combo.clear()
            for account in accounts:
                self.account_combo.addItem(account['name'])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载账户失败: {str(e)}")
    
    def get_account_names(self):
        """获取账户名称列表"""
        try:
            accounts = execute_query("SELECT name FROM accounts ORDER BY name", fetchall=True)
            return [account['name'] for account in accounts]
        except:
            return []
    
    def load_categories(self):
        """加载分类列表"""
        try:
            # 根据交易类型加载对应的分类
            transaction_type = self.transaction_type_combo.currentText()
            if transaction_type == "收入":
                categories = execute_query(
                    "SELECT name FROM categories WHERE type = 'income' ORDER BY name", 
                    fetchall=True
                )
            else:
                categories = execute_query(
                    "SELECT name FROM categories WHERE type = 'expense' ORDER BY name", 
                    fetchall=True
                )
            
            self.category_combo.clear()
            for category in categories:
                self.category_combo.addItem(category['name'])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载分类失败: {str(e)}")
    
    def get_category_names(self):
        """获取分类名称列表"""
        try:
            categories = execute_query("SELECT name FROM categories ORDER BY name", fetchall=True)
            return [category['name'] for category in categories]
        except:
            return []
    
    def on_transaction_type_changed(self, transaction_type):
        """交易类型变化时的处理"""
        # 转账类型显示对方账户，其他类型隐藏
        if transaction_type == "转账":
            self.target_account_combo.parent().show()
            # 转账类型不需要分类
            self.category_combo.parent().hide()
        else:
            self.target_account_combo.parent().hide()
            self.category_combo.parent().show()
            # 重新加载对应类型的分类
            self.load_categories()
    
    def reset_form(self):
        """重置表单"""
        self.transaction_type_combo.setCurrentIndex(0)
        self.amount_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.description_edit.clear()
        self.load_accounts()
        self.load_categories()
    
    def save_transaction(self):
        """保存交易记录"""
        try:
            # 获取表单数据
            transaction_type = self.transaction_type_combo.currentText()
            account_name = self.account_combo.currentText()
            amount_text = self.amount_edit.text().strip()
            transaction_date = self.date_edit.date().toString("yyyy-MM-dd")
            description = self.description_edit.toPlainText().strip()
            
            # 验证输入
            if not amount_text:
                QMessageBox.warning(self, "输入错误", "请输入金额")
                self.amount_edit.setFocus()
                return
            
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError("金额必须大于0")
            except ValueError as e:
                QMessageBox.warning(self, "输入错误", f"无效的金额: {str(e)}")
                self.amount_edit.setFocus()
                return
            
            # 获取账户ID
            account = execute_query(
                "SELECT id FROM accounts WHERE name = ?", 
                (account_name,), 
                fetch=True
            )
            
            if transaction_type == "转账":
                # 转账类型处理
                target_account_name = self.target_account_combo.currentText()
                
                # 不能转账给自己
                if account_name == target_account_name:
                    QMessageBox.warning(self, "操作错误", "不能转账给自己")
                    return
                
                # 获取对方账户ID
                target_account = execute_query(
                    "SELECT id FROM accounts WHERE name = ?", 
                    (target_account_name,), 
                    fetch=True
                )
                
                # 保存转出记录
                execute_query(
                    """
                    INSERT INTO transactions 
                    (account_id, category_id, type, amount, transaction_date, description, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (account['id'], None, "支出", amount, transaction_date, 
                     f"转账到{target_account_name} - {description}", self.user_info['id'])
                )
                
                # 保存转入记录
                execute_query(
                    """
                    INSERT INTO transactions 
                    (account_id, category_id, type, amount, transaction_date, description, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (target_account['id'], None, "收入", amount, transaction_date, 
                     f"从{account_name}转入 - {description}", self.user_info['id'])
                )
                
            else:
                # 普通交易处理
                category_name = self.category_combo.currentText()
                
                # 获取分类ID
                category = execute_query(
                    "SELECT id FROM categories WHERE name = ?", 
                    (category_name,), 
                    fetch=True
                )
                
                # 保存交易记录
                execute_query(
                    """
                    INSERT INTO transactions 
                    (account_id, category_id, type, amount, transaction_date, description, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (account['id'], category['id'], transaction_type, amount, 
                     transaction_date, description, self.user_info['id'])
                )
            
            # 记录操作日志
            log_operation(
                self.user_info['id'], 
                'create_transaction', 
                f"创建了{transaction_type}类型的交易记录，金额: {amount}"
            )
            
            # 显示成功消息
            QMessageBox.information(self, "保存成功", "交易记录已成功保存")
            
            # 重置表单
            self.reset_form()
            
            # 刷新查询表格
            if self.tab_widget.currentWidget() == self.query_widget:
                self.load_transactions()
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存交易记录失败: {str(e)}")
    
    def load_transactions(self):
        """加载交易记录到表格"""
        try:
            # 查询所有交易记录
            transactions = execute_query(
                """
                SELECT t.id, t.type, a.name as account_name, 
                       c.name as category_name, t.amount, 
                       t.transaction_date, t.description, t.created_at
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN categories c ON t.category_id = c.id
                ORDER BY t.transaction_date DESC
                """,
                fetchall=True
            )
            
            # 清空表格
            self.model.setRowCount(0)
            
            # 添加数据到表格
            for transaction in transactions:
                row_items = []
                
                # ID
                row_items.append(QStandardItem(str(transaction['id'])))
                row_items[-1].setEditable(False)
                
                # 交易类型
                row_items.append(QStandardItem(transaction['type']))
                row_items[-1].setEditable(False)
                
                # 账户
                row_items.append(QStandardItem(transaction['account_name']))
                row_items[-1].setEditable(False)
                
                # 分类
                category_name = transaction['category_name'] if transaction['category_name'] else ""
                row_items.append(QStandardItem(category_name))
                row_items[-1].setEditable(False)
                
                # 金额
                amount_item = QStandardItem(f"{transaction['amount']:.2f}")
                amount_item.setEditable(False)
                # 根据类型设置金额颜色
                if transaction['type'] == "收入":
                    amount_item.setForeground(QColor("#28a745"))
                elif transaction['type'] == "支出":
                    amount_item.setForeground(QColor("#dc3545"))
                row_items.append(amount_item)
                
                # 交易日期
                row_items.append(QStandardItem(transaction['transaction_date']))
                row_items[-1].setEditable(False)
                
                # 描述
                description = transaction['description'] if transaction['description'] else ""
                row_items.append(QStandardItem(description))
                row_items[-1].setEditable(False)
                
                # 创建时间
                row_items.append(QStandardItem(transaction['created_at']))
                row_items[-1].setEditable(False)
                
                # 添加行到模型
                self.model.appendRow(row_items)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载交易记录失败: {str(e)}")
    
    def search_transactions(self):
        """搜索交易记录"""
        try:
            # 获取筛选条件
            account_name = self.filter_account_combo.currentText()
            transaction_type = self.filter_type_combo.currentText()
            category_name = self.filter_category_combo.currentText()
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
            
            # 构建查询SQL
            sql = """
            SELECT t.id, t.type, a.name as account_name, 
                   c.name as category_name, t.amount, 
                   t.transaction_date, t.description, t.created_at
            FROM transactions t
            LEFT JOIN accounts a ON t.account_id = a.id
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE t.transaction_date BETWEEN ? AND ?
            """
            
            params = [start_date, end_date]
            
            # 添加账户筛选条件
            if account_name != "全部":
                sql += " AND a.name = ?"
                params.append(account_name)
            
            # 添加类型筛选条件
            if transaction_type != "全部":
                sql += " AND t.type = ?"
                params.append(transaction_type)
            
            # 添加分类筛选条件
            if category_name != "全部":
                sql += " AND c.name = ?"
                params.append(category_name)
            
            sql += " ORDER BY t.transaction_date DESC"
            
            # 执行查询
            transactions = execute_query(sql, params, fetchall=True)
            
            # 清空表格
            self.model.setRowCount(0)
            
            # 添加数据到表格
            for transaction in transactions:
                row_items = []
                
                # ID
                row_items.append(QStandardItem(str(transaction['id'])))
                row_items[-1].setEditable(False)
                
                # 交易类型
                row_items.append(QStandardItem(transaction['type']))
                row_items[-1].setEditable(False)
                
                # 账户
                row_items.append(QStandardItem(transaction['account_name']))
                row_items[-1].setEditable(False)
                
                # 分类
                category_name = transaction['category_name'] if transaction['category_name'] else ""
                row_items.append(QStandardItem(category_name))
                row_items[-1].setEditable(False)
                
                # 金额
                amount_item = QStandardItem(f"{transaction['amount']:.2f}")
                amount_item.setEditable(False)
                # 根据类型设置金额颜色
                if transaction['type'] == "收入":
                    amount_item.setForeground(QColor("#28a745"))
                elif transaction['type'] == "支出":
                    amount_item.setForeground(QColor("#dc3545"))
                row_items.append(amount_item)
                
                # 交易日期
                row_items.append(QStandardItem(transaction['transaction_date']))
                row_items[-1].setEditable(False)
                
                # 描述
                description = transaction['description'] if transaction['description'] else ""
                row_items.append(QStandardItem(description))
                row_items[-1].setEditable(False)
                
                # 创建时间
                row_items.append(QStandardItem(transaction['created_at']))
                row_items[-1].setEditable(False)
                
                # 添加行到模型
                self.model.appendRow(row_items)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索交易记录失败: {str(e)}")
    
    def clear_filters(self):
        """清除筛选条件"""
        self.filter_account_combo.setCurrentIndex(0)
        self.filter_type_combo.setCurrentIndex(0)
        self.filter_category_combo.setCurrentIndex(0)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_edit.setDate(QDate.currentDate())
        
        # 重新加载所有数据
        self.load_transactions()
    
    def edit_transaction(self):
        """修改交易记录"""
        # 获取选中的行
        selected_rows = self.transaction_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "操作错误", "请先选择要修改的交易记录")
            return
        
        # 只处理第一行
        index = selected_rows[0]
        transaction_id = self.proxy_model.data(self.proxy_model.index(index.row(), 0))
        
        # 获取交易记录详情
        try:
            transaction = execute_query(
                """
                SELECT t.id, t.type, t.account_id, t.category_id, 
                       t.amount, t.transaction_date, t.description,
                       a.name as account_name, c.name as category_name
                FROM transactions t
                LEFT JOIN accounts a ON t.account_id = a.id
                LEFT JOIN categories c ON t.category_id = c.id
                WHERE t.id = ?
                """,
                (transaction_id,),
                fetch=True
            )
            
            # 创建编辑对话框
            edit_dialog = QDialog(self)
            edit_dialog.setWindowTitle("修改交易记录")
            edit_dialog.resize(500, 400)
            
            # 创建对话框布局
            dialog_layout = QVBoxLayout(edit_dialog)
            
            # 创建表单布局
            form_layout = QFormLayout()
            
            # 交易类型
            type_combo = QComboBox()
            type_combo.addItems(["收入", "支出", "转账", "借贷"])
            type_combo.setCurrentText(transaction['type'])
            form_layout.addRow("交易类型:", type_combo)
            
            # 账户
            account_combo = QComboBox()
            accounts = execute_query("SELECT id, name FROM accounts ORDER BY name", fetchall=True)
            account_names = [account['name'] for account in accounts]
            account_combo.addItems(account_names)
            account_combo.setCurrentText(transaction['account_name'])
            form_layout.addRow("账户:", account_combo)
            
            # 分类
            category_combo = QComboBox()
            categories = execute_query(
                f"SELECT id, name FROM categories WHERE type = '{transaction['type']}' ORDER BY name", 
                fetchall=True
            )
            category_names = [category['name'] for category in categories]
            category_combo.addItems(category_names)
            if transaction['category_name']:
                category_combo.setCurrentText(transaction['category_name'])
            form_layout.addRow("分类:", category_combo)
            
            # 金额
            amount_edit = QLineEdit(str(transaction['amount']))
            form_layout.addRow("金额:", amount_edit)
            
            # 交易日期
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_from_str = QDate.fromString(transaction['transaction_date'], "yyyy-MM-dd")
            date_edit.setDate(date_from_str)
            form_layout.addRow("交易日期:", date_edit)
            
            # 描述
            description_edit = QTextEdit(transaction['description'] if transaction['description'] else "")
            description_edit.setMinimumHeight(80)
            form_layout.addRow("描述:", description_edit)
            
            # 创建按钮布局
            button_layout = QHBoxLayout()
            
            save_button = QPushButton("保存")
            save_button.clicked.connect(lambda: self.save_edit(edit_dialog, transaction_id, {
                'type': type_combo.currentText(),
                'account_name': account_combo.currentText(),
                'category_name': category_combo.currentText() if category_combo.count() > 0 else None,
                'amount': amount_edit.text(),
                'transaction_date': date_edit.date().toString("yyyy-MM-dd"),
                'description': description_edit.toPlainText()
            }))
            
            cancel_button = QPushButton("取消")
            cancel_button.clicked.connect(edit_dialog.reject)
            
            button_layout.addWidget(save_button)
            button_layout.addWidget(cancel_button)
            
            # 添加到对话框布局
            dialog_layout.addLayout(form_layout)
            dialog_layout.addLayout(button_layout)
            
            # 显示对话框
            if edit_dialog.exec_():
                # 刷新表格
                self.search_transactions()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"修改交易记录失败: {str(e)}")
    
    def save_edit(self, dialog, transaction_id, data):
        """保存修改后的交易记录"""
        try:
            # 验证金额
            try:
                amount = float(data['amount'].strip())
                if amount <= 0:
                    raise ValueError("金额必须大于0")
            except ValueError as e:
                QMessageBox.warning(self, "输入错误", f"无效的金额: {str(e)}")
                return
            
            # 获取账户ID
            account = execute_query(
                "SELECT id FROM accounts WHERE name = ?", 
                (data['account_name'],), 
                fetch=True
            )
            
            # 获取分类ID
            category_id = None
            if data['category_name']:
                category = execute_query(
                    "SELECT id FROM categories WHERE name = ?", 
                    (data['category_name'],), 
                    fetch=True
                )
                category_id = category['id']
            
            # 更新交易记录
            execute_query(
                """
                UPDATE transactions 
                SET account_id = ?, category_id = ?, type = ?, amount = ?, 
                    transaction_date = ?, description = ?, updated_at = ?
                WHERE id = ?
                """,
                (account['id'], category_id, data['type'], amount, 
                 data['transaction_date'], data['description'], 
                 datetime.now().strftime('%Y-%m-%d %H:%M:%S'), transaction_id)
            )
            
            # 记录操作日志
            log_operation(
                self.user_info['id'], 
                'update_transaction', 
                f"修改了交易记录 ID: {transaction_id}"
            )
            
            # 关闭对话框
            dialog.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存修改失败: {str(e)}")
    
    def delete_transaction(self):
        """删除交易记录"""
        # 获取选中的行
        selected_rows = self.transaction_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "操作错误", "请先选择要删除的交易记录")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除选中的 {len(selected_rows)} 条交易记录吗？\n此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 删除选中的记录
                for index in selected_rows:
                    transaction_id = self.proxy_model.data(self.proxy_model.index(index.row(), 0))
                    
                    # 删除交易记录
                    execute_query(
                        "DELETE FROM transactions WHERE id = ?", 
                        (transaction_id,)
                    )
                    
                    # 记录操作日志
                    log_operation(
                        self.user_info['id'], 
                        'delete_transaction', 
                        f"删除了交易记录 ID: {transaction_id}"
                    )
                
                # 刷新表格
                self.search_transactions()
                
                # 显示成功消息
                QMessageBox.information(self, "删除成功", f"已成功删除 {len(selected_rows)} 条交易记录")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除交易记录失败: {str(e)}")


if __name__ == "__main__":
    # 用于测试交易处理组件
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置应用程序字体
    font = QFont("SimHei", 9)
    app.setFont(font)
    
    # 创建用户信息（用于测试）
    test_user = {
        'id': 1,
        'username': 'admin',
        'fullname': '系统管理员',
        'role': 'admin'
    }
    
    # 创建并显示交易处理组件
    widget = TransactionWidget(test_user)
    widget.setWindowTitle("账务处理测试")
    widget.resize(800, 600)
    widget.show()
    
    sys.exit(app.exec_())