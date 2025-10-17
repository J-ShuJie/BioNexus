#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图形视图动画系统
提供流畅的 60 FPS 动画效果
"""

from PyQt5.QtCore import (
    QPropertyAnimation, QParallelAnimationGroup, QSequentialAnimationGroup,
    QEasingCurve, pyqtProperty, QObject, QPointF, QRectF, QTimer,
    pyqtSignal
)
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsEffect, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QTransform
import math


class AnimationManager(QObject):
    """
    动画管理器
    统一管理所有动画效果
    """
    
    def __init__(self):
        super().__init__()
        self.animations = []
        self.groups = []
    
    def create_hover_animation(self, item: QGraphicsItem, scale_factor: float = 1.05):
        """创建悬停动画"""
        # 保存原始状态
        original_scale = item.scale()
        
        # 放大动画
        scale_up = ScaleAnimation(item)
        scale_up.setDuration(150)
        scale_up.setStartValue(original_scale)
        scale_up.setEndValue(scale_factor)
        scale_up.setEasingCurve(QEasingCurve.OutCubic)
        
        # 缩小动画
        scale_down = ScaleAnimation(item)
        scale_down.setDuration(150)
        scale_down.setStartValue(scale_factor)
        scale_down.setEndValue(original_scale)
        scale_down.setEasingCurve(QEasingCurve.InCubic)
        
        return scale_up, scale_down
    
    def create_click_animation(self, item: QGraphicsItem):
        """创建点击动画"""
        # 按下效果
        press = ScaleAnimation(item)
        press.setDuration(50)
        press.setStartValue(1.0)
        press.setEndValue(0.95)
        press.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 释放效果
        release = ScaleAnimation(item)
        release.setDuration(100)
        release.setStartValue(0.95)
        release.setEndValue(1.0)
        release.setEasingCurve(QEasingCurve.OutElastic)
        
        # 组合动画
        group = QSequentialAnimationGroup()
        group.addAnimation(press)
        group.addAnimation(release)
        
        return group
    
    def create_fade_in_animation(self, item: QGraphicsItem, duration: int = 500):
        """创建淡入动画"""
        opacity_anim = OpacityAnimation(item)
        opacity_anim.setDuration(duration)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        return opacity_anim
    
    def create_slide_animation(self, item: QGraphicsItem, 
                              start_pos: QPointF, end_pos: QPointF,
                              duration: int = 300):
        """创建滑动动画"""
        pos_anim = PositionAnimation(item)
        pos_anim.setDuration(duration)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(end_pos)
        pos_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        return pos_anim
    
    def create_bounce_animation(self, item: QGraphicsItem):
        """创建弹跳动画"""
        # 向上弹
        up = PositionAnimation(item)
        up.setDuration(200)
        current_pos = item.pos()
        up.setStartValue(current_pos)
        up.setEndValue(QPointF(current_pos.x(), current_pos.y() - 10))
        up.setEasingCurve(QEasingCurve.OutQuad)
        
        # 落下
        down = PositionAnimation(item)
        down.setDuration(200)
        down.setStartValue(QPointF(current_pos.x(), current_pos.y() - 10))
        down.setEndValue(current_pos)
        down.setEasingCurve(QEasingCurve.InQuad)
        
        # 组合
        bounce = QSequentialAnimationGroup()
        bounce.addAnimation(up)
        bounce.addAnimation(down)
        
        return bounce
    
    def create_shake_animation(self, item: QGraphicsItem, intensity: float = 5):
        """创建抖动动画（用于错误提示）"""
        original_pos = item.pos()
        shake = QSequentialAnimationGroup()
        
        for i in range(4):
            move_right = PositionAnimation(item)
            move_right.setDuration(50)
            move_right.setStartValue(original_pos)
            move_right.setEndValue(QPointF(original_pos.x() + intensity, original_pos.y()))
            
            move_left = PositionAnimation(item)
            move_left.setDuration(50)
            move_left.setStartValue(QPointF(original_pos.x() + intensity, original_pos.y()))
            move_left.setEndValue(QPointF(original_pos.x() - intensity, original_pos.y()))
            
            move_center = PositionAnimation(item)
            move_center.setDuration(50)
            move_center.setStartValue(QPointF(original_pos.x() - intensity, original_pos.y()))
            move_center.setEndValue(original_pos)
            
            shake.addAnimation(move_right)
            shake.addAnimation(move_left)
            shake.addAnimation(move_center)
            
            intensity *= 0.6  # 逐渐减弱
        
        return shake
    
    def create_pulse_animation(self, item: QGraphicsItem):
        """创建脉冲动画（用于提示注意）"""
        pulse = QSequentialAnimationGroup()
        pulse.setLoopCount(-1)  # 无限循环
        
        # 放大
        scale_up = ScaleAnimation(item)
        scale_up.setDuration(500)
        scale_up.setStartValue(1.0)
        scale_up.setEndValue(1.1)
        scale_up.setEasingCurve(QEasingCurve.InOutSine)
        
        # 缩小
        scale_down = ScaleAnimation(item)
        scale_down.setDuration(500)
        scale_down.setStartValue(1.1)
        scale_down.setEndValue(1.0)
        scale_down.setEasingCurve(QEasingCurve.InOutSine)
        
        pulse.addAnimation(scale_up)
        pulse.addAnimation(scale_down)
        
        return pulse


class AnimatableItem(QObject):
    """
    可动画化的图形项包装器
    为 QGraphicsItem 添加可动画属性
    """
    
    def __init__(self, graphics_item: QGraphicsItem):
        super().__init__()
        self.item = graphics_item
        self._opacity = 1.0
        self._scale = 1.0
        self._rotation = 0.0
    
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.item.setOpacity(value)
    
    @pyqtProperty(float)
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value):
        self._scale = value
        self.item.setScale(value)
    
    @pyqtProperty(float)
    def rotation(self):
        return self._rotation
    
    @rotation.setter
    def rotation(self, value):
        self._rotation = value
        self.item.setRotation(value)
    
    @pyqtProperty(QPointF)
    def pos(self):
        return self.item.pos()
    
    @pos.setter
    def pos(self, value):
        self.item.setPos(value)


class ScaleAnimation(QPropertyAnimation):
    """缩放动画"""
    
    def __init__(self, item: QGraphicsItem):
        self.wrapper = AnimatableItem(item)
        super().__init__(self.wrapper, b"scale")


class OpacityAnimation(QPropertyAnimation):
    """透明度动画"""
    
    def __init__(self, item: QGraphicsItem):
        self.wrapper = AnimatableItem(item)
        super().__init__(self.wrapper, b"opacity")


class PositionAnimation(QPropertyAnimation):
    """位置动画"""
    
    def __init__(self, item: QGraphicsItem):
        self.wrapper = AnimatableItem(item)
        super().__init__(self.wrapper, b"pos")


class RotationAnimation(QPropertyAnimation):
    """旋转动画"""
    
    def __init__(self, item: QGraphicsItem):
        self.wrapper = AnimatableItem(item)
        super().__init__(self.wrapper, b"rotation")


class ParallaxEffect(QObject):
    """
    视差效果
    为不同层级的元素添加不同的移动速度
    """
    
    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.layers = []
    
    def add_layer(self, items: list, speed: float):
        """添加视差层"""
        self.layers.append({
            'items': items,
            'speed': speed
        })
    
    def update_parallax(self, delta_x: float, delta_y: float):
        """更新视差效果"""
        for layer in self.layers:
            for item in layer['items']:
                current_pos = item.pos()
                new_x = current_pos.x() + delta_x * layer['speed']
                new_y = current_pos.y() + delta_y * layer['speed']
                item.setPos(new_x, new_y)


class RippleEffect(QGraphicsItem):
    """
    涟漪效果
    点击时产生扩散的圆形波纹
    """
    
    def __init__(self, center: QPointF, max_radius: float = 100):
        super().__init__()
        self.center = center
        self.max_radius = max_radius
        self.current_radius = 0
        self.opacity = 1.0
        
        # 动画定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ripple)
        self.timer.start(16)  # 60 FPS
    
    def boundingRect(self):
        return QRectF(
            self.center.x() - self.max_radius,
            self.center.y() - self.max_radius,
            self.max_radius * 2,
            self.max_radius * 2
        )
    
    def paint(self, painter, option, widget):
        if self.current_radius < self.max_radius:
            painter.setOpacity(self.opacity)
            painter.setPen(QColor(100, 100, 255, int(255 * self.opacity)))
            painter.drawEllipse(self.center, self.current_radius, self.current_radius)
    
    def update_ripple(self):
        self.current_radius += 3
        self.opacity = 1.0 - (self.current_radius / self.max_radius)
        
        if self.current_radius >= self.max_radius:
            self.timer.stop()
            if self.scene():
                self.scene().removeItem(self)
        else:
            self.update()


class GlowEffect(QGraphicsDropShadowEffect):
    """
    发光效果
    为元素添加柔和的外发光
    """
    
    def __init__(self, color: QColor = QColor(100, 200, 255), 
                 blur_radius: int = 20):
        super().__init__()
        self.setColor(color)
        self.setBlurRadius(blur_radius)
        self.setOffset(0, 0)
    
    def set_intensity(self, intensity: float):
        """设置发光强度（0.0 - 1.0）"""
        color = self.color()
        color.setAlphaF(intensity)
        self.setColor(color)


class SpringAnimation(QObject):
    """
    弹簧动画
    模拟物理弹簧效果
    """
    
    position_changed = pyqtSignal(QPointF)
    
    def __init__(self, stiffness: float = 0.1, damping: float = 0.8):
        super().__init__()
        self.stiffness = stiffness
        self.damping = damping
        self.velocity = QPointF(0, 0)
        self.current_pos = QPointF(0, 0)
        self.target_pos = QPointF(0, 0)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spring)
        self.timer.setInterval(16)  # 60 FPS
    
    def set_target(self, target: QPointF):
        """设置目标位置"""
        self.target_pos = target
        if not self.timer.isActive():
            self.timer.start()
    
    def update_spring(self):
        """更新弹簧动画"""
        # 计算力
        dx = self.target_pos.x() - self.current_pos.x()
        dy = self.target_pos.y() - self.current_pos.y()
        
        # 应用弹簧力
        self.velocity.setX(self.velocity.x() + dx * self.stiffness)
        self.velocity.setY(self.velocity.y() + dy * self.stiffness)
        
        # 应用阻尼
        self.velocity.setX(self.velocity.x() * self.damping)
        self.velocity.setY(self.velocity.y() * self.damping)
        
        # 更新位置
        self.current_pos.setX(self.current_pos.x() + self.velocity.x())
        self.current_pos.setY(self.current_pos.y() + self.velocity.y())
        
        # 发射信号
        self.position_changed.emit(self.current_pos)
        
        # 检查是否停止
        if (abs(self.velocity.x()) < 0.01 and 
            abs(self.velocity.y()) < 0.01 and
            abs(dx) < 0.5 and abs(dy) < 0.5):
            self.timer.stop()
            self.current_pos = self.target_pos
            self.position_changed.emit(self.current_pos)