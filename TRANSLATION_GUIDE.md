# BioNexus 多语言系统使用指南

## 📋 系统概述

BioNexus 现在使用**简单的 YAML 多语言系统**，无需外部工具（如 Qt Linguist、lrelease），易于维护和扩展。

### ✅ 支持的语言

- **中文** (zh_CN) - 简体中文
- **英文** (en_US) - English  
- **德语** (de_DE) - Deutsch

---

## 📁 文件结构

```
BioNexus/
├── translations/
│   └── i18n/
│       ├── zh_CN.yaml          # 中文翻译
│       ├── en_US.yaml          # 英文翻译（键值相同，用作源文本）
│       └── de_DE.yaml          # 德文翻译
├── utils/
│   ├── i18n.py                 # 核心翻译系统
│   ├── translator.py           # PyQt5 集成层
│   └── qt_tr_patch.py          # Qt tr() 方法补丁
└── tools/
    ├── ts_to_yaml.py           # .ts 转 YAML 工具
    └── rebuild_yaml_translations.py  # 重建 YAML 文件
```

---

## 🎯 如何使用

### 在代码中使用翻译

所有现有的 `self.tr()` 调用**无需修改**，会自动使用新系统！

```python
# 这些代码不需要修改，自动使用 YAML 翻译
self.setWindowTitle(self.tr("BioNexus Launcher"))
button.setText(self.tr("Settings"))
label.setText(self.tr("All Tools"))
```

### 切换语言

```python
from utils.translator import switch_language

# 切换到中文
switch_language('zh_CN')

# 切换到英文
switch_language('en_US')

# 切换到德语
switch_language('de_DE')
```

---

## 🔧 如何添加新语言

### 步骤 1: 创建翻译文件

复制 `translations/i18n/en_US.yaml` 为新语言文件：

```bash
cp translations/i18n/en_US.yaml translations/i18n/fr_FR.yaml  # 法语示例
```

### 步骤 2: 翻译内容

编辑 `fr_FR.yaml`，将英文值替换为法语：

```yaml
ModernSidebar:
  All Tools: Tous les outils          # 英文 -> 法语
  Settings: Paramètres
  Search bioinformatics tools...: Rechercher des outils...
```

### 步骤 3: 更新支持的语言列表

编辑 `utils/i18n.py`，添加新语言：

```python
SUPPORTED_LANGUAGES = {
    'zh_CN': '简体中文',
    'en_US': 'English',
    'de_DE': 'Deutsch',
    'fr_FR': 'Français',  # 新增
}
```

### 步骤 4: 在设置界面添加选项

编辑 `ui/settings_panel.py` (约 315 行)：

```python
language_combo.addItem("Français", "fr_FR")  # 新增
```

完成！重启应用即可使用新语言。

---

## 📝 YAML 文件格式说明

### 结构

```yaml
ContextName:                    # 组件类名
  English Text: Translated Text # 英文作为键，翻译作为值
```

### 示例

```yaml
ModernSidebar:
  All Tools: 全部工具
  My Tools: 我的工具
  Settings: 设置

MainWindow:
  BioNexus Launcher: BioNexus Launcher
  Installation Failed: 安装失败
```

### 注意事项

1. **英文作为键**：所有翻译文件都使用英文作为键
2. **保持键一致**：所有语言文件中的键必须相同
3. **特殊字符**：YAML 自动处理 Unicode，无需转义

---

## 🛠️ 维护工具

### 从 .ts 文件重新生成 YAML

如果你修改了 `.ts` 文件（使用 Qt Linguist），可以重新生成 YAML：

```bash
python3 tools/rebuild_yaml_translations.py
```

这会：
- 从 `.ts` 文件提取最新翻译
- 重新生成所有 YAML 文件
- 保持英文作为键的结构

---

## 🔍 故障排除

### 翻译没有生效

1. **检查 YAML 文件是否存在**
   ```bash
   ls translations/i18n/
   ```

2. **检查日志**
   查看 `logs/launcher.log`，搜索 "i18n" 或 "Translation"

3. **清理缓存**
   ```bash
   find . -name "__pycache__" -exec rm -rf {} +
   find . -name "*.pyc" -delete
   ```

### 德语翻译是占位符

德语文件 (`de_DE.yaml`) 目前包含占位符文本（带 `[DE]` 后缀）。

**解决方法**: 手动编辑 `translations/i18n/de_DE.yaml`，将英文文本翻译为德语。

---

## 💡 最佳实践

1. **始终使用英文作为源文本**
   在代码中写英文字符串：
   ```python
   self.tr("Settings")  # 好
   self.tr("设置")       # 不好
   ```

2. **保持翻译文件同步**
   添加新文本时，同时更新所有语言文件

3. **使用有意义的上下文**
   相同的英文词在不同上下文可能有不同翻译

4. **定期检查翻译完整性**
   确保所有语言文件包含相同的键

---

## 📚 技术细节

### 工作原理

1. **启动时**:
   - `main.py` 调用 `install_tr_patch()` 
   - 补丁 `QWidget.tr()` 方法使用 YAML 翻译

2. **切换语言时**:
   - `TranslationManager.switch_language()`
   - 更新 `SimpleI18n` 的当前语言
   - 发出 `languageChanged` 信号
   - UI 组件接收信号并刷新

3. **翻译查找**:
   - 使用类名作为上下文
   - 在 YAML 中查找 `ContextName -> English Text`
   - 返回翻译后的文本，或原文（如果未找到）

### 向后兼容

- ✅ 所有现有的 `self.tr()` 调用无需修改
- ✅ 保留 Qt 的信号/槽机制
- ✅ 支持动态语言切换

---

## 🚀 性能

- YAML 文件在启动时一次性加载到内存
- 翻译查找是 O(1) 字典查找
- 三种语言占用内存 < 1MB
- 对应用性能影响可忽略不计

---

**生成日期**: 2025-10-20  
**系统版本**: BioNexus v1.2.20  
**文档维护**: 保持此文档与代码同步更新
