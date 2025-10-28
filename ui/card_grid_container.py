"""
自定义卡片网格容器 v1.1.3
使用绝对定位确保不出现半卡片，智能计算网格布局
支持纯垂直滚动，自动分配左右边距
"""
from PyQt5.QtWidgets import QWidget, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor
from ui.tool_card_v3 import ToolCardV3 as ToolCardV2  # 使用V3但保持兼容性
from utils.fuzzy_search import fuzzy_search_tools


class CardGridContainer(QWidget):
    """
    卡片网格容器
    使用绝对定位放置卡片，确保严格的网格布局
    """
    
    # 信号定义
    card_selected = pyqtSignal(str)
    card_install_clicked = pyqtSignal(str)
    card_launch_clicked = pyqtSignal(str)
    card_info_clicked = pyqtSignal(str)
    card_favorite_toggled = pyqtSignal(str, bool)  # 新增：收藏信号
    
    # 布局常量
    CARD_WIDTH = 170      # 卡片宽度 (新版)
    CARD_HEIGHT = 113     # 卡片高度 (新版)
    MIN_MARGIN = 20       # 最小边距
    CARD_SPACING = 10     # 卡片间距
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.cards = []  # 存储所有卡片对象
        self.selected_card = None  # 当前选中的卡片
        
        # 容器初始尺寸（会根据内容动态调整）
        self.setMinimumSize(400, 200)
        
        # 设置容器属性，避免默认绘制
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)  # 防止系统默认背景
    
    def add_card(self, tool_data: dict):
        """添加新卡片"""
        card = ToolCardV2(tool_data, self)
        
        # 连接卡片信号
        card.clicked.connect(self._on_card_clicked)
        card.install_clicked.connect(self.card_install_clicked.emit)
        card.launch_clicked.connect(self.card_launch_clicked.emit)
        # 连接新的收藏信号
        if hasattr(card, 'favorite_toggled'):
            card.favorite_toggled.connect(self.card_favorite_toggled.emit)
        
        self.cards.append(card)
        self._relayout_cards()
        card.show()
    
    def remove_card(self, tool_name: str):
        """移除指定卡片"""
        for card in self.cards[:]:  # 复制列表进行遍历
            if card.get_tool_name() == tool_name:
                card.deleteLater()
                self.cards.remove(card)
                break
        
        self._relayout_cards()
    
    def clear_cards(self):
        """清空所有卡片"""
        for card in self.cards:
            card.deleteLater()
        self.cards.clear()
        self._relayout_cards()
    
    def set_cards(self, tools_data: list):
        """设置卡片列表"""
        self.clear_cards()
        for tool_data in tools_data:
            self.add_card(tool_data)
    
    def _calculate_grid_layout(self, container_width: int) -> tuple:
        """
        计算网格布局参数
        返回: (columns, rows, left_margin, top_margin)
        """
        if not self.cards:
            return 0, 0, self.MIN_MARGIN, self.MIN_MARGIN
        
        # 计算最多能显示多少列（不出现半卡片）
        available_width = container_width
        cols_per_row = 1
        
        while True:
            next_cols = cols_per_row + 1
            required_width = (
                self.MIN_MARGIN * 2 + 
                next_cols * self.CARD_WIDTH + 
                (next_cols - 1) * self.CARD_SPACING
            )
            
            if required_width <= available_width:
                cols_per_row = next_cols
            else:
                break
        
        # 计算行数
        total_cards = len(self.cards)
        rows = (total_cards + cols_per_row - 1) // cols_per_row  # 向上取整
        
        # 计算实际使用的宽度
        used_width = (
            cols_per_row * self.CARD_WIDTH + 
            (cols_per_row - 1) * self.CARD_SPACING
        )
        
        # 剩余空间分配给左右边距
        remaining_width = available_width - used_width
        left_right_margin = max(self.MIN_MARGIN, remaining_width // 2)
        
        return cols_per_row, rows, left_right_margin, self.MIN_MARGIN
    
    def _relayout_cards(self):
        """重新布局所有卡片"""
        if not self.cards:
            # 没有卡片时，设置最小尺寸
            self.setFixedSize(400, 200)
            return
        
        # 获取父容器宽度
        parent_widget = self.parent()
        if parent_widget:
            container_width = parent_widget.width() - 40  # 减去滚动条等占用空间
        else:
            container_width = 800  # 默认宽度
        
        # 计算网格参数
        cols, rows, left_margin, top_margin = self._calculate_grid_layout(container_width)
        
        # 设置容器尺寸
        container_height = (
            top_margin * 2 + 
            rows * self.CARD_HEIGHT + 
            (rows - 1) * self.CARD_SPACING
        )
        self.setFixedSize(container_width, max(container_height, 200))
        
        # 绝对定位放置每个卡片
        for i, card in enumerate(self.cards):
            row = i // cols
            col = i % cols
            
            x = left_margin + col * (self.CARD_WIDTH + self.CARD_SPACING)
            y = top_margin + row * (self.CARD_HEIGHT + self.CARD_SPACING)
            
            card.move(x, y)
    
    def _on_card_clicked(self, tool_data: dict):
        """处理卡片点击事件，切换到详情页面"""
        # 向上传递信号，由主窗口处理页面切换
        self.card_selected.emit(tool_data['name'])
    
    def resizeEvent(self, event):
        """窗口尺寸变化时重新布局"""
        super().resizeEvent(event)
        self._relayout_cards()
    
    def filter_cards(self, search_term: str = "", categories: list = None, statuses: list = None):
        """
        智能筛选显示卡片
        使用模糊搜索算法，支持按匹配度排序
        """
        # 收集所有工具数据
        all_tools_data = [card.tool_data for card in self.cards]
        
        # 1. 应用搜索筛选（仅匹配工具名，使用模糊匹配）
        if search_term:
            matched_tools = fuzzy_search_tools(search_term, all_tools_data)
            # 将匹配结果转换为工具名集合，便于后续筛选
            matched_names = {tool['name'] for tool in matched_tools}
            # 保持匹配分数信息，用于排序
            match_scores = {tool['name']: tool['match_score'] for tool in matched_tools}
        else:
            matched_names = {tool['name'] for tool in all_tools_data}
            match_scores = {tool['name']: 1.0 for tool in all_tools_data}  # 无搜索时所有工具分数相同
        
        # 2. 应用分类和状态筛选
        visible_cards = []
        for card in self.cards:
            tool_data = card.tool_data
            tool_name = tool_data['name']
            
            # 检查是否通过搜索筛选
            if tool_name not in matched_names:
                card.hide()
                continue
            
            matches = True
            
            # 分类匹配
            if categories and tool_data.get('category') not in categories:
                matches = False
            
            # 状态匹配
            if matches and statuses and tool_data.get('status') not in statuses:
                matches = False
            
            if matches:
                card.show()
                # 为卡片添加匹配分数（用于调试或未来UI增强）
                card.match_score = match_scores.get(tool_name, 0.0)
                visible_cards.append(card)
            else:
                card.hide()
        
        # 3. 按匹配分数排序（降序），分数相同按名称排序（升序）
        if search_term and visible_cards:
            visible_cards.sort(key=lambda c: (-c.match_score, c.tool_data['name'].lower()))
        elif not search_term:
            # 无搜索时按名称字母顺序排序
            visible_cards.sort(key=lambda c: c.tool_data['name'].lower())
        
        # 4. 重新布局可见卡片
        original_cards = self.cards
        self.cards = visible_cards
        self._relayout_cards()
        self.cards = original_cards
        
        # 5. 调试信息（可选）
        if search_term:
            print(f"[搜索结果] 查询'{search_term}': {len(visible_cards)} 个匹配")
            for card in visible_cards[:3]:  # 显示前3个结果
                print(f"  {card.tool_data['name']}: {card.match_score:.4f}")
    
    def get_card_by_name(self, tool_name: str) -> ToolCardV2:
        """根据工具名称获取卡片对象"""
        if tool_name is None:
            return None
        target = tool_name.lower()
        for card in self.cards:
            try:
                if str(card.tool_data.get('name', '')).lower() == target:
                    return card
            except Exception:
                continue
        return None
    
    def paintEvent(self, event):
        """自定义绘制背景 - 简化绘制避免重叠"""
        painter = QPainter(self)
        
        # 只绘制纯色背景，不调用super()避免默认绘制
        painter.fillRect(self.rect(), QColor("#f8fafc"))


class CardScrollArea(QScrollArea):
    """
    卡片滚动区域
    包装CardGridContainer，提供纯垂直滚动功能
    """
    
    # 向上传递信号
    card_selected = pyqtSignal(str)
    card_install_clicked = pyqtSignal(str)
    card_launch_clicked = pyqtSignal(str)
    card_info_clicked = pyqtSignal(str)
    card_favorite_toggled = pyqtSignal(str, bool)  # 新增：收藏信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建网格容器
        self.grid_container = CardGridContainer()
        
        # 连接信号
        self.grid_container.card_selected.connect(self.card_selected.emit)
        self.grid_container.card_install_clicked.connect(self.card_install_clicked.emit)
        self.grid_container.card_launch_clicked.connect(self.card_launch_clicked.emit)
        self.grid_container.card_info_clicked.connect(self.card_info_clicked.emit)
        self.grid_container.card_favorite_toggled.connect(self.card_favorite_toggled.emit)  # 新增：收藏信号
        
        # 设置滚动区域属性
        self.setWidget(self.grid_container)
        self.setWidgetResizable(True)
        
        # 只允许垂直滚动
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 简化样式设置，避免冲突
        self.setObjectName("CardScrollArea")
        self.setFrameShape(self.NoFrame)  # 去除边框
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8fafc;
            }
        """)
    
    def add_card(self, tool_data: dict):
        """添加新卡片"""
        self.grid_container.add_card(tool_data)
    
    def remove_card(self, tool_name: str):
        """移除指定卡片"""
        self.grid_container.remove_card(tool_name)
    
    def clear_cards(self):
        """清空所有卡片"""
        self.grid_container.clear_cards()
    
    def set_cards(self, tools_data: list):
        """设置卡片列表"""
        self.grid_container.set_cards(tools_data)
    
    def filter_cards(self, search_term: str = "", categories: list = None, statuses: list = None):
        """筛选卡片"""
        self.grid_container.filter_cards(search_term, categories, statuses)
    
    def get_card_by_name(self, tool_name: str) -> ToolCardV2:
        """根据工具名称获取卡片对象"""
        return self.grid_container.get_card_by_name(tool_name)
    
    def resizeEvent(self, event):
        """窗口尺寸变化时通知容器"""
        super().resizeEvent(event)
        # 容器会自动通过父容器宽度计算布局
        if hasattr(self, 'grid_container'):
            self.grid_container._relayout_cards()
