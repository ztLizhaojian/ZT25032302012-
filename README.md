# 企业财务账目录入与利润核算系统

## 简介
本系统是一个完整的企业财务管理解决方案，提供账目录入、分类统计、报表生成等功能。

## 功能特点
- 用户认证与权限管理
- 账户管理（现金、银行账户等）
- 收支分类管理
- 交易记录录入与查询
- 数据可视化图表展示
- 报表生成与导出（Excel、PDF）
- 数据备份与恢复

## 运行环境
- Python 3.7+
- PyQt5
- SQLite数据库

## 安装依赖
```bash
pip install -r requirements.txt
```

## 初始化数据库
系统会自动初始化数据库，无需手动操作。

## 启动应用
```bash
python main.py
```

## 使用说明
1. 首次运行系统，默认管理员账号：
   - 用户名：admin
   - 密码：admin123
2. 登录后可在系统设置中修改密码

## 目录结构
```
├── src/              # 源代码目录
│   ├── ui/           # 用户界面组件
│   ├── database/     # 数据库管理模块
│   ├── models/       # 数据模型
│   ├── controllers/  # 控制器逻辑
│   └── utils/        # 工具类
├── data/             # 数据存储目录
├── logs/             # 日志文件目录
└── docs/             # 文档资料
```

## 技术架构
- 前端：PyQt5 + QDarkStyle
- 后端：Python原生开发
- 数据库：SQLite
- 图表：Matplotlib + PyQtChart