# BioNexus 图标资源目录

本目录包含了 BioNexus 应用的所有图标资源，按功能分类存放。

## 📁 目录结构

```
resources/icons/
├── app/          # 应用程序图标
│   └── bionexus_icon.jpeg    # 主应用图标 (1024x1024)
├── ui/           # UI界面图标
│   ├── buttons/  # 按钮图标 (待添加)
│   ├── status/   # 状态图标 (待添加)
│   └── actions/  # 操作图标 (待添加)
└── tools/        # 工具相关图标
    ├── categories/    # 工具分类图标 (待添加)
    └── individual/    # 单个工具图标 (待添加)
```

## 🎯 使用说明

### 应用图标 (app/)
- **主图标**: `bionexus_icon.jpeg` - 用于窗口标题栏、任务栏、系统托盘
- **建议尺寸**: 1024x1024 (自动缩放到所需大小)
- **支持格式**: PNG, JPEG, ICO, SVG

### UI图标 (ui/)
用于界面元素的小图标：
- **buttons/**: 按钮图标 (16x16, 24x24)
- **status/**: 状态指示图标 (16x16)
- **actions/**: 操作动作图标 (16x16, 24x24)

### 工具图标 (tools/)
用于生物信息学工具的图标：
- **categories/**: 工具分类图标 (32x32, 48x48)
- **individual/**: 单个工具图标 (32x32, 64x64)

## 💡 添加新图标时

1. 选择合适的子目录
2. 使用描述性文件名
3. 准备多个尺寸（推荐）
4. 更新此文档

## 🔧 代码中引用方式

```python
from PyQt5.QtGui import QIcon
import os

# 构建图标路径
icon_path = os.path.join("resources", "icons", "app", "bionexus_icon.jpeg")
icon = QIcon(icon_path)
self.setWindowIcon(icon)
```

---
*最后更新: 2025-09-04*