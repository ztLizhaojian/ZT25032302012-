#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业财务账目录入与利润核算系统
主入口文件
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入登录窗口
from src.ui.login_window import LoginWindow
# 导入数据库初始化
from src.database.db_manager import init_database

# 应用程序版本
APP_VERSION = "1.0.0"
APP_NAME = "企业财务系统"


def main():
    """主函数入口"""
    # 创建应用程序实例
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("企业财务管理")
    
    # 设置应用程序字体
    font = QFont("SimHei", 9)
    app.setFont(font)
    
    # 创建启动画面
    splash = QSplashScreen(QPixmap(), Qt.WindowStaysOnTopHint)
    splash.showMessage(f"正在初始化 {APP_NAME} v{APP_VERSION}...", 
                      Qt.AlignBottom | Qt.AlignCenter, Qt.black)
    splash.show()
    
    # 确保启动画面显示
    app.processEvents()
    
    try:
        # 初始化数据库
        init_database()
        
        # 显示启动画面一段时间
        QTimer.singleShot(1500, splash.close)
        
        # 显示登录窗口
        login_window = LoginWindow()
        login_window.show()
        
        # 启动应用程序主循环
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"应用程序启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()