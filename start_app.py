#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业财务系统启动器
"""

import os
import sys
import subprocess
import logging
import json
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Startup')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 依赖清单文件
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, 'requirements.txt')

# 主程序入口
MAIN_PROGRAM = os.path.join(PROJECT_ROOT, 'main.py')

def check_python_environment():
    """
    检查Python环境
    """
    logger.info("正在检查Python环境...")
    
    # 检查Python版本
    try:
        result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("未检测到Python环境。请先安装Python 3.7或更高版本。")
            return False
        
        python_version = result.stdout.strip()
        logger.info(f"已检测到Python版本: {python_version}")
        
        # 检查Python版本是否满足要求
        version_info = sys.version_info
        if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 7):
            logger.error(f"Python版本过低 ({python_version})，需要Python 3.7或更高版本。")
            return False
            
    except Exception as e:
        logger.error(f"检查Python环境时出错: {str(e)}")
        return False
    
    # 检查pip是否可用
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("未检测到pip。请确保Python安装时已包含pip。")
            return False
            
        pip_version = result.stdout.strip().split()[1]
        logger.info(f"已检测到pip版本: {pip_version}")
        
    except Exception as e:
        logger.error(f"检查pip时出错: {str(e)}")
        return False
    
    return True

def install_dependencies():
    """
    安装项目依赖
    """
    logger.info("正在检查并安装项目依赖...")
    
    if not os.path.exists(REQUIREMENTS_FILE):
        logger.warning(f"未找到依赖清单文件 {REQUIREMENTS_FILE}")
        return True
    
    try:
        # 使用pip安装依赖
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', REQUIREMENTS_FILE],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("依赖安装成功")
            return True
        else:
            logger.error(f"依赖安装失败: {result.stderr}")
            logger.warning("将尝试继续运行程序...")
            return True  # 即使安装失败也继续运行
            
    except Exception as e:
        logger.error(f"安装依赖时出错: {str(e)}")
        logger.warning("将尝试继续运行程序...")
        return True  # 即使出错也继续运行

def start_application():
    """
    启动主应用程序
    """
    logger.info("正在启动企业财务系统...")
    
    if not os.path.exists(MAIN_PROGRAM):
        logger.error(f"未找到主程序入口 {MAIN_PROGRAM}")
        return False
    
    try:
        # 启动主程序
        subprocess.run(
            [sys.executable, MAIN_PROGRAM],
            cwd=PROJECT_ROOT
        )
        return True
        
    except Exception as e:
        logger.error(f"启动应用程序时出错: {str(e)}")
        return False

def main():
    """
    启动器主函数
    """
    print("=============================================")
    print("企业财务账目录入与利润核算系统")
    print("=============================================")
    print()
    
    # 记录启动时间
    start_time = datetime.now()
    
    try:
        # 检查Python环境
        if not check_python_environment():
            print("\n按任意键退出...")
            input()
            sys.exit(1)
        
        print()
        
        # 安装依赖
        if not install_dependencies():
            print("\n按任意键退出...")
            input()
            sys.exit(1)
        
        print()
        
        # 启动应用程序
        if not start_application():
            print("\n按任意键退出...")
            input()
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"启动过程中出现未预期的错误: {str(e)}")
        print("\n按任意键退出...")
        input()
        sys.exit(1)
    
    # 计算并记录总启动时间
    total_time = datetime.now() - start_time
    logger.info(f"启动过程耗时: {total_time.total_seconds():.2f} 秒")

if __name__ == "__main__":
    main()
