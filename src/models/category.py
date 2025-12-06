# 分类模型
from src.database.db_manager import execute_query, log_operation


class CategoryModel:
    """分类模型类，负责分类相关的业务逻辑处理"""
    
    @staticmethod
    def create_category(data, user_id):
        """
        创建新分类
        
        Args:
            data: 包含分类信息的字典
            user_id: 操作用户ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 插入分类记录
            execute_query(
                """INSERT INTO categories (name, category_type, parent_id, 
                description, status, created_by, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    data['name'],
                    data['category_type'],
                    data.get('parent_id') or None,
                    data.get('description', ''),
                    data.get('status', 'active'),
                    user_id,
                    data['created_at']
                )
            )
            
            # 记录操作日志
            log_operation(
                user_id,
                'create_category',
                f"创建了分类: {data['name']} ({data['category_type']})"
            )
            
            return True
            
        except Exception as e:
            print(f"创建分类失败: {str(e)}")
            return False
    
    @staticmethod
    def update_category(category_id, data, user_id):
        """
        更新分类信息
        
        Args:
            category_id: 分类ID
            data: 包含更新信息的字典
            user_id: 操作用户ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 更新分类记录
            execute_query(
                """UPDATE categories SET name = ?, category_type = ?, parent_id = ?, 
                description = ?, status = ?, updated_by = ?, updated_at = ? 
                WHERE id = ?""",
                (
                    data['name'],
                    data['category_type'],
                    data.get('parent_id') or None,
                    data.get('description', ''),
                    data.get('status', 'active'),
                    user_id,
                    data['updated_at'],
                    category_id
                )
            )
            
            # 记录操作日志
            log_operation(
                user_id,
                'update_category',
                f"更新了分类ID: {category_id}"
            )
            
            return True
            
        except Exception as e:
            print(f"更新分类失败: {str(e)}")
            return False
    
    @staticmethod
    def delete_category(category_id, user_id):
        """
        删除分类
        
        Args:
            category_id: 分类ID
            user_id: 操作用户ID
            
        Returns:
            tuple: (是否成功, 错误信息)
        """
        try:
            # 检查分类是否有子分类
            child_count = execute_query(
                "SELECT COUNT(*) as count FROM categories WHERE parent_id = ?",
                (category_id,),
                fetch=True
            )
            
            if child_count and child_count['count'] > 0:
                return False, "该分类有子分类，无法删除"
            
            # 检查分类是否有交易记录
            transaction_count = execute_query(
                "SELECT COUNT(*) as count FROM transactions WHERE category_id = ?",
                (category_id,),
                fetch=True
            )
            
            if transaction_count and transaction_count['count'] > 0:
                return False, "该分类存在交易记录，无法删除"
            
            # 获取分类名称用于日志
            category = CategoryModel.get_category_by_id(category_id)
            category_name = category['name'] if category else str(category_id)
            
            # 删除分类
            execute_query("DELETE FROM categories WHERE id = ?", (category_id,))
            
            # 记录操作日志
            log_operation(
                user_id,
                'delete_category',
                f"删除了分类: {category_name}"
            )
            
            return True, ""
            
        except Exception as e:
            print(f"删除分类失败: {str(e)}")
            return False, f"删除失败: {str(e)}"
    
    @staticmethod
    def get_category_by_id(category_id):
        """
        根据ID获取分类信息
        
        Args:
            category_id: 分类ID
            
        Returns:
            dict: 分类信息
        """
        try:
            result = execute_query(
                "SELECT * FROM categories WHERE id = ?",
                (category_id,),
                fetch=True
            )
            return result
            
        except Exception as e:
            print(f"获取分类信息失败: {str(e)}")
            return None
    
    @staticmethod
    def get_all_categories(filters=None):
        """
        获取所有分类列表
        
        Args:
            filters: 过滤条件字典
            
        Returns:
            list: 分类列表
        """
        try:
            # 构建查询语句
            query = "SELECT * FROM categories WHERE 1=1"
            params = []
            
            # 添加过滤条件
            if filters:
                if 'category_type' in filters and filters['category_type']:
                    query += " AND type = ?"
                    params.append(filters['category_type'])
                
                if 'status' in filters and filters['status']:
                    query += " AND status = ?"
                    params.append(filters['status'])
                
                if 'parent_id' in filters and filters['parent_id'] is not None:
                    if filters['parent_id'] == 'None' or filters['parent_id'] == 'null':
                        query += " AND parent_id IS NULL"
                    else:
                        query += " AND parent_id = ?"
                        params.append(filters['parent_id'])
                
                if 'name' in filters and filters['name']:
                    query += " AND name LIKE ?"
                    params.append(f"%{filters['name']}%")
            
            # 添加排序
            query += " ORDER BY name"
            
            # 执行查询
            results = execute_query(query, params, fetch_all=True)
            
            return results
            
        except Exception as e:
            print(f"获取分类列表失败: {str(e)}")
            return []
    
    @staticmethod
    def get_categories_by_type(category_type, include_inactive=False):
        """
        根据分类类型获取分类列表
        
        Args:
            category_type: 分类类型 (income 或 expense)
            include_inactive: 是否包含非活跃分类
            
        Returns:
            list: 分类列表
        """
        try:
            query = "SELECT * FROM categories WHERE category_type = ?"
            params = [category_type]
            
            if not include_inactive:
                query += " AND status = 'active'"
            
            query += " ORDER BY name"
            
            results = execute_query(query, params, fetch_all=True)
            
            return results
            
        except Exception as e:
            print(f"获取分类列表失败: {str(e)}")
            return []
    
    @staticmethod
    def get_category_hierarchy(category_type):
        """
        获取分类层次结构
        
        Args:
            category_type: 分类类型 (income 或 expense)
            
        Returns:
            dict: 分类层次结构字典
        """
        try:
            # 获取所有分类
            categories = CategoryModel.get_categories_by_type(category_type)
            
            # 构建层次结构
            category_dict = {}
            root_categories = []
            
            # 首先将所有分类添加到字典中
            for cat in categories:
                category_id = cat['id']
                category_dict[category_id] = {
                    'id': category_id,
                    'name': cat['name'],
                    'children': []
                }
            
            # 然后构建父子关系
            for cat in categories:
                category_id = cat['id']
                parent_id = cat['parent_id']
                
                if parent_id is None:
                    # 根分类
                    root_categories.append(category_dict[category_id])
                elif parent_id in category_dict:
                    # 子分类
                    category_dict[parent_id]['children'].append(category_dict[category_id])
            
            return {
                'categories': root_categories,
                'flat_list': categories
            }
            
        except Exception as e:
            print(f"获取分类层次结构失败: {str(e)}")
            return {'categories': [], 'flat_list': []}
    
    @staticmethod
    def get_category_statistics(category_type, start_date=None, end_date=None):
        """
        获取分类统计信息
        
        Args:
            category_type: 分类类型 (income 或 expense)
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            list: 分类统计信息列表
        """
        try:
            # 构建查询语句
            query = """
            SELECT c.id, c.name, SUM(t.amount) as total_amount, COUNT(t.id) as transaction_count 
            FROM categories c 
            LEFT JOIN transactions t ON c.id = t.category_id 
            WHERE c.category_type = ?
            """
            
            params = [category_type]
            
            # 添加日期过滤
            if start_date:
                query += " AND t.transaction_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND t.transaction_date <= ?"
                params.append(end_date)
            
            # 分组和排序
            query += " GROUP BY c.id, c.name ORDER BY total_amount DESC"
            
            results = execute_query(query, params, fetch_all=True)
            
            # 确保金额为正数（特别是对于支出）
            for result in results:
                if result['total_amount'] is not None:
                    result['total_amount'] = abs(float(result['total_amount']))
                else:
                    result['total_amount'] = 0
                
                if result['transaction_count'] is None:
                    result['transaction_count'] = 0
            
            return results
            
        except Exception as e:
            print(f"获取分类统计信息失败: {str(e)}")
            return []
    
    @staticmethod
    def validate_category(data):
        """
        验证分类数据的有效性
        
        Args:
            data: 分类数据字典
            
        Returns:
            tuple: (是否有效, 错误信息)
        """
        # 验证分类名称
        if not data.get('name') or not data['name'].strip():
            return False, "分类名称不能为空"
        
        # 验证分类类型
        valid_types = ['income', 'expense']
        if data.get('category_type') not in valid_types:
            return False, "无效的分类类型"
        
        # 验证父分类（如果有）
        if 'parent_id' in data and data['parent_id'] and data['parent_id'] != 'None' and data['parent_id'] != 'null':
            try:
                parent_id = int(data['parent_id'])
                parent_category = CategoryModel.get_category_by_id(parent_id)
                
                if not parent_category:
                    return False, "指定的父分类不存在"
                
                if parent_category['category_type'] != data['category_type']:
                    return False, "父分类类型必须与当前分类类型相同"
                    
            except ValueError:
                return False, "无效的父分类ID"
        
        return True, ""