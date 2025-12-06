#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
实现系统的主要功能界面
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QDockWidget, QLabel, 
    QVBoxLayout, QHBoxLayout, QStatusBar, QMenuBar, QMenu, 
    QAction, QMessageBox, QToolBar, QSplitter
)
from PyQt5.QtGui import QFont, QIcon, QColor
from PyQt5.QtCore import Qt, QSize

# 导入其他UI模块（稍后创建）
# 暂时使用占位符，避免导入错误
try:
    from src.ui.transaction_widget import TransactionWidget
except ImportError:
    TransactionWidget = None
    
try:
    from src.ui.report_widget import ReportWidget
except ImportError:
    ReportWidget = None
    
try:
    from src.ui.dashboard_widget import DashboardWidget
except ImportError:
    DashboardWidget = None
    
try:
    from src.ui.account_widget import AccountWidget
except ImportError:
    AccountWidget = None
    
try:
    from src.ui.category_widget import CategoryWidget
except ImportError:
    CategoryWidget = None
    
try:
    from src.ui.setting_widget import SettingWidget
except ImportError:
    SettingWidget = None


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self, user_info):
        super().__init__()
        print("主窗口初始化开始...")
        self.user_info = user_info
        self.init_ui()
        print("主窗口初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle(f"企业财务系统 - {self.user_info['fullname']}")
        self.setMinimumSize(1024, 768)
        
        # 创建中心部件
        self.create_central_widget()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建侧边栏
        self.create_sidebar()
        
        # 显示欢迎信息
        self.show_welcome_message()
    
    def create_central_widget(self):
        """创建中心部件"""
        # 创建标签页部件
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabShape(QTabWidget.Rounded)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        
        # 创建各个功能标签页（处理导入失败的情况）
        if DashboardWidget is not None:
            self.dashboard_widget = DashboardWidget()
            self.tab_widget.addTab(self.dashboard_widget, "首页")
        else:
            dashboard_placeholder = QLabel("首页功能正在开发中...")
            dashboard_placeholder.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(dashboard_placeholder, "首页")
        
        if TransactionWidget is not None:
            self.transaction_widget = TransactionWidget(self.user_info)
            self.tab_widget.addTab(self.transaction_widget, "账务处理")
        else:
            transaction_placeholder = QLabel("账务处理功能正在开发中...")
            transaction_placeholder.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(transaction_placeholder, "账务处理")
        
        if ReportWidget is not None:
            self.report_widget = ReportWidget(self.user_info)
            self.tab_widget.addTab(self.report_widget, "报表分析")
        else:
            report_placeholder = QLabel("报表分析功能正在开发中...")
            report_placeholder.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(report_placeholder, "报表分析")
        
        # 连接组件信号与槽
        self.connect_components()
        
        if AccountWidget is not None:
            self.account_widget = AccountWidget(self.user_info)
            self.tab_widget.addTab(self.account_widget, "账户管理")
        else:
            account_placeholder = QLabel("账户管理功能正在开发中...")
            account_placeholder.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(account_placeholder, "账户管理")
        
        if CategoryWidget is not None:
            self.category_widget = CategoryWidget(self.user_info)
            self.tab_widget.addTab(self.category_widget, "分类管理")
        else:
            category_placeholder = QLabel("分类管理功能正在开发中...")
            category_placeholder.setAlignment(Qt.AlignCenter)
            self.tab_widget.addTab(category_placeholder, "分类管理")
        
        # 设置标签页切换事件
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # 设置为中心部件
        self.setCentralWidget(self.tab_widget)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = QMenuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        new_transaction_action = QAction("新建账务", self)
        new_transaction_action.triggered.connect(self.open_transaction_tab)
        file_menu.addAction(new_transaction_action)
        
        file_menu.addSeparator()
        
        backup_action = QAction("备份数据库", self)
        backup_action.triggered.connect(self.backup_database)
        file_menu.addAction(backup_action)
        
        restore_action = QAction("恢复数据库", self)
        restore_action.triggered.connect(self.restore_database)
        file_menu.addAction(restore_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 账务菜单
        transaction_menu = menu_bar.addMenu("账务")
        
        transaction_entry_action = QAction("账目录入", self)
        transaction_entry_action.triggered.connect(self.open_transaction_tab)
        transaction_menu.addAction(transaction_entry_action)
        
        transaction_list_action = QAction("账务列表", self)
        transaction_list_action.triggered.connect(self.open_transaction_tab)
        transaction_menu.addAction(transaction_list_action)
        
        # 报表菜单
        report_menu = menu_bar.addMenu("报表")
        
        profit_loss_action = QAction("利润表", self)
        profit_loss_action.triggered.connect(self.open_profit_loss_report)
        report_menu.addAction(profit_loss_action)
        
        balance_sheet_action = QAction("资产负债表", self)
        balance_sheet_action.triggered.connect(self.open_balance_sheet_report)
        report_menu.addAction(balance_sheet_action)
        
        cash_flow_action = QAction("现金流量表", self)
        cash_flow_action.triggered.connect(self.open_cash_flow_report)
        report_menu.addAction(cash_flow_action)
        
        # 管理菜单
        manage_menu = menu_bar.addMenu("管理")
        
        account_manage_action = QAction("账户管理", self)
        account_manage_action.triggered.connect(self.open_account_tab)
        manage_menu.addAction(account_manage_action)
        
        category_manage_action = QAction("分类管理", self)
        category_manage_action.triggered.connect(self.open_category_tab)
        manage_menu.addAction(category_manage_action)
        
        # 如果是管理员，显示用户管理菜单
        if self.user_info['role'] == 'admin':
            user_manage_action = QAction("用户管理", self)
            user_manage_action.triggered.connect(self.open_user_management)
            manage_menu.addAction(user_manage_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        # 设置菜单栏
        self.setMenuBar(menu_bar)
    
    def create_tool_bar(self):
        """创建工具栏"""
        tool_bar = QToolBar("工具栏")
        tool_bar.setIconSize(QSize(16, 16))
        
        # 添加常用操作按钮
        new_transaction_action = QAction("新建账务", self)
        new_transaction_action.triggered.connect(self.open_transaction_tab)
        tool_bar.addAction(new_transaction_action)
        
        tool_bar.addSeparator()
        
        generate_report_action = QAction("生成报表", self)
        generate_report_action.triggered.connect(self.open_report_tab)
        tool_bar.addAction(generate_report_action)
        
        tool_bar.addSeparator()
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        tool_bar.addAction(settings_action)
        
        # 添加工具栏
        self.addToolBar(tool_bar)
    
    def create_status_bar(self):
        """创建状态栏"""
        status_bar = QStatusBar()
        
        # 添加状态栏信息
        user_label = QLabel(f"当前用户: {self.user_info['fullname']}")
        status_bar.addWidget(user_label)
        
        # 在PyQt5中使用空格标签模拟分隔符
        separator = QLabel(" | ")
        status_bar.addWidget(separator)
        
        time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        status_bar.addPermanentWidget(time_label)
        
        # 更新时间定时器
        from PyQt5.QtCore import QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: time_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.timer.start(1000)
        
        # 设置状态栏
        self.setStatusBar(status_bar)
    
    def connect_components(self):
        """连接各个组件的信号与槽"""
        try:
            # 连接交易保存与报表更新
            if TransactionWidget is not None and ReportWidget is not None:
                self.transaction_widget.data_updated.connect(self.report_widget.update_reports)
        except Exception as e:
            print(f"组件连接失败: {str(e)}")
            
    def create_sidebar(self):
        """创建侧边栏"""
        # 创建侧边栏部件
        sidebar = QDockWidget("功能导航", self)
        sidebar.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        sidebar.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        
        # 创建侧边栏内容
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(5)
        
        # 添加导航按钮
        self.add_nav_button(sidebar_layout, "首页", lambda: self.tab_widget.setCurrentWidget(self.dashboard_widget))
        self.add_nav_button(sidebar_layout, "账务处理", lambda: self.tab_widget.setCurrentWidget(self.transaction_widget))
        self.add_nav_button(sidebar_layout, "报表分析", lambda: self.tab_widget.setCurrentWidget(self.report_widget))
        self.add_nav_button(sidebar_layout, "账户管理", lambda: self.tab_widget.setCurrentWidget(self.account_widget))
        self.add_nav_button(sidebar_layout, "分类管理", lambda: self.tab_widget.setCurrentWidget(self.category_widget))
        
        # 如果是管理员，显示用户管理按钮
        if self.user_info['role'] == 'admin':
            sidebar_layout.addStretch(1)
            self.add_nav_button(sidebar_layout, "用户管理", self.open_user_management)
        
        sidebar_layout.addStretch(1)
        
        # 设置侧边栏内容
        sidebar.setWidget(sidebar_widget)
        
        # 添加侧边栏
        self.addDockWidget(Qt.LeftDockWidgetArea, sidebar)
    
    def add_nav_button(self, layout, text, callback):
        """添加导航按钮到侧边栏"""
        from PyQt5.QtWidgets import QPushButton
        
        button = QPushButton(text)
        button.setFixedHeight(36)
        button.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 15px;
                border: 1px solid transparent;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-family: SimHei;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #dee2e6;
            }
            QPushButton:pressed {
                background-color: #1a73e8;
                color: white;
            }
        """)
        button.clicked.connect(callback)
        layout.addWidget(button)
    
    def show_welcome_message(self):
        """显示欢迎信息"""
        welcome_text = f"欢迎回来，{self.user_info['fullname']}！"
        if self.user_info['role'] == 'admin':
            welcome_text += " 您拥有管理员权限。"
        
        self.statusBar().showMessage(welcome_text, 5000)
    
    def on_tab_changed(self, index):
        """标签页切换事件处理"""
        tab_text = self.tab_widget.tabText(index)
        self.statusBar().showMessage(f"当前视图: {tab_text}")
    
    def open_transaction_tab(self):
        """打开账务处理标签页"""
        self.tab_widget.setCurrentWidget(self.transaction_widget)
    
    def open_report_tab(self):
        """打开报表分析标签页"""
        self.tab_widget.setCurrentWidget(self.report_widget)
    
    def open_account_tab(self):
        """打开账户管理标签页"""
        self.tab_widget.setCurrentWidget(self.account_widget)
    
    def open_category_tab(self):
        """打开分类管理标签页"""
        self.tab_widget.setCurrentWidget(self.category_widget)
    
    def open_profit_loss_report(self):
        """打开利润表报表"""
        self.tab_widget.setCurrentWidget(self.report_widget)
        # 这里可以调用报表部件的方法来显示特定报表
    
    def open_balance_sheet_report(self):
        """打开资产负债表报表"""
        self.tab_widget.setCurrentWidget(self.report_widget)
        # 这里可以调用报表部件的方法来显示特定报表
    
    def open_cash_flow_report(self):
        """打开现金流量表报表"""
        self.tab_widget.setCurrentWidget(self.report_widget)
        # 这里可以调用报表部件的方法来显示特定报表
    
    def open_user_management(self):
        """打开用户管理"""
        # 检查是否已存在用户管理标签页
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "用户管理":
                self.tab_widget.setCurrentIndex(i)
                return
        
        # 导入用户管理模块
        from src.ui.user_management_widget import UserManagementWidget
        
        # 创建用户管理标签页
        user_management_widget = UserManagementWidget(self.user_info)
        self.tab_widget.addTab(user_management_widget, "用户管理")
        self.tab_widget.setCurrentWidget(user_management_widget)
    
    def open_settings(self):
        """打开系统设置"""
        # 检查是否已存在设置标签页
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "系统设置":
                self.tab_widget.setCurrentIndex(i)
                return
        
        # 创建设置标签页
        setting_widget = SettingWidget(self.user_info)
        self.tab_widget.addTab(setting_widget, "系统设置")
        self.tab_widget.setCurrentWidget(setting_widget)
    
    def backup_database(self):
        """备份数据库"""
        try:
            from src.database.db_manager import backup_database
            
            # 显示文件对话框选择备份路径
            from PyQt5.QtWidgets import QFileDialog
            
            default_filename = f"finance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path, _ = QFileDialog.getSaveFileName(
                self, "备份数据库", default_filename, "数据库文件 (*.db);;所有文件 (*)"
            )
            
            if backup_path:
                # 执行备份
                backup_file = backup_database(backup_path)
                QMessageBox.information(self, "备份成功", f"数据库已成功备份到:\n{backup_file}")
        
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"数据库备份失败:\n{str(e)}")
    
    def restore_database(self):
        """恢复数据库"""
        try:
            from src.database.db_manager import restore_database
            
            # 显示文件对话框选择备份文件
            from PyQt5.QtWidgets import QFileDialog
            
            backup_path, _ = QFileDialog.getOpenFileName(
                self, "恢复数据库", "", "数据库文件 (*.db);;所有文件 (*)"
            )
            
            if backup_path:
                # 确认恢复操作
                reply = QMessageBox.question(
                    self, "确认恢复", 
                    "恢复数据库将覆盖当前所有数据，确定要继续吗？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 执行恢复
                    restore_database(backup_path)
                    QMessageBox.information(self, "恢复成功", "数据库已成功恢复")
                    
                    # 提示重启应用
                    QMessageBox.information(self, "提示", "请重启应用以应用数据库更改")
        
        except Exception as e:
            QMessageBox.critical(self, "恢复失败", f"数据库恢复失败:\n{str(e)}")
    
    def show_about_dialog(self):
        """显示关于对话框"""
        about_text = """企业财务账目录入与利润核算系统\n\n"""
        about_text += "版本: 1.0.0\n\n"
        about_text += "功能特点:\n"
        about_text += "- 财务账目录入与管理\n"
        about_text += "- 利润核算与分析\n"
        about_text += "- 财务报表生成\n"
        about_text += "- 数据可视化展示\n"
        about_text += "- 多用户权限管理\n\n"
        about_text += "© 2025 企业财务管理软件"
        
        QMessageBox.about(self, "关于系统", about_text)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        reply = QMessageBox.question(
            self, "确认退出", 
            "确定要退出系统吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    # 用于测试主窗口
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
    
    # 创建并显示主窗口
    main_window = MainWindow(test_user)
    main_window.show()
    
    sys.exit(app.exec_())