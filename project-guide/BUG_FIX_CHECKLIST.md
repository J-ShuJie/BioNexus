# BioNexus 1.2.2 Bug修复检查清单

## 已修复的常见错误

### ✅ ConfigManager 相关错误
- **错误**: `'ConfigManager' object has no attribute 'save_config'`
- **修复**: 使用 `save_settings()` 替代 `save_config()`
- **文件**: `main.py`, `settings_panel.py`

### ✅ UnifiedLogger 缺失方法
- **错误**: `'UnifiedLogger' object has no attribute 'log_view_switch'`
- **修复**: 添加缺失的方法 `log_view_switch`, `log_user_operation`, `log_tool_operation`
- **文件**: `utils/unified_logger.py`

### ✅ QComboBox set_state 错误
- **错误**: `'QComboBox' object has no attribute 'set_state'`
- **修复**: 在 `load_current_settings()` 中为 QComboBox 使用 `setCurrentText()` 而不是 `set_state()`
- **文件**: `ui/settings_panel.py:684-716`

### ✅ QSizePolicy 导入缺失错误
- **错误**: `name 'QSizePolicy' is not defined`
- **位置**: `ui/settings_panel.py:336`
- **原因**: 使用了 QSizePolicy 但没有导入
- **修复**: 在 PyQt5.QtWidgets 导入中添加 QSizePolicy
- **文件**: `ui/settings_panel.py:20`

### ✅ ConfigManager 覆盖默认路径问题
- **问题**: 配置文件中的空路径覆盖了 Settings.__post_init__ 设置的默认路径
- **现象**: Settings() 直接创建路径正确，但 ConfigManager().settings 路径为空
- **原因**: load_settings() 中 setattr() 无条件覆盖，包括空字符串
- **修复**: 在加载时跳过配置文件中的空路径值，保持默认值
- **文件**: `data/config.py:134-136`

### ✅ QPainterPath.addRoundedRect 类型错误
- **错误**: `addRoundedRect() argument 1 has unexpected type 'QRect'`
- **位置**: `ui/modern_sidebar.py:146,203,283`
- **原因**: QPainterPath.addRoundedRect() 需要 QRectF 类型，而不是 QRect
- **修复**: 导入 QRectF，将所有 QRect 转换为 QRectF(rect)
- **文件**: `ui/modern_sidebar.py:13,146,203,283`

### ✅ ToolCardV2 缺失 set_selected 方法错误
- **错误**: `'ToolCardV2' object has no attribute 'set_selected'`
- **位置**: `ui/main_window.py:563`
- **原因**: ToolCardV2 没有实现选中状态管理
- **修复**: 添加 is_selected 属性和 set_selected() 方法，包含选中样式
- **文件**: `ui/tool_card_v2.py:24,220-238`

### ✅ PyQt5 信号双重连接冲突错误
- **错误**: 按钮点击信号发送但对应函数未执行，或执行异常
- **症状**: 在调试日志中能看到信号发送，但目标函数不被调用
- **原因**: **同一信号被连接了两次**，造成信号槽连接冲突
- **排查方法**: 
  1. 搜索项目中所有 `signal_name.connect()` 调用
  2. 检查是否存在重复连接（通常在不同初始化方法中）
- **典型场景**:
  - `_create_toolbar()` 中连接了信号
  - `setup_connections()` 中又连接了相同信号
- **修复**: 移除重复的信号连接，保留一个即可
- **检查位置**: `ui/main_window.py` 信号连接相关方法
- **实例**: 筛选按钮 `filter_clicked` 信号在两处被连接导致功能失效

### 🔧 正在修复的错误

### ✅ manual_settings_frame 属性错误
- **错误**: `'SettingsPanel' object has no attribute 'manual_settings_frame'`
- **位置**: `ui/settings_panel.py:850`
- **原因**: `_on_update_mode_changed` 方法引用了不存在的属性
- **修复**: 使用控件的 `parent()` 方法直接控制可见性，而不是引用不存在的frame
- **文件**: `ui/settings_panel.py:845-868`

## 常见错误模式

### 1. 属性名称不匹配
- 检查类属性是否在 `__init__` 中正确初始化
- 确保方法调用的属性名称与定义一致

### 2. 方法名称错误
- 检查方法调用是否与实际方法名匹配
- 确保导入的类有所需的方法

### 3. 控件类型处理
- QComboBox 使用 `setCurrentText()` / `setCurrentIndex()`
- 开关控件使用 `set_state()`
- QSpinBox 使用 `setValue()`

### 4. 变量作用域问题
- 在异常处理中避免使用与内置模块同名的变量
- 使用 `import os as os_module` 避免作用域冲突

### 5. PyQt5 信号连接问题
- **重复连接检查**: 同一信号不要在多处连接，容易造成冲突
- **连接位置统一**: 建议统一在 `setup_connections()` 方法中处理
- **调试技巧**: 使用详细日志记录信号发送和接收情况
- **排查方法**: `grep -r "signal_name.connect" .` 查找所有连接点

## 下次修复检查项

1. [ ] 检查所有新增的属性是否在 `__init__` 中初始化
2. [ ] 验证所有方法调用是否存在对应的方法定义
3. [ ] 确认控件类型与调用方法匹配
4. [ ] 测试所有UI控件的状态加载和保存
5. [ ] 检查变量作用域和命名冲突
6. [ ] **检查信号连接是否重复** - 搜索 `.connect(` 确保每个信号只连接一次
7. [ ] 验证信号发送和接收的日志记录是否匹配

## 新增功能

### ✅ 现代化工具栏（与侧边栏中线对齐）
- **设计理念**: 工具栏分界线精确对齐侧边栏搜索框和导航按钮之间的中线
- **高度计算**: 
  - 侧边栏搜索框底部：y=52
  - 侧边栏导航按钮顶部：y=70
  - 中线位置：y=61
  - 工具栏高度：61px
- **视觉优化**:
  - 采用与侧边栏相同的渐变背景
  - 圆角按钮设计，保持界面一致性
  - 数字徽章显示下载数量
  - 悬停动画和按压反馈
- **功能增强**:
  - 自动更新下载计数显示
  - 筛选激活状态视觉反馈
  - 基于 paintEvent 的高性能渲染
- **文件**: `ui/modern_toolbar.py`, `ui/main_window.py:17,234-244,411-423,745-751`

## 新增功能

### ✅ 现代化侧边栏升级（paintEvent 自绘）
- **升级**: 从传统 Qt 控件组合升级为基于 paintEvent 的完全自绘实现
- **风格**: macOS Big Sur 现代化设计，微妙渐变背景 + 圆角按钮
- **功能增强**: 
  - 🎨 自绘渐变背景和毛玻璃效果
  - 📱 圆角搜索框 + 内置搜索图标  
  - ✨ 平滑动画过渡（200ms 缓动效果）
  - 🔤 图标 + 文字组合设计（📋全部工具 ⭐我的工具 ⚙️设置）
  - 💫 悬停状态动画和视觉反馈
- **尺寸优化**: 减小控件和字体大小，更加精致紧凑
  - 搜索框：40px→32px 高度，圆角 20px→16px
  - 导航按钮：50px→40px 间距，字体 14px→11px
  - 最近工具：35px→28px 间距，字体 11px→10px
  - 状态点：6px→4px 直径
- **兼容性**: 保持所有原有 API 接口，无缝替换
- **性能**: 基于 paintEvent 自绘，渲染性能更优
- **文件**: `ui/modern_sidebar.py`，`ui/main_window.py:16,161`

### ✅ 默认路径配置修复
- **问题**: 配置文件中路径为空，不显示现有的 installed_tools 和 envs_cache 目录
- **修复**: 在 Settings.__post_init__ 中自动设置项目相对路径
- **结果**: 
  - `default_install_dir` → `./installed_tools` (已有FastQC等工具)
  - `conda_env_path` → `./envs_cache` (已有java和python环境)
- **文件**: `data/config.py:70-79`

### ✅ 路径显示UI优化（换行布局）
- **问题**: 路径设置控件与标签在同一行，长路径显示不完整
- **修复**: 
  - 为 ResponsiveSettingsItem 添加 vertical_layout 模式
  - 路径输入框使用垂直布局，独占一行显示
  - 使用等宽字体，便于查看路径结构
  - 设置最小宽度，确保长路径能够显示
- **文件**: `ui/responsive_layout.py:335-404`, `ui/settings_panel.py:305,316`

### ✅ 路径输入框+浏览按钮UI改进  
- **改进**: 将路径设置从单纯按钮改为输入框+浏览按钮组合
- **优势**: 
  - 直接显示当前路径值，用户一目了然
  - 支持直接输入修改路径
  - 支持图形化浏览选择路径
  - 实时路径验证（无效路径显示红色边框）
  - 使用等宽字体便于阅读路径
- **影响范围**: 默认安装目录、Conda环境路径设置
- **文件**: `ui/settings_panel.py:320-476`

## 2025-09-04 修复记录

### ✅ QDropShadowEffect 导入错误
- **错误**: `ImportError: cannot import name 'QDropShadowEffect' from 'PyQt5.QtGui'`
- **原因**: 应该是 `QGraphicsDropShadowEffect`，且从 `PyQt5.QtWidgets` 导入
- **修复**: 修改 `modern_filter_card.py` 和 `modern_download_card.py` 的导入语句
- **文件**: `ui/modern_filter_card.py`, `ui/modern_download_card.py`

### ✅ 日志系统增强
- **日志目录优化**: 日志保存在项目本地 `logs` 目录，文件名包含日期
- **新增错误处理器**: `utils/error_handler.py` 提供全局异常捕获和详细日志
- **日志结构**: 主日志、错误日志、崩溃日志、会话日志分离管理
- **文件**: `utils/helpers.py`, `utils/error_handler.py`, `main.py`

---
*最后更新: 2025-09-04*