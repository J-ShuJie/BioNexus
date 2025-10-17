# BioNexus 编码规范与铁律

## 🚫 铁律 (IRON RULES) - 绝对禁止

### ❌ 文本显示组件禁令
**严格禁止使用以下PyQt5组件进行文本显示：**

- `QLabel` - 存在文字截断问题
- `QTextEdit` - 性能差且难以精确控制  
- `QTextBrowser` - 渲染不一致
- `QPlainTextEdit` - 字体问题
- `QLineEdit` - 仅限必要的输入框使用

### ✅ 强制替代方案

**推荐优先级排序：**
1. **🎯 paintEvent自绘制** (最佳方案) - 完全控制，高性能，无截断
2. `smart_text_module.py` 中的智能文本组件
3. `QPushButton` (用于可点击的文本)  
4. 自绘制 `QWidget` (用于复杂文本布局)

**paintEvent绘制模板：**
```python
def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 设置字体和颜色
    font = QFont("微软雅黑", 12)
    painter.setFont(font)
    painter.setPen(QColor("#333333"))
    
    # 绘制文本 (自动处理截断和居中)
    text_rect = self.rect().adjusted(10, 5, -10, -5)
    painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)
```

### 📋 禁令原因
1. **文字截断**: QLabel在固定尺寸容器中经常截断文字
2. **字体渲染**: 在不同DPI和系统上字体显示不一致
3. **布局冲突**: 与响应式布局系统兼容性差
4. **性能问题**: QText系列组件资源消耗大
5. **样式限制**: CSS样式支持有限，难以实现现代化设计

## ⚖️ 编码规范

### 1. 文件头部规范
每个UI文件必须在文档字符串顶部包含铁律声明：

```python
\"\"\"
文件功能描述
==========

⚠️  铁律：禁止使用 QLabel 和 QText 系列组件！
🚫 IRON RULE: NEVER USE QLabel, QTextEdit, QTextBrowser, QPlainTextEdit
✅ 替代方案: 使用 smart_text_module.py 中的智能文本组件
📋 原因: QLabel/QText 存在文字截断、字体渲染、DPI适配等问题
\"\"\"
```

### 2. 组件命名规范
- UI类名: `ModernXxxWidget` 或 `SmartXxxComponent`
- 信号名: `xxx_clicked`, `xxx_changed`  
- 方法名: `_on_xxx_event`, `_update_xxx_state`

### 3. 错误处理规范
所有UI组件必须包含错误处理：

```python
try:
    # UI逻辑
    pass
except Exception as e:
    log_error(f"{self.__class__.__name__}.method_name", e)
    print(f"组件错误: {e}")
```

### 4. 调试信息规范
复杂初始化过程必须包含步骤化调试输出：

```python
def complex_initialization(self):
    print("【DEBUG】步骤1: 描述")
    # 代码
    print("【DEBUG】步骤2: 描述")  
    # 代码
```

## 🛡️ 代码审查检查清单

### UI组件检查
- [ ] 是否使用了禁止的文本组件？
- [ ] 是否包含铁律声明？
- [ ] 信号-槽参数是否匹配？
- [ ] 是否有适当的错误处理？
- [ ] 内存管理是否正确？

### PyQt5特定检查  
- [ ] lambda表达式是否正确捕获变量？
- [ ] CSS选择器是否使用Qt标准类名？
- [ ] widget清理是否使用`setParent(None)`？
- [ ] 是否避免了循环引用？

### 性能检查
- [ ] 是否避免了不必要的重绘？
- [ ] 是否正确使用了布局管理器？
- [ ] 信号连接是否在适当时机断开？

## 🎯 强制执行

### 开发阶段
- 每次提交前运行代码检查脚本
- IDE配置禁止导入相关组件的警告
- 代码审查必须检查铁律遵守情况

### 运行时检查
```python
# 在应用启动时检查
def verify_coding_standards():
    forbidden_imports = ['QLabel', 'QTextEdit', 'QTextBrowser', 'QPlainTextEdit']
    for module in sys.modules.values():
        if hasattr(module, '__file__') and 'ui/' in str(module.__file__):
            for forbidden in forbidden_imports:
                if hasattr(module, forbidden):
                    raise RuntimeError(f"违反铁律: {module.__file__} 导入了禁止的组件 {forbidden}")
```

---

**⚠️ 警告**: 违反铁律将导致难以调试的UI问题，必须严格遵守！
**🎯 目标**: 确保所有文本显示稳定、美观、响应式适配