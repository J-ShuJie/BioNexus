"""
第三方包管理
============
此目录统一管理所有外部依赖的代码

管理规则：
1. 每个第三方包独立子目录
2. 保留原始许可证
3. 记录来源和版本信息
4. 必要时可以进行适配修改

使用方式：
```python
# 便捷导入
from vendor import AutoResizingTextEdit

# 或明确路径导入
from vendor.auto_resizing.text_edit import AutoResizingTextEdit
```
"""

# 便捷导入 - 常用的第三方组件
from .auto_resizing.text_edit import AutoResizingTextEdit

# 公开接口
__all__ = [
    'AutoResizingTextEdit',
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'BioNexus Team'