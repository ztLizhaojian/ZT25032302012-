#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理界面组件
实现用户列表、添加、编辑、删除和权限管理功能
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入PyQt5模块
try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
        QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox, QGroupBox, QLabel,
        QHeaderView, QCheckBox, QAction, QMenu, QInputDialog, QMessageBox, QDateTimeEdit,
        QTabWidget, QSplitter, QFrame, QGridLayout, QSizePolicy
    )
    from PyQt5.QtCore import Qt, QDateTime, pyqtSignal, QSortFilterProxyModel
    from PyQt5.QtGui import QFont, QIcon, QColor, QBrush
    from PyQt5 import QtCore
    
    # 添加中文显示支持
    QtCore.QTextCodec.setCodecForLocale(QtCore.QTextCodec.codecForName("UTF-8"))
    
    PYQT5_AVAILABLE = True
except ImportError as e:
    logging.error(f"导入PyQt5模块失败: {str(e)}")
    PYQT5_AVAILABLE = False

# 导入控制器和模型
try:
    from src.controllers.auth_controller import auth_controller
    from src.models.user import user_model
    from src.controllers.settings_controller import settings_controller
    CONTROLLERS_AVAILABLE = True
except ImportError as e:
    logging.error(f"导入控制器和模型失败: {str(e)}")
    CONTROLLERS_AVAILABLE = False


class UserManagementWidget(QWidget):
    """
    用户管理界面组件
    """
    
    # 信号定义
    user_updated = pyqtSignal()  # 用户信息更新信号
    user_deleted = pyqtSignal(int)  # 用户删除信号，传递用户ID
    
    def __init__(self, current_user_id=None, parent=None):
        """
        初始化用户管理界面
        
        Args:
            current_user_id: 当前登录用户ID
            parent: 父组件
        """
        super().__init__(parent)
        
        # 设置属性
        self.current_user_id = current_user_id
        self.users_data = []  # 存储用户数据
        
        # 检查依赖
        if not PYQT5_AVAILABLE:
            QMessageBox.critical(self, "错误", "无法加载PyQt5库，请安装PyQt5后重试。")
            return
        
        if not CONTROLLERS_AVAILABLE:
            QMessageBox.critical(self, "错误", "无法加载控制器和模型，请检查程序安装。")
            return
        
        # 初始化UI
        self.init_ui()
        
        # 加载用户数据
        self.load_users()
    
    def init_ui(self):
        """
        初始化用户界面
        """
        # 设置整体布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建顶部操作栏
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        # 添加用户按钮
        self.btn_add_user = QPushButton("添加用户")
        self.btn_add_user.setIcon(QIcon.fromTheme("list-add", QIcon()))
        self.btn_add_user.setToolTip("添加新用户")
        self.btn_add_user.clicked.connect(self.add_user)
        top_layout.addWidget(self.btn_add_user)
        
        # 刷新按钮
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setIcon(QIcon.fromTheme("view-refresh", QIcon()))
        self.btn_refresh.setToolTip("刷新用户列表")
        self.btn_refresh.clicked.connect(self.load_users)
        top_layout.addWidget(self.btn_refresh)
        
        # 查找用户框
        self.search_layout = QHBoxLayout()
        self.search_label = QLabel("查找:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入用户名或邮箱")
        self.search_input.textChanged.connect(self.filter_users)
        self.search_layout.addWidget(self.search_label)
        self.search_layout.addWidget(self.search_input)
        top_layout.addLayout(self.search_layout)
        
        # 填充剩余空间
        top_layout.addStretch()
        
        # 添加到主布局
        main_layout.addLayout(top_layout)
        
        # 创建用户表格
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(7)  # ID, 用户名, 角色, 邮箱, 创建时间, 最后登录, 状态
        self.user_table.setHorizontalHeaderLabels(["ID", "用户名", "角色", "邮箱", "创建时间", "最后登录", "状态"])
        
        # 设置表格属性
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止直接编辑
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)  # 选择整行
        self.user_table.setSelectionMode(QTableWidget.SingleSelection)  # 单选模式
        
        # 设置表格列宽
        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID列自动调整宽度
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 用户名列拉伸
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 角色列自动调整
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # 邮箱列拉伸
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 创建时间列自动调整
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 最后登录列自动调整
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # 状态列自动调整
        
        # 设置右键菜单
        self.user_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.user_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 双击编辑用户
        self.user_table.cellDoubleClicked.connect(self.edit_user)
        
        # 添加到主布局
        main_layout.addWidget(self.user_table)
        
        # 创建底部操作按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)
        
        # 编辑用户按钮
        self.btn_edit_user = QPushButton("编辑用户")
        self.btn_edit_user.setIcon(QIcon.fromTheme("document-edit", QIcon()))
        self.btn_edit_user.setToolTip("编辑选中的用户")
        self.btn_edit_user.clicked.connect(self.edit_user)
        bottom_layout.addWidget(self.btn_edit_user)
        
        # 删除用户按钮
        self.btn_delete_user = QPushButton("删除用户")
        self.btn_delete_user.setIcon(QIcon.fromTheme("list-remove", QIcon()))
        self.btn_delete_user.setToolTip("删除选中的用户")
        self.btn_delete_user.clicked.connect(self.delete_user)
        bottom_layout.addWidget(self.btn_delete_user)
        
        # 重置密码按钮
        self.btn_reset_password = QPushButton("重置密码")
        self.btn_reset_password.setIcon(QIcon.fromTheme("security-high", QIcon()))
        self.btn_reset_password.setToolTip("重置选中用户的密码")
        self.btn_reset_password.clicked.connect(self.reset_password)
        bottom_layout.addWidget(self.btn_reset_password)
        
        # 切换用户状态按钮
        self.btn_toggle_status = QPushButton("切换状态")
        self.btn_toggle_status.setIcon(QIcon.fromTheme("user-available", QIcon()))
        self.btn_toggle_status.setToolTip("启用/禁用选中的用户")
        self.btn_toggle_status.clicked.connect(self.toggle_user_status)
        bottom_layout.addWidget(self.btn_toggle_status)
        
        # 添加到主布局
        main_layout.addLayout(bottom_layout)
        
        # 创建状态栏
        self.status_bar = QLabel("就绪")
        self.status_bar.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_bar.setFrameShape(QFrame.StyledPanel)
        main_layout.addWidget(self.status_bar)
        
        # 初始禁用按钮
        self.update_button_states()
    
    def load_users(self):
        """
        加载用户列表数据
        """
        try:
            # 显示加载状态
            self.status_bar.setText("正在加载用户数据...")
            
            # 获取所有用户数据
            if user_model and hasattr(user_model, 'get_all_users'):
                self.users_data = user_model.get_all_users()
            else:
                self.users_data = []
            
            # 更新表格显示
            self.update_user_table()
            
            # 更新状态栏
            self.status_bar.setText(f"共加载 {len(self.users_data)} 个用户")
            
        except Exception as e:
            logging.error(f"加载用户数据失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"加载用户数据失败: {str(e)}")
            self.status_bar.setText("加载用户数据失败")
    
    def update_user_table(self):
        """
        更新用户表格显示
        """
        # 清空表格
        self.user_table.setRowCount(0)
        
        # 添加数据到表格
        for user in self.users_data:
            row_position = self.user_table.rowCount()
            self.user_table.insertRow(row_position)
            
            # 创建表格项
            user_id = user.get('id', '')
            username = user.get('username', '')
            role = user.get('role', '')
            email = user.get('email', '')
            created_at = user.get('created_at', '')
            last_login = user.get('last_login', '')
            is_active = user.get('is_active', True)
            
            # 设置表格项
            self.user_table.setItem(row_position, 0, QTableWidgetItem(str(user_id)))
            self.user_table.setItem(row_position, 1, QTableWidgetItem(username))
            
            # 设置角色显示
            role_item = QTableWidgetItem(role)
            if role == 'admin':
                role_item.setBackground(QBrush(QColor(220, 230, 255)))
            elif role == 'manager':
                role_item.setBackground(QBrush(QColor(220, 255, 230)))
            else:
                role_item.setBackground(QBrush(QColor(255, 245, 220)))
            self.user_table.setItem(row_position, 2, role_item)
            
            self.user_table.setItem(row_position, 3, QTableWidgetItem(email))
            self.user_table.setItem(row_position, 4, QTableWidgetItem(created_at))
            self.user_table.setItem(row_position, 5, QTableWidgetItem(last_login or "未登录"))
            
            # 设置状态显示
            status_item = QTableWidgetItem("启用" if is_active else "禁用")
            status_item.setTextAlignment(Qt.AlignCenter)
            if is_active:
                status_item.setForeground(QBrush(Qt.green))
            else:
                status_item.setForeground(QBrush(Qt.red))
                # 禁用的用户行显示为灰色
                for col in range(self.user_table.columnCount()):
                    item = self.user_table.item(row_position, col)
                    if item:
                        item.setForeground(QBrush(QColor(150, 150, 150)))
            self.user_table.setItem(row_position, 6, status_item)
        
        # 更新按钮状态
        self.update_button_states()
    
    def update_button_states(self):
        """
        更新按钮状态
        根据是否有选中行启用或禁用相关按钮
        """
        # 获取选中行
        selected_rows = self.user_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        # 更新按钮状态
        self.btn_edit_user.setEnabled(has_selection)
        self.btn_delete_user.setEnabled(has_selection)
        self.btn_reset_password.setEnabled(has_selection)
        self.btn_toggle_status.setEnabled(has_selection)
        
        # 如果有选中行，更新按钮状态文本
        if has_selection:
            user_id = int(self.user_table.item(selected_rows[0].row(), 0).text())
            is_admin = self.user_table.item(selected_rows[0].row(), 2).text() == 'admin'
            is_active = self.user_table.item(selected_rows[0].row(), 6).text() == '启用'
            
            # 当前用户不能编辑或删除自己
            is_current_user = user_id == self.current_user_id
            self.btn_delete_user.setEnabled(has_selection and not is_current_user and not is_admin)
            self.btn_edit_user.setEnabled(has_selection and not (is_admin and not is_admin))
            
            # 更新切换状态按钮文本
            self.btn_toggle_status.setText("禁用用户" if is_active else "启用用户")
    
    def filter_users(self, text):
        """
        过滤用户列表
        
        Args:
            text: 过滤文本
        """
        # 遍历所有行
        for row in range(self.user_table.rowCount()):
            # 获取用户名和邮箱
            username_item = self.user_table.item(row, 1)
            email_item = self.user_table.item(row, 3)
            
            if username_item and email_item:
                username = username_item.text().lower()
                email = email_item.text().lower()
                
                # 检查是否包含过滤文本
                if text.lower() in username or text.lower() in email:
                    self.user_table.setRowHidden(row, False)
                else:
                    self.user_table.setRowHidden(row, True)
    
    def show_context_menu(self, position):
        """
        显示右键菜单
        
        Args:
            position: 菜单显示位置
        """
        # 获取选中行
        selected_rows = self.user_table.selectionModel().selectedRows()
        
        # 如果有选中行，显示菜单
        if selected_rows:
            # 创建菜单
            context_menu = QMenu(self)
            
            # 添加菜单项
            edit_action = QAction("编辑用户", self)
            edit_action.triggered.connect(self.edit_user)
            context_menu.addAction(edit_action)
            
            delete_action = QAction("删除用户", self)
            delete_action.triggered.connect(self.delete_user)
            context_menu.addAction(delete_action)
            
            reset_action = QAction("重置密码", self)
            reset_action.triggered.connect(self.reset_password)
            context_menu.addAction(reset_action)
            
            # 分隔线
            context_menu.addSeparator()
            
            # 切换状态菜单项
            is_active = self.user_table.item(selected_rows[0].row(), 6).text() == '启用'
            toggle_text = "禁用用户" if is_active else "启用用户"
            toggle_action = QAction(toggle_text, self)
            toggle_action.triggered.connect(self.toggle_user_status)
            context_menu.addAction(toggle_action)
            
            # 显示菜单
            context_menu.exec_(self.user_table.mapToGlobal(position))
    
    def add_user(self):
        """
        添加新用户
        """
        # 打开添加用户对话框
        dialog = UserDialog(self)
        
        # 如果对话框成功关闭并保存
        if dialog.exec_() == QDialog.Accepted:
            # 获取用户数据
            user_data = dialog.get_user_data()
            
            try:
                # 创建用户
                if user_model and hasattr(user_model, 'create_user'):
                    result = user_model.create_user(
                        username=user_data['username'],
                        password=user_data['password'],
                        role=user_data['role'],
                        email=user_data['email']
                    )
                    
                    if result['success']:
                        # 刷新用户列表
                        self.load_users()
                        self.status_bar.setText(f"用户 '{user_data['username']}' 创建成功")
                        self.user_updated.emit()
                    else:
                        QMessageBox.warning(self, "警告", f"创建用户失败: {result['message']}")
                else:
                    QMessageBox.warning(self, "警告", "无法创建用户，请检查系统配置")
            
            except Exception as e:
                logging.error(f"添加用户失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"添加用户失败: {str(e)}")
    
    def edit_user(self):
        """
        编辑选中的用户
        """
        # 获取选中行
        selected_rows = self.user_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择一个用户")
            return
        
        # 获取用户ID和数据
        row = selected_rows[0].row()
        user_id = int(self.user_table.item(row, 0).text())
        
        # 查找用户数据
        user_data = None
        for user in self.users_data:
            if user.get('id') == user_id:
                user_data = user
                break
        
        if not user_data:
            QMessageBox.warning(self, "警告", "找不到用户数据")
            return
        
        # 检查权限
        is_admin = user_data.get('role') == 'admin'
        is_current_user_admin = any(u.get('id') == self.current_user_id and u.get('role') == 'admin' for u in self.users_data)
        
        # 非管理员不能编辑管理员用户
        if is_admin and not is_current_user_admin:
            QMessageBox.warning(self, "警告", "您没有权限编辑管理员用户")
            return
        
        # 打开编辑用户对话框
        dialog = UserDialog(self, user_data=user_data)
        
        # 如果对话框成功关闭并保存
        if dialog.exec_() == QDialog.Accepted:
            # 获取更新的用户数据
            updated_data = dialog.get_user_data()
            
            try:
                # 更新用户
                if user_model and hasattr(user_model, 'update_user'):
                    result = user_model.update_user(
                        user_id=user_id,
                        username=updated_data['username'],
                        role=updated_data['role'],
                        email=updated_data['email'],
                        password=updated_data['password'] if updated_data['password'] else None
                    )
                    
                    if result['success']:
                        # 刷新用户列表
                        self.load_users()
                        self.status_bar.setText(f"用户 '{updated_data['username']}' 更新成功")
                        self.user_updated.emit()
                    else:
                        QMessageBox.warning(self, "警告", f"更新用户失败: {result['message']}")
                else:
                    QMessageBox.warning(self, "警告", "无法更新用户，请检查系统配置")
            
            except Exception as e:
                logging.error(f"更新用户失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"更新用户失败: {str(e)}")
    
    def delete_user(self):
        """
        删除选中的用户
        """
        # 获取选中行
        selected_rows = self.user_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择一个用户")
            return
        
        # 获取用户ID和名称
        row = selected_rows[0].row()
        user_id = int(self.user_table.item(row, 0).text())
        username = self.user_table.item(row, 1).text()
        role = self.user_table.item(row, 2).text()
        
        # 检查是否是当前用户
        if user_id == self.current_user_id:
            QMessageBox.warning(self, "警告", "不能删除当前登录的用户")
            return
        
        # 检查是否是管理员用户
        is_current_user_admin = any(u.get('id') == self.current_user_id and u.get('role') == 'admin' for u in self.users_data)
        if role == 'admin' and not is_current_user_admin:
            QMessageBox.warning(self, "警告", "您没有权限删除管理员用户")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除用户 '{username}' 吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 删除用户
                if user_model and hasattr(user_model, 'delete_user'):
                    result = user_model.delete_user(user_id)
                    
                    if result['success']:
                        # 刷新用户列表
                        self.load_users()
                        self.status_bar.setText(f"用户 '{username}' 删除成功")
                        self.user_deleted.emit(user_id)
                    else:
                        QMessageBox.warning(self, "警告", f"删除用户失败: {result['message']}")
                else:
                    QMessageBox.warning(self, "警告", "无法删除用户，请检查系统配置")
            
            except Exception as e:
                logging.error(f"删除用户失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"删除用户失败: {str(e)}")
    
    def reset_password(self):
        """
        重置选中用户的密码
        """
        # 获取选中行
        selected_rows = self.user_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择一个用户")
            return
        
        # 获取用户ID和名称
        row = selected_rows[0].row()
        user_id = int(self.user_table.item(row, 0).text())
        username = self.user_table.item(row, 1).text()
        
        # 输入新密码
        new_password, ok = QInputDialog.getText(
            self,
            "重置密码",
            f"请输入用户 '{username}' 的新密码:\n(留空将生成随机密码)",
            QLineEdit.Password
        )
        
        if ok:
            try:
                # 重置密码
                if user_model and hasattr(user_model, 'reset_password'):
                    result = user_model.reset_password(user_id, new_password if new_password else None)
                    
                    if result['success']:
                        message = f"密码重置成功！{f'新密码: {result.get('new_password')}' if result.get('new_password') else ''}"
                        QMessageBox.information(self, "成功", message)
                        self.status_bar.setText(f"用户 '{username}' 的密码已重置")
                    else:
                        QMessageBox.warning(self, "警告", f"重置密码失败: {result['message']}")
                else:
                    QMessageBox.warning(self, "警告", "无法重置密码，请检查系统配置")
            
            except Exception as e:
                logging.error(f"重置密码失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"重置密码失败: {str(e)}")
    
    def toggle_user_status(self):
        """
        切换用户状态（启用/禁用）
        """
        # 获取选中行
        selected_rows = self.user_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择一个用户")
            return
        
        # 获取用户ID和当前状态
        row = selected_rows[0].row()
        user_id = int(self.user_table.item(row, 0).text())
        username = self.user_table.item(row, 1).text()
        is_active = self.user_table.item(row, 6).text() == '启用'
        role = self.user_table.item(row, 2).text()
        
        # 检查是否是管理员用户
        is_current_user_admin = any(u.get('id') == self.current_user_id and u.get('role') == 'admin' for u in self.users_data)
        if role == 'admin' and not is_current_user_admin:
            QMessageBox.warning(self, "警告", "您没有权限修改管理员用户的状态")
            return
        
        # 确认操作
        action = "禁用" if is_active else "启用"
        reply = QMessageBox.question(
            self,
            f"确认{action}",
            f"确定要{action}用户 '{username}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 更新用户状态
                if user_model and hasattr(user_model, 'update_user_status'):
                    result = user_model.update_user_status(user_id, not is_active)
                    
                    if result['success']:
                        # 刷新用户列表
                        self.load_users()
                        self.status_bar.setText(f"用户 '{username}' 已{action}")
                        self.user_updated.emit()
                    else:
                        QMessageBox.warning(self, "警告", f"{action}用户失败: {result['message']}")
                else:
                    QMessageBox.warning(self, "警告", f"无法{action}用户，请检查系统配置")
            
            except Exception as e:
                logging.error(f"{action}用户失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"{action}用户失败: {str(e)}")


class UserDialog(QDialog):
    """
    用户添加/编辑对话框
    """
    
    def __init__(self, parent=None, user_data=None):
        """
        初始化用户对话框
        
        Args:
            parent: 父组件
            user_data: 用户数据，为None时表示添加新用户
        """
        super().__init__(parent)
        
        self.user_data = user_data
        self.is_edit_mode = user_data is not None
        
        # 设置对话框属性
        self.setWindowTitle("编辑用户" if self.is_edit_mode else "添加用户")
        self.setFixedSize(400, 320)
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        """
        初始化对话框UI
        """
        # 设置整体布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 创建表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 用户名输入框
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setMinimumWidth(200)
        form_layout.addRow("用户名:", self.username_input)
        
        # 密码输入框
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("留空表示不修改密码" if self.is_edit_mode else "请输入密码")
        form_layout.addRow("密码:", self.password_input)
        
        # 确认密码输入框
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("留空表示不修改密码" if self.is_edit_mode else "请再次输入密码")
        form_layout.addRow("确认密码:", self.confirm_password_input)
        
        # 角色选择框
        self.role_combo = QComboBox()
        self.role_combo.addItems(["user", "manager", "admin"])
        form_layout.addRow("角色:", self.role_combo)
        
        # 邮箱输入框
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("请输入邮箱地址")
        form_layout.addRow("邮箱:", self.email_input)
        
        # 添加表单到主布局
        main_layout.addLayout(form_layout)
        
        # 添加按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 取消按钮
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        # 填充空间
        button_layout.addStretch()
        
        # 保存按钮
        self.btn_save = QPushButton("保存")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_save)
        
        # 添加到主布局
        main_layout.addLayout(button_layout)
        
        # 如果是编辑模式，填充现有数据
        if self.is_edit_mode:
            self.username_input.setText(self.user_data.get('username', ''))
            self.role_combo.setCurrentText(self.user_data.get('role', 'user'))
            self.email_input.setText(self.user_data.get('email', ''))
    
    def accept(self):
        """
        处理对话框接受事件，验证表单数据
        """
        # 验证用户名
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "警告", "用户名不能为空")
            return
        
        # 验证密码
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # 如果不是编辑模式或修改了密码，需要验证密码
        if not self.is_edit_mode or password:
            # 检查密码长度
            min_length = settings_controller.get_setting('security.password_min_length', 6) if settings_controller else 6
            if len(password) < min_length:
                QMessageBox.warning(self, "警告", f"密码长度不能少于{min_length}个字符")
                return
            
            # 检查密码一致性
            if password != confirm_password:
                QMessageBox.warning(self, "警告", "两次输入的密码不一致")
                return
        
        # 验证邮箱
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "警告", "邮箱地址不能为空")
            return
        
        # 简单的邮箱格式验证
        if '@' not in email or '.' not in email.split('@')[-1]:
            QMessageBox.warning(self, "警告", "邮箱地址格式不正确")
            return
        
        # 接受对话框
        super().accept()
    
    def get_user_data(self):
        """
        获取用户数据
        
        Returns:
            dict: 用户数据字典
        """
        return {
            'username': self.username_input.text().strip(),
            'password': self.password_input.text(),  # 可能为空，表示不修改
            'role': self.role_combo.currentText(),
            'email': self.email_input.text().strip()
        }


if __name__ == "__main__":
    # 测试用户管理界面
    if PYQT5_AVAILABLE:
        app = QApplication(sys.argv)
        
        # 设置应用程序样式
        app.setStyle("Fusion")
        
        # 创建用户管理组件
        widget = UserManagementWidget(current_user_id=1)
        widget.show()
        
        # 运行应用程序
        sys.exit(app.exec_())
    else:
        print("请安装PyQt5后运行此测试")