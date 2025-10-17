"""
占位符工具基类
用于展示UI和作为接口示例，但不具备实际安装功能
这些工具将在未来版本中逐步实现

⚠️ 注意：继承此类的工具仅用于UI展示和接口演示
实际功能工具应继承 base.py 中的 ToolInterface
"""
from typing import Dict, List, Optional, Callable, Any
from .base import ToolInterface


class PlaceholderTool(ToolInterface):
    """
    占位符工具基类
    提供模拟的安装、卸载、启动功能，用于UI展示
    """
    
    # 子类需要覆盖的元数据
    METADATA = {
        'name': 'PlaceholderTool',
        'version': '0.0.0',
        'category': 'unknown',
        'description': '占位符工具',
        'size': '未知',
        'requires': [],
        'status': 'available',
        'homepage': '#',
        'documentation': '#',
        'license': '未知'
    }
    
    def __init__(self):
        """初始化占位符工具"""
        # 占位符工具不需要实际的安装路径
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取工具元数据"""
        # 添加占位符标记
        metadata = self.METADATA.copy()
        metadata['is_placeholder'] = True  # 标记为占位符
        metadata['status'] = 'available'  # 始终显示为可安装
        metadata['placeholder_message'] = '此工具功能即将推出'
        return metadata
    
    def get_download_sources(self) -> List[Dict[str, Any]]:
        """返回模拟的下载源"""
        return [
            {
                'name': '功能开发中',
                'url': '#',
                'priority': 1,
                'location': 'N/A',
                'message': '此工具的实际安装功能正在开发中'
            }
        ]
    
    def check_dependencies(self) -> Dict[str, bool]:
        """模拟依赖检查"""
        # 返回空依赖或模拟依赖
        if self.METADATA.get('requires'):
            return {dep: False for dep in self.METADATA['requires']}
        return {}
    
    def install(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """
        模拟安装过程
        ⚠️ 注意：这只是UI演示，不会实际安装任何文件
        """
        import time
        
        if progress_callback:
            progress_callback("🚧 此工具暂未实现实际安装功能", 0)
            time.sleep(1)
            progress_callback("这是一个占位符，用于展示UI效果", 50)
            time.sleep(1)
            progress_callback("实际功能将在后续版本中实现", 100)
        
        # 返回False表示没有实际安装
        return False
    
    def uninstall(self) -> bool:
        """
        模拟卸载
        占位符工具没有实际文件，直接返回True
        """
        return True
    
    def launch(self, args: Optional[List[str]] = None) -> bool:
        """
        模拟启动
        显示提示信息
        """
        print(f"⚠️ {self.METADATA['name']} 是占位符工具，暂无实际功能")
        return False
    
    def verify_installation(self) -> bool:
        """
        验证安装状态
        占位符工具始终返回未安装
        """
        return False