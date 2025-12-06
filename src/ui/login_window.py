#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QPixmap, QIcon
from src.database.db_manager import init_db, get_db_path
from src.controllers.auth_controller import AuthController
from src.ui.main_window import MainWindow

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.auth_controller = AuthController()
        self.init_db()
        self.init_ui()
    
    def init_db(self):
        """初始化数据库"""
        try:
            # 使用db_manager中的初始化方法
            init_db()
            print(f"数据库初始化成功: {get_db_path()}")
        except Exception as e:
            print(f"数据库初始化失败: {str(e)}")
            QMessageBox.critical(None, "数据库错误", f"无法初始化数据库: {str(e)}")
            sys.exit(1)
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("财务管理系统 - 登录")
        self.setGeometry(100, 100, 500, 600)
        self.setFixedSize(500, 600)
        
        # 设置窗口居中
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
        # 主容器
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #ffffff;")
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(30)
        
        # Logo区域
        logo_widget = QWidget()
        logo_widget.setStyleSheet("background-color: transparent;")
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(20)
        
        # Logo标签
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setText("💰")
        logo_label.setStyleSheet("""
            font-size: 64px;
            margin-bottom: 20px;
        """)
        
        # 标题
        title_label = QLabel("财务管理")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont(self.get_available_font(), 24, QFont.Bold))
        title_label.setStyleSheet("""
            color: #1a73e8;
            margin-bottom: 10px;
        """)
        
        # 副标题
        subtitle_label = QLabel("Financial Management System")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont(self.get_available_font(), 12))
        subtitle_label.setStyleSheet("""
            color: #5f6368;
        """)
        
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(title_label)
        logo_layout.addWidget(subtitle_label)
        
        # 登录表单区域
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: transparent;")
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(20)
        
        # 用户名输入框
        username_widget = QWidget()
        username_widget.setStyleSheet("background-color: transparent;")
        username_layout = QVBoxLayout(username_widget)
        username_layout.setContentsMargins(0, 0, 0, 0)
        username_layout.setSpacing(6)
        
        username_label = QLabel("用户名")
        username_label.setFont(QFont(self.get_available_font(), 11, QFont.Medium))
        username_label.setStyleSheet("color: #202124;")
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setFixedHeight(55)
        font_family = self.get_available_font()
        self.username_edit.setStyleSheet("""
            QLineEdit {
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
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
                box-shadow: 0 1px 6px rgba(26, 115, 232, 0.2);
                outline: none;
            }
            QLineEdit:hover:not(:focus) {
                border-color: #5f6368;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
            }
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
            QLineEdit {
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
            }
            QLineEdit:focus {
                border: 2px solid #1a73e8;
                box-shadow: 0 1px 6px rgba(26, 115, 232, 0.2);
                outline: none;
            }
            QLineEdit:hover:not(:focus) {
                border-color: #5f6368;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
            }
        """ % font_family)
        
        # 创建显示/隐藏密码按钮
        self.toggle_password_btn = QPushButton()
        self.toggle_password_btn.setFixedSize(50, 55)
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
            QCheckBox {
                color: #5f6368;
                font-family: %s;
                font-size: 14px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #dfe1e5;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #1a73e8;
                border: 2px solid #1a73e8;
            }
            QCheckBox::indicator:checked::after {
                content: "";
                position: relative;
                left: 6px;
                top: 2px;
                width: 5px;
                height: 10px;
                border: solid white;
                border-width: 0 2px 2px 0;
                transform: rotate(45deg);
            }
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
            QPushButton {
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
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #3367d6, stop: 1 #0d5cb6);
                box-shadow: 0 3px 8px rgba(66, 133, 244, 0.4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #2a56c6, stop: 1 #0a4aab);
                box-shadow: 0 1px 4px rgba(66, 133, 244, 0.3);
            }
            QPushButton:disabled {
                background: #dadce0;
                color: #9aa0a6;
                box-shadow: none;
            }
        """ % font_family)
        self.login_button.clicked.connect(self.handle_login)
        
        # 为登录按钮添加悬停动画效果
        self.login_button.installEventFilter(self)
        
        # 添加到表单布局
        form_layout.addWidget(username_widget)
        form_layout.addWidget(password_widget)
        form_layout.addWidget(remember_widget)
        form_layout.addWidget(self.login_button)
        
        # 添加到主布局
        main_layout.addWidget(logo_widget)
        main_layout.addWidget(form_widget)
        main_layout.addStretch(1)
        
        # 设置焦点和事件处理
        self.username_edit.setFocus()
        self.username_edit.returnPressed.connect(self.password_edit.setFocus)
        self.password_edit.returnPressed.connect(self.handle_login)
        
        # 为输入框添加事件过滤器
        self.username_edit.installEventFilter(self)
        self.password_edit.installEventFilter(self)
        
        # 初始化淡入动画
        self.init_fade_in_animation()
    
    def toggle_password_visibility(self):
        """切换密码可见性"""
        if self.password_edit.echoMode() == QLineEdit.Password:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setText("🙈")
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setText("👁")
    
    def handle_forgot_password(self, event):
        """处理忘记密码"""
        QMessageBox.information(self, "提示", "请联系系统管理员重置密码。\n默认用户名：admin\n默认密码：admin123")
    
    def validate_inputs(self):
        """验证输入"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not username:
            self.show_validation_error(self.username_edit, "请输入用户名")
            return False
        
        if not password:
            self.show_validation_error(self.password_edit, "请输入密码")
            return False
            
        return True
    
    def show_validation_error(self, widget, message):
        """显示验证错误信息"""
        font_family = self.get_available_font()
        if widget == self.username_edit:
            widget.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #ea4335;
                    border-radius: 12px;
                    padding: 0 20px;
                    font-family: %s;
                    font-size: 16px;
                    background-color: #fef2f2;
                    color: #202124;
                    font-weight: 400;
                    box-shadow: 0 1px 6px rgba(234, 67, 53, 0.2);
                }
            """ % font_family)
        elif widget == self.password_edit:
            widget.setStyleSheet("""
                QLineEdit {
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
                }
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
            widget.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #dfe1e5;
                    border-radius: 12px;
                    padding: 0 20px;
                    font-family: %s;
                    font-size: 16px;
                    background-color: #ffffff;
                    color: #202124;
                    font-weight: 400;
                }
                QLineEdit:focus {
                    border: 2px solid #1a73e8;
                    box-shadow: 0 1px 6px rgba(26, 115, 232, 0.2);
                }
            """ % font_family)
        elif widget == self.password_edit:
            widget.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #dfe1e5;
                    border-top-left-radius: 12px;
                    border-bottom-left-radius: 12px;
                    padding: 0 20px;
                    font-family: %s;
                    font-size: 16px;
                    background-color: #ffffff;
                    color: #202124;
                    font-weight: 400;
                }
                QLineEdit:focus {
                    border: 2px solid #1a73e8;
                    border-left: 2px solid #dfe1e5;
                    box-shadow: 0 1px 6px rgba(26, 115, 232, 0.2);
                }
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
                }
                QPushButton:hover {
                    background-color: #f8f9fa;
                }
            """)
    
    def handle_login(self):
        """处理登录"""
        if not self.validate_inputs():
            return
        
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        # 禁用登录按钮防止重复点击
        self.login_button.setEnabled(False)
        self.login_button.setText("登录中...")
        
        try:
            # 使用认证控制器验证用户凭据
            result = self.auth_controller.login(username, password)
            
            if result['success']:
                # 登录成功，获取用户信息
                self.current_user = {
                    'id': result['user']['id'],
                    'username': result['user']['username'],
                    'fullname': result['user']['fullname'] if result['user'].get('fullname') else result['user']['username'],
                    'role': result['user']['role'] if result['user'].get('role') else 'user'
                }
                print(f"用户 {username} 登录成功")
                self.accept_login()
            else:
                print(f"登录失败: {result.get('message', '用户名或密码错误')}")
                self.show_validation_error(self.username_edit, result.get('message', '用户名或密码错误'))
        except Exception as e:
            print(f"登录过程中发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"登录过程中发生错误: {str(e)}")
        finally:
            # 恢复登录按钮状态
            self.login_button.setEnabled(True)
            self.login_button.setText("登录")
    
    def accept_login(self):
        """接受登录，打开主窗口"""
        # 创建登录成功淡出动画
        self.animate_login_success()
    
    def animate_login_success(self):
        """登录成功动画"""
        # 创建淡出动画
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(500)  # 500毫秒
        self.fade_out_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        
        # 动画完成后打开主窗口
        self.fade_out_animation.finished.connect(self.open_main_window)
        
        # 启动动画
        self.fade_out_animation.start()
        print("登录成功动画开始")
    
    def open_main_window(self):
        """打开主窗口"""
        try:
            print("正在创建主窗口...")
            # 创建主窗口实例
            self.main_window = MainWindow(self.current_user)
            print("主窗口创建成功，正在显示...")
            self.main_window.show()
            print("主窗口显示成功，正在关闭登录窗口...")
            
            # 强制刷新界面
            self.main_window.repaint()
            QApplication.processEvents()
            
            # 关闭登录窗口
            self.close()
            print("登录窗口关闭成功，跳转完成")
            
        except Exception as e:
            import traceback
            print(f"加载主窗口错误: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"无法加载主窗口: {str(e)}")
            # 重新显示登录窗口
            self.show()
            self.setWindowOpacity(1.0)
    
    def get_available_font(self):
        """获取可用的中文字体"""
        # 尝试多种中文字体作为备选
        for font_family in ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "WenQuanYi Micro Hei", "Heiti TC", "Sans Serif"]:
            font = QFont(font_family)
            if font.exactMatch():
                return font_family
        return "Sans Serif"  # 默认字体
    
    def init_fade_in_animation(self):
        """初始化窗口淡入动画"""
        # 设置初始透明度为0
        self.setWindowOpacity(0.0)
        
        # 创建透明度动画
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(800)  # 动画持续时间800毫秒
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)  # 使用缓动曲线使动画更自然
        
        # 启动动画
        self.fade_animation.start()
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于处理按钮悬停动画和输入框焦点动画"""
        if obj == self.login_button:
            if event.type() == event.HoverEnter:
                # 鼠标进入按钮区域时的动画
                self.animate_button_scale(self.login_button, 1.0, 1.05)
            elif event.type() == event.HoverLeave:
                # 鼠标离开按钮区域时的动画
                self.animate_button_scale(self.login_button, 1.05, 1.0)
        elif obj in [self.username_edit, self.password_edit]:
            if event.type() == event.FocusIn:
                # 输入框获得焦点时的动画
                self.animate_input_focus(obj, True)
            elif event.type() == event.FocusOut:
                # 输入框失去焦点时的动画
                self.animate_input_focus(obj, False)
        
        return super().eventFilter(obj, event)
    
    def animate_button_scale(self, button, start_value, end_value):
        """按钮缩放动画"""
        if not hasattr(button, 'scale_animation'):
            button.scale_animation = QPropertyAnimation(button, b"geometry")
        
        # 获取当前几何信息
        geom = button.geometry()
        center_x = geom.x() + geom.width() / 2
        center_y = geom.y() + geom.height() / 2
        
        # 计算缩放后的几何信息
        scale_factor = end_value / start_value
        new_width = int(geom.width() * scale_factor)
        new_height = int(geom.height() * scale_factor)
        new_x = int(center_x - new_width / 2)
        new_y = int(center_y - new_height / 2)
        
        # 设置动画属性
        button.scale_animation.setDuration(200)
        button.scale_animation.setStartValue(geom)
        button.scale_animation.setEndValue(button.geometry().adjusted(
            (geom.width() - new_width) // 2,
            (geom.height() - new_height) // 2,
            -(geom.width() - new_width) // 2,
            -(geom.height() - new_height) // 2
        ))
        button.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 启动动画
        button.scale_animation.start()
    
    def animate_input_focus(self, input_widget, has_focus):
        """输入框焦点动画"""
        # 创建动画对象
        animation = QPropertyAnimation(input_widget, b"geometry")
        animation.setDuration(150)  # 150毫秒
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 获取当前几何位置
        current_geometry = input_widget.geometry()
        
        if has_focus:
            # 获得焦点时稍微放大
            new_width = int(current_geometry.width() * 1.02)
            new_height = int(current_geometry.height() * 1.02)
            new_x = int(current_geometry.x() - (new_width - current_geometry.width()) / 2)
            new_y = int(current_geometry.y() - (new_height - current_geometry.height()) / 2)
        else:
            # 失去焦点时恢复原大小
            new_width = int(current_geometry.width() / 1.02)
            new_height = int(current_geometry.height() / 1.02)
            new_x = int(current_geometry.x() + (current_geometry.width() - new_width) / 2)
            new_y = int(current_geometry.y() + (current_geometry.height() - new_height) / 2)
        
        # 设置动画值
        animation.setStartValue(current_geometry)
        animation.setEndValue(QRect(new_x, new_y, new_width, new_height))
        
        # 启动动画
        animation.start()
    
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