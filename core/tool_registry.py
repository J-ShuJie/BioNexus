"""
工具注册中心
自动发现和管理所有工具插件
"""
import importlib
import pkgutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from .tools.base import ToolInterface


class ToolRegistry:
    """
    工具注册中心
    自动发现tools目录下的所有工具并进行管理
    """
    
    def __init__(self):
        """初始化注册中心"""
        self.tools: Dict[str, ToolInterface] = {}
        self.logger = logging.getLogger(__name__)
        self.discover_tools()
    
    def discover_tools(self):
        """
        自动发现并加载所有工具
        扫描core/tools目录下的所有Python模块
        """
        tools_dir = Path(__file__).parent / 'tools'
        
        if not tools_dir.exists():
            self.logger.warning(f"工具目录不存在: {tools_dir}")
            return
        
        # 遍历tools目录下的所有模块
        for module_info in pkgutil.iter_modules([str(tools_dir)]):
            # 跳过私有模块和base模块
            if module_info.name.startswith('_') or module_info.name == 'base':
                continue
            
            try:
                # 动态导入模块
                module_name = f'core.tools.{module_info.name}'
                module = importlib.import_module(module_name)
                
                # 查找实现了ToolInterface的类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    # 检查是否是类且继承自ToolInterface
                    if (isinstance(attr, type) and 
                        issubclass(attr, ToolInterface) and 
                        attr != ToolInterface):
                        
                        # 实例化工具类
                        tool_instance = attr()
                        
                        # 获取工具元数据
                        metadata = tool_instance.get_metadata()
                        tool_name = metadata.get('name')
                        
                        if tool_name:
                            self.tools[tool_name] = tool_instance
                            self.logger.info(f"已注册工具: {tool_name}")
                        else:
                            self.logger.warning(f"工具缺少名称: {attr_name}")
                            
            except Exception as e:
                self.logger.error(f"加载工具模块失败 {module_info.name}: {e}")
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """
        获取所有已注册工具的信息
        
        Returns:
            工具信息列表，每个元素是工具的元数据字典
        """
        tools_list = []
        for tool in self.tools.values():
            try:
                tools_list.append(tool.to_dict())
            except Exception as e:
                self.logger.error(f"获取工具信息失败: {e}")
        return tools_list
    
    def get_tool(self, name: str) -> Optional[ToolInterface]:
        """
        获取指定名称的工具实例
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，如果不存在则返回None
        """
        return self.tools.get(name)
    
    def get_tool_names(self) -> List[str]:
        """
        获取所有已注册工具的名称列表
        
        Returns:
            工具名称列表
        """
        return list(self.tools.keys())
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        获取指定分类的工具列表
        
        Args:
            category: 工具分类
            
        Returns:
            该分类下的工具信息列表
        """
        tools_list = []
        for tool in self.tools.values():
            try:
                metadata = tool.get_metadata()
                if metadata.get('category') == category:
                    tools_list.append(tool.to_dict())
            except Exception as e:
                self.logger.error(f"获取工具分类信息失败: {e}")
        return tools_list
    
    def get_installed_tools(self) -> List[Dict[str, Any]]:
        """
        获取所有已安装的工具列表
        
        Returns:
            已安装工具的信息列表
        """
        installed_tools = []
        for tool in self.tools.values():
            try:
                if tool.verify_installation():
                    installed_tools.append(tool.to_dict())
            except Exception as e:
                self.logger.error(f"检查工具安装状态失败: {e}")
        return installed_tools
    
    def refresh(self):
        """
        刷新工具注册表
        重新扫描并加载所有工具
        """
        self.tools.clear()
        self.discover_tools()
    
    def register_tool(self, tool: ToolInterface) -> bool:
        """
        手动注册一个工具
        
        Args:
            tool: 工具实例
            
        Returns:
            是否注册成功
        """
        try:
            metadata = tool.get_metadata()
            name = metadata.get('name')
            
            if not name:
                self.logger.error("工具缺少名称，无法注册")
                return False
            
            if name in self.tools:
                self.logger.warning(f"工具 {name} 已存在，将被覆盖")
            
            self.tools[name] = tool
            self.logger.info(f"成功注册工具: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"注册工具失败: {e}")
            return False
    
    def unregister_tool(self, name: str) -> bool:
        """
        注销一个工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否注销成功
        """
        if name in self.tools:
            del self.tools[name]
            self.logger.info(f"已注销工具: {name}")
            return True
        else:
            self.logger.warning(f"工具 {name} 不存在")
            return False