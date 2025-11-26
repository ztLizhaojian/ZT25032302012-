#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业财务账目录入与利润核算系统
主入口文件
"""

import sys
import os
import logging
import argparse
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 确保日志目录存在
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'app.log'), 'a', 'utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Main')

# 导入PyQt组件
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer, QSettings

# 导入登录窗口
from src.ui.login_window import LoginWindow
# 导入数据库初始化
from src.database.db_manager import init_db as init_database

# 应用程序版本
APP_VERSION = "1.0.0"
APP_NAME = "企业财务系统"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')


def load_config():
    """加载配置文件"""
    default_config = {
        "app_theme": "light",
        "show_splash": True,
        "splash_duration": 1500,
        "auto_check_updates": False
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}  # 合并默认配置和用户配置
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
    return default_config


def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存配置文件失败: {str(e)}")


def set_application_font(app):
    """动态设置应用程序字体，确保中文正常显示"""
    # 尝试使用多种中文字体作为备选
    for font_family in ["SimHei", "Microsoft YaHei", "Arial Unicode MS", "WenQuanYi Micro Hei", "Heiti TC"]:
        font = QFont(font_family, 9)
        if font.exactMatch():
            app.setFont(font)
            logger.info(f"已设置应用字体: {font_family}")
            return True
    # 如果没有找到理想的字体，设置默认字体
    font = QFont()
    font.setFamily("Sans Serif")
    font.setPointSize(9)
    app.setFont(font)
    logger.info("使用默认字体")
    return False


def create_splash_screen(app):
    """创建启动画面"""
    splash = QSplashScreen(QPixmap(), Qt.WindowStaysOnTopHint)
    splash.setStyleSheet("background-color: #ffffff;")
    
    # 尝试加载自定义启动图片
    splash_image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'splash.png')
    if os.path.exists(splash_image_path):
        try:
            pixmap = QPixmap(splash_image_path)
            splash.setPixmap(pixmap)
        except Exception as e:
            logger.warning(f"加载启动图片失败: {str(e)}")
    
    # 显示启动信息
    splash.showMessage(f"正在初始化 {APP_NAME} v{APP_VERSION}...", 
                      Qt.AlignBottom | Qt.AlignCenter, Qt.black)
    splash.show()
    app.processEvents()
    return splash


def initialize_database():
    """初始化数据库并返回状态"""
    try:
        init_database()
        logger.info("数据库初始化成功")
        return True
    except Exception as e:
        error_msg = f"数据库初始化失败: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION}")
    parser.add_argument('--no-splash', action='store_true', help='不显示启动画面')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    return parser.parse_args()


def main():
    """主函数入口"""
    # 记录启动时间
    start_time = datetime.now()
    logger.info(f"{APP_NAME} v{APP_VERSION} 启动中...")
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 如果启用调试模式，设置日志级别为DEBUG
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")
    
    # 加载配置
    config = load_config()
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("企业财务管理")
    app.setOrganizationDomain("company.finance")
    
    # 设置应用程序字体
    set_application_font(app)
    
    # 创建并显示启动画面
    splash = None
    if config["show_splash"] and not args.no_splash:
        splash = create_splash_screen(app)
    
    try:
        # 初始化数据库
        db_result = initialize_database()
        if isinstance(db_result, tuple) and db_result[0] is False:
            # 数据库初始化失败，但仍尝试继续启动应用
            logger.warning("数据库初始化失败，但将继续启动应用")
        
        # 显示启动画面一段时间
        if splash:
            QTimer.singleShot(config["splash_duration"], splash.close)
        
        # 显示登录窗口
        login_window = LoginWindow()
        login_window.show()
        
        # 记录启动完成时间
        end_time = datetime.now()
        logger.info(f"应用启动完成，耗时: {(end_time - start_time).total_seconds():.2f} 秒")
        
        # 启动应用程序主循环
        sys.exit(app.exec_())
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
        sys.exit(0)
    except Exception as e:
        error_msg = f"应用程序启动失败: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        # 即使发生错误，也尝试显示登录窗口作为最后的保障
        try:
            if splash:
                splash.close()
            login_window = LoginWindow()
            login_window.show()
            sys.exit(app.exec_())
        except:
            # 如果连登录窗口都无法显示，则退出
            sys.exit(1)


if __name__ == "__main__":
    # 导入traceback用于详细错误记录
    import traceback
    main()