"""
遮罩层组件 - 用于弹出菜单时的背景变暗效果
================================================
提供半透明黑色遮罩，点击即关闭关联的弹出组件
支持渐入渐出动画效果
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QBrush, QPaintEvent, QMouseEvent


class OverlayWidget(QWidget):
    """
    半透明遮罩层组件
    用于模态对话框或弹出菜单的背景遮罩
    """
    
    # 信号定义
    clicked = pyqtSignal()  # 点击遮罩时发出
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 遮罩透明度
        self._opacity = 0.0
        self.target_opacity = 0.3  # 目标透明度
        
        # 动画设置
        self.fade_animation = QPropertyAnimation(self, b"opacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 初始化UI
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI设置"""
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        
        # 初始隐藏
        self.hide()
        
    @pyqtProperty(float)
    def opacity(self):
        """透明度属性"""
        return self._opacity
        
    @opacity.setter
    def opacity(self, value):
        """设置透明度"""
        self._opacity = value
        self.update()
        
    def paintEvent(self, event: QPaintEvent):
        """绘制遮罩层"""
        if self._opacity <= 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制半透明黑色背景
        overlay_color = QColor(0, 0, 0)
        overlay_color.setAlphaF(self._opacity)
        painter.fillRect(self.rect(), QBrush(overlay_color))
        
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            
    def show_animated(self):
        """带动画的显示遮罩"""
        # 设置覆盖整个父窗口
        if self.parent():
            self.setGeometry(self.parent().rect())
            
        # 重置透明度
        self._opacity = 0.0
        self.show()
        self.raise_()
        
        # 启动渐入动画
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(self.target_opacity)
        self.fade_animation.start()
        
    def hide_animated(self):
        """带动画的隐藏遮罩"""
        # 启动渐出动画
        self.fade_animation.setStartValue(self._opacity)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self._on_fade_out_finished)
        self.fade_animation.start()
        
    def _on_fade_out_finished(self):
        """渐出动画完成后隐藏组件"""
        self.hide()
        try:
            self.fade_animation.finished.disconnect(self._on_fade_out_finished)
        except:
            pass
            
    def resizeEvent(self, event):
        """窗口大小改变时调整遮罩大小"""
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())