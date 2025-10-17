# BioNexus 1.2.9 全面日志系统

## 概述

BioNexus 1.2.9 引入了全面的日志记录系统，确保捕获所有错误、性能信息和操作记录，方便问题诊断和性能优化。

## 日志系统架构

### 1. 多层日志系统
- **comprehensive_logger.py**: 主要的全面日志系统，捕获所有类型的事件
- **unified_logger.py**: 统一日志管理器，向后兼容现有代码
- **error_handler.py**: 专门的错误处理和异常捕获
- **helpers.py**: 基础日志配置

### 2. 日志文件结构

```
logs/
└── YYYY-MM-DD/
    └── session_YYYYMMDD_HHMMSS/
        ├── startup.log          # 启动过程记录
        ├── runtime.log          # 运行时日志
        ├── errors.log           # 错误和异常
        ├── qt_errors.log        # Qt框架相关错误
        ├── ui_operations.log    # UI操作记录
        ├── performance.log      # 性能指标
        ├── debug.log           # 调试信息
        ├── system_info.log     # 系统信息
        ├── session_summary.txt # 会话总结
        └── crash_report_*.json # 崩溃报告（如有）
```

## 主要功能

### 1. 全面错误捕获
- **Python异常**: 所有未处理的Python异常都会被捕获并记录
- **Qt错误**: PyQt5框架的所有错误和警告都会被记录
- **模块导入错误**: 记录所有模块导入的成功/失败状态
- **启动错误**: 详细记录应用启动过程中的所有问题

### 2. 性能监控
- **启动时间**: 监控各个启动阶段的耗时
- **操作响应时间**: 记录UI操作的响应时间
- **资源使用**: 监控内存和CPU使用情况

### 3. 用户操作记录
- **界面操作**: 记录用户的所有界面操作
- **工具管理**: 记录工具的安装、启动、删除等操作
- **设置变更**: 记录用户设置的变更

## 使用方法

### 1. 基本使用

```python
from utils.comprehensive_logger import get_comprehensive_logger

logger = get_comprehensive_logger()

# 记录错误
logger.log_error("操作类型", "错误描述", {"context": "额外信息"})

# 记录UI操作
logger.log_ui_operation("按钮点击", "主窗口.安装按钮", {"tool": "FastQC"})

# 记录性能
logger.log_performance("工具启动", 1250.5, {"tool": "FastQC"})
```

### 2. 性能监控

```python
from utils.comprehensive_logger import PerformanceTimer

# 使用上下文管理器自动计时
with PerformanceTimer("数据库查询"):
    # 执行需要监控的操作
    result = database.query()
```

### 3. 启动阶段记录

```python
logger.log_startup_phase("模块加载", "UI组件初始化完成", True)
logger.log_startup_phase("数据库连接", "连接失败: 超时", False)
```

## 错误报告

### 1. 自动错误报告
当发生严重错误时，系统会自动创建详细的错误报告：
- **崩溃报告**: JSON格式，包含完整的错误信息和系统状态
- **会话总结**: 文本格式，包含整个会话的统计信息
- **紧急日志**: 当日志系统本身出错时的备用记录

### 2. 手动错误报告
```python
logger = get_comprehensive_logger()
report_path = logger.create_summary_report()
print(f"错误报告已生成: {report_path}")
```

## 日志查看和分析

### 1. 查看最新日志
```bash
# 查看今天的日志目录
ls logs/$(date +%Y-%m-%d)/

# 查看最新会话的错误日志
tail -f logs/$(date +%Y-%m-%d)/session_*/errors.log
```

### 2. 分析常见问题
- **启动失败**: 查看 `startup.log` 和 `errors.log`
- **性能问题**: 查看 `performance.log`
- **UI问题**: 查看 `ui_operations.log` 和 `qt_errors.log`
- **崩溃分析**: 查看 `crash_report_*.json`

## 配置选项

### 1. 日志级别
可以通过环境变量控制日志详细程度：
```bash
export BIONEXUS_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 2. 日志保留策略
系统会自动管理日志文件：
- 保留最近30天的日志
- 每个会话的日志独立存储
- 自动压缩超过7天的日志文件

## 故障排除

### 1. 日志系统本身的问题
如果日志系统出现问题，会创建紧急备用日志：
- `emergency_startup_error_*.log`
- `critical_startup_error_*.log`

### 2. 权限问题
如果无法写入日志目录，检查：
- 应用程序目录的写入权限
- 磁盘空间是否充足
- 防病毒软件是否阻止文件创建

## 最佳实践

### 1. 开发者
- 在关键操作前后添加日志记录
- 使用适当的日志级别
- 提供有意义的上下文信息

### 2. 用户
- 遇到问题时，首先查看最新的日志文件
- 提交bug报告时附带相关的日志文件
- 定期清理过期的日志文件

## API参考

### ComprehensiveLogger类

#### 主要方法
- `log_error(error_type, message, context=None)`: 记录错误
- `log_startup_phase(phase, details="", success=True)`: 记录启动阶段
- `log_ui_operation(operation, component, details=None)`: 记录UI操作
- `log_performance(operation, duration_ms, details=None)`: 记录性能
- `log_debug(component, message, data=None)`: 记录调试信息
- `create_summary_report()`: 创建会话总结报告
- `close_session()`: 关闭当前会话

#### 工具函数
- `get_comprehensive_logger()`: 获取全局日志实例
- `init_comprehensive_logging(app_version)`: 初始化日志系统
- `PerformanceTimer(operation_name)`: 性能计时上下文管理器

## 版本历史

### v1.2.9
- 引入全面日志系统
- 添加Qt错误捕获
- 实现性能监控
- 自动错误报告生成

### v1.1.12
- 基础日志功能
- 简单错误记录

---

**注意**: 日志文件可能包含敏感信息，在分享日志时请注意隐私保护。