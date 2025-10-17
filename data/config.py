"""
配置管理模块
处理应用设置的保存和加载，对应JavaScript中的配置相关功能
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from .models import Tool, AppState, DEFAULT_TOOLS, DEFAULT_DOWNLOAD_TASKS, ToolCategory, ToolStatus


def tool_to_dict(tool: Tool) -> dict:
    """
    将Tool对象转换为字典，确保枚举值转换为字符串
    """
    data = asdict(tool)
    # 转换枚举值为字符串
    if 'category' in data and isinstance(data['category'], ToolCategory):
        data['category'] = data['category'].value
    if 'status' in data and isinstance(data['status'], ToolStatus):
        data['status'] = data['status'].value
    return data


@dataclass
class Settings:
    """
    应用设置结构
    对应JavaScript中设置页面的各种开关和配置
    """
    # 常规设置
    auto_update: bool = True  # 保留向后兼容，实际使用tool_update设置
    check_tool_status_on_startup: bool = False
    show_detailed_install_log: bool = True
    
    # 新增：语言设置
    language: str = "zh_CN"  # zh_CN, en_US, ja_JP, es_ES, fr_FR
    
    # 新增：工具更新设置（仅管理第三方工具，不包括BioNexus本体）
    tool_update: dict = field(default_factory=lambda: {
        'update_mode': 'auto',
        'check_frequency': 1,
        'show_notification': True,
        'last_check': None
    })
    
    # 环境设置
    default_install_dir: str = ""
    conda_env_path: str = ""
    
    # 高级选项
    use_mirror_source: bool = True
    keep_install_cache: bool = False
    
    # 收藏工具列表
    favorite_tools: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        if self.tool_update is None:
            self.tool_update = {
                'update_mode': 'auto',           # auto/manual - 工具更新模式
                'check_frequency': 1,            # 检查频率（天）
                'show_notification': True,       # 显示通知（仅manual模式有效）
                'last_check': None,              # 上次检查时间
                'skipped_versions': {},          # 永久跳过的工具版本 {tool_name: version}
                'silent_versions': {},           # 临时静默的工具版本 {tool_name: version}
                'auto_update_time': '02:00'      # 自动更新时间
            }
        
        # 设置默认路径（如果为空）
        if not self.default_install_dir:
            # 获取项目根目录下的 installed_tools 路径
            project_root = Path(__file__).parent.parent
            self.default_install_dir = str(project_root / "installed_tools")
        
        if not self.conda_env_path:
            # 获取项目根目录下的 envs_cache 路径
            project_root = Path(__file__).parent.parent
            self.conda_env_path = str(project_root / "envs_cache")


class ConfigManager:
    """
    配置管理器
    负责应用配置的持久化存储和读取
    对应JavaScript中的配置文件操作
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，如果为None则使用默认位置
        """
        # 初始化日志记录器
        self.logger = logging.getLogger(__name__)
        
        if config_dir is None:
            # 默认配置目录：用户家目录下的.bionexus文件夹
            config_dir = Path.home() / ".bionexus"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.tools_file = self.config_dir / "tools.json"
        self.recent_tools_file = self.config_dir / "recent_tools.json"
        
        # 初始化默认配置
        self._settings = Settings()
        self._tools: List[Dict] = []
        self._recent_tools: List[str] = []
        self._app_state = AppState()
        
        # 向后兼容：添加favorite_tools属性
        self.favorite_tools = []
        
        # 加载已保存的配置
        self.load_all_configs()
    
    def load_all_configs(self):
        """加载所有配置文件"""
        self.load_settings()
        self.load_tools()
        self.load_recent_tools()
        # 同步favorite_tools到实例属性（向后兼容）
        self.favorite_tools = self._settings.favorite_tools.copy()
        logging.info(f"初始化收藏列表: {self.favorite_tools}")
    
    def load_settings(self) -> Settings:
        """
        加载应用设置
        对应JavaScript中从localStorage读取设置
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logging.info(f"加载配置文件: {self.config_file}")
                    
                    # 更新设置对象
                    for key, value in data.items():
                        if hasattr(self._settings, key):
                            # 特殊处理路径设置：如果配置文件中的路径为空，保留默认值
                            if key in ['default_install_dir', 'conda_env_path'] and not value:
                                continue  # 跳过空路径，保持__post_init__中设置的默认值
                            setattr(self._settings, key, value)
                            logging.debug(f"加载设置: {key} = {value}")
                    
                    # 向后兼容性处理：检查并添加缺失的favorite_tools字段
                    if 'favorite_tools' not in data:
                        logging.info("检测到旧版配置文件，添加favorite_tools字段")
                        self._settings.favorite_tools = []
                        # 立即保存更新后的配置
                        self.save_settings()
                    else:
                        logging.info(f"加载收藏列表: {len(self._settings.favorite_tools)} 个工具")
            except json.JSONDecodeError as e:
                logging.error(f"配置文件JSON格式错误 {self.config_file}: {e}")
                logging.info("使用默认设置")
            except PermissionError as e:
                logging.error(f"没有权限读取配置文件 {self.config_file}: {e}")
            except FileNotFoundError as e:
                logging.warning(f"配置文件不存在 {self.config_file}，将使用默认设置")
            except Exception as e:
                logging.error(f"加载设置时发生未知错误: {e}")
        
        return self._settings
    
    def save_settings(self) -> bool:
        """
        保存应用设置
        对应JavaScript中保存设置到配置文件
        """
        try:
            # 同步favorite_tools到settings（向后兼容）
            self._settings.favorite_tools = self.favorite_tools.copy()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self._settings), f, ensure_ascii=False, indent=2)
            logging.info(f"设置已成功保存到 {self.config_file}")
            return True
        except PermissionError as e:
            logging.error(f"没有权限写入配置文件 {self.config_file}: {e}")
            return False
        except OSError as e:
            logging.error(f"磁盘空间不足或I/O错误 {self.config_file}: {e}")
            return False
        except TypeError as e:
            logging.error(f"设置数据序列化失败: {e}")
            return False
        except Exception as e:
            logging.error(f"保存设置时发生未知错误: {e}")
            return False
    
    def load_tools(self) -> List[Dict]:
        """
        加载工具数据
        对应JavaScript中的toolsData数组
        """
        if self.tools_file.exists():
            try:
                with open(self.tools_file, 'r', encoding='utf-8') as f:
                    self._tools = json.load(f)
                logging.info(f"工具数据已从 {self.tools_file} 加载成功")
            except json.JSONDecodeError as e:
                logging.error(f"工具数据文件JSON格式错误 {self.tools_file}: {e}")
                logging.info("使用默认工具数据")
                self._tools = [tool_to_dict(tool) for tool in DEFAULT_TOOLS]
            except PermissionError as e:
                logging.error(f"没有权限读取工具数据文件 {self.tools_file}: {e}")
                self._tools = [tool_to_dict(tool) for tool in DEFAULT_TOOLS]
            except Exception as e:
                logging.error(f"加载工具数据时发生未知错误: {e}")
                self._tools = [tool_to_dict(tool) for tool in DEFAULT_TOOLS]
        else:
            # 首次运行，使用默认数据
            self._tools = [tool_to_dict(tool) for tool in DEFAULT_TOOLS]
            self.save_tools()
        
        return self._tools
    
    def save_tools(self) -> bool:
        """
        保存工具数据
        对应JavaScript中更新toolsData后的持久化
        """
        try:
            with open(self.tools_file, 'w', encoding='utf-8') as f:
                json.dump(self._tools, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"保存工具数据失败: {e}")
            return False
    
    def load_recent_tools(self) -> List[str]:
        """
        加载最近使用的工具列表
        对应JavaScript中的最近使用工具功能
        """
        if self.recent_tools_file.exists():
            try:
                with open(self.recent_tools_file, 'r', encoding='utf-8') as f:
                    self._recent_tools = json.load(f)
            except Exception as e:
                print(f"加载最近使用工具失败: {e}")
                self._recent_tools = []
        
        return self._recent_tools
    
    def save_recent_tools(self) -> bool:
        """保存最近使用的工具列表"""
        try:
            with open(self.recent_tools_file, 'w', encoding='utf-8') as f:
                json.dump(self._recent_tools, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存最近使用工具失败: {e}")
            return False
    
    def update_recent_tools(self, tool_name: str):
        """
        更新最近使用工具列表
        将工具添加到列表顶部，保持最多5个
        对应JavaScript中的updateRecentToolsList函数
        """
        # 如果工具已存在，先移除
        if tool_name in self._recent_tools:
            self._recent_tools.remove(tool_name)
        
        # 添加到列表顶部
        self._recent_tools.insert(0, tool_name)
        
        # 保持最多5个
        if len(self._recent_tools) > 5:
            self._recent_tools = self._recent_tools[:5]
        
        # 保存到文件
        self.save_recent_tools()
    
    def remove_from_recent_tools(self, tool_name: str):
        """
        从最近使用工具列表中移除指定工具
        用于工具卸载时清理最近使用记录
        """
        if tool_name in self._recent_tools:
            self._recent_tools.remove(tool_name)
            # 保存到文件
            self.save_recent_tools()
            print(f"[ConfigManager] 从最近使用列表中移除工具: {tool_name}")
    
    def toggle_favorite_tool(self, tool_name: str) -> bool:
        """
        切换工具收藏状态
        返回新的收藏状态
        """
        logging.info(f"切换收藏状态: {tool_name}")
        logging.debug(f"切换前收藏列表: {self.favorite_tools}")
        
        if tool_name in self.favorite_tools:
            self.favorite_tools.remove(tool_name)
            self._settings.favorite_tools.remove(tool_name)
            is_favorite = False
            logging.info(f"移除收藏: {tool_name}")
        else:
            self.favorite_tools.append(tool_name)
            self._settings.favorite_tools.append(tool_name)
            is_favorite = True
            logging.info(f"添加收藏: {tool_name}")
        
        logging.debug(f"切换后收藏列表: {self.favorite_tools}")
        logging.debug(f"切换后设置中的收藏列表: {self._settings.favorite_tools}")
        
        # 保存设置
        save_result = self.save_settings()
        if save_result:
            logging.info(f"收藏状态已保存: {tool_name} -> {'收藏' if is_favorite else '取消收藏'}")
        else:
            logging.error(f"收藏状态保存失败: {tool_name}")
        
        return is_favorite
    
    def is_tool_favorite(self, tool_name: str) -> bool:
        """检查工具是否被收藏"""
        return tool_name in self.favorite_tools
    
    def get_favorite_tools(self) -> List[str]:
        """获取收藏的工具列表"""
        return self.favorite_tools.copy()
    
    def update_setting(self, setting_name: str, value: Any):
        """
        更新单个设置项
        对应JavaScript中的设置变更处理
        """
        if hasattr(self._settings, setting_name):
            setattr(self._settings, setting_name, value)
            self.save_settings()
            return True
        return False
    
    def update_tool_status(self, tool_name: str, status: str, **kwargs):
        """
        更新工具状态
        对应JavaScript中安装完成后更新工具数据
        """
        for tool in self._tools:
            if tool['name'] == tool_name:
                tool['status'] = status
                # 更新其他可选字段
                for key, value in kwargs.items():
                    if key in tool:
                        tool[key] = value
                self.save_tools()
                return True
        return False
    
    def get_tools_by_status(self, status: str) -> List[Dict]:
        """根据状态获取工具列表"""
        return [tool for tool in self._tools if tool['status'] == status]
    
    def get_tools_by_category(self, category: str) -> List[Dict]:
        """根据分类获取工具列表"""
        return [tool for tool in self._tools if tool['category'] == category]
    
    # 属性访问器
    @property
    def settings(self) -> Settings:
        return self._settings
    
    @property
    def tools(self) -> List[Dict]:
        return self._tools
    
    @property
    def recent_tools(self) -> List[str]:
        return self._recent_tools
    
    @property
    def app_state(self) -> AppState:
        return self._app_state