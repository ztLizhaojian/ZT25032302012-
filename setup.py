#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业财务账目录入与利润核算系统 - 安装配置脚本
用于打包和安装应用程序
"""

import os
import sys
from setuptools import setup, find_packages

# 获取项目根目录
here = os.path.abspath(os.path.dirname(__file__))

# 读取版本信息
version = "1.0.0"

# 读取依赖项
with open(os.path.join(here, 'requirements.txt'), 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# 读取README内容
try:
    with open(os.path.join(here, 'README.md'), 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "企业财务账目录入与利润核算系统 - 提供全面的财务管理解决方案"

# 定义包数据
package_data = {
    'src': ['resources/*', 'resources/icons/*', 'resources/styles/*'],
}

# 定义安装配置
setup(
    # 基本信息
    name="finance-management-system",
    version=version,
    description="企业财务账目录入与利润核算系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://example.com/finance-management-system",
    author="Finance System Development Team",
    author_email="finance-system@example.com",
    license="MIT",
    
    # 分类信息
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Win32 (MS Windows)",
        "Intended Audience :: Business/Enterprise",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Chinese (Simplified)",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    
    # 语言
    keywords="财务 会计 管理系统 利润核算",
    
    # 包信息
    packages=find_packages(include=['src', 'src.*']),
    package_data=package_data,
    
    # 依赖项
    install_requires=requirements,
    
    # 额外依赖
    extras_require={
        'dev': ['pytest>=6.0', 'black>=21.5b1', 'flake8>=3.9.0'],
        'test': ['pytest>=6.0', 'coverage>=5.5'],
    },
    
    # 入口点
    entry_points={
        'console_scripts': [
            'finance-system=src.main:main',
        ],
    },
    
    # 数据文件
    data_files=[
        ('finance-system', ['README.md', 'requirements.txt']),
        ('finance-system/data', []),
        ('finance-system/logs', []),
    ],
    
    # Python版本要求
    python_requires='>=3.8,<3.11',
    
    # 其他选项
    include_package_data=True,
    zip_safe=False,
    project_urls={
        'Bug Reports': 'https://example.com/finance-management-system/issues',
        'Documentation': 'https://example.com/finance-management-system/docs',
        'Source': 'https://example.com/finance-management-system/source',
    },
)