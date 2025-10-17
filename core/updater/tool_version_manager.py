"""
生物信息学工具版本管理器
管理所有集成工具的版本检查和更新
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path


class ToolVersionManager:
    """
    生物信息学工具版本管理器
    
    负责：
    1. 检查已安装工具的版本更新
    2. 发现新的可用工具
    3. 管理工具版本历史记录
    4. 提供工具更新建议
    """
    
    def __init__(self, config_manager=None):
        """初始化工具版本管理器"""
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # 延迟导入以避免循环依赖和PyQt5依赖
        self.tool_manager = None
        
        # 版本检查缓存
        self._version_cache = {}
        self._cache_duration = 3600  # 1小时缓存
        
        self.logger.info("工具版本管理器初始化完成")
    
    def check_tool_updates(self) -> Dict[str, Any]:
        """
        检查所有已安装工具的版本更新
        
        Returns:
            Dict: 更新信息
            格式: {
                'updates_available': True/False,
                'tool_updates': [
                    {
                        'name': 'FastQC',
                        'current_version': '0.11.9',
                        'latest_version': '0.12.1',
                        'update_size': '11.2 MB',
                        'changelog': 'Bug fixes and improvements',
                        'priority': 'recommended'  # critical, recommended, optional
                    }
                ],
                'new_tools': [
                    {
                        'name': 'MultiQC',
                        'description': 'Aggregate results from bioinformatics analyses',
                        'category': 'quality',
                        'size': '8.5 MB'
                    }
                ],
                'total_updates': 2
            }
        """
        self.logger.info("开始检查工具版本更新...")
        
        result = {
            'updates_available': False,
            'tool_updates': [],
            'new_tools': [],
            'total_updates': 0
        }
        
        try:
            # 获取所有已安装的工具
            installed_tools = self._get_installed_tools()
            
            # 检查每个工具的更新
            for tool_name, current_info in installed_tools.items():
                update_info = self._check_single_tool_update(tool_name, current_info)
                if update_info:
                    result['tool_updates'].append(update_info)
            
            # 检查新的可用工具（暂时跳过）
            # new_tools = self._check_new_tools()
            # result['new_tools'] = new_tools
            
            result['total_updates'] = len(result['tool_updates'])
            result['updates_available'] = result['total_updates'] > 0
            
            if result['updates_available']:
                self.logger.info(f"发现 {result['total_updates']} 个工具更新")
            else:
                self.logger.info("所有工具都是最新版本")
                
        except Exception as e:
            self.logger.error(f"检查工具更新失败: {e}")
        
        return result
    
    def _get_tool_manager(self):
        """获取工具管理器实例（延迟导入）"""
        if self.tool_manager is None:
            try:
                from core.tool_manager import ToolManager
                self.tool_manager = ToolManager(self.config_manager)
            except Exception as e:
                self.logger.error(f"初始化工具管理器失败: {e}")
        return self.tool_manager
    
    def _get_installed_tools(self) -> Dict[str, Dict[str, Any]]:
        """获取所有已安装的工具信息"""
        installed_tools = {}
        
        try:
            # 直接检查已安装的工具目录
            from pathlib import Path
            install_base = Path("installed_tools")
            
            if install_base.exists():
                for tool_dir in install_base.iterdir():
                    if tool_dir.is_dir():
                        tool_name = tool_dir.name
                        try:
                            # 尝试获取工具实例来获取版本信息
                            tool_instance = self._get_tool_instance(tool_name)
                            if tool_instance and tool_instance.verify_installation():
                                metadata = tool_instance.get_metadata()
                                installed_tools[tool_name] = {
                                    'version': metadata.get('version', '未知'),
                                    'install_path': str(tool_dir),
                                    'category': metadata.get('category', 'unknown')
                                }
                        except Exception as e:
                            self.logger.warning(f"获取 {tool_name} 信息失败: {e}")
        
        except Exception as e:
            self.logger.error(f"获取已安装工具列表失败: {e}")
        
        return installed_tools
    
    def _get_tool_instance(self, tool_name: str):
        """获取工具实例"""
        try:
            if tool_name.lower() == 'fastqc':
                from core.tools.fastqc import FastQC
                return FastQC()
            # 可以在这里添加其他工具
            return None
        except Exception as e:
            self.logger.error(f"创建 {tool_name} 实例失败: {e}")
            return None
    
    def _check_single_tool_update(self, tool_name: str, current_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """检查单个工具的版本更新"""
        try:
            # 获取工具实例
            tool_instance = self._get_tool_instance(tool_name)
            if not tool_instance:
                return None
            
            # 获取工具的最新元数据（包含最新版本信息）
            latest_metadata = tool_instance.get_metadata()
            current_version = current_info.get('version', '未知')
            latest_version = latest_metadata.get('version', '未知')
            
            # 简单的版本比较（这里可以改进为更复杂的版本比较逻辑）
            if self._is_version_newer(latest_version, current_version):
                return {
                    'name': tool_name,
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'update_size': latest_metadata.get('size', '未知'),
                    'changelog': latest_metadata.get('release_notes', '更新内容详见官方说明'),
                    'priority': self._determine_update_priority(tool_name, current_version, latest_version),
                    'category': current_info.get('category', 'unknown'),
                    'homepage': latest_metadata.get('homepage', '')
                }
            
        except Exception as e:
            self.logger.error(f"检查 {tool_name} 更新失败: {e}")
        
        return None
    
    def _is_version_newer(self, latest: str, current: str) -> bool:
        """
        简单的版本比较
        这里使用基础的字符串比较，可以改进为更复杂的语义版本比较
        """
        if latest == '未知' or current == '未知':
            return False
        
        try:
            # 简单的数字版本比较 (如 0.12.1 vs 0.11.9)
            latest_parts = [int(x) for x in latest.split('.') if x.isdigit()]
            current_parts = [int(x) for x in current.split('.') if x.isdigit()]
            
            # 补齐长度
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
            
        except Exception:
            # 如果版本解析失败，使用字符串比较
            return latest > current
    
    def _determine_update_priority(self, tool_name: str, current: str, latest: str) -> str:
        """
        确定更新优先级
        
        Returns:
            'critical': 安全更新或重要bug修复
            'recommended': 功能改进和性能提升
            'optional': 次要更新
        """
        try:
            current_parts = [int(x) for x in current.split('.') if x.isdigit()]
            latest_parts = [int(x) for x in latest.split('.') if x.isdigit()]
            
            if len(current_parts) >= 2 and len(latest_parts) >= 2:
                # 主版本更新 (x.0.0) - 推荐
                if latest_parts[0] > current_parts[0]:
                    return 'recommended'
                # 次版本更新 (0.x.0) - 推荐
                elif latest_parts[1] > current_parts[1]:
                    return 'recommended'
                # 补丁版本 (0.0.x) - 可选
                else:
                    return 'optional'
        
        except Exception:
            pass
        
        return 'optional'
    
    def get_update_summary(self) -> str:
        """
        获取更新摘要文本
        用于UI显示
        """
        try:
            updates = self.check_tool_updates()
            
            if not updates['updates_available']:
                return "所有工具都是最新版本"
            
            tool_count = len(updates['tool_updates'])
            new_count = len(updates['new_tools'])
            
            summary_parts = []
            if tool_count > 0:
                summary_parts.append(f"{tool_count}个工具有更新")
            if new_count > 0:
                summary_parts.append(f"{new_count}个新工具可用")
            
            return "、".join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"获取更新摘要失败: {e}")
            return "检查更新失败"