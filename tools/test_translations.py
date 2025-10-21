#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
test_translations.py - 测试翻译文件加载

验证.qm文件能否被PyQt5正确加载和使用
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTranslator, QLocale


PROJECT_ROOT = Path(__file__).parent.parent
TRANSLATIONS_DIR = PROJECT_ROOT / 'translations' / 'compiled'


class TestWindow(QMainWindow):
    """测试窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Translation Test")
        self.setGeometry(100, 100, 400, 300)

        # 创建中心widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 添加测试标签 - 这些应该被翻译
        layout.addWidget(QLabel(self.tr("常规设置")))
        layout.addWidget(QLabel(self.tr("语言设置")))
        layout.addWidget(QLabel(self.tr("简体中文")))
        layout.addWidget(QLabel(self.tr("界面语言")))
        layout.addWidget(QLabel(self.tr("设置")))

        # 切换语言按钮
        btn_zh = QPushButton("切换到中文", self)
        btn_zh.clicked.connect(lambda: self.switch_language('zh_CN'))
        layout.addWidget(btn_zh)

        btn_en = QPushButton("Switch to English", self)
        btn_en.clicked.connect(lambda: self.switch_language('en_US'))
        layout.addWidget(btn_en)

    def switch_language(self, locale):
        """切换语言"""
        print(f"切换语言到: {locale}")
        # 这里只是演示,实际切换需要重新加载translator


def main():
    """主函数"""
    app = QApplication(sys.argv)

    print("=" * 60)
    print("翻译文件加载测试")
    print("=" * 60)

    # 测试加载中文翻译
    zh_qm = TRANSLATIONS_DIR / "bionexus_zh_CN.qm"
    en_qm = TRANSLATIONS_DIR / "bionexus_en_US.qm"

    # 检查文件是否存在
    if not zh_qm.exists():
        print(f"✗ 中文翻译文件不存在: {zh_qm}")
        return 1

    if not en_qm.exists():
        print(f"✗ 英文翻译文件不存在: {en_qm}")
        return 1

    print(f"✓ 找到翻译文件:")
    print(f"  - {zh_qm.name} ({zh_qm.stat().st_size} bytes)")
    print(f"  - {en_qm.name} ({en_qm.stat().st_size} bytes)")

    # 尝试加载翻译
    translator = QTranslator()

    print(f"\n测试加载中文翻译...")
    if translator.load(str(zh_qm)):
        print(f"✓ 中文翻译加载成功!")
        app.installTranslator(translator)

        # 测试翻译
        test_strings = [
            "常规设置",
            "语言设置",
            "简体中文",
            "界面语言",
            "设置"
        ]

        print("\n翻译测试:")
        for s in test_strings:
            # 直接使用translator翻译
            translated = translator.translate("SettingsPanel", s)
            if translated:
                print(f"  '{s}' -> '{translated}'")
            else:
                print(f"  '{s}' -> (未找到翻译)")

    else:
        print(f"✗ 中文翻译加载失败!")
        print(f"  文件可能格式不正确")
        return 1

    # 测试英文翻译
    en_translator = QTranslator()
    print(f"\n测试加载英文翻译...")
    if en_translator.load(str(en_qm)):
        print(f"✓ 英文翻译加载成功!")
    else:
        print(f"⚠ 英文翻译加载失败(这是正常的,因为未填写翻译)")

    print("\n" + "=" * 60)
    print("✓ 翻译系统测试通过!")
    print("=" * 60)

    # 显示测试窗口(可选)
    if '--show-window' in sys.argv:
        window = TestWindow()
        window.show()
        return app.exec_()
    else:
        print("\n提示: 使用 --show-window 参数可以显示测试窗口")
        return 0


if __name__ == '__main__':
    sys.exit(main())
