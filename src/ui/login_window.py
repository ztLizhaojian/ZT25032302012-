#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录窗口模块
实现用户登录和认证功能
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QMessageBox, QFrame, QApplication
)
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QSize, QEvent

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入数据库操作
from src.database.db_manager import execute_query, log_operation


class LoginWindow(QMainWindow):
    """登录窗口类"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_user = None
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("企业财务系统 - 登录")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # 居中显示
        self.center_window()
        
        # 创建主部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(50, 30, 50, 30)
        main_layout.setSpacing(20)
        
        # 创建标题
        title_label = QLabel("企业财务系统")
        title_label.setFont(QFont("SimHei", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1a73e8;")
        
        subtitle_label = QLabel("请登录您的账户")
        subtitle_label.setFont(QFont("SimHei", 10))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #666;")
        
        # 创建登录表单
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(15)
        
        # 用户名输入框
        username_widget = QWidget()
        username_layout = QVBoxLayout(username_widget)
        username_layout.setContentsMargins(0, 0, 0, 0)
        username_layout.setSpacing(5)
        
        username_label = QLabel("用户名")
        username_label.setFont(QFont("SimHei", 9))
        username_label.setStyleSheet("color: #333;")
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setFixedHeight(36)
        self.username_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding-left: 10px;
                font-family: SimHei;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #1a73e8;
                outline: none;
                background-color: #f8f9fa;
            }
        """)
        
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_edit)
        
        # 密码输入框
        password_widget = QWidget()
        password_layout = QVBoxLayout(password_widget)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(5)
        
        password_label = QLabel("密码")
        password_label.setFont(QFont("SimHei", 9))
        password_label.setStyleSheet("color: #333;")
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setFixedHeight(36)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding-left: 10px;
                font-family: SimHei;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #1a73e8;
                outline: none;
                background-color: #f8f9fa;
            }
        """)
        
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_edit)
        
        # 添加到表单布局
        form_layout.addWidget(username_widget)
        form_layout.addWidget(password_widget)
        
        # 创建分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #eee;")
        
        # 创建登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setFixedHeight(36)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 4px;
                font-family: SimHei;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        self.login_button.clicked.connect(self.handle_login)
        
        # 添加到主布局
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        main_layout.addWidget(form_widget)
        main_layout.addWidget(separator)
        main_layout.addWidget(self.login_button)
        
        # 设置焦点
        self.username_edit.setFocus()
        
        # 连接回车键
        self.username_edit.returnPressed.connect(self.password_edit.setFocus)
        self.password_edit.returnPressed.connect(self.handle_login)
    
    def center_window(self):
        """将窗口居中显示"""
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def handle_login(self):
        """处理登录逻辑"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        # 验证输入
        if not username:
            QMessageBox.warning(self, "登录失败", "请输入用户名")
            self.username_edit.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "登录失败", "请输入密码")
            self.password_edit.setFocus()
            return
        
        # 验证用户凭据
        try:
            # 简单的密码验证（实际应用中应该使用密码哈希）
            user = execute_query(
                "SELECT id, username, fullname, role FROM users WHERE username = ? AND password = ?",
                (username, password),
                fetch=True
            )
            
            if user:
                # 登录成功，更新最后登录时间
                execute_query(
                    "UPDATE users SET last_login = ? WHERE id = ?",
                    (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['id'])
                )
                
                # 记录登录日志
                log_operation(user['id'], 'login', f'用户 {username} 登录系统')
                
                # 保存当前用户信息
                self.current_user = {
                    'id': user['id'],
                    'username': user['username'],
                    'fullname': user['fullname'],
                    'role': user['role']
                }
                
                # 隐藏登录窗口并显示主窗口
                self.accept_login()
                
            else:
                # 登录失败
                QMessageBox.warning(self, "登录失败", "用户名或密码错误")
                self.password_edit.clear()
                self.password_edit.setFocus()
                
                # 记录失败日志
                log_operation(None, 'login_failed', f'尝试使用用户名 {username} 登录失败')
                
        except Exception as e:
            QMessageBox.critical(self, "登录错误", f"登录过程中发生错误: {str(e)}")
            print(f"登录错误: {str(e)}")
    
    def accept_login(self):
        """接受登录，打开主窗口"""
        try:
            # 导入主窗口模块
            from src.ui.main_window import MainWindow
            
            # 创建主窗口实例
            self.main_window = MainWindow(self.current_user)
            self.main_window.show()
            
            # 关闭登录窗口
            self.close()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载主窗口: {str(e)}")
            print(f"加载主窗口错误: {str(e)}")
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # 判断焦点位置，决定执行登录还是切换焦点
            if self.username_edit.hasFocus():
                self.password_edit.setFocus()
            elif self.password_edit.hasFocus():
                self.handle_login()
        
        super().keyPressEvent(event)


if __name__ == "__main__":
    # 用于测试登录窗口
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置应用程序字体
    font = QFont("SimHei", 9)
    app.setFont(font)
    
    # 创建并显示登录窗口
    login_window = LoginWindow()
    login_window.show()
    
    sys.exit(app.exec_())