"""
工具接口基类
所有工具必须继承此基类并实现所有抽象方法
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable, Any


class ToolInterface(ABC):
    """
    工具接口定义
    所有生物信息学工具必须实现此接口
    """
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取工具元数据
        
        Returns:
            包含以下字段的字典:
            - name: str - 工具名称
            - version: str - 版本号
            - category: str - 分类(quality/sequence/genomics/rnaseq/phylogeny)
            - description: str - 工具描述
            - size: str - 安装大小
            - requires: list - 依赖项列表
            - status: str - 安装状态(installed/available/update)
        """
        pass
    
    @abstractmethod
    def get_download_sources(self) -> List[Dict[str, Any]]:
        """
        获取下载源列表
        
        Returns:
            下载源列表，每个源包含:
            - name: str - 源名称
            - url: str - 下载地址
            - priority: int - 优先级(1最高)
            - location: str - 服务器位置(CN/US/UK等)
        """
        pass
    
    @abstractmethod
    def install(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> bool:
        """
        安装工具
        
        Args:
            progress_callback: 进度回调函数，接收(status_text, percentage)
            
        Returns:
            bool - 安装是否成功
        """
        pass
    
    @abstractmethod
    def uninstall(self) -> bool:
        """
        卸载工具
        
        Returns:
            bool - 卸载是否成功
        """
        pass
    
    @abstractmethod
    def launch(self, args: Optional[List[str]] = None) -> bool:
        """
        启动工具
        
        Args:
            args: 启动参数列表
            
        Returns:
            bool - 启动是否成功
        """
        pass
    
    @abstractmethod
    def verify_installation(self) -> bool:
        """
        验证工具是否已安装
        
        Returns:
            bool - 是否已安装
        """
        pass
    
    @abstractmethod
    def check_dependencies(self) -> Dict[str, bool]:
        """
        检查依赖项
        
        Returns:
            依赖项检查结果，key为依赖名，value为是否满足
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式，供UI层使用
        
        Returns:
            包含工具所有信息的字典
        """
        metadata = self.get_metadata()
        metadata['installed'] = self.verify_installation()
        return metadata