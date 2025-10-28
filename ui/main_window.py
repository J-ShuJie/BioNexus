"""
主窗口组件
整合所有UI组件，提供完整的应用界面
包含标题栏、边栏、主内容区、工具栏等
对应HTML中的整体布局结构和JavaScript交互逻辑

⚠️  铁律：禁止使用 QLabel 和 QText 系列组件！
🚫 IRON RULE: NEVER USE QLabel, QTextEdit, QTextBrowser, QPlainTextEdit
✅ 替代方案: 使用 smart_text_module.py 中的智能文本组件
📋 原因: QLabel/QText 存在文字截断、字体渲染、DPI适配等问题
"""
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QScrollArea, QFrame, QPushButton,
    QLabel, QGridLayout, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

# 获取logger
logger = logging.getLogger('BioNexus.MainWindow')

from .modern_sidebar import ModernSidebar
from .modern_toolbar import ModernToolbar
from .tool_card import ToolCard
from .tool_card_v2 import ToolCardV2
from .tool_detail_panel import ToolDetailDialog
# 使用增强版详情页面，解决自适应高度和边距问题
from .tool_detail_enhanced import EnhancedDetailPage as ToolDetailPage
# from .filter_panel import FilterPanel  # 旧系统，已停用
from .modern_filter_card import ModernFilterCard
from .modern_download_card import ModernDownloadCard
from .overlay_widget import OverlayWidget
from .settings_panel import SettingsPanel
from .workflows_main_view import WorkflowsMainView
from .workflows_detail_view import WorkflowsDetailView
try:
    from .tool_picker_page import ToolPickerPage
except Exception:
    ToolPickerPage = None
from .card_grid_container import CardScrollArea
# from .download_status_panel import DownloadStatusPanel  # 旧系统，已停用
from core.tool_manager import ToolManager
from data.config import ConfigManager
from data.models import AppState
from utils.unified_logger import get_logger, performance_monitor, operation_logger
from utils.path_resolver import PathResolver
from utils.workflows_manager import WorkflowsManager
# EnvironmentManager 延迟加载，不是启动必需的


# TitleBar类已移除，使用系统原生标题栏


class MainWindow(QMainWindow):
    """
    主窗口类
    整合所有UI组件，提供完整的应用界面
    对应HTML中的整体布局和JavaScript应用逻辑
    """
    
    def __init__(self):
        super().__init__()
        
        print(f"🔧 [DEBUG VERSION] 主窗口版本: 2025-09-09-10:25 - 修复下载状态链路中断问题")
        
        # 初始化组件
        self.config_manager = ConfigManager()

        # 设置路径解析器的配置管理器（让所有工具都能读取路径配置）
        PathResolver.set_config_manager(self.config_manager)

        self.tool_manager = ToolManager(self.config_manager)
        self.app_state = self.config_manager.app_state

        # 环境管理器延迟加载（按需初始化，不是启动必需的）
        self.env_manager = None
        
        # 初始化新的工具更新系统（仅管理第三方工具，不包括BioNexus本体）
        from core.updater.tool_update_controller import ToolUpdateController
        self.tool_update_controller = ToolUpdateController(self, self.config_manager, self.tool_manager)
        
        # 启动时更新检查标记（不再使用定时器延迟）
        
        # 监控系统（由main.py设置）
        self.monitor = None
        
        # UI组件
        self.title_bar = None
        self.sidebar = None
        self.tools_grid = None
        self.settings_panel = None
        self.workflows_main_view = None
        self.workflows_detail_view = None
        self.tool_picker_page = None
        self.workflows_manager = None
        self.filter_panel = None
        self.download_status_panel = None
        self.main_content_stack = None
        self.current_detail_page = None  # 当前详情页面
        self.overlay = None  # 遮罩层
        # 当前工作流上下文（用于返回与标题显示）
        self._current_workflow_name = None
        # 运行状态轮询（兜底），用于个别工具无法正确回调停止时
        from PyQt5.QtCore import QTimer
        self._run_state_timer = QTimer(self)
        self._run_state_timer.setInterval(1500)
        self._run_state_timer.timeout.connect(self._poll_running_state)
        self._running_tool_name = None
        # 进度节流缓存：避免卡片在进度频繁更新时闪烁
        self._progress_cache = {}  # {tool_name: { 'p': int, 's': str, 'ts': float }}
        # 选择器详情上下文标记
        self._in_picker_detail = False
        
        # 筛选状态
        self.current_search = ""
        self.current_categories = []
        self.current_statuses = []

        # Initialization completion flag - prevent retranslateUi before UI is ready
        self._ui_fully_initialized = False

        self.init_ui()
        self.setup_connections()
        self.load_styles()
        self.load_initial_data()
        self._set_window_icon()

        # 检测并处理路径迁移
        self._check_and_handle_path_migration()

        # Connect translation manager language change signal
        try:
            logger.info("Connecting to translation system...")
            from utils.translator import get_translator
            translator = get_translator()
            logger.debug("Got translator instance")
            translator.languageChanged.connect(self.retranslateUi)
            logger.info("SUCCESS: Connected languageChanged signal to retranslateUi slot")
        except Exception as e:
            logger.error(f"FAILED: Unable to connect translation system: {e}")
            import traceback
            logger.error(traceback.format_exc())

        # Mark UI as fully initialized - retranslateUi can now safely run
        self._ui_fully_initialized = True
        logger.info("MainWindow initialization completed - UI ready for language switching")

    def _calculate_window_size(self):
        """
        计算智能窗口大小
        屏幕尺寸的50%，但不小于900x600
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # 计算屏幕50%的大小
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        
        # 50%屏幕大小
        window_width = int(screen_width * 0.5)
        window_height = int(screen_height * 0.5)
        
        # 设置最小值
        min_width = 900
        min_height = 600
        
        # 应用最小值限制
        window_width = max(window_width, min_width)
        window_height = max(window_height, min_height)
        
        return window_width, window_height
    
    def _center_window(self):
        """
        将窗口居中显示
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        window_geometry = self.geometry()
        
        # 计算居中位置
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        
        # 移动窗口到中心
        self.move(x, y)
    
    def init_ui(self):
        """
        初始化用户界面
        对应HTML中的主体结构
        """
        # 设置窗口属性
        self.setWindowTitle("BioNexus Launcher")
        
        # 智能设置窗口大小
        window_width, window_height = self._calculate_window_size()
        
        # 设置最小尺寸：确保至少能显示1个完整卡片
        # 最小宽度 = 侧边栏(250) + 最小边距*2(40) + 卡片宽度(81) + 预留空间(29)
        min_window_width = 250 + 40 + 81 + 29  # = 400px
        self.setMinimumSize(max(min_window_width, 400), 600)
        self.resize(window_width, window_height)
        
        # 窗口居中显示
        self._center_window()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 垂直排列：标题栏 + 内容区
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 使用系统原生标题栏（移除了自定义标题栏）
        
        # 主内容区域 - 水平排列：边栏 + 内容
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 左侧边栏 - 使用现代化版本
        self.sidebar = ModernSidebar()
        content_layout.addWidget(self.sidebar)
        
        # 右侧主内容区
        self._create_main_content_area(content_layout)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)
        
        # 创建遮罩层（初始隐藏）
        self.overlay = OverlayWidget(central_widget)
        self.overlay.clicked.connect(self._on_overlay_clicked)
        
        central_widget.setLayout(main_layout)
        
        # 使用系统原生标题栏（已移除无边框设置）
    
    def _create_main_content_area(self, content_layout: QHBoxLayout):
        """
        创建右侧主内容区域
        对应HTML中的main-content结构
        """
        # 主内容容器
        main_content_widget = QWidget()
        main_content_widget.setObjectName("MainContent")
        main_content_layout = QVBoxLayout()
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)
        
        # 顶部工具栏
        self._create_toolbar(main_content_layout)
        
        # 内容堆栈 - 切换不同视图
        self.main_content_stack = QStackedWidget()
        
        # 工具展示区域 - 使用新的卡片滚动容器
        self.tools_grid = CardScrollArea()
        self.main_content_stack.addWidget(self.tools_grid)
        
        # 设置面板
        self.settings_panel = SettingsPanel(self.config_manager)
        self.main_content_stack.addWidget(self.settings_panel)

        # 工作流管理器与页面
        try:
            self.workflows_manager = WorkflowsManager(self.config_manager.config_dir)
            self.workflows_main_view = WorkflowsMainView(self.workflows_manager)
            self.workflows_detail_view = WorkflowsDetailView()
            self.main_content_stack.addWidget(self.workflows_main_view)
            self.main_content_stack.addWidget(self.workflows_detail_view)
            # 懒加载 ToolPickerPage（首次需要时再创建）
        except Exception as e:
            logger.error(f"初始化工作流视图失败: {e}")
        
        main_content_layout.addWidget(self.main_content_stack)
        main_content_widget.setLayout(main_content_layout)
        
        # 主内容区域包含筛选面板的容器
        content_container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        container_layout.addWidget(main_content_widget)
        
        # 现代化悬浮卡片系统
        self.modern_filter_card = None
        
        # 🎯 预创建下载卡片（隐藏状态），确保能记录所有下载/卸载状态
        print("【MAIN WINDOW】开始预创建下载卡片...")
        try:
            from .modern_download_card import ModernDownloadCard
            self.modern_download_card = ModernDownloadCard(self)
            self.modern_download_card.card_closed.connect(self._close_modern_download_card)
            self.modern_download_card.hide()  # 初始隐藏
            print(f"【MAIN WINDOW】✅ 预创建下载卡片完成，对象地址: {id(self.modern_download_card)}")
        except Exception as e:
            print(f"【MAIN WINDOW】❌ 预创建下载卡片失败: {e}")
            self.modern_download_card = None
        
        # 初始化下载按钮状态（在面板创建后）
        self._update_download_button_state()
        
        content_container.setLayout(container_layout)
        content_layout.addWidget(content_container)
    
    def _create_toolbar(self, main_content_layout: QVBoxLayout):
        """
        创建现代化工具栏 - 与侧边栏中线对齐
        """
        # 使用现代化工具栏
        self.toolbar = ModernToolbar()
        
        # 连接信号
        print(f"【CONNECTION DEBUG】连接工具栏信号")
        print(f"【CONNECTION DEBUG】工具栏对象: {self.toolbar}")
        print(f"【CONNECTION DEBUG】filter_clicked 信号: {self.toolbar.filter_clicked}")
        self.toolbar.filter_clicked.connect(self._toggle_filter_panel)
        print(f"【CONNECTION DEBUG】已连接 filter_clicked -> _toggle_filter_panel")
        
        self.toolbar.download_status_clicked.connect(self._toggle_download_status_panel)
        print(f"【CONNECTION DEBUG】已连接 download_status_clicked -> _toggle_download_status_panel")
        
        # 连接返回按钮信号
        # 统一入口：根据当前上下文决定返回目标
        self._back_target = 'main'  # main | workflows
        self._last_non_detail_view = 'all-tools'
        self.toolbar.back_clicked.connect(self._on_toolbar_back)
        print(f"【CONNECTION DEBUG】已连接 back_clicked -> _on_toolbar_back")
        
        main_content_layout.addWidget(self.toolbar)
        
        # 为兼容性创建虚拟的按钮引用
        self.filter_btn = type('obj', (object,), {'clicked': self.toolbar.filter_clicked})
        self.download_status_btn = type('obj', (object,), {'clicked': self.toolbar.download_status_clicked})
    
    def setup_connections(self):
        """
        设置信号连接
        对应JavaScript中的事件监听器设置
        """
        # 已移除自定义标题栏相关连接（使用系统原生标题栏）
        
        # 边栏信号连接
        self.sidebar.search_changed.connect(self._on_search_changed)
        self.sidebar.view_changed.connect(self._on_view_changed)
        self.sidebar.recent_tool_clicked.connect(self._on_recent_tool_clicked)

        # 工作流视图连接
        if self.workflows_main_view:
            self.workflows_main_view.new_workflow_requested.connect(self._on_new_workflow)
            self.workflows_main_view.open_workflow_requested.connect(self._on_open_workflow)
            self.workflows_main_view.rename_workflow_requested.connect(self._on_rename_workflow)
            self.workflows_main_view.duplicate_workflow_requested.connect(self._on_duplicate_workflow)
            self.workflows_main_view.delete_workflow_requested.connect(self._on_delete_workflow)
        if self.workflows_detail_view:
            self.workflows_detail_view.back_requested.connect(self._on_back_from_workflow)
            self.workflows_detail_view.add_tool_requested.connect(self._on_pick_tool_for_workflow)
            self.workflows_detail_view.remove_tool_requested.connect(self._on_remove_tool_from_workflow)
            self.workflows_detail_view.move_up_requested.connect(lambda idx: self._on_move_tool_in_workflow(idx, -1))
            self.workflows_detail_view.move_down_requested.connect(lambda idx: self._on_move_tool_in_workflow(idx, +1))
            # 详情请求（来自工作流中的工具卡）
            self.workflows_detail_view.tool_detail_requested.connect(self._on_card_selected)
            # 非管理模式下，卡片走标准安装/启动逻辑
            try:
                self.workflows_detail_view.cards.card_install_clicked.connect(self._on_install_tool)
                self.workflows_detail_view.cards.card_launch_clicked.connect(self._on_launch_tool)
            except Exception:
                pass
        
        # 移除重复的筛选按钮连接 - 已在 _create_toolbar 中连接
        print(f"【CONNECTION DEBUG】跳过重复的筛选按钮连接，因为已在工具栏创建时连接")
        
        # 现代化卡片信号连接将在卡片创建时动态连接
        # 顶栏动作通道
        self._connect_toolbar_actions()
        
        # 工具管理器信号连接
        print("[系统初始化] 开始连接工具管理器信号")
        self.tool_manager.tool_installed.connect(self._on_tool_installed)
        print("[系统初始化] tool_installed 信号已连接到 _on_tool_installed")
        self.tool_manager.tool_launched.connect(self._on_tool_launched)
        print("[系统初始化] tool_launched 信号已连接到 _on_tool_launched")
        self.tool_manager.tool_uninstalled.connect(self._on_tool_uninstalled)
        print("[系统初始化] tool_uninstalled 信号已连接到 _on_tool_uninstalled")
        self.tool_manager.installation_progress.connect(self._on_installation_progress)
        print("[系统初始化] installation_progress 信号已连接到 _on_installation_progress")
        self.tool_manager.error_occurred.connect(self._on_tool_error)
        print("[系统初始化] error_occurred 信号已连接到 _on_tool_error")
        # 新增：统一处理工具状态变化（installed/available/update等）
        try:
            self.tool_manager.tool_status_changed.connect(self._on_tool_status_changed)
            print("[系统初始化] tool_status_changed 信号已连接到 _on_tool_status_changed")
        except Exception as e:
            print(f"[系统初始化] 警告：无法连接 tool_status_changed 信号: {e}")
        # 新增：工具使用时间更新信号
        try:
            self.tool_manager.usage_time_updated.connect(self._on_usage_time_updated)
            print("[系统初始化] ✅ usage_time_updated 信号已连接到 _on_usage_time_updated")
            import logging
            logger = logging.getLogger(__name__)
            logger.info("✅ [MainWindow-初始化] usage_time_updated 信号已连接到 _on_usage_time_updated")
        except Exception as e:
            print(f"[系统初始化] ❌ 警告：无法连接 usage_time_updated 信号: {e}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ [MainWindow-初始化] 无法连接 usage_time_updated 信号: {e}")
            import traceback
            logger.error(traceback.format_exc())
        print("[系统初始化] 所有工具管理器信号连接完成")
        
        # 设置面板信号连接
        self.settings_panel.setting_changed.connect(self._on_setting_changed)
        
        # 卡片滚动区域信号连接
        self.tools_grid.card_selected.connect(self._on_card_selected)
        self.tools_grid.card_install_clicked.connect(self._on_install_tool)
        self.tools_grid.card_launch_clicked.connect(self._on_launch_tool)
        # 连接收藏信号（如果卡片容器支持）
        if hasattr(self.tools_grid, 'card_favorite_toggled'):
            self.tools_grid.card_favorite_toggled.connect(self._on_tool_favorite_toggled)
        # 移除了card_info_clicked，改为直接显示详情页面
    
    def load_styles(self):
        """
        加载样式表
        对应HTML中的CSS样式
        """
        try:
            from pathlib import Path
            style_file = Path(__file__).parent.parent / "resources" / "styles.qss"
            
            if style_file.exists():
                with open(style_file, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
            else:
                print(f"样式文件不存在: {style_file}")
        except Exception as e:
            print(f"加载样式文件失败: {e}")
    
    def load_initial_data(self):
        """
        加载初始数据
        对应JavaScript中的初始化数据加载
        """
        # 更新工具显示
        self._update_tools_display()
        
        # 更新最近使用工具列表
        self.sidebar.update_recent_tools(self.config_manager.recent_tools)
        
        # 设置默认视图
        self._on_view_changed("all-tools")
        
        # 设置工具更新连接并立即检查更新（作为加载过程的一部分）
        self._setup_tool_update_connections()
        if self._should_check_updates_on_startup():
            self._startup_check_for_updates()
    
    @performance_monitor("更新工具显示")
    def _update_tools_display(self):
        """更新工具显示"""
        # 使用新架构从tool_manager获取工具数据
        tools_data = self.tool_manager.get_all_tools_data()
        
        # 添加收藏状态到工具数据
        favorite_count = 0
        for tool in tools_data:
            tool['is_favorite'] = self.config_manager.is_tool_favorite(tool['name'])
            if tool['is_favorite']:
                favorite_count += 1
        
        # 应用排序
        tools_data = self._sort_tools(tools_data)
        
        print(f"[工具显示] 共 {len(tools_data)} 个工具，其中 {favorite_count} 个已收藏，已按首字母排序")
        
        self.tools_grid.set_cards(tools_data)
        self._apply_current_filters()
    
    def _sort_tools(self, tools_data: list, sort_by: str = "name") -> list:
        """
        对工具列表进行排序
        
        Args:
            tools_data: 工具数据列表
            sort_by: 排序方式，支持：
                - "name": 按工具名称首字母排序（默认）
                - "status": 按状态排序（已安装优先）
                - "category": 按分类排序
                - "favorite": 按收藏状态排序（收藏优先）
        
        Returns:
            排序后的工具列表
        """
        if sort_by == "name":
            # 按首字母排序（忽略大小写）
            return sorted(tools_data, key=lambda tool: tool['name'].lower())
        
        elif sort_by == "status":
            # 按状态排序：已安装 > 需更新 > 未安装
            status_priority = {"installed": 0, "update": 1, "available": 2}
            return sorted(tools_data, key=lambda tool: (
                status_priority.get(tool['status'], 3),  # 状态优先级
                tool['name'].lower()  # 同状态内按名称排序
            ))
        
        elif sort_by == "category":
            # 按分类排序，同分类内按名称排序
            return sorted(tools_data, key=lambda tool: (
                tool.get('category', 'unknown').lower(),
                tool['name'].lower()
            ))
        
        elif sort_by == "favorite":
            # 按收藏状态排序：收藏优先，同状态内按名称排序
            return sorted(tools_data, key=lambda tool: (
                not tool.get('is_favorite', False),  # False(未收藏)排在后面
                tool['name'].lower()
            ))
        
        else:
            # 默认按名称排序
            return sorted(tools_data, key=lambda tool: tool['name'].lower())
    
    def _force_refresh_all_ui(self):
        """强制刷新所有UI组件 - 解决状态不同步问题"""
        print("[强制刷新] 开始刷新所有UI组件")
        
        # 1. 强制刷新工具列表
        self._update_tools_display()
        
        # 2. 强制更新工具网格
        self.tools_grid.update()
        self.tools_grid.repaint()
        
        # 3. 强制刷新主窗口
        self.update()
        self.repaint()
        
        # 4. 处理所有待处理的事件
        from PyQt5.QtWidgets import QApplication
        QApplication.processEvents()
        
        print("[强制刷新] UI刷新完成")

    @performance_monitor("应用筛选条件")
    def _apply_current_filters(self):
        """应用当前的筛选条件"""
        self.tools_grid.filter_cards(
            self.current_search, 
            self.current_categories, 
            self.current_statuses
        )
    
    # _toggle_maximize方法已移除（使用原生标题栏后不需要）
    
    def _on_search_changed(self, search_term: str):
        """
        搜索内容变化处理
        对应JavaScript中的handleSearch函数
        """
        # 记录搜索操作到监控系统
        if self.monitor and search_term.strip():
            self.monitor.log_user_operation("搜索工具", {"关键词": search_term})
        
        self.current_search = search_term.lower()
        # 在不同页面应用到对应网格
        current_widget = self.main_content_stack.currentWidget() if self.main_content_stack else None
        if current_widget is self.tools_grid:
            self._apply_current_filters()
        elif self.tool_picker_page and (current_widget is self.tool_picker_page):
            try:
                self.tool_picker_page.filter_cards(self.current_search, [], [])
            except Exception:
                pass
    
    @performance_monitor("视图切换")
    @operation_logger("视图切换")
    def _on_view_changed(self, view_name: str):
        """
        视图切换处理
        对应JavaScript中的handleNavClick和renderCurrentView函数
        """
        # 记录视图切换到监控系统
        if self.monitor:
            self.monitor.log_view_switch(
                self.app_state.current_view, 
                view_name, 
                True
            )
        
        self.app_state.current_view = view_name
        self.current_view = view_name  # 保存当前视图用于收藏刷新
        # 记录最近的非详情视图
        if view_name in ("all-tools", "my-tools", "settings", "workflows"):
            self._last_non_detail_view = view_name
        
        if view_name == "all-tools":
            # 显示所有工具 - 重要：清除所有筛选条件显示全部工具
            self.main_content_stack.setCurrentWidget(self.tools_grid)
            # 清除筛选条件，确保显示所有工具
            self.current_categories = []
            self.current_statuses = []
            self._update_tools_display()
            # 顶栏：默认按钮
            self.toolbar.set_default_buttons_visible(True)
            self.toolbar.clear_actions()
            self.toolbar.switch_to_list_mode()
            self._back_target = 'main'
            self.toolbar.set_back_target("")
            
        elif view_name == "my-tools":
            # 显示收藏的工具
            self.main_content_stack.setCurrentWidget(self.tools_grid)
            self._show_favorite_tools()
            # 顶栏：默认按钮
            self.toolbar.set_default_buttons_visible(True)
            self.toolbar.clear_actions()
            self.toolbar.switch_to_list_mode()
            self._back_target = 'main'
            self.toolbar.set_back_target("")
            
        elif view_name == "settings":
            # 显示设置页面
            self.main_content_stack.setCurrentWidget(self.settings_panel)
            self.settings_panel.refresh_settings()
            # 顶栏：隐藏默认按钮（设置页不需要）
            self.toolbar.set_default_buttons_visible(False)
            self.toolbar.clear_actions()
            self.toolbar.switch_to_list_mode()
            self._back_target = 'main'
            self.toolbar.set_back_target("")
        elif view_name == "workflows":
            # 显示工作流列表
            if self.workflows_main_view:
                self.workflows_main_view.refresh()
                self.main_content_stack.setCurrentWidget(self.workflows_main_view)
                # 顶栏：隐藏默认，显示“新建工作流”
                self.toolbar.switch_to_list_mode()
                self.toolbar.set_default_buttons_visible(False)
                self.toolbar.set_actions([
                    {'id': 'new_wf', 'text': '新建工作流', 'type': 'normal'}
                ])
                self._back_target = 'main'
                self.toolbar.set_back_target("")
    
    def _on_recent_tool_clicked(self, tool_name: str):
        """
        最近使用工具点击处理
        对应JavaScript中的handleRecentItemClick函数
        """
        # 记录最近工具点击到监控系统
        if self.monitor:
            self.monitor.log_user_operation("点击最近工具", {"工具名": tool_name})
        
        # 切换到全部工具视图
        self.sidebar.set_active_view("all-tools")
        self._on_view_changed("all-tools")
        
        # 清除搜索条件
        self.sidebar.clear_search()
        self.current_search = ""
        self.current_categories = []
        self.current_statuses = []
        
        # 选中对应工具
        QTimer.singleShot(100, lambda: self._select_tool_card(tool_name))
    
    def _toggle_filter_panel(self):
        """
        切换筛选面板显示状态 - 1.2.1版本
        对应JavaScript中的handleFilterToggle函数
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"【MAIN WINDOW DEBUG】=== _toggle_filter_panel 函数被调用 ===")
        print(f"【MAIN WINDOW DEBUG】=== _toggle_filter_panel 函数被调用 ===")
        
        # 现代化悬浮卡片切换逻辑（旧系统已移除）
        print(f"【MAIN WINDOW DEBUG】检查现代化筛选卡片状态: card={self.modern_filter_card}")
        logger.info(f"【MAIN WINDOW DEBUG】检查现代化筛选卡片状态: card={self.modern_filter_card}")
        
        if self.modern_filter_card and self.modern_filter_card.isVisible():
            print(f"【MAIN WINDOW DEBUG】现代化筛选卡片当前可见，准备关闭")
            logger.info(f"【MAIN WINDOW DEBUG】现代化筛选卡片当前可见，准备关闭")
            self._close_modern_filter_card()
        else:
            print(f"【MAIN WINDOW DEBUG】现代化筛选卡片当前隐藏，准备打开")
            logger.info(f"【MAIN WINDOW DEBUG】现代化筛选卡片当前隐藏，准备打开")
            try:
                self._open_modern_filter_card()
                print(f"【MAIN WINDOW DEBUG】_open_modern_filter_card 调用完成")
                logger.info(f"【MAIN WINDOW DEBUG】_open_modern_filter_card 调用完成")
            except Exception as e:
                print(f"【MAIN WINDOW DEBUG】_open_modern_filter_card 发生异常: {e}")
                logger.error(f"【MAIN WINDOW DEBUG】_open_modern_filter_card 发生异常: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"【MAIN WINDOW DEBUG】=== _toggle_filter_panel 函数执行完成 ===")
        logger.info(f"【MAIN WINDOW DEBUG】=== _toggle_filter_panel 函数执行完成 ===")
        
        # 记录到日志 - 移到最后，确保函数完整执行
        if hasattr(self, 'monitor') and self.monitor:
            self.monitor.log_user_operation("筛选按钮点击", {"function": "_toggle_filter_panel"})
            print(f"【MAIN WINDOW DEBUG】已记录到监控日志")

    # =========================
    # 工作流视图 - 事件处理
    # =========================
    def _on_new_workflow(self):
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, self.tr("新建工作流"), self.tr("名称"))
        if ok and name.strip():
            self.workflows_manager.create_workflow(name.strip())
            if self.workflows_main_view:
                self.workflows_main_view.refresh()

    def _on_open_workflow(self, workflow_id: str):
        wf = self.workflows_manager.get_workflow(workflow_id)
        if not wf:
            return
        self._current_workflow_id = workflow_id
        try:
            self._current_workflow_name = wf.name
        except Exception:
            self._current_workflow_name = None
        self.workflows_detail_view.set_workflow(wf.id, wf.name, wf.tools)
        self.main_content_stack.setCurrentWidget(self.workflows_detail_view)
        # 顶栏：工作流详情（返回 + 添加工具 + 工具管理）
        self.toolbar.switch_to_detail_mode()
        self.toolbar.set_default_buttons_visible(False)
        self.toolbar.set_actions([
            {'id': 'add', 'text': '添加工具', 'type': 'normal'},
            {'id': 'edit_toggle', 'text': '工具管理', 'type': 'toggle'}
        ])
        self._back_target = 'workflows'
        try:
            self.toolbar.set_back_target(self.tr("工作流"))
        except Exception:
            pass

    def _on_back_from_workflow(self):
        self._on_view_changed("workflows")

    def _on_rename_workflow(self, workflow_id: str):
        wf = self.workflows_manager.get_workflow(workflow_id)
        if not wf:
            return
        from PyQt5.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, self.tr("重命名工作流"), self.tr("新名称"), text=wf.name)
        if ok and new_name.strip():
            self.workflows_manager.rename_workflow(workflow_id, new_name.strip())
            if self.workflows_main_view:
                self.workflows_main_view.refresh()

    def _on_duplicate_workflow(self, workflow_id: str):
        self.workflows_manager.duplicate_workflow(workflow_id)
        if self.workflows_main_view:
            self.workflows_main_view.refresh()

    def _on_delete_workflow(self, workflow_id: str):
        from PyQt5.QtWidgets import QMessageBox
        r = QMessageBox.question(self, self.tr("确认删除"), self.tr("删除工作流将移除其中的工具集合，且不可撤销。确认删除？"))
        if r == QMessageBox.Yes:
            self.workflows_manager.delete_workflow(workflow_id)
            if self.workflows_main_view:
                self.workflows_main_view.refresh()

    def _on_pick_tool_for_workflow(self):
        # 内嵌选择页：首次创建并加入堆栈
        if (self.tool_picker_page is None) and ToolPickerPage:
            self.tool_picker_page = ToolPickerPage(self.config_manager, self)
            self.tool_picker_page.tool_selected.connect(self._on_tool_picked_in_page)
            # 选择器内“详情”请求
            try:
                self.tool_picker_page.detail_requested.connect(self._on_picker_detail_requested)
            except Exception:
                pass
            self.main_content_stack.addWidget(self.tool_picker_page)
        # 切换到选择页
        if self.tool_picker_page:
            self.main_content_stack.setCurrentWidget(self.tool_picker_page)
            # 顶栏进入“页面详情模式”，隐藏默认按钮，显示“完成”
            self.toolbar.switch_to_detail_mode()
            self.toolbar.set_default_buttons_visible(False)
            self.toolbar.set_actions([
                {'id': 'picker_done', 'text': '完成', 'type': 'normal'}
            ])
            # 返回目标：当前工作流名称（动态）
            try:
                wf = self.workflows_manager.get_workflow(getattr(self, '_current_workflow_id', ''))
                if wf:
                    self.toolbar.set_back_target(wf.name)
                else:
                    # 回退为“工作流”
                    self.toolbar.set_back_target(self.tr("工作流"))
            except Exception:
                pass

    def _on_remove_tool_from_workflow(self, index: int):
        """从当前工作流移除工具；若工具已安装，询问是否同时卸载。"""
        from PyQt5.QtWidgets import QMessageBox
        wf = self.workflows_manager.get_workflow(getattr(self, '_current_workflow_id', ''))
        if not wf:
            return
        # 获取工具名
        try:
            item = wf.tools[index]
            tool_name = getattr(item, 'tool_name', None) or item.get('tool_name')
        except Exception:
            tool_name = None
        # 判断是否安装
        is_installed = False
        if tool_name:
            try:
                info = self.tool_manager.get_tool_info(tool_name)
                is_installed = (info.get('status') == 'installed') if info else False
            except Exception:
                # 回退到配置查询
                try:
                    for td in self.config_manager.tools:
                        if td.get('name') == tool_name:
                            is_installed = (td.get('status') == 'installed')
                            break
                except Exception:
                    is_installed = False
        # 已安装：询问是否同时卸载
        if is_installed and tool_name:
            reply = QMessageBox.question(
                self,
                self.tr("提示"),
                self.tr("{0} 已安装，是否同时卸载？\n\n是：从工作流移除并卸载工具\n否：仅从工作流移除\n取消：不执行操作").format(tool_name),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.No
            )
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                # 先发起卸载（异步），然后从工作流移除
                try:
                    self.tool_manager.uninstall_tool(tool_name)
                except Exception:
                    pass
                # 继续移除
        # 执行移除
        self.workflows_manager.remove_tool(wf.id, index)
        wf = self.workflows_manager.get_workflow(wf.id)
        self.workflows_detail_view.set_workflow(wf.id, wf.name, wf.tools)

    def _on_move_tool_in_workflow(self, index: int, direction: int):
        wf = self.workflows_manager.get_workflow(getattr(self, '_current_workflow_id', ''))
        if not wf:
            return
        if self.workflows_manager.move_tool(wf.id, index, direction):
            wf = self.workflows_manager.get_workflow(wf.id)
            self.workflows_detail_view.set_workflow(wf.id, wf.name, wf.tools)

    def _on_toolbar_back(self):
        from PyQt5.QtWidgets import QWidget
        # 优先处理“选择器详情”返回：先回到选择器列表页
        try:
            if self._in_picker_detail:
                self._return_to_picker_page()
                return
        except Exception:
            pass
        # 其次处理选择器列表页的返回：回到工作流详情页
        try:
            if self.tool_picker_page and self.main_content_stack.currentWidget() is self.tool_picker_page:
                self._return_to_workflow_detail()
                return
        except Exception:
            pass
        # 根据当前页面与目标，决定返回行为
        current = self.main_content_stack.currentWidget() if self.main_content_stack else None
        if self._back_target == 'workflows':
            # 如果当前是工具详情页，回到工作流详情；如果当前已在工作流详情，回到工作流列表
            if current is self.workflows_detail_view:
                self._on_back_from_workflow()  # 返回到工作流列表
            else:
                self._return_to_workflow_detail()  # 返回到当前工作流详情
            return
        # 其他情况，回到主工具列表
        self.go_back_to_main()

    # 统一处理顶栏动作
    def _connect_toolbar_actions(self):
        try:
            self.toolbar.action_clicked.disconnect()
        except Exception:
            pass
        try:
            self.toolbar.action_toggled.disconnect()
        except Exception:
            pass
        self.toolbar.action_clicked.connect(self._on_toolbar_action_clicked)
        self.toolbar.action_toggled.connect(self._on_toolbar_action_toggled)

    def _on_toolbar_action_clicked(self, action_id: str):
        if action_id == 'new_wf':
            self._on_new_workflow()
        elif action_id == 'add':
            self._on_pick_tool_for_workflow()
        elif action_id == 'picker_done':
            # 完成选择，返回到工作流详情
            self._return_to_workflow_detail()
        elif action_id == 'picker_add':
            # 在“选择器详情页”中，添加当前详情工具
            try:
                if self.current_detail_page and hasattr(self.current_detail_page, 'tool_data'):
                    tool_name = self.current_detail_page.tool_data.get('name')
                    if tool_name:
                        self._on_tool_picked_in_page(tool_name)
            except Exception:
                pass

    def _on_toolbar_action_toggled(self, action_id: str, state: bool):
        if action_id == 'edit_toggle':
            # 切换详情页编辑模式
            try:
                self.workflows_detail_view.set_edit_mode(state)
            except Exception:
                pass

    def _on_tool_picked_in_page(self, tool_name: str):
        # 添加确认（今日不再提示）
        from PyQt5.QtWidgets import QMessageBox, QCheckBox
        if not self.workflows_manager.is_add_confirm_suppressed_today():
            msg = QMessageBox(self)
            msg.setWindowTitle(self.tr("确认添加"))
            msg.setText(self.tr("确认将 {0} 添加到当前工作流？").format(tool_name))
            cb = QCheckBox(self.tr("今日不再提示"))
            msg.setCheckBox(cb)
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            if msg.exec() == QMessageBox.Ok:
                if cb.isChecked():
                    self.workflows_manager.suppress_add_confirm_today()
            else:
                return
        # 实际添加
        wf = self.workflows_manager.get_workflow(getattr(self, '_current_workflow_id', ''))
        if wf:
            self.workflows_manager.add_tool(wf.id, tool_name)
            wf = self.workflows_manager.get_workflow(wf.id)
            self.workflows_detail_view.set_workflow(wf.id, wf.name, wf.tools)

    def _return_to_workflow_detail(self):
        """返回到当前工作流详情页，并恢复工具栏动作"""
        try:
            wf = self.workflows_manager.get_workflow(getattr(self, '_current_workflow_id', ''))
        except Exception:
            wf = None
        if wf and self.workflows_detail_view:
            # 若正处于工具详情页，先移除旧详情页，避免后续点击被误判“已在显示”
            try:
                if self.current_detail_page:
                    self.main_content_stack.removeWidget(self.current_detail_page)
                    self.current_detail_page.deleteLater()
                    self.current_detail_page = None
            except Exception:
                pass
            # 切回详情视图
            self.workflows_detail_view.set_workflow(wf.id, wf.name, wf.tools)
            self.main_content_stack.setCurrentWidget(self.workflows_detail_view)
            # 顶栏：恢复“添加工具 + 工具管理”，返回目标为“工作流”
            self.toolbar.switch_to_detail_mode()
            self.toolbar.set_default_buttons_visible(False)
            self.toolbar.set_actions([
                {'id': 'add', 'text': '添加工具', 'type': 'normal'},
                {'id': 'edit_toggle', 'text': '工具管理', 'type': 'toggle'}
            ])
            self._back_target = 'workflows'
            try:
                self.toolbar.set_back_target(self.tr("工作流"))
            except Exception:
                pass
        else:
            # 回退到工作流列表
            self._on_back_from_workflow()

    def _return_to_picker_page(self):
        """从选择器详情返回到选择器卡片列表页"""
        self._in_picker_detail = False
        try:
            if self.tool_picker_page:
                self.main_content_stack.setCurrentWidget(self.tool_picker_page)
                # 顶栏：选择器列表模式（返回 {工作流名} + 完成）
                self.toolbar.switch_to_detail_mode()
                self.toolbar.set_default_buttons_visible(False)
                self.toolbar.set_actions([
                    {'id': 'picker_done', 'text': '完成', 'type': 'normal'}
                ])
                wf = self.workflows_manager.get_workflow(getattr(self, '_current_workflow_id', ''))
                self.toolbar.set_back_target(wf.name if wf else self.tr('工作流'))
        except Exception:
            pass

    def _on_picker_detail_requested(self, tool_name: str):
        """在选择器中请求查看某个工具详情（特殊模式）"""
        # 查找工具数据
        tool_data = None
        try:
            tool_data = self.tool_manager.get_tool_info(tool_name)
        except Exception:
            tool_data = None
        if not tool_data:
            return
        # 显示详情页（复用通用详情页）
        self.show_tool_detail_page(tool_data)
        # 进入选择器详情上下文：顶栏显示“添加 + 完成”，返回目标为工作流名
        self._in_picker_detail = True
        # 隐藏详情页内的启动/安装/卸载按钮，避免与“添加”语义冲突
        try:
            if self.current_detail_page:
                for attr in ('launch_btn', 'install_btn', 'uninstall_btn'):
                    btn = getattr(self.current_detail_page, attr, None)
                    if btn:
                        btn.hide()
        except Exception:
            pass
        try:
            self.toolbar.set_default_buttons_visible(False)
            self.toolbar.set_actions([
                {'id': 'picker_add', 'text': '添加', 'type': 'normal'},
                {'id': 'picker_done', 'text': '完成', 'type': 'normal'}
            ])
            wf = self.workflows_manager.get_workflow(getattr(self, '_current_workflow_id', ''))
            self.toolbar.set_back_target(wf.name if wf else self.tr('工作流'))
        except Exception:
            pass
    
    def _open_filter_panel(self):
        """打开筛选面板 - 1.2.1版本"""
        print(f"【MAIN WINDOW DEBUG】=== _open_filter_panel 函数开始执行 ===")
        
        # 如果下载状态面板打开，先关闭它（保持相互排斥的新特性）
        if hasattr(self, 'modern_download_card') and self.modern_download_card and self.modern_download_card.isVisible():
            print(f"【MAIN WINDOW DEBUG】关闭现代化下载卡片")
            self._close_modern_download_card()
        # 旧系统已移除，无需检查 download_status_panel
            
        # 设置当前筛选状态
        print(f"【MAIN WINDOW DEBUG】设置筛选状态: 分类={self.current_categories}, 状态={self.current_statuses}")
        self.filter_panel.set_selected_filters(self.current_categories, self.current_statuses)
        
        print(f"【MAIN WINDOW DEBUG】调用 filter_panel.show() 显示筛选面板")
        
        # 强制重新应用圆角样式（每次显示时都重新设置）
        self.filter_panel.setWindowFlags(Qt.FramelessWindowHint)
        self.filter_panel.setAttribute(Qt.WA_TranslucentBackground, True)
        import logging
        logger = logging.getLogger('BioNexus.ui_operations')
        logger.info(f"[主窗口] 强制重新应用筛选面板圆角样式")
        print(f"【MAIN WINDOW DEBUG】强制重新应用筛选面板圆角样式")
        
        # 悬浮面板定位：右侧边距20px，顶部边距100px
        panel_x = self.width() - self.filter_panel.width() - 20
        panel_y = 100
        self.filter_panel.move(panel_x, panel_y)
        print(f"【MAIN WINDOW DEBUG】筛选面板定位到: ({panel_x}, {panel_y})")
        
        self.filter_panel.show()
        print(f"【MAIN WINDOW DEBUG】筛选面板 show() 调用完成，当前可见状态: {self.filter_panel.isVisible()}")
        
        # 更新现代化工具栏状态（适配新的工具栏）
        if hasattr(self, 'toolbar'):
            print(f"【MAIN WINDOW DEBUG】更新工具栏筛选状态为激活")
            self.toolbar.set_filter_active(True)
        
        print(f"【MAIN WINDOW DEBUG】=== _open_filter_panel 函数执行完成 ===")
    
    # def _close_filter_panel(self):  # 旧系统方法，已不再使用
    
    def _open_modern_filter_card(self):
        """打开现代化筛选卡片 - 参考下载卡片逻辑"""
        import logging
        logger = logging.getLogger(__name__)
        print(f"【MAIN WINDOW DEBUG】=== _open_modern_filter_card 函数开始执行 ===")
        logger.info(f"【MAIN WINDOW DEBUG】=== _open_modern_filter_card 函数开始执行 ===")
        
        # 如果下载卡片打开，先关闭它（相互排斥）
        if self.modern_download_card and self.modern_download_card.isVisible():
            print(f"【MAIN WINDOW DEBUG】关闭现代化下载卡片")
            self._close_modern_download_card()
        # 旧系统已移除，无需检查 download_status_panel
            
        # 如果卡片不存在，创建它
        if not self.modern_filter_card:
            print("【MAIN WINDOW DEBUG】创建现代化筛选卡片")
            logger.info("【MAIN WINDOW DEBUG】创建现代化筛选卡片")
            from .modern_filter_card import ModernFilterCard
            try:
                self.modern_filter_card = ModernFilterCard(self)
                print(f"【MAIN WINDOW DEBUG】筛选卡片创建成功: {self.modern_filter_card}")
            except Exception as e:
                print(f"【MAIN WINDOW ERROR】创建筛选卡片失败: {e}")
                import traceback
                print(f"【MAIN WINDOW ERROR】详细错误:\n{traceback.format_exc()}")
                return
            
            # 连接信号 - 保持与旧版本完全一致
            self.modern_filter_card.filters_applied.connect(self._on_filters_applied)
            self.modern_filter_card.filters_reset.connect(self._on_filters_reset)
            self.modern_filter_card.card_closed.connect(self._close_modern_filter_card)
            print("【MAIN WINDOW DEBUG】现代化筛选卡片信号连接完成")
            logger.info("【MAIN WINDOW DEBUG】现代化筛选卡片信号连接完成")
        
        # 设置当前筛选状态
        print(f"【MAIN WINDOW DEBUG】设置筛选状态: 分类={self.current_categories}, 状态={self.current_statuses}")
        logger.info(f"【MAIN WINDOW DEBUG】设置筛选状态: 分类={self.current_categories}, 状态={self.current_statuses}")
        self.modern_filter_card.set_selected_filters(self.current_categories, self.current_statuses)
        
        # 获取精确的位置信息 - 与下载卡片完全一致的逻辑
        toolbar_rect = self.toolbar.geometry()
        filter_button_rect = self.toolbar.filter_rect
        
        print(f"【MAIN WINDOW DEBUG】工具栏矩形: {toolbar_rect}")
        print(f"【MAIN WINDOW DEBUG】筛选按钮矩形: {filter_button_rect}")
        logger.info(f"【MAIN WINDOW DEBUG】工具栏矩形: {toolbar_rect}")
        logger.info(f"【MAIN WINDOW DEBUG】筛选按钮矩形: {filter_button_rect}")
        
        # 显示遮罩层
        print("【MAIN WINDOW DEBUG】显示遮罩层")
        logger.info("【MAIN WINDOW DEBUG】显示遮罩层")
        self.overlay.show_animated()
        
        # 显示卡片 - 使用智能定位（靠右对齐）
        print("【MAIN WINDOW DEBUG】开始显示现代化筛选卡片")
        logger.info("【MAIN WINDOW DEBUG】开始显示现代化筛选卡片")
        try:
            self.modern_filter_card.show_aligned_to_toolbar(
                toolbar_bottom=toolbar_rect.bottom(),
                button_rect=filter_button_rect,
                window_rect=self.rect()
            )
        except Exception as e:
            print(f"【MAIN WINDOW ERROR】显示筛选卡片失败: {e}")
            import traceback
            print(f"【MAIN WINDOW ERROR】详细错误:\n{traceback.format_exc()}")
        
        # 确保卡片在遮罩层之上
        print("【MAIN WINDOW DEBUG】将卡片提升到最前面")
        logger.info("【MAIN WINDOW DEBUG】将卡片提升到最前面")
        self.modern_filter_card.raise_()
        
        # 更新工具栏状态 - 设置按钮为激活状态（蓝色）
        if hasattr(self, 'toolbar'):
            print(f"【MAIN WINDOW DEBUG】更新工具栏筛选状态为激活")
            self.toolbar.set_filter_active(True)
        
        print(f"【MAIN WINDOW DEBUG】=== _open_modern_filter_card 函数执行完成 ===")
    
    def _close_modern_filter_card(self):
        """关闭现代化筛选卡片"""
        print(f"【MAIN WINDOW DEBUG】=== _close_modern_filter_card 函数开始执行 ===")
        
        if self.modern_filter_card:
            print(f"【MAIN WINDOW DEBUG】隐藏现代化筛选卡片")
            self.modern_filter_card.hide()
        
        # 隐藏遮罩层
        self.overlay.hide_animated()
        
        # 更新工具栏状态
        if hasattr(self, 'toolbar'):
            print(f"【MAIN WINDOW DEBUG】更新工具栏筛选状态为非激活")
            self.toolbar.set_filter_active(False)
        
        print(f"【MAIN WINDOW DEBUG】=== _close_modern_filter_card 函数执行完成 ===")
    
    
    def _on_filters_applied(self, categories: list, statuses: list):
        """
        筛选条件应用处理
        对应JavaScript中的applyFilters函数
        """
        # 记录筛选应用到监控系统
        if self.monitor:
            self.monitor.log_user_operation("应用筛选", {
                "分类": categories,
                "状态": statuses
            })
        
        self.current_categories = categories
        self.current_statuses = statuses
        self._apply_current_filters()
    
    def _on_overlay_clicked(self):
        """遮罩层点击事件处理 - 关闭所有弹出卡片"""
        # 关闭筛选卡片
        if self.modern_filter_card and self.modern_filter_card.isVisible():
            self._close_modern_filter_card()
        
        # 关闭下载卡片
        if self.modern_download_card and self.modern_download_card.isVisible():
            self._close_modern_download_card()
    
    def _on_filters_reset(self):
        """
        筛选条件重置处理
        对应JavaScript中的resetFilters函数
        """
        # 记录筛选重置到监控系统
        if self.monitor:
            self.monitor.log_user_operation("重置筛选", {})
        
        self.current_categories = []
        self.current_statuses = []
        self._apply_current_filters()
    
    def _on_tool_installed(self, tool_name: str):
        """工具安装完成处理"""
        import logging
        logger = logging.getLogger(__name__)
        
        msg = f"[日志-I1] *** _on_tool_installed 信号回调被触发 ***: {tool_name}"
        print(msg)
        logger.info(msg)
        
        # 记录工具安装到监控系统
        if self.monitor:
            msg = f"[日志-I2] 记录安装操作到监控系统: {tool_name}"
            print(msg)
            logger.info(msg)
            self.monitor.log_tool_operation(tool_name, "安装", True)
        
        # 更新工具卡片状态
        msg = f"[日志-I3] 开始更新工具卡片状态: {tool_name}"
        print(msg)
        logger.info(msg)
        # 主工具网格
        card = self.tools_grid.get_card_by_name(tool_name)
        if card:
            msg = f"[日志-I4] 找到工具卡片({type(card).__name__})，更新状态: {tool_name}"
            print(msg)
            logger.info(msg)
            # 先清除安装进度状态
            card.set_installing_state(False, 0, "")
            msg = f"[日志-I5] 已清除安装进度状态: {tool_name}"
            print(msg)
            logger.info(msg)
            
            # 优先使用卡片API切换按钮与状态
            if hasattr(card, 'update_tool_status'):
                card.update_tool_status("installed", 
                                       executable_path=f"/path/to/{tool_name.lower()}",
                                       disk_usage="15.2 MB")
                msg = f"[日志-I6] 已通过update_tool_status切换为已安装: {tool_name}"
            elif hasattr(card, 'tool_data'):
                card.tool_data['status'] = 'installed'
                card.tool_data['executable_path'] = f"/path/to/{tool_name.lower()}"
                card.tool_data['disk_usage'] = "15.2 MB"
                card.update(); card.repaint()
                msg = f"[日志-I6] 已更新ToolCardV3数据并重绘: {tool_name}"
            else:
                msg = f"[日志-I6] 警告：未知的卡片类型，无法更新状态: {tool_name}"
            print(msg)
            logger.info(msg)
        else:
            msg = f"[日志-I4] 警告：未找到工具卡片: {tool_name}"
            print(msg)
            logger.warning(msg)
        # 工作流详情页中的卡片（若存在）
        try:
            if self.workflows_detail_view and hasattr(self.workflows_detail_view, 'cards'):
                wcard = self.workflows_detail_view.cards.get_card_by_name(tool_name)
                if wcard:
                    if hasattr(wcard, 'set_installing_state'):
                        wcard.set_installing_state(False, 0, "")
                    if hasattr(wcard, 'update_tool_status'):
                        wcard.update_tool_status("installed", 
                                                 executable_path=f"/path/to/{tool_name.lower()}",
                                                 disk_usage="15.2 MB")
                    elif hasattr(wcard, 'tool_data'):
                        wcard.tool_data['status'] = 'installed'
                        wcard.tool_data['executable_path'] = f"/path/to/{tool_name.lower()}"
                        wcard.tool_data['disk_usage'] = "15.2 MB"
                        wcard.update(); wcard.repaint()
        except Exception:
            pass
        
        # 更新最近使用列表
        msg = f"[日志-I7] 更新最近使用列表: {tool_name}"
        print(msg)
        logger.info(msg)
        self.config_manager.update_recent_tools(tool_name)
        self.sidebar.update_recent_tools(self.config_manager.recent_tools)
        msg = f"[日志-I8] 最近使用列表更新完成: {tool_name}"
        print(msg)
        logger.info(msg)
        
        # 刷新整个工具列表显示（确保状态同步）
        msg = f"[日志-I9] *** 开始强制刷新UI ***: {tool_name}"
        print(msg)
        logger.info(msg)
        self._force_refresh_all_ui()
        
        # 如果当前在详情页面且是刚安装的工具，刷新详情页面显示
        if (self.current_detail_page and 
            hasattr(self.current_detail_page, 'tool_data') and 
            self.current_detail_page.tool_data['name'] == tool_name):
            print(f"[日志-I11] 当前详情页面显示的是刚安装的工具，刷新页面: {tool_name}")
            logger.info(f"[日志-I11] 当前详情页面显示的是刚安装的工具，刷新页面: {tool_name}")
            
            # 更新工具数据状态
            print(f"[日志-I12] 更新详情页面工具数据状态: {tool_name} -> installed")
            logger.info(f"[日志-I12] 更新详情页面工具数据状态: {tool_name} -> installed")
            self.current_detail_page.tool_data['status'] = 'installed'
            self.current_detail_page.tool_data['executable_path'] = f"/path/to/{tool_name.lower()}"
            self.current_detail_page.tool_data['disk_usage'] = "15.2 MB"
            
            # 刷新详情页面显示（重新创建UI，这会根据新状态显示正确的按钮）
            if hasattr(self.current_detail_page, 'update_ui'):
                print(f"[日志-I13] 调用详情页面的update_ui方法: {tool_name}")
                logger.info(f"[日志-I13] 调用详情页面的update_ui方法: {tool_name}")
                self.current_detail_page.update_ui()
                print(f"[日志-I14] 详情页面update_ui调用完成: {tool_name}")
                logger.info(f"[日志-I14] 详情页面update_ui调用完成: {tool_name}")
            else:
                # 如果没有update_ui方法，重新创建详情页面
                print(f"[日志-I13] 详情页面没有update_ui方法，重新创建页面: {tool_name}")
                logger.info(f"[日志-I13] 详情页面没有update_ui方法，重新创建页面: {tool_name}")
                tool_data = self.current_detail_page.tool_data
                self.show_tool_detail_page(tool_data)
        
        msg = f"[日志-I10] *** UI刷新完成 ***: {tool_name}"
        print(msg)
        logger.info(msg)
    
    @pyqtSlot(str)
    def _on_tool_launched(self, tool_name: str):
        """工具启动完成处理

        🔥 使用 @pyqtSlot 装饰器确保信号正确传递
        """
        # 记录工具启动到监控系统
        if self.monitor:
            self.monitor.log_tool_operation(tool_name, "启动", True)

        # 更新最近使用列表
        self.config_manager.update_recent_tools(tool_name)
        self.sidebar.update_recent_tools(self.config_manager.recent_tools)

        # 更新详情页运行状态（如果当前显示的是该工具）
        if (self.current_detail_page and
            hasattr(self.current_detail_page, 'update_running_state') and
            hasattr(self.current_detail_page, 'tool_data') and
            self.current_detail_page.tool_data.get('name') == tool_name):
            self.current_detail_page.update_running_state(True)
            logger.info(f"✅ [MainWindow-工具启动] 已更新详情页运行状态: {tool_name}")

            # 🔥 与关闭时保持一致：在父容器上也调用update()和repaint()
            self.current_detail_page.update()
            self.current_detail_page.repaint()
            # 修复：使用正确的堆栈部件引用
            if self.main_content_stack:
                self.main_content_stack.update()
                self.main_content_stack.repaint()
            QApplication.processEvents()
            logger.info(f"🎨 [MainWindow-强制刷新] 已强制刷新父容器和QStackedWidget")

        # 启动兜底轮询（用于无法正确回调停止的工具）
        try:
            self._running_tool_name = tool_name
            if hasattr(self, 'tool_manager') and getattr(self.tool_manager, 'usage_tracker', None):
                self._run_state_timer.start()
        except Exception:
            pass
    
    def _on_tool_uninstalled(self, tool_name: str):
        """工具卸载完成处理"""
        import logging
        logger = logging.getLogger(__name__)
        
        print(f"[日志-D1] *** _on_tool_uninstalled 信号回调被触发 ***: {tool_name}")
        
        # 记录工具卸载到监控系统
        if self.monitor:
            print(f"[日志-D2] 记录卸载操作到监控系统: {tool_name}")
            self.monitor.log_tool_operation(tool_name, "卸载", True)
        
        # 🎯 更新下载卡片：标记卸载任务完成
        if self.modern_download_card:
            display_name = self.tr("{0} (卸载)").format(tool_name)
            # 使用100%进度和完成状态
            self.modern_download_card.add_or_update_download(display_name, 100, self.tr("卸载完成"))
        
        # 更新下载按钮状态
        self._update_download_button_state()
        
        # 更新工具卡片状态
        print(f"[日志-D3] 开始更新工具卡片状态: {tool_name}")
        card = self.tools_grid.get_card_by_name(tool_name)
        if card:
            print(f"[日志-D4] 找到工具卡片({type(card).__name__})，更新状态: {tool_name}")
            # 先清除卸载进度状态
            card.set_installing_state(False, 0, "")
            print(f"[日志-D5] 已清除卸载进度状态: {tool_name}")
            
            # 优先使用卡片API切换按钮与状态
            if hasattr(card, 'update_tool_status'):
                card.update_tool_status("available", executable_path="", disk_usage="")
                print(f"[日志-D6] 已通过update_tool_status切换为未安装状态: {tool_name}")
            elif hasattr(card, 'tool_data'):
                card.tool_data['status'] = 'available'
                card.tool_data['executable_path'] = ""
                card.tool_data['disk_usage'] = ""
                card.update(); card.repaint()
                print(f"[日志-D6] 已更新ToolCardV3数据并重绘为未安装状态: {tool_name}")
            else:
                print(f"[日志-D6] 警告：未知的卡片类型，无法更新状态: {tool_name}")
        else:
            print(f"[日志-D4] 警告：未找到工具卡片: {tool_name}")
        
        # 从最近使用列表中移除
        print(f"[日志-D7] 从最近使用列表中移除: {tool_name}")
        logger.info(f"[日志-D7] 从最近使用列表中移除: {tool_name}")
        try:
            self.config_manager.remove_from_recent_tools(tool_name)
            self.sidebar.update_recent_tools(self.config_manager.recent_tools)
            print(f"[日志-D8] 最近使用列表更新完成: {tool_name}")
            logger.info(f"[日志-D8] 最近使用列表更新完成: {tool_name}")
        except Exception as e:
            print(f"[日志-D8] 警告：更新最近使用列表失败: {e}")
            logger.error(f"[日志-D8] 警告：更新最近使用列表失败: {e}")
        
        # 刷新工具列表显示
        print(f"[日志-D9] *** 开始强制刷新UI ***: {tool_name}")
        logger.info(f"[日志-D9] *** 开始强制刷新UI ***: {tool_name}")
        self._force_refresh_all_ui()

        # 同步更新工作流详情页中的卡片
        try:
            if self.workflows_detail_view and hasattr(self.workflows_detail_view, 'cards'):
                wcard = self.workflows_detail_view.cards.get_card_by_name(tool_name)
                if wcard:
                    if hasattr(wcard, 'set_installing_state'):
                        wcard.set_installing_state(False, 0, "")
                    if hasattr(wcard, 'tool_data'):
                        wcard.tool_data['status'] = 'available'
                        wcard.tool_data['executable_path'] = ""
                        wcard.tool_data['disk_usage'] = ""
                        wcard.update(); wcard.repaint()
        except Exception:
            pass
        
        # 如果当前在详情页面且是刚卸载的工具，刷新详情页面显示
        if (self.current_detail_page and 
            hasattr(self.current_detail_page, 'tool_data') and 
            self.current_detail_page.tool_data['name'] == tool_name):
            print(f"[日志-D11] 当前详情页面显示的是刚卸载的工具，刷新页面: {tool_name}")
            logger.info(f"[日志-D11] 当前详情页面显示的是刚卸载的工具，刷新页面: {tool_name}")
            
            # 更新工具数据状态
            print(f"[日志-D12] 更新详情页面工具数据状态: {tool_name} -> available")
            logger.info(f"[日志-D12] 更新详情页面工具数据状态: {tool_name} -> available")
            # 确保运行状态复位
            try:
                if hasattr(self.current_detail_page, 'update_running_state'):
                    self.current_detail_page.update_running_state(False)
            except Exception:
                pass
            self.current_detail_page.tool_data['status'] = 'available'
            self.current_detail_page.tool_data['executable_path'] = ""
            self.current_detail_page.tool_data['disk_usage'] = ""
            
            # 刷新详情页面显示
            if hasattr(self.current_detail_page, 'update_ui'):
                print(f"[日志-D13] 调用详情页面的update_ui方法: {tool_name}")
                logger.info(f"[日志-D13] 调用详情页面的update_ui方法: {tool_name}")
                self.current_detail_page.update_ui()
                print(f"[日志-D14] 详情页面update_ui调用完成: {tool_name}")
                logger.info(f"[日志-D14] 详情页面update_ui调用完成: {tool_name}")
            else:
                # 如果没有update_ui方法，重新创建详情页面
                print(f"[日志-D13] 详情页面没有update_ui方法，重新创建页面: {tool_name}")
                logger.info(f"[日志-D13] 详情页面没有update_ui方法，重新创建页面: {tool_name}")
                tool_data = self.current_detail_page.tool_data
                self.show_tool_detail_page(tool_data)
        
        print(f"[日志-D10] *** UI刷新完成 ***: {tool_name}")
        logger.info(f"[日志-D10] *** UI刷新完成 ***: {tool_name}")

    def _on_tool_status_changed(self, tool_name: str, new_status: str):
        """统一处理工具状态变化（包括installed/available/update等）。"""
        import logging
        logger = logging.getLogger(__name__)
        print(f"[状态变更] 工具状态变化: {tool_name} -> {new_status}")
        logger.info(f"[状态变更] 工具状态变化: {tool_name} -> {new_status}")

        # 更新主网格卡片
        card = self.tools_grid.get_card_by_name(tool_name)
        if card:
            # 清除任何进行中的安装/卸载进度显示
            if hasattr(card, 'set_installing_state'):
                card.set_installing_state(False, 0, "")
            if hasattr(card, 'update_tool_status'):
                card.update_tool_status(new_status)
            elif hasattr(card, 'tool_data'):
                card.tool_data['status'] = new_status
                card.update(); card.repaint()
        else:
            logger.info(f"[状态变更] 未找到卡片: {tool_name}，刷新整个工具网格")

        # 同步更新工作流详情页中的卡片
        try:
            if self.workflows_detail_view and hasattr(self.workflows_detail_view, 'cards'):
                wcard = self.workflows_detail_view.cards.get_card_by_name(tool_name)
                if wcard:
                    if hasattr(wcard, 'set_installing_state'):
                        wcard.set_installing_state(False, 0, "")
                    if hasattr(wcard, 'update_tool_status'):
                        wcard.update_tool_status(new_status)
                    elif hasattr(wcard, 'tool_data'):
                        wcard.tool_data['status'] = new_status
                        wcard.update(); wcard.repaint()
        except Exception:
            pass

        # 如果当前详情显示的是该工具且状态变为非已安装，复位“运行中”按钮
        try:
            if (self.current_detail_page and hasattr(self.current_detail_page, 'tool_data') and
                self.current_detail_page.tool_data.get('name') == tool_name and
                str(new_status).lower() != 'installed' and
                hasattr(self.current_detail_page, 'update_running_state')):
                self.current_detail_page.update_running_state(False)
        except Exception:
            pass

        # 刷新列表并重应用筛选，确保所有视图（包括收藏、筛选视图）立即反映新状态
        self._update_tools_display()
        self._apply_current_filters()
    
    def _on_installation_progress(self, tool_name: str, progress: int, status_text: str):
        """安装/卸载进度更新处理（接收 ToolManager 的进度信号）"""
        import logging
        logger = logging.getLogger(__name__)
        import time
        
        # 🎯 判断是安装还是卸载任务
        is_uninstall = "卸载" in status_text or "删除" in status_text or "清理" in status_text or "停止" in status_text
        task_type = "卸载" if is_uninstall else "安装"
        
        print(f"【下载状态链路-P1】收到{task_type}进度信号: {tool_name} - {progress}% - {status_text}")
        logger.info(f"【下载状态链路-P1】收到{task_type}进度信号: {tool_name} - {progress}% - {status_text}")
        
        # 进度节流：避免频繁重绘导致的闪烁
        try:
            now = time.time()
            cache = self._progress_cache.get(tool_name) or {'p': None, 's': None, 'ts': 0}
            same_progress = (progress == cache['p'])
            same_status = (status_text == cache['s'])
            too_fast = (now - (cache['ts'] or 0)) < 0.15
            # 对于仅状态文本变化且时间间隔过短的更新，跳过卡片重绘（仍更新下载卡片）
            skip_card_update = (too_fast and same_progress and same_status)
            # 更新缓存
            self._progress_cache[tool_name] = {'p': progress, 's': status_text, 'ts': now}
        except Exception:
            skip_card_update = False

        # 更新主网格卡片状态
        card = self.tools_grid.get_card_by_name(tool_name)
        if card and not skip_card_update:
            print(f"【下载状态链路-P2】✅ 找到工具卡片，更新进度显示")
            logger.info(f"【下载状态链路-P2】✅ 找到工具卡片，更新进度显示")
            # 根据任务类型设置状态：安装=True，卸载=False
            is_installing_operation = not is_uninstall
            card.set_installing_state(is_installing_operation, progress, status_text)
        else:
            print(f"【下载状态链路-P2】⚠️ 未找到工具卡片: {tool_name}")
            logger.warning(f"【下载状态链路-P2】⚠️ 未找到工具卡片: {tool_name}")
        
        # 同步更新：工作流详情页中的卡片（如果存在）
        if not skip_card_update:
            try:
                if self.workflows_detail_view and hasattr(self.workflows_detail_view, 'cards'):
                    wcard = self.workflows_detail_view.cards.get_card_by_name(tool_name)
                    if wcard and hasattr(wcard, 'set_installing_state'):
                        is_installing_operation = not is_uninstall
                        wcard.set_installing_state(is_installing_operation, progress, status_text)
                        wcard.update(); wcard.repaint()
            except Exception:
                pass

        print(f"【下载状态链路-P2.5】✅ 工具卡片更新完成，继续执行后续流程")
        logger.info(f"【下载状态链路-P2.5】✅ 工具卡片更新完成，继续执行后续流程")
        
        # 如果当前在详情页面且是正在安装/卸载的工具，更新详情页面按钮进度
        if (self.current_detail_page and 
            hasattr(self.current_detail_page, 'tool_data') and 
            self.current_detail_page.tool_data['name'] == tool_name):
            print(f"【下载状态链路-P3】更新详情页面进度: {tool_name}, {progress}%, {status_text}")
            logger.info(f"【下载状态链路-P3】更新详情页面进度: {tool_name}, {progress}%, {status_text}")
            if hasattr(self.current_detail_page, 'set_installing_state'):
                # 根据任务类型设置状态：安装=True，卸载=False
                is_installing_operation = not is_uninstall
                self.current_detail_page.set_installing_state(is_installing_operation, progress, status_text)
        
        print(f"【下载状态链路-P3.5】✅ 详情页面检查完成，准备更新下载面板")
        logger.info(f"【下载状态链路-P3.5】✅ 详情页面检查完成，准备更新下载面板")
        
        # 统一更新现代化下载卡片
        print(f"【下载状态链路-P4】✅ 现在检查现代化下载卡片")
        logger.info(f"【下载状态链路-P4】✅ 现在检查现代化下载卡片")
        
        # 🎯 更新现代化下载卡片（现在预创建了，始终存在）
        if self.modern_download_card:
            # 为卸载任务添加特殊标记，让下载卡片能正确显示状态
            display_name = self.tr("{0} (卸载)").format(tool_name) if is_uninstall else tool_name
            print(f"【下载状态链路-P5】✅ 更新下载卡片: {display_name} - {progress}% - {status_text}")
            logger.info(f"【下载状态链路-P5】✅ 更新下载卡片: {display_name} - {progress}% - {status_text}")
            try:
                self.modern_download_card.add_or_update_download(display_name, progress, status_text)
                print(f"【下载状态链路-P5.1】✅ 下载卡片更新成功")
                logger.info(f"【下载状态链路-P5.1】✅ 下载卡片更新成功")
            except Exception as e:
                print(f"【下载状态链路-P5.1】❌ 下载卡片更新异常: {e}")
                logger.error(f"【下载状态链路-P5.1】❌ 下载卡片更新异常: {e}")
        else:
            print(f"【下载状态链路-P5】❌ 严重错误：下载卡片不存在！状态丢失！")
            logger.error(f"【下载状态链路-P5】❌ 严重错误：下载卡片不存在！状态丢失！")
        
        # 更新下载按钮状态
        print(f"【下载状态链路-P6】更新工具栏下载按钮状态")
        logger.info(f"【下载状态链路-P6】更新工具栏下载按钮状态")
        self._update_download_button_state()
        print(f"【下载状态链路-P6.1】✅ 工具栏下载按钮状态更新完成")
        logger.info(f"【下载状态链路-P6.1】✅ 工具栏下载按钮状态更新完成")
    
    def _on_tool_error(self, tool_name: str, error_message: str):
        """工具错误处理"""
        # 记录工具错误到监控系统
        if self.monitor:
            self.monitor.log_tool_operation(tool_name, "错误", False, error_message)
        
        QMessageBox.critical(self, self.tr("{0} 错误").format(tool_name), error_message)
        
        # 重置安装状态
        card = self.tools_grid.get_card_by_name(tool_name)
        if card:
            card.set_installing_state(False)
        
        # 如果当前在详情页面且是出错的工具，清除详情页面安装状态
        if (self.current_detail_page and 
            hasattr(self.current_detail_page, 'tool_data') and 
            self.current_detail_page.tool_data['name'] == tool_name):
            print(f"[安装错误-详情页面] 清除详情页面安装状态: {tool_name}")
            if hasattr(self.current_detail_page, 'set_installing_state'):
                self.current_detail_page.set_installing_state(False)
        
        # 更新现代化下载卡片为失败状态
        if self.modern_download_card:
            self.modern_download_card.mark_download_failed(tool_name, error_message)
        
        # 更新下载按钮状态
        self._update_download_button_state()

    @pyqtSlot(str, int)
    def _on_usage_time_updated(self, tool_name: str, total_runtime: int):
        """
        工具使用时间更新处理（工具停止时触发）

        🔥 使用 @pyqtSlot 装饰器确保跨线程信号正确传递

        Args:
            tool_name: 工具名称
            total_runtime: 总使用时间（秒）
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🎯 [MainWindow-信号接收] 工具={tool_name}, 时间={total_runtime}秒")

        # 🔥 关键修复：像启动时一样，直接同步调用！不用异步！
        # 更新详情页运行状态为停止（如果当前显示的是该工具）
        if (self.current_detail_page and
            hasattr(self.current_detail_page, 'update_running_state') and
            hasattr(self.current_detail_page, 'tool_data') and
            self.current_detail_page.tool_data.get('name') == tool_name):

            self.current_detail_page.update_running_state(False)
            logger.info(f"✅ [MainWindow-工具停止] 已更新详情页运行状态: {tool_name}")

            # 更新使用时间
            if hasattr(self.current_detail_page, 'update_usage_time'):
                self.current_detail_page.update_usage_time(total_runtime)
                logger.info(f"✅ [MainWindow-工具停止] 已更新使用时间")

            # 🔥 网上查到的关键解决方案：update()不会更新子widget！
            # 需要在父容器上也调用update()和repaint()
            self.current_detail_page.update()
            self.current_detail_page.repaint()
            # 修复：使用正确的堆栈部件引用
            if self.main_content_stack:
                self.main_content_stack.update()
                self.main_content_stack.repaint()
            QApplication.processEvents()
            logger.info(f"🎨 [MainWindow-强制刷新] 已强制刷新父容器和QStackedWidget")

        # 停止兜底轮询
        try:
            if self._running_tool_name == tool_name:
                self._run_state_timer.stop()
                self._running_tool_name = None
        except Exception:
            pass

    def _poll_running_state(self):
        """兜底轮询：检测详情页显示的工具是否已退出进程（防止回调丢失）。"""
        try:
            if not self._running_tool_name:
                return
            ut = getattr(self.tool_manager, 'usage_tracker', None)
            active = getattr(ut, 'active_sessions', {}) if ut else {}
            if self._running_tool_name not in active:
                # 主动将按钮置回“启动”
                if (self.current_detail_page and hasattr(self.current_detail_page, 'tool_data') and
                    self.current_detail_page.tool_data.get('name') == self._running_tool_name and
                    hasattr(self.current_detail_page, 'update_running_state')):
                    self.current_detail_page.update_running_state(False)
                    self.current_detail_page.update(); self.current_detail_page.repaint()
                self._run_state_timer.stop()
                self._running_tool_name = None
        except Exception:
            # 静默失败，避免干扰
            pass

        # 检查当前详情页
        logger.info(f"🔍 [MainWindow-详情页检查] current_detail_page: {self.current_detail_page}")

        if not self.current_detail_page:
            logger.info(f"⚠️ [MainWindow-详情页检查] 当前没有详情页，跳过刷新")
            return

        logger.info(f"🔍 [MainWindow-详情页检查] 详情页类型: {type(self.current_detail_page).__name__}")
        logger.info(f"🔍 [MainWindow-详情页检查] 详情页是否有tool_data: {hasattr(self.current_detail_page, 'tool_data')}")

        if hasattr(self.current_detail_page, 'tool_data'):
            current_tool_name = self.current_detail_page.tool_data.get('name', 'Unknown')
            logger.info(f"🔍 [MainWindow-详情页检查] 详情页显示的工具: {current_tool_name}")
            logger.info(f"🔍 [MainWindow-详情页检查] 是否匹配: {current_tool_name == tool_name}")

        # 如果当前详情页显示的是这个工具，直接更新UI（不重建页面）
        if (self.current_detail_page and
            hasattr(self.current_detail_page, 'tool_data') and
            self.current_detail_page.tool_data['name'] == tool_name):

            logger.info(f"✅ [MainWindow-直接更新UI] 匹配成功，开始更新: {tool_name}")

            # 🎯 方案：直接调用update方法，像启动时一样
            # 这个方法已经被证明能工作（启动按钮能立即变成"运行中"）

            # 🔍 诊断：检查Qt事件循环状态（在update之前）
            from PyQt5.QtCore import QThread, QCoreApplication
            current_thread = QThread.currentThread()
            main_thread = QCoreApplication.instance().thread()
            logger.info(f"🔍 [MainWindow-诊断-BEFORE] 当前线程: {current_thread}")
            logger.info(f"🔍 [MainWindow-诊断-BEFORE] 主线程: {main_thread}")
            logger.info(f"🔍 [MainWindow-诊断-BEFORE] 是否在主线程: {current_thread == main_thread}")
            logger.info(f"🔍 [MainWindow-诊断-BEFORE] hasPendingEvents: {QCoreApplication.hasPendingEvents()}")

            # 1. 更新使用时间显示
            if hasattr(self.current_detail_page, 'update_usage_time'):
                QApplication.processEvents()
                logger.info(f"⏱️ [MainWindow-直接更新UI] 调用 update_usage_time({total_runtime})")
                self.current_detail_page.update_usage_time(total_runtime)
                logger.info(f"✅ [MainWindow-直接更新UI] 使用时间已更新")

                # 强制刷新时间标签
                if hasattr(self.current_detail_page, 'usage_time_label') and self.current_detail_page.usage_time_label:
                    self.current_detail_page.usage_time_label.update()
                    self.current_detail_page.usage_time_label.repaint()
                    logger.info(f"🔄 [MainWindow-直接更新UI] 已强制刷新时间标签")

                QApplication.processEvents()
            else:
                logger.warning(f"⚠️ [MainWindow-直接更新UI] 详情页没有 update_usage_time 方法")

            # 2. 强制刷新UI（确保渲染） - 多次处理事件
            logger.info(f"🔄 [MainWindow-强制刷新] 开始多次强制刷新")

            # 刷新详情页
            self.current_detail_page.update()
            self.current_detail_page.repaint()

            # 刷新父容器（StackedWidget）
            if self.current_detail_page.parent():
                self.current_detail_page.parent().update()
                self.current_detail_page.parent().repaint()

            # 🔥 强制StackedWidget显示当前页面
            if self.main_content_stack:
                self.main_content_stack.setCurrentWidget(self.current_detail_page)
                self.main_content_stack.update()
                self.main_content_stack.repaint()
                logger.info(f"🔄 [MainWindow-强制刷新] StackedWidget已强制刷新")

            # 刷新整个窗口
            self.update()
            self.repaint()

            # 多次处理事件（确保Qt完全渲染）
            for i in range(5):
                QApplication.processEvents()
                logger.info(f"🔄 [MainWindow-强制刷新] 第{i+1}次处理事件")

            logger.info(f"✅ [MainWindow-直接更新UI] UI已强制刷新（5次）")

            # 3. 使用QTimer延迟再次刷新（确保在主事件循环中）
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._delayed_ui_refresh())
            logger.info(f"⏰ [MainWindow-延迟刷新] 已设置100ms延迟刷新")
        else:
            logger.info(f"⚠️ [MainWindow-详情页检查] 详情页不匹配，不刷新")

        logger.info(f"🎯 [MainWindow-信号接收] ========== 使用时间更新处理完成 ==========")

    def _delayed_ui_refresh(self):
        """延迟刷新当前详情页UI（无参数版本）"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"⏰ [MainWindow-延迟刷新] 开始延迟刷新当前详情页")

        if self.current_detail_page:
            # 刷新详情页
            self.current_detail_page.update()
            self.current_detail_page.repaint()
            logger.info(f"⏰ [MainWindow-延迟刷新] 详情页已刷新")

            # 强制StackedWidget显示当前页面
            if self.main_content_stack:
                self.main_content_stack.setCurrentWidget(self.current_detail_page)
                self.main_content_stack.update()
                self.main_content_stack.repaint()
                logger.info(f"⏰ [MainWindow-延迟刷新] StackedWidget已刷新")

            # 刷新父容器
            if self.current_detail_page.parent():
                self.current_detail_page.parent().update()
                self.current_detail_page.parent().repaint()

            # 刷新整个窗口
            self.update()
            self.repaint()

            # 处理事件
            QApplication.processEvents()
            logger.info(f"✅ [MainWindow-延迟刷新] 延迟刷新完成")

    def _delayed_refresh(self, tool_name: str):
        """延迟刷新UI（确保Qt完全渲染）"""
        logger.info(f"⏰ [MainWindow-延迟刷新] 开始延迟刷新: {tool_name}")

        # 再次刷新详情页和父容器
        if (self.current_detail_page and
            hasattr(self.current_detail_page, 'tool_data') and
            self.current_detail_page.tool_data.get('name') == tool_name):

            # 刷新详情页
            self.current_detail_page.update()
            self.current_detail_page.repaint()
            logger.info(f"⏰ [MainWindow-延迟刷新] 详情页已刷新")

            # 刷新父容器
            if self.main_content_stack:
                self.main_content_stack.update()
                self.main_content_stack.repaint()
                logger.info(f"⏰ [MainWindow-延迟刷新] 父容器已刷新")

            # 刷新整个窗口
            self.update()
            self.repaint()
            logger.info(f"⏰ [MainWindow-延迟刷新] 主窗口已刷新")

            # 处理事件
            QApplication.processEvents()
            logger.info(f"⏰ [MainWindow-延迟刷新] 延迟刷新完成")

    def _on_setting_changed(self, setting_name: str, value):
        """设置变更处理"""
        # 记录设置变更到监控系统
        if self.monitor:
            self.monitor.log_user_operation("设置变更", {
                "设置项": setting_name,
                "新值": str(value)
            })
        
        # 处理特殊的设置变更
        if setting_name == "check_updates_now":
            # 立即检查工具更新请求（来自设置面板的手动检查，无论结果都要弹窗）
            self.tool_update_controller.check_for_updates_from_settings()
        elif setting_name.startswith("tool_update_"):
            # 工具更新相关设置变更，通知更新控制器
            if hasattr(self, 'tool_update_controller'):
                current_settings = self.tool_update_controller.get_update_settings()
                # 更新相应的设置项
                setting_key = setting_name.replace("tool_update_", "")
                current_settings[setting_key] = value
                self.tool_update_controller.update_settings(current_settings)
        
        print(f"设置已更新: {setting_name} = {value}")
    
    def _select_tool_card(self, tool_name: str):
        """选中指定的工具卡片"""
        card = self.tools_grid.get_card_by_name(tool_name)
        if card:
            card.set_selected(True)
    
    def _on_card_selected(self, tool_name: str):
        """处理卡片选中事件（现在改为显示详情页面）"""
        import logging
        logger = logging.getLogger(__name__)

        # 🔥 关键修复：如果当前已经显示该工具的详情页，不要重建！
        if (self.current_detail_page and
            self.main_content_stack.currentWidget() is self.current_detail_page and
            hasattr(self.current_detail_page, 'tool_data') and
            self.current_detail_page.tool_data.get('name') == tool_name):
            logger.info(f"✅ [_on_card_selected] 已在显示 {tool_name} 详情页，跳过重建")
            # 只刷新数据（重新加载total_runtime）
            self.config_manager.load_tools()
            for tool in self.config_manager.tools:
                if tool.get('name') == tool_name:
                    self.current_detail_page.tool_data['total_runtime'] = tool.get('total_runtime', 0)
                    if hasattr(self.current_detail_page, 'update_usage_time'):
                        self.current_detail_page.update_usage_time(tool.get('total_runtime', 0))
                    logger.info(f"✅ [_on_card_selected] 已刷新 {tool_name} 数据")
                    break
            return

        # 获取工具数据
        tool_data = self.tool_manager.get_tool_info(tool_name)
        if tool_data:
            self.show_tool_detail_page(tool_data)
    
    def _on_install_tool(self, tool_name: str):
        """处理工具安装请求（从工具卡片触发）"""
        import logging
        logger = logging.getLogger(__name__)
        
        msg = f"【下载状态链路-1】工具卡片安装请求: {tool_name}"
        print(msg)
        logger.info(msg)
        
        # 🎯 记录调用源
        import traceback
        call_stack = traceback.extract_stack()
        if len(call_stack) > 2:
            caller = call_stack[-3]
            print(f"【下载状态链路-1.1】调用源: {caller.filename}:{caller.lineno} in {caller.name}")
            logger.info(f"【下载状态链路-1.1】调用源: {caller.filename}:{caller.lineno} in {caller.name}")
        
        if self.monitor:
            self.monitor.log_user_operation("请求安装工具", {"工具名": tool_name})
        
        # 🎯 检查下载卡片是否存在
        if self.modern_download_card:
            print(f"【下载状态链路-2】✅ 下载卡片已存在，准备接收状态更新")
            logger.info(f"【下载状态链路-2】✅ 下载卡片已存在，准备接收状态更新")
        else:
            print(f"【下载状态链路-2】❌ 警告：下载卡片不存在！状态可能丢失")
            logger.warning(f"【下载状态链路-2】❌ 警告：下载卡片不存在！状态可能丢失")
        
        # 规范化工具名（大小写不敏感匹配到注册名称）
        try:
            canonical = tool_name
            try:
                all_td = self.tool_manager.get_all_tools_data()
                for it in all_td:
                    if it.get('name','').lower() == tool_name.lower():
                        canonical = it.get('name', tool_name)
                        break
            except Exception:
                pass
            tool_name = canonical
        except Exception:
            pass

        msg = f"【下载状态链路-3】开始调用 tool_manager.install_tool: {tool_name}"
        print(msg)
        logger.info(msg)
        success = self.tool_manager.install_tool(tool_name)
        
        msg = f"【下载状态链路-4】tool_manager.install_tool 返回结果: {success}"
        print(msg)
        logger.info(msg)
        
        if not success:
            msg = f"【下载状态链路-5】❌ 安装失败，显示警告对话框: {tool_name}"
            print(msg)
            logger.error(msg)
            QMessageBox.warning(self, self.tr("安装失败"), self.tr("无法启动 {0} 的安装过程").format(tool_name))
        else:
            msg = f"【下载状态链路-6】✅ 安装请求成功提交，等待 installation_progress 信号: {tool_name}"
            print(msg)
            logger.info(msg)
            
            # 如果当前在详情页面且是正在安装的工具，设置初始安装状态
            if (self.current_detail_page and 
                hasattr(self.current_detail_page, 'tool_data') and 
                self.current_detail_page.tool_data['name'] == tool_name):
                print(f"[安装开始-详情页面] 设置详情页面初始安装状态: {tool_name}")
                logger.info(f"[安装开始-详情页面] 设置详情页面初始安装状态: {tool_name}")
                if hasattr(self.current_detail_page, 'set_installing_state'):
                    self.current_detail_page.set_installing_state(True, 0, self.tr("准备安装..."))
    
    def _on_launch_tool(self, tool_name: str):
        """处理工具启动请求"""
        if self.monitor:
            self.monitor.log_user_operation("请求启动工具", {"工具名": tool_name})
        # 规范化工具名
        try:
            canonical = tool_name
            try:
                all_td = self.tool_manager.get_all_tools_data()
                for it in all_td:
                    if it.get('name','').lower() == tool_name.lower():
                        canonical = it.get('name', tool_name)
                        break
            except Exception:
                pass
            tool_name = canonical
        except Exception:
            pass

        success = self.tool_manager.launch_tool(tool_name)
        if not success:
            QMessageBox.warning(self, self.tr("启动失败"), self.tr("无法启动 {0}").format(tool_name))
    
    def _on_uninstall_tool(self, tool_name: str):
        """处理工具卸载请求（从详情页面或工具卡片触发）"""
        import logging
        logger = logging.getLogger(__name__)
        
        print(f"【下载状态链路-U1】工具卸载请求: {tool_name}")
        logger.info(f"【下载状态链路-U1】工具卸载请求: {tool_name}")
        
        # 🎯 记录调用源
        import traceback
        call_stack = traceback.extract_stack()
        if len(call_stack) > 2:
            caller = call_stack[-3]
            print(f"【下载状态链路-U1.1】调用源: {caller.filename}:{caller.lineno} in {caller.name}")
            logger.info(f"【下载状态链路-U1.1】调用源: {caller.filename}:{caller.lineno} in {caller.name}")
        
        if self.monitor:
            self.monitor.log_user_operation("请求卸载工具", {"工具名": tool_name})
        
        # 规范化工具名
        try:
            canonical = tool_name
            try:
                all_td = self.tool_manager.get_all_tools_data()
                for it in all_td:
                    if it.get('name','').lower() == tool_name.lower():
                        canonical = it.get('name', tool_name)
                        break
            except Exception:
                pass
            tool_name = canonical
        except Exception:
            pass

        # 🎯 检查下载卡片是否存在
        if self.modern_download_card:
            print(f"【下载状态链路-U2】✅ 下载卡片已存在，准备接收卸载状态更新")
            logger.info(f"【下载状态链路-U2】✅ 下载卡片已存在，准备接收卸载状态更新")
        else:
            print(f"【下载状态链路-U2】❌ 警告：下载卡片不存在！卸载状态可能丢失")
            logger.warning(f"【下载状态链路-U2】❌ 警告：下载卡片不存在！卸载状态可能丢失")
        
        # 显示确认对话框
        print(f"【下载状态链路-U3】显示卸载确认对话框: {tool_name}")
        logger.info(f"【下载状态链路-U3】显示卸载确认对话框: {tool_name}")
        reply = QMessageBox.question(
            self,
            self.tr("确认卸载"),
            self.tr("您确定要卸载 {0} 吗？\n\n卸载后将删除工具文件和相关配置，此操作不可撤销。").format(tool_name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            print(f"【下载状态链路-U4】✅ 用户确认卸载，开始执行: {tool_name}")
            logger.info(f"【下载状态链路-U4】✅ 用户确认卸载，开始执行: {tool_name}")
            # 显示卸载进度（在卡片上显示）
            card = self.tools_grid.get_card_by_name(tool_name)
            if card:
                print(f"【下载状态链路-U5】✅ 找到工具卡片，设置卸载进度: {tool_name}")
                logger.info(f"【下载状态链路-U5】✅ 找到工具卡片，设置卸载进度: {tool_name}")
                card.set_installing_state(True, 0, self.tr("准备卸载..."))
            else:
                print(f"【下载状态链路-U5】❌ 警告：未找到工具卡片: {tool_name}")
                logger.warning(f"【下载状态链路-U5】❌ 警告：未找到工具卡片: {tool_name}")
            
            # 如果当前在详情页面且是正在卸载的工具，设置初始卸载状态
            if (self.current_detail_page and 
                hasattr(self.current_detail_page, 'tool_data') and 
                self.current_detail_page.tool_data['name'] == tool_name):
                print(f"【下载状态链路-U6】设置详情页面初始卸载状态: {tool_name}")
                logger.info(f"【下载状态链路-U6】设置详情页面初始卸载状态: {tool_name}")
                if hasattr(self.current_detail_page, 'set_installing_state'):
                    self.current_detail_page.set_installing_state(True, 0, self.tr("准备卸载..."))
            
            # 执行卸载
            print(f"[日志-U5] 开始调用 tool_manager.uninstall_tool: {tool_name}")
            success = self.tool_manager.uninstall_tool(tool_name)
            print(f"[日志-U6] tool_manager.uninstall_tool 返回结果: {success}")
            
            if success:
                print(f"[日志-U7] 卸载成功，显示成功对话框: {tool_name}")
                QMessageBox.information(self, self.tr("卸载成功"), self.tr("{0} 已成功卸载").format(tool_name))
                # 注释：移除自动跳转，让用户可以选择何时返回
                # if hasattr(self, 'current_detail_page') and self.current_detail_page:
                #     print(f"[日志-U8] 当前在详情页面，返回主界面: {tool_name}")
                #     self.go_back_to_main()
                print(f"[日志-U9] 卸载处理完成，等待 tool_uninstalled 信号: {tool_name}")
            else:
                print(f"[日志-U10] 卸载失败，清除进度并显示警告: {tool_name}")
                # 清除卸载进度显示
                if card:
                    card.set_installing_state(False, 0, "")
                
                # 如果当前在详情页面且是卸载失败的工具，清除详情页面卸载状态
                if (self.current_detail_page and 
                    hasattr(self.current_detail_page, 'tool_data') and 
                    self.current_detail_page.tool_data['name'] == tool_name):
                    print(f"[卸载失败-详情页面] 清除详情页面卸载状态: {tool_name}")
                    if hasattr(self.current_detail_page, 'set_installing_state'):
                        self.current_detail_page.set_installing_state(False)
                
                QMessageBox.warning(self, self.tr("卸载失败"), self.tr("无法卸载 {0}，请检查工具是否正在使用中").format(tool_name))
        else:
            print(f"[日志-U11] 用户取消了卸载操作: {tool_name}")
    
    def _on_tool_info(self, tool_name: str):
        """显示工具详情信息"""
        if self.monitor:
            self.monitor.log_user_operation("查看工具详情", {"工具名": tool_name})
        
        tool_data = self.tool_manager.get_tool_info(tool_name)
        if tool_data:
            # 构建详情信息
            details_text = self.tr("工具名称: {0}\n").format(tool_data['name'])
            details_text += self.tr("版本: {0}\n").format(tool_data['version'])
            try:
                from utils.tool_localization import get_localized_tool_description
                desc_text = get_localized_tool_description(tool_data)
            except Exception:
                desc_text = tool_data.get('description', '')
            details_text += self.tr("Description: {0}\n").format(desc_text)
            details_text += self.tr("安装来源: {0}\n").format(tool_data['install_source'])

            if tool_data.get('executable_path'):
                details_text += self.tr("可执行文件: {0}\n").format(tool_data['executable_path'])

            if tool_data.get('disk_usage'):
                details_text += self.tr("磁盘占用: {0}\n").format(tool_data['disk_usage'])

            if tool_data.get('total_runtime', 0) > 0:
                runtime = tool_data['total_runtime']
                hours = runtime // 3600
                minutes = (runtime % 3600) // 60
                details_text += self.tr("使用时长: {0}小时{1}分钟\n").format(hours, minutes)

            QMessageBox.information(self, self.tr("{0} 详情").format(tool_name), details_text)
    
    def _on_tool_favorite_toggled(self, tool_name: str, is_favorite: bool):
        """
        处理工具收藏状态切换
        """
        print(f"[收藏信号-1] *** _on_tool_favorite_toggled 被触发 ***: {tool_name}, is_favorite={is_favorite}")
        
        # 记录到监控系统
        if self.monitor:
            self.monitor.log_user_operation("收藏工具", {
                "工具名": tool_name,
                "收藏状态": "收藏" if is_favorite else "取消收藏"
            })
            print(f"[收藏信号-2] 已记录到监控系统")
        
        # 使用ConfigManager的方法更新收藏状态（自动保存）
        print(f"[收藏操作] 切换前 - {tool_name}: {'收藏' if is_favorite else '非收藏'}")
        actual_state = self.config_manager.toggle_favorite_tool(tool_name)
        print(f"[收藏操作] 切换后 - {tool_name}: {'收藏' if actual_state else '非收藏'}")
        
        # 更新工具卡片UI（无论状态是否一致都要更新，确保同步）
        print(f"[收藏操作-同步1] 开始更新工具卡片UI: {tool_name} -> {'收藏' if actual_state else '未收藏'}")
        if hasattr(self, 'tools_grid'):
            card = self.tools_grid.get_card_by_name(tool_name)
            if card:
                print(f"[收藏操作-同步2] 找到工具卡片 {type(card).__name__}: {tool_name}")
                
                # 检查卡片类型并调用相应方法
                if hasattr(card, 'set_favorite'):
                    card.set_favorite(actual_state)
                    print(f"[收藏操作-同步3] 调用 set_favorite 方法更新: {tool_name} -> {'收藏' if actual_state else '未收藏'}")
                elif hasattr(card, 'is_favorite'):
                    # 直接设置属性并重绘（适配其他卡片类型）
                    card.is_favorite = actual_state
                    card.update()
                    card.repaint()
                    print(f"[收藏操作-同步3] 直接设置 is_favorite 属性并重绘: {tool_name} -> {'收藏' if actual_state else '未收藏'}")
                else:
                    print(f"[收藏操作-同步3] 警告：卡片不支持收藏更新: {type(card).__name__}")
                    
                print(f"[收藏操作-同步4] 工具卡片UI更新完成: {tool_name}")
            else:
                print(f"[收藏操作-同步2] 警告：未找到工具卡片: {tool_name}")
        else:
            print(f"[收藏操作-同步1] 警告：tools_grid 不存在")
        
        # 如果当前在详情页面且是同一个工具，同步更新详情页面的收藏按钮
        if (self.current_detail_page and 
            hasattr(self.current_detail_page, 'tool_data') and 
            self.current_detail_page.tool_data['name'] == tool_name and
            hasattr(self.current_detail_page, 'set_favorite_state')):
            print(f"[收藏操作] 同步更新详情页面收藏按钮: {tool_name} -> {'收藏' if actual_state else '未收藏'}")
            self.current_detail_page.set_favorite_state(actual_state)
        
        print(f"【收藏结果】{tool_name} - {'已收藏' if actual_state else '取消收藏'}")
        
        # 如果当前处于“我的工具”页面，刷新显示
        if hasattr(self, 'current_view') and self.current_view == "my-tools":
            print(f"[收藏操作] 当前在我的工具页面，刷新显示")
            self._show_favorite_tools()
        else:
            print(f"[收藏操作] 当前视图: {getattr(self, 'current_view', 'unknown')}，不需刷新我的工具")
    
    def _show_favorite_tools(self):
        """显示收藏的工具"""
        import logging
        logging.info("开始显示收藏工具")
        
        # 获取所有工具数据
        all_tools = self.tool_manager.get_all_tools_data()
        logging.debug(f"获取到 {len(all_tools)} 个工具")
        
        # 添加收藏状态
        for tool in all_tools:
            tool['is_favorite'] = self.config_manager.is_tool_favorite(tool['name'])
            if tool['is_favorite']:
                logging.debug(f"收藏工具: {tool['name']}")
        
        # 过滤出收藏的工具
        favorite_tools = [tool for tool in all_tools if tool['is_favorite']]
        favorite_names = [tool['name'] for tool in favorite_tools]
        
        # 显示收藏工具
        self.tools_grid.set_cards(favorite_tools)
        
        logging.info(f"显示收藏工具: {len(favorite_tools)} 个 - {favorite_names}")
        print(f"[收藏页面] 显示收藏工具: {len(favorite_tools)} 个 - {favorite_names}")
    
    def closeEvent(self, event):
        """
        窗口关闭事件处理
        清理资源
        """
        # 记录窗口关闭到监控系统
        if self.monitor:
            self.monitor.log_user_operation("应用关闭", {"关闭方式": "窗口关闭按钮"})
        
        
        # 清理现代化下载卡片
        if self.modern_download_card:
            self.modern_download_card.hide()
            self.modern_download_card = None
        
        # 清理工具管理器资源
        self.tool_manager.cleanup()
        
        # 保存应用状态
        # 这里可以保存窗口大小、位置等状态信息
        
        event.accept()
    
    def show_tool_detail_page(self, tool_data: dict):
        """显示工具详情页面"""
        import logging
        logger = logging.getLogger(__name__)

        # 🔥 关键修复：每次显示详情页前，从文件重新加载tools.json，确保数据最新
        # 解决问题：内存缓存可能过期，导致显示旧数据
        self.config_manager.load_tools()
        logger.info(f"🔄 [show_tool_detail_page] 已从文件重新加载tools.json")

        # 确保工具数据包含收藏状态
        tool_data['is_favorite'] = self.config_manager.is_tool_favorite(tool_data['name'])

        # 从 config_manager.tools 加载最新的使用时间/启动次数（关键修复！）
        # usage_tracker 将数据保存到 config_manager.tools 中
        if self.config_manager and self.config_manager.tools:
            for tool in self.config_manager.tools:
                if tool.get('name') == tool_data['name']:
                    total_runtime = tool.get('total_runtime', 0)
                    tool_data['total_runtime'] = total_runtime
                    # Web 工具的启动次数
                    if 'launch_count' in tool:
                        tool_data['launch_count'] = tool.get('launch_count', 0)
                        logger.info(f"🌐 [show_tool_detail_page] 从config加载启动次数: {tool_data['launch_count']} 次")
                    logger.info(f"📊 [show_tool_detail_page] 从config加载使用时间: {total_runtime}秒")
                    break

        # 确保有默认值
        if 'total_runtime' not in tool_data:
            tool_data['total_runtime'] = 0
            logger.info(f"📊 [show_tool_detail_page] 使用默认时间: 0秒")

        # 🔥 关键修复：如果当前已经显示该工具的详情页，不要重建！
        if (self.current_detail_page and
            hasattr(self.current_detail_page, 'tool_data') and
            self.current_detail_page.tool_data.get('name') == tool_data['name']):
            logger.info(f"⚠️ [show_tool_detail_page] 已在显示 {tool_data['name']} 详情页，跳过重建，只刷新数据")
            # 更新数据到当前页面
            self.current_detail_page.tool_data['total_runtime'] = tool_data.get('total_runtime', 0)
            self.current_detail_page.tool_data['launch_count'] = tool_data.get('launch_count', 0)
            # 刷新显示：根据工具类型传入合适的值
            if hasattr(self.current_detail_page, 'update_usage_time'):
                is_web = (tool_data.get('tool_type') == 'web_launcher') or (tool_data.get('install_source') == 'web') \
                         or (str(tool_data.get('version','')).lower() == 'online')
                value = tool_data.get('launch_count', 0) if is_web else tool_data.get('total_runtime', 0)
                self.current_detail_page.update_usage_time(value)
            return  # 直接返回，不重建

        print(f"[详情页面] 创建详情页面: {tool_data['name']}, 收藏状态: {'收藏' if tool_data['is_favorite'] else '未收藏'}")
        logger.info(f"📄 [show_tool_detail_page] 准备创建详情页: {tool_data['name']}, total_runtime: {tool_data.get('total_runtime', 0)}")

        # 创建详情页面
        detail_page = ToolDetailPage(tool_data, self)
        detail_page_id = id(detail_page)
        logger.info(f"🆔 [show_tool_detail_page] 新详情页已创建，实例ID: {detail_page_id}")

        # 🔧 方案3：检查工具是否正在运行，保持运行状态
        if self.tool_manager and hasattr(self.tool_manager, 'usage_tracker'):
            # 检查工具是否有活跃的监控会话
            tool_name = tool_data['name']
            is_running = False
            if self.tool_manager.usage_tracker and hasattr(self.tool_manager.usage_tracker, 'active_sessions'):
                is_running = tool_name in self.tool_manager.usage_tracker.active_sessions

            if is_running:
                logger.info(f"🔧 [show_tool_detail_page] 检测到工具正在运行: {tool_name}，调用update_running_state")
                # 🔥 关键修复：使用统一的update_running_state方法，避免样式冲突
                detail_page.update_running_state(True)
                logger.info(f"✅ [show_tool_detail_page] 运行状态已设置为运行中")

        # 🔥 关键修复：删除旧的详情页，防止阴阳代码
        if self.current_detail_page:
            old_page_id = id(self.current_detail_page)
            logger.info(f"🗑️ [show_tool_detail_page] 删除旧详情页，实例ID: {old_page_id}")

            # 从StackedWidget中移除
            self.main_content_stack.removeWidget(self.current_detail_page)

            # 立即删除（不用deleteLater）
            try:
                import sip
                if not sip.isdeleted(self.current_detail_page):
                    sip.delete(self.current_detail_page)
                    logger.info(f"✅ [show_tool_detail_page] 旧详情页已同步删除")
            except Exception as e:
                self.current_detail_page.deleteLater()
                logger.info(f"⚠️ [show_tool_detail_page] 旧详情页使用异步删除: {e}")

            self.current_detail_page = None

            # 处理事件，确保删除完成
            QApplication.processEvents()
            logger.info(f"✅ [show_tool_detail_page] 旧详情页删除完成")

        # 连接返回信号（现在返回按钮在工具栏上，但保留这个以兼容）
        detail_page.back_requested.connect(self.go_back_to_main)
        detail_page.install_requested.connect(self._on_install_tool)
        detail_page.launch_requested.connect(self._on_launch_tool)
        detail_page.uninstall_requested.connect(self._on_uninstall_tool)
        detail_page.favorite_toggled.connect(self._on_tool_favorite_toggled)

        # 添加到堆栈并切换
        self.main_content_stack.addWidget(detail_page)
        self.main_content_stack.setCurrentWidget(detail_page)
        self.current_detail_page = detail_page
        logger.info(f"✅ [show_tool_detail_page] 新详情页已设置为当前widget，实例ID: {detail_page_id}")
        
        # 切换工具栏到详情页模式
        self.toolbar.switch_to_detail_mode()
        # 根据来源视图设置动态返回目标标签
        try:
            back_map = {
                'all-tools': self.tr('全部工具'),
                'my-tools': self.tr('我的工具'),
                'settings': self.tr('设置'),
                'workflows': (self._current_workflow_name or self.tr('工作流')),
            }
            label = back_map.get(getattr(self, '_last_non_detail_view', ''), '')
            self.toolbar.set_back_target(label)
            # 同步设置返回目标：确保从工作流进入详情时返回到工作流页面
            if getattr(self, '_last_non_detail_view', '') == 'workflows':
                self._back_target = 'workflows'
            else:
                self._back_target = 'main'
        except Exception:
            pass
        
        # 记录操作
        if self.monitor:
            self.monitor.log_user_operation("查看工具详情", {"工具名": tool_data.get('name', 'Unknown')})
    
    def go_back_to_main(self):
        """返回到主页面"""
        # 切换到工具网格页面
        self.main_content_stack.setCurrentWidget(self.tools_grid)
        
        # 移除当前详情页面
        if self.current_detail_page:
            self.main_content_stack.removeWidget(self.current_detail_page)
            self.current_detail_page.deleteLater()
            self.current_detail_page = None
        
        # 切换工具栏到列表模式
        self.toolbar.switch_to_list_mode()
        self.toolbar.set_default_buttons_visible(True)
        self.toolbar.clear_actions()
        
        # 记录操作
        if self.monitor:
            self.monitor.log_user_operation("返回主页面", {})
    
    # ====== 统一更新系统 v1.1.12 ======
    
    # 移除了 _on_update_clicked 方法 - 不再需要主界面更新按钮
    
    def _setup_tool_update_connections(self):
        """设置工具更新系统的信号连接"""
        # 连接工具更新控制器的信号
        self.tool_update_controller.update_status_changed.connect(self._on_tool_update_status_changed)
        self.tool_update_controller.history_updated.connect(self._on_tool_update_history_changed)
        
        # 连接设置面板的更新检查请求
        self.settings_panel.setting_changed.connect(self._on_setting_changed)
    
    def _should_check_updates_on_startup(self) -> bool:
        """检查是否应该在启动时检查更新"""
        settings = self.config_manager.settings
        if hasattr(settings, 'tool_update') and settings.tool_update:
            update_mode = settings.tool_update.get('update_mode', 'auto')
            return update_mode in ['auto', 'manual']  # 两种模式都需要检查，只是处理方式不同
        return True  # 默认检查
    
    def _startup_check_for_updates(self):
        """启动时检查工具更新（新版本）"""
        # 这是启动时的自动检查，不是手动触发
        self.tool_update_controller.check_for_updates(is_manual=False)
    
    # 移除了 _check_for_updates 方法 - 手动检查现在直接通过工具更新控制器处理
    
    def _on_tool_update_status_changed(self, tool_name: str, status: str):
        """处理工具更新状态变化"""
        # 在现代化下载卡片显示更新进度（旧面板已停用）
        if hasattr(self, 'modern_download_card') and self.modern_download_card:
            title = self.tr("{0} 更新").format(tool_name)
            if status == "更新中":
                self.modern_download_card.add_or_update_download(title, 0, self.tr("准备更新..."))
            elif status == "更新成功":
                self.modern_download_card.add_or_update_download(title, 100, self.tr("更新完成"))
                self._update_tools_display()
            elif status == "更新失败":
                self.modern_download_card.add_or_update_download(title, 0, self.tr("更新失败"))
        
        # 重置更新按钮状态（如果是手动触发）
        if hasattr(self, 'update_btn'):
            self._reset_update_button()
    
    def _on_tool_update_history_changed(self, history: list):
        """处理工具更新历史变化"""
        # 可以在这里更新UI显示更新历史
        pass
    
    def _reset_update_button(self):
        """重置更新按钮状态"""
        self.update_btn.setText("⬇")
        self.update_btn.setEnabled(True)
        self.update_btn.setToolTip(self.tr("检查更新"))
    
    # 注意：旧的统一更新对话框方法已被移除
    # 新的工具更新系统通过 tool_update_controller 处理所有更新逻辑
    # 包括更新对话框、进度显示和完成通知
    
    # ===========================================
    # 下载状态面板控制方法
    # ===========================================
    
    def _toggle_download_status_panel(self):
        """切换下载状态面板显示/隐藏 - 使用现代化悬浮卡片"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"【MAIN WINDOW DEBUG】=== _toggle_download_status_panel 函数被调用 ===")
        print(f"【MAIN WINDOW DEBUG】=== _toggle_download_status_panel 函数被调用 ===")
        
        # 如果筛选卡片打开，先关闭它（相互排斥）
        if self.modern_filter_card and self.modern_filter_card.isVisible():
            print(f"【MAIN WINDOW DEBUG】关闭现代化筛选卡片")
            logger.info(f"【MAIN WINDOW DEBUG】关闭现代化筛选卡片")
            self._close_modern_filter_card()
        # 旧系统已移除，无需检查 filter_panel
        
        # 切换现代化下载卡片
        print(f"【MAIN WINDOW DEBUG】检查现代化下载卡片状态: card={self.modern_download_card}")
        logger.info(f"【MAIN WINDOW DEBUG】检查现代化下载卡片状态: card={self.modern_download_card}")
        
        if self.modern_download_card and self.modern_download_card.isVisible():
            print(f"【MAIN WINDOW DEBUG】现代化下载卡片当前可见，准备关闭")
            logger.info(f"【MAIN WINDOW DEBUG】现代化下载卡片当前可见，准备关闭")
            self._close_modern_download_card()
        else:
            print(f"【MAIN WINDOW DEBUG】现代化下载卡片当前隐藏，准备打开")
            logger.info(f"【MAIN WINDOW DEBUG】现代化下载卡片当前隐藏，准备打开")
            try:
                self._show_modern_download_card()
                print(f"【MAIN WINDOW DEBUG】_show_modern_download_card 调用完成")
                logger.info(f"【MAIN WINDOW DEBUG】_show_modern_download_card 调用完成")
            except Exception as e:
                print(f"【MAIN WINDOW DEBUG】_show_modern_download_card 发生异常: {e}")
                logger.error(f"【MAIN WINDOW DEBUG】_show_modern_download_card 发生异常: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"【MAIN WINDOW DEBUG】=== _toggle_download_status_panel 函数执行完成 ===")
        logger.info(f"【MAIN WINDOW DEBUG】=== _toggle_download_status_panel 函数执行完成 ===")
    
    # 旧版下载状态面板方法已移除，统一使用现代化下载卡片
    
    def _show_modern_download_card(self):
        """显示现代化下载状态卡片"""
        import logging
        logger = logging.getLogger(__name__)
        print(f"【MAIN WINDOW DEBUG】=== _show_modern_download_card 函数开始执行 ===")
        logger.info(f"【MAIN WINDOW DEBUG】=== _show_modern_download_card 函数开始执行 ===")
        
        # 🎯 下载卡片已在初始化时预创建，无需重复创建
        if not self.modern_download_card:
            print("【MAIN WINDOW ERROR】下载卡片未正确初始化！")
            logger.error("【MAIN WINDOW ERROR】下载卡片未正确初始化！")
            return
        
        # 显示遮罩层
        print("【MAIN WINDOW DEBUG】显示遮罩层")
        logger.info("【MAIN WINDOW DEBUG】显示遮罩层")
        self.overlay.show_animated()
        
        # 获取精确的位置信息
        toolbar_rect = self.toolbar.geometry()
        download_button_rect = self.toolbar.download_rect
        
        print(f"【MAIN WINDOW DEBUG】工具栏矩形: {toolbar_rect}")
        print(f"【MAIN WINDOW DEBUG】下载按钮矩形: {download_button_rect}")
        logger.info(f"【MAIN WINDOW DEBUG】工具栏矩形: {toolbar_rect}")
        logger.info(f"【MAIN WINDOW DEBUG】下载按钮矩形: {download_button_rect}")
        
        # 显示卡片 - 传递完整的几何信息
        print("【MAIN WINDOW DEBUG】开始显示现代化下载卡片")
        logger.info("【MAIN WINDOW DEBUG】开始显示现代化下载卡片")
        self.modern_download_card.show_aligned_to_toolbar(
            toolbar_bottom=toolbar_rect.bottom(),
            button_rect=download_button_rect,
            window_rect=self.rect()
        )
        
        # 确保卡片在遮罩层之上
        print("【MAIN WINDOW DEBUG】将卡片提升到最前面")
        logger.info("【MAIN WINDOW DEBUG】将卡片提升到最前面")
        self.modern_download_card.raise_()
        
        # 更新工具栏状态 - 设置下载按钮为激活状态
        if hasattr(self, 'toolbar'):
            self.toolbar.set_download_active(True)
        
        # 同步旧版面板的数据到新卡片
        self._sync_download_data_to_modern_card()
    
    def _close_modern_download_card(self):
        """关闭现代化下载状态卡片"""
        if self.modern_download_card:
            self.modern_download_card.hide()
        
        # 隐藏遮罩层
        self.overlay.hide_animated()
        
        # 更新工具栏状态
        if hasattr(self, 'toolbar'):
            self.toolbar.set_download_active(False)
    
    def _sync_download_data_to_modern_card(self):
        """同步下载数据到现代化卡片"""
        if not self.modern_download_card:
            return
        
        # 从旧版下载状态面板获取数据并同步到新卡片
        # 这里需要根据旧版面板的数据结构进行适配
        if hasattr(self.download_status_panel, 'download_items'):
            for tool_name, old_item in self.download_status_panel.download_items.items():
                if hasattr(old_item, 'progress_bar') and hasattr(old_item, 'status_label'):
                    progress = old_item.progress_bar.value()
                    status = old_item.status_label.text()
                    self.modern_download_card.add_or_update_download(tool_name, progress, status)
        
        # 现代化工具栏不需要手动更新样式
    
    def _update_download_button_state(self):
        """更新下载按钮的状态显示"""
        # 只从现代化下载卡片获取计数（旧系统已移除）
        if self.modern_download_card:
            active_count, total_count = self.modern_download_card.get_download_count()
        else:
            # 默认值：没有下载任务
            active_count, total_count = 0, 0
        
        # 更新现代化工具栏的下载计数
        if hasattr(self, 'toolbar'):
            self.toolbar.set_download_count(active_count)
    
    def _set_window_icon(self):
        """设置应用窗口图标"""
        import os
        
        # 构建图标路径
        icon_path = os.path.join("resources", "icons", "app", "bionexus_icon.jpeg")
        
        # 检查图标文件是否存在
        if os.path.exists(icon_path):
            try:
                # 创建并设置图标
                app_icon = QIcon(icon_path)
                self.setWindowIcon(app_icon)
                
                # 同时设置应用程序图标（任务栏等）
                if QApplication.instance():
                    QApplication.instance().setWindowIcon(app_icon)
                
                print(f"【ICON】应用图标设置成功: {icon_path}")
            except Exception as e:
                print(f"【ICON ERROR】设置图标失败: {e}")
        else:
            print(f"【ICON WARNING】图标文件未找到: {icon_path}")
            # 尝试备用路径（兼容性）
            fallback_path = "icon.jpeg"
            if os.path.exists(fallback_path):
                try:
                    app_icon = QIcon(fallback_path)
                    self.setWindowIcon(app_icon)
                    print(f"【ICON】使用备用图标: {fallback_path}")
                except Exception as e:
                    print(f"【ICON ERROR】备用图标也失败: {e}")

    def check_all_tools_status(self):
        """
        检查所有已安装工具的状态
        在启动时调用（如果设置启用）
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info("开始检查所有已安装工具状态...")

        # 获取所有已安装的工具
        installed_tools = self.config_manager.get_tools_by_status('installed')

        if not installed_tools:
            logger.info("没有已安装的工具需要检查")
            return

        logger.info(f"找到 {len(installed_tools)} 个已安装工具，开始验证...")

        # 记录检查结果
        check_results = {
            'valid': [],      # 状态正常的工具
            'invalid': [],    # 状态异常的工具
            'errors': []      # 检查出错的工具
        }

        for tool_data in installed_tools:
            tool_name = tool_data.get('name')

            try:
                # 获取工具实例
                tool_instance = self.tool_manager.get_tool(tool_name)

                if not tool_instance:
                    logger.warning(f"无法获取工具实例: {tool_name}")
                    check_results['errors'].append(tool_name)
                    continue

                # 验证安装状态
                is_valid = tool_instance.verify_installation()

                if is_valid:
                    logger.info(f"✓ {tool_name} - 状态正常")
                    check_results['valid'].append(tool_name)
                else:
                    logger.warning(f"✗ {tool_name} - 状态异常（安装文件可能已损坏或移动）")
                    check_results['invalid'].append(tool_name)

                    # 更新工具状态为 available
                    self.config_manager.update_tool_status(tool_name, 'available')

                    # 刷新UI中的工具卡片
                    if tool_name in self.tool_cards:
                        card = self.tool_cards[tool_name]
                        card.set_available_state()

            except Exception as e:
                logger.error(f"检查 {tool_name} 状态时出错: {e}")
                check_results['errors'].append(tool_name)

        # 记录检查摘要
        logger.info("=" * 50)
        logger.info(f"工具状态检查完成:")
        logger.info(f"  - 正常: {len(check_results['valid'])} 个")
        logger.info(f"  - 异常: {len(check_results['invalid'])} 个")
        logger.info(f"  - 错误: {len(check_results['errors'])} 个")

        if check_results['invalid']:
            logger.warning(f"发现异常工具: {', '.join(check_results['invalid'])}")

        logger.info("=" * 50)

        # 如果有异常工具，显示通知（可选）
        if check_results['invalid']:
            invalid_count = len(check_results['invalid'])
            logger.info(f"检测到 {invalid_count} 个工具状态异常，已自动更新状态")

    def _check_and_handle_path_migration(self):
        """
        检测并处理路径迁移
        当软件位置变更且用户有手动设置的绝对路径时，提示用户选择处理方式
        """
        import logging
        from pathlib import Path
        from PyQt5.QtCore import QTimer

        logger = logging.getLogger(__name__)

        # 需要检查的路径设置
        path_settings = ['default_install_dir', 'conda_env_path']

        for setting_name in path_settings:
            saved_path = getattr(self.config_manager.settings, setting_name, "")

            # 空路径跳过（使用默认值）
            if not saved_path:
                continue

            saved_path_obj = Path(saved_path)

            # 相对路径跳过（已经是理想状态）
            if not saved_path_obj.is_absolute():
                continue

            # 是绝对路径，检查是否指向旧版本
            current_dir = Path.cwd()
            current_dir_str = str(current_dir).replace('\\', '/')

            # 检查路径是否不在当前软件目录下
            try:
                saved_path_obj.relative_to(current_dir)
                # 能计算相对路径，说明在当前目录下，继续检查
            except ValueError:
                # 不在当前目录下，这是真正的外部路径，不处理
                logger.info(f"{setting_name} 指向外部路径，保持不变: {saved_path}")
                continue

            # 在当前目录下，但使用了绝对路径（可能是旧版本遗留）
            # 检查路径中是否包含旧版本号
            if 'BioNexus_' in saved_path and current_dir_str not in saved_path:
                # 发现路径迁移情况
                logger.info(f"检测到路径迁移: {setting_name} = {saved_path}")

                # 计算新的默认路径
                from utils.path_resolver import get_path_resolver
                path_resolver = get_path_resolver()

                if setting_name == 'default_install_dir':
                    new_path = str(path_resolver.get_install_dir())
                elif setting_name == 'conda_env_path':
                    new_path = str(path_resolver.get_env_cache_dir())
                else:
                    continue

                # 延迟显示对话框，确保主窗口已完全显示
                def show_migration_dialog():
                    from ui.path_migration_dialog import PathMigrationDialog

                    dialog = PathMigrationDialog(saved_path, new_path, setting_name, self)
                    if dialog.exec_() == PathMigrationDialog.Accepted:
                        choice = dialog.get_user_choice()

                        if choice == 'migrate':
                            # 用户选择迁移到新路径
                            logger.info(f"用户选择迁移路径: {setting_name} -> {new_path}")

                            # 转换为相对路径保存
                            try:
                                relative_path = Path(new_path).relative_to(current_dir)
                                path_to_save = str(relative_path)
                            except ValueError:
                                path_to_save = new_path

                            setattr(self.config_manager.settings, setting_name, path_to_save)
                            self.config_manager.save_settings()

                            logger.info(f"路径已更新并保存: {path_to_save}")
                        else:
                            # 用户选择保留原路径
                            logger.info(f"用户选择保留原路径: {setting_name} = {saved_path}")

                # 延迟500ms显示对话框
                QTimer.singleShot(500, show_migration_dialog)

    def retranslateUi(self, locale: str = None):
        """
        Retranslate UI text - Real-time language switching
        Recreates key UI components to apply new translations
        """
        logger.info("=" * 60)
        logger.info("retranslateUi CALLED")
        logger.info(f"Locale parameter: {locale}")

        if not getattr(self, '_ui_fully_initialized', False):
            logger.warning("SKIPPED: retranslateUi called before UI fully initialized")
            return

        logger.info("UI is fully initialized, proceeding with retranslation...")

        try:
            from utils.translator import tr

            # 1. Update window title
            self.setWindowTitle(tr("BioNexus Launcher"))
            logger.debug("Window title updated")

            # 2. Update sidebar (call its retranslateUi, don't recreate)
            if hasattr(self, 'sidebar') and self.sidebar:
                if hasattr(self.sidebar, 'retranslateUi'):
                    self.sidebar.retranslateUi()
                    logger.debug("Sidebar retranslated")

            # 3. Update toolbar
            if hasattr(self, 'toolbar') and self.toolbar:
                if hasattr(self.toolbar, 'retranslateUi'):
                    self.toolbar.retranslateUi()
                    logger.debug("Toolbar retranslated")

            # 4. Update tool cards (they auto-connect to languageChanged signal)
            # Tool cards will update themselves automatically, but refresh display to ensure
            self._update_tools_display()
            logger.debug("Tool cards display refreshed")

            # 5. Force UI update
            self.update()
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()

            logger.info("SUCCESS: UI retranslation completed")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"EXCEPTION in retranslateUi: {e}")
            import traceback
            logger.error(traceback.format_exc())
