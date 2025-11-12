#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用cx_Freeze打包应用程序的配置脚本
"""

import sys
import os
from cx_Freeze import setup, Executable

# 获取当前文件所在目录
base_dir = os.path.dirname(os.path.abspath(__file__))

# 设置Python路径，确保可以找到项目模块
sys.path.append(base_dir)

# 判断是否为Windows平台
if sys.platform == "win32":
    base = "Win32GUI"  # 不显示控制台窗口
else:
    base = None

# 定义包含的文件和目录
include_files = [
    (os.path.join(base_dir, "src", "resources"), "resources"),
    (os.path.join(base_dir, "data"), "data"),
    (os.path.join(base_dir, "logs"), "logs"),
]

# 构建选项配置
build_exe_options = {
    # 包含的Python包
    "packages": [
        "os", "sys", "PyQt5", "sqlite3", "matplotlib", 
        "pandas", "numpy", "passlib", "yaml", "dateutil",
        "matplotlib.backends.backend_qt5agg"
    ],
    # 排除的包
    "excludes": [
        "tkinter", "jupyter", "notebook", "IPython",
        "docutils", "setuptools", "pkg_resources"
    ],
    # 包含的文件
    "include_files": include_files,
    # 包含的模块
    "includes": [
        "PyQt5.sip", "PyQt5.QtPrintSupport", 
        "matplotlib.backends.backend_qt5", "matplotlib.figure"
    ],
    # 压缩级别 (0-9)
    "optimize": 2,
    # 包含Microsoft Visual C++运行时库
    "include_msvcr": True,
    # 输出目录
    "build_exe": os.path.join(base_dir, "build"),
}

# 定义可执行文件
executables = [
    Executable(
        script=os.path.join(base_dir, "main.py"),  # 主脚本
        base=base,                                 # GUI模式
        target_name="财务账目录入与利润核算系统.exe",  # 输出文件名
        icon=os.path.join(base_dir, "src", "resources", "icons", "app_icon.svg"),  # 图标文件
        shortcut_name="企业财务账目录入与利润核算系统",  # 快捷方式名称
        shortcut_dir="ProgramMenuFolder",  # 快捷方式目录
        copyright="© 2024 企业财务账目录入与利润核算系统开发团队"
    )
]

# 设置信息
setup(
    name="企业财务账目录入与利润核算系统",
    version="1.0.0",
    description="企业财务账目录入与利润核算系统 - 提供全面的财务管理解决方案",
    author="Finance System Development Team",
    author_email="finance-system@example.com",
    options={"build_exe": build_exe_options},
    executables=executables,
    # 安装后的元数据
    license="MIT",
    keywords="财务 会计 管理系统 利润核算",
    url="https://example.com/finance-management-system",
)

if __name__ == "__main__":
    # 可以在这里添加额外的打包前检查或准备工作
    print("开始使用cx_Freeze打包应用程序...")
    # 确保数据目录存在
    data_dir = os.path.join(base_dir, "data")
    logs_dir = os.path.join(base_dir, "logs")
    
    for directory in [data_dir, logs_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建目录: {directory}")
    
    print("准备工作完成，请运行: python setup_cxfreeze.py build")