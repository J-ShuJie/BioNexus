# AutoResizingTextEdit - 自适应高度文本编辑器

## 📋 项目信息

- **原项目**: [auto-resizing-text-edit](https://github.com/cameel/auto-resizing-text-edit)
- **原作者**: cameel
- **许可证**: MIT License
- **集成日期**: 2025-09-01
- **获取方式**: 直接复制源码并适配
- **原始版本**: master分支

## 🎯 功能说明

AutoResizingTextEdit 是一个基于 QTextEdit 的 PyQt5 组件，能够根据文本内容自动调整高度。

**核心特性：**
- ✅ 高度自动适应文本内容
- ✅ 保持字体大小固定不变
- ✅ 支持文本自动换行
- ✅ 与Qt布局系统完美集成
- ✅ 可设置最小显示行数
- ✅ 支持只读和可编辑模式

**适用场景：**
- 工具详情页面的描述文本
- 配置说明和帮助文档
- 动态内容展示区域
- 需要高度自适应的任何文本区域

## 🔧 使用方式

### 基本用法

```python
from vendor.auto_resizing.text_edit import AutoResizingTextEdit

# 创建自适应文本编辑器
editor = AutoResizingTextEdit()
editor.setPlainText("这是一个会根据内容自动调整高度的文本编辑器")

# 设置为只读模式（常用于展示内容）
editor.setReadOnly(True)
```

### 高级用法

```python
# 设置最小行数
editor.setMinimumLines(3)  # 至少显示3行的高度

# 设置样式
editor.setStyleSheet("""
    QTextEdit {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 15px;
        font-size: 13px;
        background-color: #f8fafc;
    }
""")

# 便捷创建函数
from vendor.auto_resizing.text_edit import create_auto_resizing_text_edit

content_display = create_auto_resizing_text_edit(
    text="工具详细介绍...",
    minimum_lines=2,
    read_only=True
)
```

### BioNexus 项目中的应用

```python
# 在详情页面中使用
def create_description_section(self):
    section_widget = QWidget()
    layout = QVBoxLayout(section_widget)
    
    # 标题
    title_label = create_smart_label_v2("工具介绍")
    title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
    
    # 自适应内容区域
    description_edit = AutoResizingTextEdit()
    description_edit.setPlainText(self.tool_data.get('description', ''))
    description_edit.setReadOnly(True)
    description_edit.setMinimumLines(3)
    
    layout.addWidget(title_label)
    layout.addWidget(description_edit)
    
    return section_widget
```

## 🏗️ 技术原理

### 核心机制

1. **heightForWidth 机制**
   ```python
   def hasHeightForWidth(self):
       return True  # 告诉Qt：高度依赖宽度
   
   def heightForWidth(self, width):
       # 计算给定宽度下的精确高度
       document = self.document().clone()
       document.setTextWidth(width - margins)
       return document.size().height() + margins
   ```

2. **自动更新机制**
   ```python
   self.textChanged.connect(self.updateGeometry)
   ```

3. **最小高度保证**
   ```python
   minimum_height = font_metrics.lineSpacing() * self._minimum_lines
   content_height = max(document_height, minimum_height)
   ```

### 与原生QTextEdit的区别

| 特性 | QTextEdit | AutoResizingTextEdit |
|------|-----------|---------------------|
| 高度控制 | 固定或手动设置 | ✅ 根据内容自动调整 |
| 布局集成 | 需要额外处理 | ✅ 完美集成Qt布局 |
| 最小高度 | 不支持 | ✅ 支持最小行数设置 |
| 文本截断 | 可能发生 | ✅ 绝对不会截断 |

## 🔄 本地修改记录

**集成到BioNexus时的修改：**
- ✅ 添加了详细的中文注释
- ✅ 增加了 `create_auto_resizing_text_edit()` 便捷函数
- ✅ 添加了 `setMinimumLines()` 最小行数功能
- ✅ 重写了 `setPlainText()` 和 `setHtml()` 确保立即更新
- ✅ 保持了原始API的100%兼容性

**未修改的部分：**
- 核心算法逻辑保持原样
- API接口完全兼容
- 原始功能特性不变

## ⚠️ 使用注意事项

1. **布局要求**
   - 必须放在支持动态尺寸的布局中（如QVBoxLayout）
   - 避免设置固定高度（会覆盖自动调整功能）

2. **性能考虑**
   - 文本内容变化时会触发重新计算，大量文本可能影响性能
   - 建议对超长文本进行分页或截断处理

3. **样式设置**
   - 内边距和边距会影响高度计算，设置样式后测试显示效果
   - 行间距设置会影响最小行数的实际高度

## 🧪 测试验证

**已验证的场景：**
- ✅ 短文本（1-2行）正确显示
- ✅ 长文本（多行）自动换行和调整
- ✅ 动态修改内容实时更新高度
- ✅ 最小行数限制正常工作
- ✅ 在QVBoxLayout中正确集成
- ✅ 响应式布局兼容性良好

## 📞 技术支持

**原项目问题**：请参考 [GitHub Issues](https://github.com/cameel/auto-resizing-text-edit/issues)

**BioNexus集成问题**：
- 查看本项目的开发者文档
- 检查 `vendor/LICENSES.md` 了解使用限制
- 参考详情页面的实际使用示例

---

**维护状态**: ✅ 活跃维护  
**最后测试**: 2025-09-01  
**兼容版本**: PyQt5 5.15+