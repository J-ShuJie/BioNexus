# 工具使用时间跟踪功能

## 概述

BioNexus 1.2.27+ 实现了完整的工具使用时间跟踪功能，能够自动记录每个工具的启动、运行和关闭时间，并累计总使用时长。

## 功能特性

### ✓ 自动记录
- 工具启动时自动开始跟踪
- 工具关闭时自动停止并更新统计
- 无需用户手动操作

### ✓ 精确监控
- 使用进程ID (PID) 进行精确跟踪
- 后台线程定期检查进程状态（默认5秒间隔）
- 支持长时间运行的GUI工具（Cytoscape、IGV等）

### ✓ 持久化存储
- 自动保存到配置文件 `~/.bionexus/tools.json`
- 记录两个关键数据：
  - `last_used`: 最后使用时间（ISO 8601格式）
  - `total_runtime`: 总运行时长（秒）

### ✓ UI显示
- 工具详情页面显示累计使用时间
- 格式：X小时Y分钟

## 架构设计

### 核心组件

#### 1. `ToolUsageTracker` (utils/tool_usage_tracker.py)
负责工具使用时间的跟踪和监控：

```python
class ToolUsageTracker:
    """
    工具使用时间跟踪器

    功能：
    - 记录工具启动时间
    - 后台监控进程状态
    - 计算并更新使用时长
    - 保存到配置文件
    """
```

**关键方法**：
- `start_tracking(tool_name, pid)` - 开始跟踪
- `stop_tracking(tool_name)` - 停止跟踪
- `_monitor_processes()` - 后台监控（线程）
- `_update_tool_usage_stats()` - 更新统计

#### 2. `ToolManager` (core/tool_manager.py)
集成跟踪器：

```python
def launch_tool(self, tool_name: str) -> bool:
    # ... 启动工具 ...

    # 开始跟踪
    if self.usage_tracker:
        pid = self._get_tool_process_pid(tool_name)
        self.usage_tracker.start_tracking(tool_name, pid)
```

#### 3. `ConfigManager` (data/config.py)
负责数据持久化：

```python
# tools.json 中的数据结构
{
  "name": "Cytoscape",
  "last_used": "2025-01-20T14:30:00",
  "total_runtime": 3600,  # 秒
  ...
}
```

## 工作流程

### 启动流程

```
用户点击"启动"
    ↓
ToolManager.launch_tool()
    ↓
工具实例.launch()
    ↓
获取进程PID
    ↓
ToolUsageTracker.start_tracking(tool_name, pid)
    ↓
创建 ToolUsageSession
    ↓
启动后台监控线程（如果未启动）
```

### 监控流程

```
后台监控线程（每5秒）
    ↓
遍历所有活动会话
    ↓
检查进程是否还在运行（通过PID）
    ↓
如果进程已结束:
    - 标记会话结束
    - 计算运行时长
    - 更新配置文件
    - 从活动会话中移除
```

### 数据更新流程

```
进程结束检测
    ↓
计算运行时长 = end_time - start_time
    ↓
读取当前 total_runtime
    ↓
new_runtime = current_runtime + session_duration
    ↓
更新 tools.json:
    - last_used = session.end_time
    - total_runtime = new_runtime
    ↓
保存配置文件
    ↓
触发回调（如果有）
```

## 进程检测策略

### 1. 精确检测（推荐）
如果能获取到PID，使用 `psutil.Process(pid).is_running()` 进行精确检测。

### 2. 进程名检测（后备）
如果无法获取PID，通过进程名模糊匹配：

```python
process_name_map = {
    'Cytoscape': ['cytoscape.exe', 'java.exe'],
    'IGV': ['igv.exe', 'java.exe'],
    'FastQC': ['fastqc.exe', 'java.exe'],
    ...
}
```

**注意**：进程名检测不太准确，可能误判。

## 获取PID的方法

```python
def _get_tool_process_pid(self, tool_name: str) -> Optional[int]:
    """
    启动后立即查找最近创建的匹配进程

    策略：
    1. 等待0.5秒让进程完全启动
    2. 遍历所有进程
    3. 匹配进程名
    4. 只考虑最近10秒内启动的进程
    5. 返回最新的进程PID
    """
```

## 配置选项

### 监控间隔

可以在创建 `ToolUsageTracker` 时指定：

```python
tracker = ToolUsageTracker(config_manager, check_interval=5)  # 5秒检查一次
```

**推荐值**：
- 快速检测：2-3秒
- 平衡模式：5秒（默认）
- 节能模式：10秒

## 数据格式

### tools.json 示例

```json
[
  {
    "name": "Cytoscape",
    "category": "visualization",
    "status": "installed",
    "last_used": "2025-01-20T14:30:00.123456",
    "total_runtime": 7200,
    "...": "..."
  }
]
```

### 运行时长显示格式

```python
runtime = 7265  # 秒
hours = runtime // 3600  # 2
minutes = (runtime % 3600) // 60  # 1
seconds = runtime % 60  # 5

# 显示: "2小时1分钟"
```

## 测试

### 运行测试脚本

```bash
python test_usage_tracker.py
```

**测试选项**：
1. 基本跟踪功能测试（不需要真实工具）
2. 真实工具跟踪测试（需要手动启动 Cytoscape）

### 手动测试步骤

1. 启动 BioNexus
2. 启动任意已安装的工具（如 Cytoscape）
3. 运行工具一段时间
4. 关闭工具
5. 查看 `~/.bionexus/tools.json` 文件
6. 验证 `last_used` 和 `total_runtime` 已更新

## 注意事项

### 1. 依赖项

需要安装 `psutil`：

```bash
pip install psutil
```

### 2. 权限问题

在某些系统上，访问进程信息可能需要管理员权限。如果遇到 `AccessDenied` 错误，是正常现象，跟踪器会自动回退到进程名检测。

### 3. Java 工具特殊处理

对于 Java 工具（Cytoscape、IGV、FastQC），主进程名是 `java.exe`，可能与其他 Java 应用混淆。建议在启动时尽快获取PID以提高准确性。

### 4. 应用关闭

当用户关闭 BioNexus 时，`ToolManager.cleanup()` 会被调用，自动停止所有跟踪并保存数据。

## 扩展功能

### 自定义回调

可以设置回调函数，在使用时间更新时执行自定义操作：

```python
def on_usage_updated(tool_name: str, new_runtime: int):
    print(f"{tool_name} 总使用时间已更新: {new_runtime}秒")

tracker.on_usage_updated = on_usage_updated
```

### 获取活动会话信息

```python
# 获取所有活动会话
sessions = tracker.get_active_sessions()

# 获取特定工具的会话信息
info = tracker.get_session_info("Cytoscape")
if info:
    print(f"Cytoscape 已运行 {info['current_duration']} 秒")
```

## 故障排除

### 问题：跟踪器无法检测到工具关闭

**可能原因**：
- PID 获取失败
- 进程名不匹配

**解决方案**：
1. 检查日志：`ToolManager` 会记录PID获取情况
2. 添加或更新进程名映射
3. 调整监控间隔

### 问题：使用时间不准确

**可能原因**：
- 进程启动延迟
- 多个同名进程

**解决方案**：
- 确保在工具启动后立即获取PID
- 使用更精确的进程匹配规则

## 未来改进

- [ ] 支持更多工具的进程名映射
- [ ] 提供实时使用时间显示（在工具卡片上）
- [ ] 添加使用统计报表功能
- [ ] 支持按日期范围统计使用时长
- [ ] 导出使用报告功能
