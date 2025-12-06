#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分类管理组件
实现财务分类的增删改查功能
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


class CategoryWidget(QWidget):
    """分类管理组件类"""
    
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.init_ui()
        self.load_categories()
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建分类操作组
        operation_group = QGroupBox("分类操作")
        operation_layout = QHBoxLayout(operation_group)
        operation_layout.setContentsMargins(15, 15, 15, 15)
        operation_layout.setSpacing(10)
        
        # 添加分类按钮
        self.add_button = QPushButton("添加分类")
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
        self.add_button.clicked.connect(self.add_category)
        
        # 修改分类按钮
        self.edit_button = QPushButton("修改分类")
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
        self.edit_button.clicked.connect(self.edit_category)
        
        # 删除分类按钮
        self.delete_button = QPushButton("删除分类")
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
        self.delete_button.clicked.connect(self.delete_category)
        
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
        self.refresh_button.clicked.connect(self.load_categories)
        
        # 添加按钮到操作布局
        operation_layout.addWidget(self.add_button)
        operation_layout.addWidget(self.edit_button)
        operation_layout.addWidget(self.delete_button)
        operation_layout.addWidget(self.refresh_button)
        operation_layout.addStretch()
        
        # 创建分类表格
        self.category_table = QTableView()
        self.category_model = QStandardItemModel()
        self.category_model.setHorizontalHeaderLabels(['ID', '分类名', '类型', '备注'])
        self.category_table.setModel(self.category_model)
        
        # 设置表格属性
        self.category_table.setAlternatingRowColors(True)
        self.category_table.setSelectionBehavior(QTableView.SelectRows)
        self.category_table.setSelectionMode(QTableView.SingleSelection)
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.category_table.verticalHeader().setVisible(False)
        self.category_table.setEditTriggers(QTableView.NoEditTriggers)
        
        # 添加到主布局
        main_layout.addWidget(operation_group)
        main_layout.addWidget(self.category_table)
    
    def load_categories(self):
        """加载分类数据"""
        try:
            # 清空现有数据
            self.category_model.removeRows(0, self.category_model.rowCount())
            
            # 查询分类数据
            query = "SELECT id, name, category_type, description FROM categories ORDER BY id"
            rows = execute_query(query, fetch_all=True)
            
            # 填充表格数据
            for row_data in rows:
                items = []
                # 按顺序获取需要的字段值
                items.append(QStandardItem(str(row_data['id'])))
                items.append(QStandardItem(str(row_data['name'])))
                items.append(QStandardItem(str(row_data['category_type'])))
                items.append(QStandardItem(str(row_data['description'])))
                # 设置文本居中
                for item in items:
                    item.setTextAlignment(Qt.AlignCenter)
                self.category_model.appendRow(items)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载分类数据失败: {str(e)}")
    
    def add_category(self):
        """添加分类"""
        dialog = CategoryDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, category_type, description = dialog.get_data()
            try:
                # 插入新分类
                query = "INSERT INTO categories (name, category_type, description) VALUES (?, ?, ?)"
                execute_query(query, (name, category_type, description))
                
                # 记录操作日志
                log_operation(self.user_info['id'], "添加分类", f"添加了分类: {name}")
                
                # 刷新数据
                self.load_categories()
                
                QMessageBox.information(self, "成功", "分类添加成功!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加分类失败: {str(e)}")
    
    def edit_category(self):
        """修改分类"""
        # 获取选中的行
        selected_rows = self.category_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要修改的分类!")
            return
        
        row = selected_rows[0].row()
        category_id = self.category_model.item(row, 0).text()
        category_name = self.category_model.item(row, 1).text()
        category_type = self.category_model.item(row, 2).text()
        category_description = self.category_model.item(row, 3).text()
        
        # 显示编辑对话框
        dialog = CategoryDialog(self, category_name, category_type, category_description)
        if dialog.exec_() == QDialog.Accepted:
            name, category_type, description = dialog.get_data()
            try:
                # 更新分类信息
                query = "UPDATE categories SET name=?, category_type=?, description=? WHERE id=?"
                execute_query(query, (name, category_type, description, category_id))
                
                # 记录操作日志
                log_operation(self.user_info['id'], "修改分类", f"修改分类: {category_name} -> {name}")
                
                # 刷新数据
                self.load_categories()
                
                QMessageBox.information(self, "成功", "分类修改成功!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"修改分类失败: {str(e)}")
    
    def delete_category(self):
        """删除分类"""
        # 获取选中的行
        selected_rows = self.category_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的分类!")
            return
        
        row = selected_rows[0].row()
        category_id = self.category_model.item(row, 0).text()
        category_name = self.category_model.item(row, 1).text()
        
        # 确认删除
        reply = QMessageBox.question(self, "确认", f"确定要删除分类 '{category_name}' 吗?", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # 删除分类
                query = "DELETE FROM categories WHERE id=?"
                execute_query(query, (category_id,))
                
                # 记录操作日志
                log_operation(self.user_info['id'], "删除分类", f"删除了分类: {category_name}")
                
                # 刷新数据
                self.load_categories()
                
                QMessageBox.information(self, "成功", "分类删除成功!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除分类失败: {str(e)}")


class CategoryDialog(QDialog):
    """分类对话框类"""
    
    def __init__(self, parent, name="", category_type="", description=""):
        super().__init__(parent)
        self.setWindowTitle("分类信息")
        self.setFixedSize(400, 250)
        self.name = name
        self.category_type = category_type
        self.description = description
        self.init_ui()
    
    def init_ui(self):
        """初始化对话框界面"""
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 分类名输入
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.name)
        self.name_edit.setPlaceholderText("请输入分类名")
        layout.addRow("分类名:", self.name_edit)
        
        # 类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["收入", "支出"])
        if self.category_type == "收入":
            self.type_combo.setCurrentIndex(0)
        elif self.category_type == "支出":
            self.type_combo.setCurrentIndex(1)
        layout.addRow("类型:", self.type_combo)
        
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
            self.type_combo.currentText(),
            self.description_edit.text().strip()
        )
    
    def accept(self):
        """确认操作"""
        # 验证输入
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "警告", "分类名不能为空!")
            return
        
        super().accept()