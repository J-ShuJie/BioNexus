"""
现代化工具栏组件 - 与侧边栏中线对齐
=============================================
精确对齐侧边栏的视觉中线（y=61）
采用相同的设计语言，保持界面统一性
"""

from PyQt5.QtWidgets import QWidget, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import (
    QPainter, QLinearGradient, QColor, QBrush, QPen,
    QFont, QFontMetrics, QPainterPath
)


class ModernToolbar(QWidget):
    """
    现代化工具栏 - 精确对齐侧边栏中线
    高度61px，与侧边栏搜索框和导航按钮的中线完美对齐
    """
    
    # 信号定义
    filter_clicked = pyqtSignal()
    download_status_clicked = pyqtSignal()
    back_clicked = pyqtSignal()  # 新增：返回按钮信号
    action_clicked = pyqtSignal(str)  # 自定义动作按钮点击（非切换类）
    action_toggled = pyqtSignal(str, bool)  # 自定义动作切换
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 状态变量
        self.hover_button = None
        self.download_count = 0  # 正在下载的数量
        self.filter_active = False  # 筛选是否激活
        self.download_active = False  # 下载是否激活
        self.is_detail_mode = False  # 新增：是否在详情页模式
        self.back_label = ""  # 返回目标文本（为空则使用默认）
        self._default_buttons_visible = True  # 控制筛选/下载是否显示
        self.back_pressed = False  # 新增：返回按钮是否被按下
        # 自定义动作按钮
        self._actions = []  # type: list
        self._action_defs = []  # type: list

        # 按钮区域
        self.download_rect = QRect()
        self.filter_rect = QRect()
        self.back_rect = QRect()  # 新增：返回按钮区域
        
        # 动画属性
        self.animation_progress = 0.0
        self.hover_animation = QPropertyAnimation(self, b"animationProgress")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 淑入淡出动画
        self.fade_progress = 0.0
        self.fade_animation = QPropertyAnimation(self, b"fadeProgress")
        self.fade_animation.setDuration(150)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 颜色主题 - 与侧边栏保持一致
        self.colors = {
            'bg_start': QColor(250, 251, 252),      # #fafbfc
            'bg_end': QColor(241, 245, 249),        # #f1f5f9
            'button_normal': QColor(255, 255, 255, 180),
            'button_hover': QColor(59, 130, 246, 40),
            'button_active': QColor(59, 130, 246),  # 蓝色激活状态
            'button_active_bg': QColor(59, 130, 246, 50),  # 激活背景
            'button_active_border': QColor(37, 99, 235),  # 深蓝边框
            'text_primary': QColor(30, 41, 59),
            'text_secondary': QColor(100, 116, 139),
            'text_active': QColor(255, 255, 255),  # 激活时白色文字
            'border': QColor(226, 232, 240),
            'badge_bg': QColor(239, 68, 68),        # 红色徽章背景
            'success': QColor(16, 185, 129),        # 绿色成功
        }
        
        self._setup_widget()
        self._connect_language_change()
    
    def _setup_widget(self):
        """设置控件属性"""
        # 精确高度61px - 与侧边栏中线对齐
        self.setFixedHeight(61)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 确保按钮区域初始化
        self._update_button_rects()
    
    @pyqtProperty(float)
    def animationProgress(self):
        return self.animation_progress
    
    @animationProgress.setter
    def animationProgress(self, value):
        self.animation_progress = value
        self.update()
    
    @pyqtProperty(float)
    def fadeProgress(self):
        return self.fade_progress
    
    @fadeProgress.setter
    def fadeProgress(self, value):
        self.fade_progress = value
        self.update()
    
    def paintEvent(self, event):
        """主绘制方法"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        self._draw_background(painter)
        
        # 绘制按钮
        self._draw_buttons(painter)
        
        # 绘制底部分界线
        self._draw_separator(painter)
    
    def _draw_background(self, painter):
        """绘制渐变背景 - 与侧边栏风格一致"""
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, self.colors['bg_start'])
        gradient.setColorAt(1, self.colors['bg_end'])
        
        painter.fillRect(self.rect(), QBrush(gradient))
    
    def _draw_separator(self, painter):
        """绘制底部分界线 - 正好在中线位置"""
        pen = QPen(self.colors['border'])
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
    
    def _update_button_rects(self):
        """更新按钮区域 - 独立方法确保初始化"""
        button_size = 36
        button_spacing = 12
        right_margin = 20
        left_margin = 20
        
        # 筛选按钮位置
        filter_x = self.width() - right_margin - button_size
        filter_y = (self.height() - button_size) // 2
        self.filter_rect = QRect(filter_x, filter_y, button_size, button_size)
        
        # 下载状态按钮位置
        download_x = filter_x - button_spacing - button_size
        download_y = filter_y
        self.download_rect = QRect(download_x, download_y, button_size, button_size)
        
        # 返回按钮位置（左侧）- 动态宽度基于文本
        f = QFont(); f.setPointSize(13); f.setBold(True)
        fm = QFontMetrics(f)
        text = self._get_back_text()
        text_w = fm.boundingRect(text).width() + 24  # 左右内边距
        back_width = max(80, min(200, text_w))
        back_x = left_margin
        back_y = (self.height() - button_size) // 2
        self.back_rect = QRect(back_x, back_y, back_width, button_size)
    
    def _draw_buttons(self, painter):
        """绘制工具栏按钮"""
        # 确保按钮区域是最新的
        self._update_button_rects()
        
        if self.is_detail_mode:
            # 详情页模式：只显示返回按钮
            self._draw_back_button(painter, self.back_rect, 
                                  self.hover_button == "back")
        else:
            # 列表模式：默认显示筛选和下载按钮（可关闭）
            # 设置透明度（用于淡入淡出效果）
            if self.fade_animation.state() == QPropertyAnimation.Running:
                painter.setOpacity(self.fade_progress)
            if self._default_buttons_visible:
                self._draw_button(painter, self.download_rect, "📥", "download", 
                                 self.hover_button == "download", self.download_active)
                self._draw_button(painter, self.filter_rect, "🔧", "filter",
                                 self.hover_button == "filter", self.filter_active)
            
            # 如果有下载，绘制数字徽章
            if self._default_buttons_visible and self.download_count > 0:
                self._draw_badge(painter, self.download_rect, str(self.download_count))
            
            painter.setOpacity(1.0)  # 恢复透明度
    
    def _draw_button(self, painter, rect, icon, button_id, is_hover, is_active):
        """绘制单个按钮 - 增强激活状态效果"""
        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 8, 8)
        
        # 背景颜色 - 增强激活状态
        if is_active:
            # 激活状态：蓝色背景
            bg_color = self.colors['button_active_bg']
        elif is_hover:
            opacity = int(25 + self.animation_progress * 30)
            bg_color = QColor(self.colors['button_hover'])
            bg_color.setAlpha(opacity)
        else:
            bg_color = QColor(255, 255, 255, 100)
        
        painter.fillPath(path, QBrush(bg_color))
        
        # 边框 - 激活状态使用深蓝边框
        if is_active:
            pen = QPen(self.colors['button_active_border'], 2)
        else:
            pen = QPen(self.colors['border'], 1)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # 图标颜色 - 激活时白色，普通时灰色
        font = QFont()
        font.setPointSize(16)
        painter.setFont(font)
        
        if is_active:
            text_color = self.colors['text_active']  # 白色
        else:
            text_color = self.colors['text_secondary']  # 灰色
        
        painter.setPen(QPen(text_color))
        
        # 居中绘制图标
        fm = QFontMetrics(font)
        icon_rect = fm.boundingRect(icon)
        icon_x = rect.x() + (rect.width() - icon_rect.width()) // 2
        icon_y = rect.y() + (rect.height() + icon_rect.height()) // 2 - 3
        painter.drawText(icon_x, icon_y, icon)
    
    def _draw_badge(self, painter, button_rect, count_text):
        """绘制数字徽章"""
        # 徽章位置 - 按钮右上角
        badge_radius = 8
        badge_x = button_rect.right() - badge_radius
        badge_y = button_rect.top() + 2
        
        # 绘制红色圆形背景
        painter.setBrush(QBrush(self.colors['badge_bg']))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawEllipse(badge_x - badge_radius, badge_y - badge_radius,
                          badge_radius * 2, badge_radius * 2)
        
        # 绘制数字
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255)))
        
        fm = QFontMetrics(font)
        text_rect = fm.boundingRect(count_text)
        text_x = badge_x - text_rect.width() // 2
        text_y = badge_y + text_rect.height() // 2 - 2
        painter.drawText(text_x, text_y, count_text)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # 确保按钮区域是最新的
        self._update_button_rects()
        
        pos = event.pos()
        old_hover = self.hover_button
        new_hover = None
        
        if self.is_detail_mode:
            if self.back_rect.contains(pos):
                new_hover = "back"
        else:
            if self.download_rect.contains(pos):
                new_hover = "download"
            elif self.filter_rect.contains(pos):
                new_hover = "filter"
        
        if new_hover != old_hover:
            self.hover_button = new_hover
            self._animate_hover()
            self.update()
        
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"【TOOLBAR DEBUG】鼠标点击事件开始 - 按钮类型: {event.button()}")
        print(f"【TOOLBAR DEBUG】鼠标点击事件开始 - 按钮类型: {event.button()}")
        
        if event.button() != Qt.LeftButton:
            print(f"【TOOLBAR DEBUG】非左键点击，忽略")
            return
        
        # 确保按钮区域是最新的
        self._update_button_rects()
        
        pos = event.pos()
        print(f"【TOOLBAR DEBUG】点击位置: {pos}")
        print(f"【TOOLBAR DEBUG】下载按钮区域: {self.download_rect}")
        print(f"【TOOLBAR DEBUG】筛选按钮区域: {self.filter_rect}")
        
        if self.is_detail_mode:
            if self.back_rect.contains(pos):
                print(f"【TOOLBAR DEBUG】点击命中返回按钮，发送 back_clicked 信号")
                self.back_pressed = True  # 设置按下状态
                self.update()  # 立即更新显示按下效果
                self.back_clicked.emit()
        else:
            if self.download_rect.contains(pos):
                print(f"【TOOLBAR DEBUG】点击命中下载按钮，发送 download_status_clicked 信号")
                self.download_status_clicked.emit()
            elif self.filter_rect.contains(pos):
                print(f"【TOOLBAR DEBUG】点击命中筛选按钮，发送 filter_clicked 信号")
                self.filter_clicked.emit()
                print(f"【TOOLBAR DEBUG】filter_clicked 信号已发送")
            else:
                print(f"【TOOLBAR DEBUG】点击未命中任何按钮")
        
        print(f"【TOOLBAR DEBUG】鼠标点击事件处理完成")
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 重置按钮按下状态"""
        if self.back_pressed:
            self.back_pressed = False
            self.update()
        super().mouseReleaseEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self.hover_button:
            self.hover_button = None
            self.update()
        if self.back_pressed:
            self.back_pressed = False
            self.update()
        super().leaveEvent(event)
    
    def _animate_hover(self):
        """启动悬停动画"""
        if self.hover_animation.state() == QPropertyAnimation.Running:
            self.hover_animation.stop()
        
        if self.hover_button:
            self.hover_animation.setStartValue(0.0)
            self.hover_animation.setEndValue(1.0)
        else:
            self.hover_animation.setStartValue(1.0)
            self.hover_animation.setEndValue(0.0)
        
        self.hover_animation.start()
    
    def set_download_count(self, count):
        """设置下载数量"""
        self.download_count = count
        self.update()

    # =========================
    # 公共API：外部控制默认按钮/动作按钮
    # =========================
    def set_default_buttons_visible(self, visible: bool):
        self._default_buttons_visible = bool(visible)
        # 自定义动作按钮布局可能要占据右侧，该方法只负责隐藏默认绘制
        self.update()

    def clear_actions(self):
        for b in self._actions:
            try:
                b.deleteLater()
            except Exception:
                pass
        self._actions.clear()
        self._action_defs.clear()
        self.update()

    def set_actions(self, actions):
        """
        设置右侧自定义动作按钮。
        actions: [{ 'id': str, 'text': str, 'type': 'normal'|'toggle' }]
        """
        # 清理旧按钮
        self.clear_actions()
        if not actions:
            return
        self._action_defs = actions[:]
        # 创建按钮（右对齐，从右往左排）
        for act in actions:
            btn = QPushButton(self.tr(act.get('text', '')), self)
            t = (act.get('type') or 'normal').lower()
            if t == 'toggle':
                btn.setCheckable(True)
                btn.toggled.connect(lambda state, aid=act.get('id',''): self.action_toggled.emit(aid, state))
            else:
                btn.clicked.connect(lambda _, aid=act.get('id',''): self.action_clicked.emit(aid))
            self._style_action_button(btn)
            btn.show()
            self._actions.append(btn)
        # 初次布局
        self._layout_action_buttons()
        self.update()

    def _style_action_button(self, btn: QPushButton):
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(28)
        btn.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: #ffffff; border: none; border-radius: 6px; padding: 4px 8px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:pressed { background-color: #1d4ed8; }
            QPushButton:checked { background-color: #10b981; }
        """)

    def _layout_action_buttons(self):
        if not self._actions:
            return
        right_margin = 20
        spacing = 8
        x = self.width() - right_margin
        y = (self.height() - 28) // 2
        # 右对齐，从右往左排
        for btn in reversed(self._actions):
            w = max(80, btn.sizeHint().width())
            x = x - w
            btn.setGeometry(x, y, w, 28)
            x = x - spacing
    
    def set_filter_active(self, active):
        """设置筛选激活状态 - 蓝色高亮效果"""
        self.filter_active = active
        self.update()
    
    def set_download_active(self, active):
        """设置下载激活状态 - 蓝色高亮效果"""
        self.download_active = active
        self.update()
    
    def _draw_back_button(self, painter, rect, is_hover):
        """绘制返回按钮 - 超强视觉效果版本"""
        # 保存画家状态
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 调试信息
        print(f"绘制返回按钮: hover={is_hover}, pressed={self.back_pressed}")
        
        # 根据状态调整矩形（明显的点击效果）
        draw_rect = QRectF(rect)
        if self.back_pressed:
            # 点击时明显缩小
            shrink = 3
            draw_rect = QRectF(
                rect.x() + shrink,
                rect.y() + shrink,
                rect.width() - shrink * 2,
                rect.height() - shrink * 2
            )
            print("返回按钮：点击状态")
        elif is_hover:
            # 悬停时明显放大
            expand = 2
            draw_rect = QRectF(
                rect.x() - expand,
                rect.y() - expand,
                rect.width() + expand * 2,
                rect.height() + expand * 2
            )
            print("返回按钮：悬停状态")
        else:
            print("返回按钮：正常状态")
        
        # 创建圆角路径
        path = QPainterPath()
        path.addRoundedRect(draw_rect, 8, 8)
        
        # 背景渐变 - 更强烈的对比
        gradient = QLinearGradient(draw_rect.topLeft(), draw_rect.bottomLeft())
        if self.back_pressed:
            # 点击状态：非常明显的深色
            gradient.setColorAt(0, QColor(41, 128, 185, 220))  # 明亮蓝色
            gradient.setColorAt(1, QColor(52, 152, 219, 240))
        elif is_hover:
            # 悬停状态：明亮的白色渐变
            gradient.setColorAt(0, QColor(255, 255, 255, 120))
            gradient.setColorAt(1, QColor(240, 240, 240, 100))
        else:
            # 正常状态：可见的灰白色
            gradient.setColorAt(0, QColor(255, 255, 255, 80))
            gradient.setColorAt(1, QColor(245, 245, 245, 60))
        
        painter.fillPath(path, QBrush(gradient))
        
        # 边框 - 非常明显的边框
        if self.back_pressed:
            # 点击时：粗的蓝色边框
            border_color = QColor(52, 152, 219, 255)
            border_width = 3
        elif is_hover:
            # 悬停时：明亮的边框
            border_color = QColor(100, 100, 100, 200)
            border_width = 2
        else:
            # 正常边框：可见的灰色边框
            border_color = QColor(180, 180, 180, 150)
            border_width = 1.5
        
        pen = QPen(border_color, border_width)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # 外发光效果（仅在悬停时）
        if is_hover and not self.back_pressed:
            # 绘制外发光
            glow_path = QPainterPath()
            glow_rect = QRectF(
                draw_rect.x() - 2,
                draw_rect.y() - 2,
                draw_rect.width() + 4,
                draw_rect.height() + 4
            )
            glow_path.addRoundedRect(glow_rect, 10, 10)
            painter.setPen(QPen(QColor(100, 100, 255, 60), 1))
            painter.drawPath(glow_path)
        
        # 绘制图标和文字
        font = QFont()
        font.setPointSize(13)  # 稍微大一点
        font.setBold(True)
        painter.setFont(font)
        
        # 文字颜色根据状态变化 - 更强对比
        if self.back_pressed:
            text_color = QColor(255, 255, 255, 255)  # 点击时纯白色
        elif is_hover:
            text_color = QColor(20, 20, 20, 255)  # 悬停时深黑色
        else:
            text_color = QColor(80, 80, 80, 255)  # 正常深灰色
        
        painter.setPen(QPen(text_color))
        
        # 绘制箭头和文字（应用省略号以适配宽度）
        full_text = self._get_back_text()
        fm = QFontMetrics(font)
        # 为了避免绘制区域溢出，给左右各预留6px内边距
        available_w = max(0, int(draw_rect.width()) - 12)
        elided_text = fm.elidedText(full_text, Qt.ElideRight, available_w)
        text_rect = fm.boundingRect(elided_text)
        text_x = int(draw_rect.x() + (draw_rect.width() - text_rect.width()) // 2)
        text_y = int(draw_rect.y() + (draw_rect.height() + text_rect.height()) // 2 - 2)
        
        # 文字阴影效果
        if self.back_pressed:
            # 点击时：深色阴影
            painter.setPen(QPen(QColor(0, 0, 0, 120)))
            painter.drawText(text_x + 1, text_y + 1, elided_text)
            painter.setPen(QPen(text_color))
        elif is_hover:
            # 悬停时：白色高光
            painter.setPen(QPen(QColor(255, 255, 255, 100)))
            painter.drawText(text_x - 1, text_y - 1, elided_text)
            painter.setPen(QPen(text_color))
        
        painter.drawText(text_x, text_y, elided_text)
        
        # 恢复画家状态
        painter.restore()
    
    def switch_to_detail_mode(self):
        """切换到详情页模式"""
        if not self.is_detail_mode:
            # 淡出筛选和下载按钮
            self.fade_animation.setStartValue(1.0)
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.finished.connect(self._on_fade_out_finished)
            self.fade_animation.start()
    
    def switch_to_list_mode(self):
        """切换到列表模式"""
        if self.is_detail_mode:
            self.is_detail_mode = False
            # 淡入筛选和下载按钮
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.start()
            self.update()
    
    def _on_fade_out_finished(self):
        """淡出动画完成"""
        self.is_detail_mode = True
        # 淡入返回按钮
        self.fade_animation.finished.disconnect()  # 断开之前的连接
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        self.update()
    
    def resizeEvent(self, event):
        """窗口大小改变事件 - 确保按钮位置正确"""
        super().resizeEvent(event)
        self._update_button_rects()
        self._layout_action_buttons()
        self.update()

    def _connect_language_change(self):
        """Connect to language change signal"""
        try:
            from utils.translator import get_translator
            translator = get_translator()
            translator.languageChanged.connect(self.retranslateUi)
        except Exception as e:
            print(f"Warning: Could not connect language change signal in ModernToolbar: {e}")

    def retranslateUi(self):
        """Retranslate toolbar text - for language switching"""
        # Toolbar text is drawn in paintEvent, so just trigger a repaint
        self.update()

    # ============== 公共API：设置返回目标文本 ==============
    def set_back_target(self, text: str):
        try:
            self.back_label = text or ""
        except Exception:
            self.back_label = ""
        # 更新按钮区域以适配新文本
        self._update_button_rects()
        self.update()

    def _get_back_text(self) -> str:
        label = self.back_label.strip()
        if not label:
            label = self.tr("Back")
        # 使用左箭头 + 空格 + 目标
        return f"← {label}"
