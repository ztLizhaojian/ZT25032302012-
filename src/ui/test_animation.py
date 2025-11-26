#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from login_window import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置应用程序字体以确保中文正常显示
    font_set = False
    for font_family in ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "WenQuanYi Micro Hei", "Heiti TC"]:
        font = QFont(font_family, 9)
        if font.exactMatch():
            app.setFont(font)
            font_set = True
            break
    
    if not font_set:
        app.setFont(QFont("Sans Serif", 9))
    
    # 创建并显示登录窗口
    login_window = LoginWindow()
    login_window.show()
    
    sys.exit(app.exec_())