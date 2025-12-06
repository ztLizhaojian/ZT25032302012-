#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("init_database.log"),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger("InitDatabase")

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('src')

def main():
    """主函数"""
    try:
        logger.info("开始初始化数据库...")
        
        # 导入数据库模块
        from database.db_manager import init_db
        from database.db_migration import DBMigration
        
        # 初始化数据库
        init_db()
        
        # 获取数据库路径
        db_path = os.path.join('data', 'finance_system.db')
        
        # 创建迁移对象并插入初始数据
        migration = DBMigration(db_path)
        migration.insert_initial_data()
        
        logger.info("数据库初始化完成！")
        logger.info("默认管理员用户：admin/admin123")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)