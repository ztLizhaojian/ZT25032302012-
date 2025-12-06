# 测试UserModel的create_user方法
from src.models.user_model import UserModel

print("测试UserModel.create_user方法...")

try:
    # 创建测试用户
    result = UserModel.create_user({
        'username': 'testuser123',
        'password': 'Test@1234',
        'fullname': '测试用户',
        'email': 'test@example.com'
    })
    
    print(f"创建用户结果: {result}")
    
    if result['success']:
        print("✓ 用户创建成功")
    else:
        print("✗ 用户创建失败")
        
except Exception as e:
    print(f"✗ 创建用户出错: {str(e)}")
    import traceback
    traceback.print_exc()