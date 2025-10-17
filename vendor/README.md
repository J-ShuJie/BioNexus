# vendor/ - 第三方包管理

## 📋 目录说明

此目录统一管理所有外部依赖的代码，确保第三方组件的规范化集成和维护。

## 📂 目录结构

```
vendor/
├── __init__.py              # 包初始化和便捷导入
├── README.md               # 本文件 - 总体说明
├── LICENSES.md             # 所有第三方许可证汇总
└── auto_resizing/          # AutoResizingTextEdit包
    ├── __init__.py
    ├── text_edit.py        # 核心代码
    ├── LICENSE             # MIT许可证
    └── README.md           # 包说明文档
```

## 🔧 使用方式

### 便捷导入（推荐）
```python
from vendor import AutoResizingTextEdit

# 使用
widget = AutoResizingTextEdit()
widget.setPlainText("自动调整高度的文本编辑器")
```

### 明确路径导入
```python
from vendor.auto_resizing.text_edit import AutoResizingTextEdit
```

## 📦 已集成的第三方包

| 包名 | 版本 | 许可证 | 用途 | 状态 |
|------|------|--------|------|------|
| AutoResizingTextEdit | master (2024) | MIT | 自动高度调整的文本编辑器 | ✅ 已集成 |

## 🔄 添加新第三方包的流程

1. **创建包目录**：`mkdir vendor/package_name`
2. **复制源码**：将第三方代码复制到目录中
3. **保留许可证**：复制原始LICENSE文件
4. **编写说明**：创建README.md记录来源和用法
5. **更新__init__.py**：添加便捷导入
6. **更新LICENSES.md**：添加许可证信息

## ⚠️ 重要规则

1. **禁止修改第三方代码**：除非必要的适配，保持代码原样
2. **保留许可证信息**：每个包必须包含原始LICENSE
3. **记录来源信息**：在README.md中记录获取日期、版本、来源
4. **统一命名规范**：使用snake_case目录名，与Python包名一致

## 📄 许可证合规

所有第三方包的许可证信息汇总在 `LICENSES.md` 中，使用前请确认：
- 许可证与项目兼容
- 满足原作者的使用要求
- 正确标注原作者信息

## 🔍 问题排查

如果遇到导入问题：
1. 检查 `__init__.py` 是否存在
2. 确认包名拼写正确
3. 查看 `LICENSES.md` 了解包的状态
4. 参考各包的 README.md 获取使用说明

---

**维护者**: BioNexus 开发团队  
**最后更新**: 2025-09-01