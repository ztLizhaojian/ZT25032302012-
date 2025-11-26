#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
账户管理组件
实现账户的增删改查功能
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox, 
    QTableView, QHeaderView, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QGroupBox, QMessageBox, QDialog, QFormLayout
)
from PyQt5.QtGui import QFont, QColor, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据库操作
from src.database.db_manager import execute_query, log_operation


class AccountWidget(QWidget):
    """账户管理组件类"""
    
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.init_ui()
        self.load_accounts()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建账户操作组
        operation_group = QGroupBox("账户操作")
        operation_layout = QHBoxLayout(operation_group)
        operation_layout.setContentsMargins(15, 15, 15, 15)
        operation_layout.setSpacing(10)
        
        # 添加账户按钮
        self.add_button = QPushButton("添加账户")
        self.add_button.setFixedHeight(36)
        self.add_button.setStyleSheet("""
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
        self.add_button.clicked.connect(self.add_account)
        
        # 修改账户按钮
        self.edit_button = QPushButton("修改账户")
        self.edit_button.setFixedHeight(36)
        self.edit_button.setStyleSheet("""
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
        self.edit_button.clicked.connect(self.edit_account)
        
        # 删除账户按钮
        self.delete_button = QPushButton("删除账户")
        self.delete_button.setFixedHeight(36)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
            }
            QPushButton:hover {
                background-color: #bd2130;
            }
        """)
        self.delete_button.clicked.connect(self.delete_account)
        
        # 刷新按钮
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setFixedHeight(36)
        self.refresh_button.setStyleSheet("""
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
        self.refresh_button.clicked.connect(self.load_accounts)
        
        # 添加按钮到操作布局
        operation_layout.addWidget(self.add_button)
        operation_layout.addWidget(self.edit_button)
        operation_layout.addWidget(self.delete_button)
        operation_layout.addWidget(self.refresh_button)
        operation_layout.addStretch()
        
        # 创建账户表格
        self.account_table = QTableView()
        self.account_model = QStandardItemModel()
        self.account_model.setHorizontalHeaderLabels(['ID', '账户名', '余额', '备注'])
        self.account_table.setModel(self.account_model)
        
        # 设置表格属性
        self.account_table.setAlternatingRowColors(True)
        self.account_table.setSelectionBehavior(QTableView.SelectRows)
        self.account_table.setSelectionMode(QTableView.SingleSelection)
        self.account_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.account_table.verticalHeader().setVisible(False)
        self.account_table.setEditTriggers(QTableView.NoEditTriggers)
        
        # 添加到主布局
        main_layout.addWidget(operation_group)
        main_layout.addWidget(self.account_table)
    
    def load_accounts(self):
        """加载账户数据"""
        try:
            # 清空现有数据
            self.account_model.removeRows(0, self.account_model.rowCount())
            
            # 查询账户数据
            query = "SELECT id, name, balance, description FROM accounts ORDER BY id"
            rows = execute_query(query, fetchall=True)
            
            # 填充表格数据
            for row_data in rows:
                items = []
                for i, data in enumerate(row_data):
                    item = QStandardItem(str(data))
                    item.setTextAlignment(Qt.AlignCenter)
                    items.append(item)
                self.account_model.appendRow(items)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载账户数据失败: {str(e)}")
    
    def add_account(self):
        """添加账户"""
        dialog = AccountDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, balance, description = dialog.get_data()
            try:
                # 插入新账户
                query = "INSERT INTO accounts (name, balance, description) VALUES (?, ?, ?)"
                execute_query(query, (name, balance, description), commit=True)
                
                # 记录操作日志
                log_operation(self.user_info['id'], f"添加账户: {name}")
                
                # 刷新数据
                self.load_accounts()
                
                QMessageBox.information(self, "成功", "账户添加成功!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加账户失败: {str(e)}")
    
    def edit_account(self):
        """修改账户"""
        # 获取选中的行
        selected_rows = self.account_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要修改的账户!")
            return
        
        row = selected_rows[0].row()
        account_id = self.account_model.item(row, 0).text()
        account_name = self.account_model.item(row, 1).text()
        account_balance = self.account_model.item(row, 2).text()
        account_description = self.account_model.item(row, 3).text()
        
        # 显示编辑对话框
        dialog = AccountDialog(self, account_name, account_balance, account_description)
        if dialog.exec_() == QDialog.Accepted:
            name, balance, description = dialog.get_data()
            try:
                # 更新账户信息
                query = "UPDATE accounts SET name=?, balance=?, description=? WHERE id=?"
                execute_query(query, (name, balance, description, account_id), commit=True)
                
                # 记录操作日志
                log_operation(self.user_info['id'], f"修改账户: {account_name} -> {name}")
                
                # 刷新数据
                self.load_accounts()
                
                QMessageBox.information(self, "成功", "账户修改成功!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"修改账户失败: {str(e)}")
    
    def delete_account(self):
        """删除账户"""
        # 获取选中的行
        selected_rows = self.account_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的账户!")
            return
        
        row = selected_rows[0].row()
        account_id = self.account_model.item(row, 0).text()
        account_name = self.account_model.item(row, 1).text()
        
        # 确认删除
        reply = QMessageBox.question(self, "确认", f"确定要删除账户 '{account_name}' 吗?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # 删除账户
                query = "DELETE FROM accounts WHERE id=?"
                execute_query(query, (account_id,), commit=True)
                
                # 记录操作日志
                log_operation(self.user_info['id'], f"删除账户: {account_name}")
                
                # 刷新数据
                self.load_accounts()
                
                QMessageBox.information(self, "成功", "账户删除成功!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除账户失败: {str(e)}")


class AccountDialog(QDialog):
    """账户对话框类"""
    
    def __init__(self, parent, name="", balance="", description=""):
        super().__init__(parent)
        self.setWindowTitle("账户信息")
        self.setFixedSize(400, 250)
        self.name = name
        self.balance = balance
        self.description = description
        self.init_ui()
    
    def init_ui(self):
        """初始化对话框界面"""
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 账户名输入
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.name)
        self.name_edit.setPlaceholderText("请输入账户名")
        layout.addRow("账户名:", self.name_edit)
        
        # 余额输入
        self.balance_edit = QLineEdit()
        self.balance_edit.setText(self.balance)
        self.balance_edit.setPlaceholderText("请输入初始余额")
        layout.addRow("余额:", self.balance_edit)
        
        # 备注输入
        self.description_edit = QLineEdit()
        self.description_edit.setText(self.description)
        self.description_edit.setPlaceholderText("请输入备注信息")
        layout.addRow("备注:", self.description_edit)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addRow(button_layout)
        
        # 设置焦点
        self.name_edit.setFocus()
    
    def get_data(self):
        """获取对话框数据"""
        return (
            self.name_edit.text().strip(),
            float(self.balance_edit.text().strip()) if self.balance_edit.text().strip() else 0.0,
            self.description_edit.text().strip()
        )
    
    def accept(self):
        """确认操作"""
        # 验证输入
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "警告", "账户名不能为空!")
            return
        
        try:
            # 验证余额
            balance = self.balance_edit.text().strip()
            if balance:
                float(balance)
        except ValueError:
            QMessageBox.warning(self, "警告", "余额必须是有效的数字!")
            return
        
        super().accept()