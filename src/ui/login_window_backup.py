#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录窗口模块
实现用户登录和认证功能
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QMessageBox, QFrame, QApplication,
    QCheckBox, QGridLayout
)
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize, QEvent, QPoint, QTimer

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
        # 设置字体以确保中文正常显示
        self.set_default_font()
        self.init_ui()
        self.current_user = None
        
    def set_default_font(self):
        """设置默认字体以确保中文正常显示"""
        # 尝试使用多种中文字体作为备选
        for font_family in ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "WenQuanYi Micro Hei", "Heiti TC"]:
            font = QFont(font_family)
            if font.exactMatch():
                QApplication.setFont(font)
                return
        # 如果没有找到理想的字体，设置一个通用字体
        font = QFont("Sans Serif")
        QApplication.setFont(font)
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("企业财务系统 - 登录")
        self.setFixedSize(550, 520)  # 增大窗口以提供更舒适的空间
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # 设置窗口图标
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons', 'logo.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass  # 如果图标不存在，不影响程序运行
        
        # 居中显示
        self.center_window()
        
        # 创建主部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置背景色和渐变效果 - 使用更现代的渐变
        central_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                      stop:0 #f8fafc, 
                                      stop:1 #e2e8f0);
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(60, 30, 60, 30)
        main_layout.setSpacing(30)  # 增加间距以提高可读性
        
        # 创建标题和图标区域
        title_widget = QWidget()
        title_widget.setStyleSheet("background-color: transparent;")
        title_layout = QVBoxLayout(title_widget)
        title_layout.setAlignment(Qt.AlignCenter)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(15)  # 增加标题区域的间距
        
        # 创建应用图标 - 使用更现代的设计
        icon_label = QLabel()
        icon_label.setFixedSize(80, 80)
        icon_label.setStyleSheet("""
            background-color: #3b82f6;  # 使用更现代的蓝色
            border-radius: 20px;
            border: 4px solid white;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        """)
        
        # 为图标添加悬停效果
        icon_label.installEventFilter(self)
        
        # 创建标题 - 使用更现代的字体和颜色
        title_label = QLabel("企业财务账目录入与利润核算系统")
        title_label.setFont(QFont(self.get_available_font(), 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #1e3a8a; font-weight: 700;")
        
        subtitle_label = QLabel("请登录您的账户以访问系统")
        subtitle_label.setFont(QFont(self.get_available_font(), 12))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #64748b;")
        
        # 添加到标题布局
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        # 创建登录表单容器 - 使用更现代的卡片设计
        form_widget = QWidget()
        form_widget.setStyleSheet("""
            background-color: white;
            border-radius: 20px;
            padding: 20px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
        "")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(35, 30, 35, 30)
        form_layout.setSpacing(24)  # 增加表单元素间距
        
        # 用户名输入框
        username_widget = QWidget()
        username_widget.setStyleSheet("background-color: transparent;")
        username_layout = QVBoxLayout(username_widget)
        username_layout.setContentsMargins(10, 0, 0, 0)
        username_layout.setSpacing(6)
        
        username_label = QLabel("用户名")
        username_label.setFont(QFont(self.get_available_font(), 11, QFont.Medium))
        username_label.setStyleSheet("color: #202124;")
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setFixedHeight(55)
        font_family = self.get_available_font()
        self.username_edit.setStyleSheet("""
            QLineEdit {{
                border: 2px solid #dfe1e5;
                border-radius: 12px;
                padding: 0 20px;
                font-family: %s;
                font-size: 16px;
                background-color: #ffffff;
                color: #202124;
                font-weight: 400;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }}
            QLineEdit:focus {{
                border: 2px solid #1a73e8;
                box-shadow: 0 1px 6px rgba(26, 115, 232, 0.2);
                outline: none;
            }}
            QLineEdit:hover:not(:focus) {{
                border-color: #5f6368;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
            }}
        """ % font_family)
        
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_edit)
        
        # 密码输入框
        password_widget = QWidget()
        password_widget.setStyleSheet("background-color: transparent;")
        password_layout = QVBoxLayout(password_widget)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(6)
        
        password_label = QLabel("密码")
        password_label.setFont(QFont(self.get_available_font(), 11, QFont.Medium))
        password_label.setStyleSheet("color: #202124;")
        
        # 创建密码输入容器
        password_input_container = QWidget()
        password_input_container.setStyleSheet("background-color: transparent;")
        password_input_layout = QHBoxLayout(password_input_container)
        password_input_layout.setContentsMargins(0, 0, 0, 0)
        password_input_layout.setSpacing(0)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setFixedHeight(55)
        font_family = self.get_available_font()
        self.password_edit.setStyleSheet("""
            QLineEdit {{
                border: 2px solid #dfe1e5;
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
                padding: 0 20px;
                font-family: %s;
                font-size: 16px;
                background-color: #ffffff;
                color: #202124;
                font-weight: 400;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }}
            QLineEdit:focus {{
                border: 2px solid #1a73e8;
                box-shadow: 0 1px 6px rgba(26, 115, 232, 0.2);
                outline: none;
            }}
            QLineEdit:hover:not(:focus) {{
                border-color: #5f6368;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
            }}
        """ % font_family)
        
        # 创建显示/隐藏密码按钮
        self.toggle_password_btn = QPushButton()
        self.toggle_password_btn.setFixedSize(50, 50)
        self.toggle_password_btn.setText("👁")
        self.toggle_password_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #dfe1e5;
                border-left: none;
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
                background-color: #ffffff;
                color: #5f6368;
                font-size: 16px;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                color: #1a73e8;
                border-color: #5f6368;
            }
            QPushButton:pressed {
                background-color: #e8eaed;
                color: #0d47a1;
            }
        """)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        
        password_input_layout.addWidget(self.password_edit)
        password_input_layout.addWidget(self.toggle_password_btn)
        
        password_layout.addWidget(password_label)
        password_layout.addWidget(password_input_container)
        
        # 添加记住密码选项
        remember_widget = QWidget()
        remember_widget.setStyleSheet("background-color: transparent;")
        remember_layout = QHBoxLayout(remember_widget)
        remember_layout.setContentsMargins(0, 0, 0, 0)
        
        self.remember_checkbox = QCheckBox("记住密码")
        self.remember_checkbox.setFont(QFont(self.get_available_font(), 10))
        font_family = self.get_available_font()
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {{
                color: #5f6368;
                font-family: %s;
                font-size: 14px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #dfe1e5;
                background-color: #ffffff;
            }}
            QCheckBox::indicator:checked {{
                background-color: #1a73e8;
                border: 2px solid #1a73e8;
            }}
            QCheckBox::indicator:checked::after {{
                content: "";
                position: relative;
                left: 6px;
                top: 2px;
                width: 5px;
                height: 10px;
                border: solid white;
                border-width: 0 2px 2px 0;
                transform: rotate(45deg);
            }}
        """ % font_family)
        
        # 找回密码链接（可点击）
        forgot_label = QLabel("忘记密码?")
        forgot_label.setFont(QFont(self.get_available_font(), 10))
        forgot_label.setStyleSheet("""
            color: #1a73e8; 
            text-decoration: underline;
            transition: all 0.3s ease;
        """)
        forgot_label.setCursor(Qt.PointingHandCursor)
        forgot_label.mousePressEvent = self.handle_forgot_password
        
        # 为忘记密码链接添加悬停效果
        forgot_label.enterEvent = lambda event: forgot_label.setStyleSheet("""
            color: #0d5cb6; 
            text-decoration: underline;
        """)
        forgot_label.leaveEvent = lambda event: forgot_label.setStyleSheet("""
            color: #1a73e8; 
            text-decoration: underline;
        """)
        
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.addStretch(1)
        remember_layout.addWidget(forgot_label)
        
        # 创建登录按钮
        self.login_button = QPushButton("登录")
        self.login_button.setFixedHeight(50)
        font_family = self.get_available_font()
        self.login_button.setStyleSheet("""
            QPushButton {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4285f4, stop: 1 #1a73e8);
                color: white;
                border: none;
                border-radius: 12px;
                font-family: %s;
                font-size: 16px;
                font-weight: 600;
                box-shadow: 0 2px 6px rgba(66, 133, 244, 0.3);
                transition: all 0.3s ease;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #3367d6, stop: 1 #0d5cb6);
                box-shadow: 0 3px 8px rgba(66, 133, 244, 0.4);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #2a56c6, stop: 1 #0a4aab);
                box-shadow: 0 1px 4px rgba(66, 133, 244, 0.3);
            }}
            QPushButton:disabled {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #dadce0, stop: 1 #bdc1c6);
                color: #5f6368;
                box-shadow: none;
            }}
        """ % font_family)
        self.login_button.clicked.connect(self.handle_login)
        
        # 添加到表单布局
        form_layout.addWidget(username_widget)
        form_layout.addWidget(password_widget)
        form_layout.addWidget(remember_widget)
        form_layout.addWidget(self.login_button)
        
        # 添加版权信息 - 改进字体和颜色
        footer_widget = QWidget()
        footer_widget.setStyleSheet("background-color: transparent;")
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(5)
        
        version_label = QLabel("版本 1.0.0")
        version_label.setFont(QFont(self.get_available_font(), 10))
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #64748b;")
        
        copyright_label = QLabel("© 2025 企业财务管理系统")
        copyright_label.setFont(QFont(self.get_available_font(), 9))
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #94a3b8;")
        
        footer_layout.addWidget(version_label)
        footer_layout.addWidget(copyright_label)
        
        # 添加到主布局
        main_layout.addWidget(title_widget)
        main_layout.addWidget(form_widget)
        main_layout.addWidget(footer_widget)
        
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
        
        # 验证输入格式
        if not username:
            self.show_validation_error(self.username_edit, "请输入用户名")
            return
        
        # 验证用户名格式（简单验证：长度和字符类型）
        if len(username) < 3 or len(username) > 20:
            self.show_validation_error(self.username_edit, "用户名长度应在3-20个字符之间")
            return
            
        if not username.replace('_', '').replace('-', '').isalnum():
            self.show_validation_error(self.username_edit, "用户名只能包含字母、数字、下划线和连字符")
            return
            
        if not password:
            self.show_validation_error(self.password_edit, "请输入密码")
            return
            
        # 验证密码格式
        if len(password) < 6:
            self.show_validation_error(self.password_edit, "密码长度不能少于6个字符")
            return
        
        # 显示加载状态
        self.login_button.setEnabled(False)
        self.login_button.setText("登录中...")
        
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
                self.show_validation_error(self.password_edit, "用户名或密码错误")
                self.password_edit.clear()
                self.password_edit.setFocus()
                
                # 记录失败日志
                log_operation(None, 'login_failed', f'尝试使用用户名 {username} 登录失败')
                
        except Exception as e:
            QMessageBox.critical(self, "登录错误", f"登录过程中发生错误: {str(e)}")
            print(f"登录错误: {str(e)}")
        finally:
            # 恢复登录按钮状态
            self.login_button.setEnabled(True)
            self.login_button.setText("登录")
            
    def show_validation_error(self, widget, message):
        """显示验证错误信息"""
        font_family = self.get_available_font()
        if widget == self.username_edit:
            widget.setStyleSheet("""
                QLineEdit {{
                    border: 2px solid #ea4335;
                    border-radius: 12px;
                    padding: 0 20px;
                    font-family: %s;
                    font-size: 16px;
                    background-color: #fef2f2;
                    color: #202124;
                    font-weight: 400;
                    box-shadow: 0 1px 6px rgba(234, 67, 53, 0.2);
                }}
            """ % font_family)
        elif widget == self.password_edit:
            widget.setStyleSheet("""
                QLineEdit {{
                    border: 2px solid #ea4335;
                    border-top-left-radius: 12px;
                    border-bottom-left-radius: 12px;
                    padding: 0 20px;
                    font-family: %s;
                    font-size: 16px;
                    background-color: #fef2f2;
                    color: #202124;
                    font-weight: 400;
                    box-shadow: 0 1px 6px rgba(234, 67, 53, 0.2);
                }}
            """ % font_family)
            self.toggle_password_btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid #ea4335;
                    border-left: none;
                    border-top-right-radius: 12px;
                    border-bottom-right-radius: 12px;
                    background-color: #fef2f2;
                    color: #ea4335;
                    font-size: 16px;
                    box-shadow: 0 1px 6px rgba(234, 67, 53, 0.2);
                }
            """)
        
        QMessageBox.warning(self, "验证失败", message)
        widget.setFocus()
        # 恢复原始样式
        QTimer.singleShot(500, lambda: self.reset_input_style(widget))
            
    def reset_input_style(self, widget):
        """重置输入框样式"""
        font_family = self.get_available_font()
        if widget == self.username_edit:
            self.username_edit.setStyleSheet("""
                QLineEdit {{
                    border: 2px solid #dfe1e5;
                    border-radius: 12px;
                    padding: 0 20px;
                    font-family: %s;
                    font-size: 16px;
                    background-color: #ffffff;
                    color: #202124;
                    font-weight: 400;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;
                }}
                QLineEdit:focus {{
                    border: 2px solid #1a73e8;
                    box-shadow: 0 1px 6px rgba(26, 115, 232, 0.2);
                    outline: none;
                }}
                QLineEdit:hover:not(:focus) {{
                    border-color: #5f6368;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
                }}
            """ % font_family)
        elif widget == self.password_edit:
            self.password_edit.setStyleSheet("""
                QLineEdit {{
                    border: 2px solid #dfe1e5;
                    border-top-left-radius: 12px;
                    border-bottom-left-radius: 12px;
                    padding: 0 20px;
                    font-family: %s;
                    font-size: 16px;
                    background-color: #ffffff;
                    color: #202124;
                    font-weight: 400;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;
                }}
                QLineEdit:focus {{
                    border: 2px solid #1a73e8;
                    box-shadow: 0 1px 6px rgba(26, 115, 232, 0.2);
                    outline: none;
                }}
                QLineEdit:hover:not(:focus) {{
                    border-color: #5f6368;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
                }}
            """ % font_family)
            self.toggle_password_btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid #dfe1e5;
                    border-left: none;
                    border-top-right-radius: 12px;
                    border-bottom-right-radius: 12px;
                    background-color: #ffffff;
                    color: #5f6368;
                    font-size: 16px;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;
                }
                QPushButton:hover {
                    background-color: #f8f9fa;
                    color: #1a73e8;
                    border-color: #5f6368;
                }
                QPushButton:pressed {
                    background-color: #e8eaed;
                    color: #0d47a1;
                }
            """)
    
    def toggle_password_visibility(self):
        """切换密码显示/隐藏状态"""
        if self.password_edit.echoMode() == QLineEdit.Password:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("👁️‍🗨️")
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("👁")
    
    def handle_forgot_password(self, event):
        """处理忘记密码点击事件"""
        QMessageBox.information(self, "忘记密码", "请联系系统管理员重置您的密码。")
    
    def eventFilter(self, source, event):
        """为UI元素添加事件过滤器"""
        # 为图标添加悬停效果
        if hasattr(source, 'text') and source.text() == "":
            if event.type() == QEvent.HoverEnter:
                source.setStyleSheet("""
                    background-color: #1557b0;
                    border-radius: 18px;
                    border: 3px solid white;
                """)
                return True
            elif event.type() == QEvent.HoverLeave:
                source.setStyleSheet("""
                    background-color: #1a73e8;
                    border-radius: 18px;
                    border: 3px solid white;
                """)
                return True
        return super().eventFilter(source, event)
    
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
    
    def get_available_font(self):
        """获取可用的中文字体"""
        # 尝试多种中文字体作为备选
        for font_family in ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "WenQuanYi Micro Hei", "Heiti TC", "Sans Serif"]:
            font = QFont(font_family)
            if font.exactMatch():
                return font_family
        return "Sans Serif"  # 默认字体
        
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
    
    # 设置应用程序字体以确保中文正常显示
    for font_family in ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "WenQuanYi Micro Hei", "Heiti TC"]:
        font = QFont(font_family, 9)
        if font.exactMatch():
            app.setFont(font)
            break
    
    # 创建并显示登录窗口
    login_window = LoginWindow()
    login_window.show()
    
    sys.exit(app.exec_())