# 工具使用时间跟踪 - 代码逻辑详解

## 📊 数据存储单位

### 核心存储格式

**配置文件中使用 `秒` 作为存储单位**：

```json
{
  "name": "Cytoscape",
  "total_runtime": 3600,  // 单位：秒
  "last_used": "2025-01-20T14:30:00"  // ISO 8601 格式
}
```

**为什么用秒？**
- ✅ 精度高：可以记录短时间使用（如测试工具）
- ✅ 标准化：便于计算和转换
- ✅ 累加简单：直接相加即可

---

## 🔄 完整代码流程

### 情况 1️⃣: 用户启动工具（成功获取 PID）

```python
# 步骤 1: 用户点击启动按钮
用户点击 "启动 Cytoscape"
    ↓
# 步骤 2: ToolManager 调用 launch_tool
def launch_tool(self, tool_name: str):
    tool_instance = self.registry.get_tool(tool_name)  # 获取 Cytoscape 实例
    success = tool_instance.launch()  # 启动 Cytoscape

    if success:
        # 步骤 3: 获取进程 PID
        pid = self._get_tool_process_pid(tool_name)  # 例如: 12345

        # 步骤 4: 开始跟踪
        self.usage_tracker.start_tracking("Cytoscape", 12345)
```

#### 详细步骤：

**步骤 3: 获取进程 PID**
```python
def _get_tool_process_pid(self, tool_name: str):
    import psutil
    import time

    # 等待进程完全启动
    time.sleep(0.5)

    # 查找进程
    current_time = time.time()
    candidates = []

    for proc in psutil.process_iter(['pid', 'name', 'create_time']):
        proc_name = proc.info['name']

        # 匹配进程名（例如 'cytoscape.exe'）
        if 'cytoscape' in proc_name.lower():
            # 只考虑最近 10 秒内启动的进程
            if current_time - proc.info['create_time'] < 10:
                candidates.append((proc.info['pid'], proc.info['create_time']))

    # 返回最新的进程
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]  # 返回 PID，例如 12345

    return None  # 未找到
```

**步骤 4: 开始跟踪**
```python
def start_tracking(self, tool_name: str, pid: int):
    # 创建使用会话
    session = ToolUsageSession(tool_name, pid)
    session.start_time = datetime.now()  # 例如: 2025-01-20 14:30:00
    session.is_active = True

    # 保存到活动会话
    self.active_sessions["Cytoscape"] = session

    # 启动监控线程（如果未启动）
    if not self.is_monitoring:
        self._start_monitor_thread()
```

---

### 情况 2️⃣: 后台监控检测进程（进程仍在运行）

```python
# 监控线程每 5 秒执行一次
def _monitor_processes(self):
    while self.is_monitoring:
        time.sleep(5)  # 等待 5 秒

        # 检查每个活动会话
        for tool_name, session in self.active_sessions.items():
            # 例如: tool_name = "Cytoscape", session.pid = 12345

            # 检查进程是否还在运行
            if self._is_process_running(session.pid):
                # ✓ 进程仍在运行，继续监控
                current_duration = session.get_current_duration()
                # 例如: 已运行 150 秒
                print(f"Cytoscape 已运行 {current_duration} 秒")
            else:
                # ✗ 进程已结束，触发结束流程
                self._end_session(tool_name)
```

#### 进程检查逻辑：

```python
def _is_process_running(self, pid: int) -> bool:
    try:
        process = psutil.Process(pid)
        return process.is_running()  # True or False
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False  # 进程不存在或无权限访问
```

---

### 情况 3️⃣: 检测到工具关闭

```python
# 监控线程检测到进程已结束
def _monitor_processes(self):
    # ... 在循环中检测到进程不存在
    if not self._is_process_running(12345):
        # 触发结束流程
        self._end_session("Cytoscape")
```

#### 结束会话流程：

```python
def _end_session(self, tool_name: str):
    session = self.active_sessions["Cytoscape"]

    # 步骤 1: 标记结束时间
    session.end_time = datetime.now()  # 例如: 2025-01-20 14:35:00
    session.is_active = False

    # 步骤 2: 计算运行时长
    duration = session.end_time - session.start_time
    session.duration_seconds = int(duration.total_seconds())  # 例如: 300 秒

    # 步骤 3: 更新配置文件
    self._update_tool_usage_stats("Cytoscape", session)

    # 步骤 4: 移除活动会话
    del self.active_sessions["Cytoscape"]
```

---

### 情况 4️⃣: 更新配置文件

```python
def _update_tool_usage_stats(self, tool_name: str, session: ToolUsageSession):
    # 步骤 1: 查找工具数据
    tools = self.config_manager.tools
    for tool in tools:
        if tool['name'] == "Cytoscape":
            tool_data = tool
            break

    # 步骤 2: 更新 last_used
    tool_data['last_used'] = session.end_time.isoformat()
    # 结果: "2025-01-20T14:35:00"

    # 步骤 3: 累加 total_runtime
    current_runtime = tool_data.get('total_runtime', 0)  # 例如: 1200 秒（之前的累计）
    new_runtime = current_runtime + session.duration_seconds  # 1200 + 300 = 1500 秒
    tool_data['total_runtime'] = new_runtime

    # 步骤 4: 保存到配置文件
    self.config_manager.save_tools()
    # 写入 ~/.bionexus/tools.json
```

**配置文件更新结果**：
```json
{
  "name": "Cytoscape",
  "total_runtime": 1500,  // 累加后的总时长（秒）
  "last_used": "2025-01-20T14:35:00"
}
```

---

### 情况 5️⃣: 用户启动工具（无法获取 PID）

```python
def launch_tool(self, tool_name: str):
    success = tool_instance.launch()

    if success:
        # 尝试获取 PID
        pid = self._get_tool_process_pid(tool_name)  # 返回 None

        # 即使没有 PID，也开始跟踪
        self.usage_tracker.start_tracking("Cytoscape", None)
```

#### 无 PID 的监控流程：

```python
def _monitor_processes(self):
    for tool_name, session in self.active_sessions.items():
        if session.pid:
            # 有 PID，使用精确检测
            if not self._is_process_running(session.pid):
                self._end_session(tool_name)
        else:
            # 没有 PID，使用进程名检测（不太准确）
            if not self._is_tool_process_running(tool_name):
                self._end_session(tool_name)
```

**进程名检测逻辑**：
```python
def _is_tool_process_running(self, tool_name: str) -> bool:
    # 进程名映射
    process_name_map = {
        'Cytoscape': ['cytoscape.exe', 'java.exe'],
        'IGV': ['igv.exe', 'java.exe'],
    }

    possible_names = process_name_map.get(tool_name, [])

    # 遍历所有进程
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] in possible_names:
            return True  # 找到匹配的进程

    return False  # 没有找到
```

**问题**：可能会误判（如果系统中有其他 Java 进程）

---

### 情况 6️⃣: 应用关闭时的清理

```python
# 用户关闭 BioNexus 主窗口
def closeEvent(self, event):
    # 调用清理方法
    self.tool_manager.cleanup()
    event.accept()

# ToolManager 的清理
def cleanup(self):
    if self.usage_tracker:
        # 停止所有跟踪
        self.usage_tracker.stop_all_tracking()
```

#### 停止所有跟踪：

```python
def stop_all_tracking(self):
    # 遍历所有活动会话
    for tool_name in list(self.active_sessions.keys()):
        # 标记结束
        session = self.active_sessions[tool_name]
        session.mark_ended()

        # 更新统计
        self._update_tool_usage_stats(tool_name, session)

    # 停止监控线程
    self.is_monitoring = False
```

**效果**：即使用户没有手动关闭工具，BioNexus 关闭时也会保存所有使用时间。

---

### 情况 7️⃣: 工具异常崩溃

```python
# 监控线程会自动检测
def _monitor_processes(self):
    time.sleep(5)

    # 检查进程
    if not self._is_process_running(pid):
        # 进程不存在（可能崩溃了）
        self._end_session(tool_name)
        # 自动保存使用时间
```

**效果**：即使工具崩溃，使用时间仍会被记录。

---

### 情况 8️⃣: 同一工具多次启动

```python
def start_tracking(self, tool_name: str, pid: int):
    # 检查是否已有活动会话
    if tool_name in self.active_sessions:
        # 先结束旧会话
        self._end_session(tool_name)

    # 创建新会话
    session = ToolUsageSession(tool_name, pid)
    self.active_sessions[tool_name] = session
```

**效果**：
- 旧会话会被正确结束并保存
- 新会话从头开始计时
- 不会丢失任何使用时间

---

## 🧮 时间计算示例

### 示例 1: 短时间使用

```python
# 启动时间: 2025-01-20 14:30:00
# 结束时间: 2025-01-20 14:30:45
# 运行时长: 45 秒

duration = end_time - start_time
duration_seconds = int(duration.total_seconds())  # 45

# 保存到配置文件
tool_data['total_runtime'] = 0 + 45  # 45 秒
```

### 示例 2: 长时间使用

```python
# 启动时间: 2025-01-20 14:00:00
# 结束时间: 2025-01-20 16:30:00
# 运行时长: 2.5 小时

duration = end_time - start_time
duration_seconds = int(duration.total_seconds())  # 9000 秒

# 保存到配置文件
tool_data['total_runtime'] = 0 + 9000  # 9000 秒
```

### 示例 3: 多次累加

```python
# 第一次使用: 300 秒（5 分钟）
total_runtime = 0 + 300  # 300

# 第二次使用: 600 秒（10 分钟）
total_runtime = 300 + 600  # 900

# 第三次使用: 3600 秒（1 小时）
total_runtime = 900 + 3600  # 4500

# 最终: 4500 秒 = 1 小时 15 分钟
```

---

## 🔍 边界情况处理

### 1. 进程查找失败

```python
pid = self._get_tool_process_pid(tool_name)  # 返回 None

if pid:
    # 使用 PID 跟踪（精确）
    self.usage_tracker.start_tracking(tool_name, pid)
else:
    # 使用进程名跟踪（模糊）
    self.usage_tracker.start_tracking(tool_name, None)
```

### 2. 权限不足

```python
try:
    process = psutil.Process(pid)
    return process.is_running()
except psutil.AccessDenied:
    # 无法访问进程信息
    # 回退到进程名检测
    return self._is_tool_process_running(tool_name)
```

### 3. 进程启动延迟

```python
def _get_tool_process_pid(self, tool_name: str):
    # 等待进程完全启动
    time.sleep(0.5)

    # 只查找最近 10 秒内启动的进程
    if current_time - proc.info['create_time'] < 10:
        candidates.append(proc)
```

### 4. 配置文件损坏

```python
def _update_tool_usage_stats(self, tool_name: str, session):
    try:
        # 更新并保存
        self.config_manager.save_tools()
    except Exception as e:
        # 记录错误但不崩溃
        self.logger.error(f"保存失败: {e}")
```

---

## 📈 性能考虑

### 监控频率

```python
check_interval = 5  # 默认 5 秒检查一次

# 为什么选择 5 秒？
# - 太频繁（1秒）: 浪费 CPU 资源
# - 太慢（30秒）: 可能延迟检测工具关闭
# - 5秒: 平衡性能和响应速度
```

### 线程安全

```python
with self._lock:
    # 访问和修改活动会话时使用锁
    session = self.active_sessions[tool_name]
```

### 内存占用

```python
# 每个会话对象很小
class ToolUsageSession:
    tool_name: str        # ~50 bytes
    pid: int              # 8 bytes
    start_time: datetime  # 24 bytes
    end_time: datetime    # 24 bytes
    duration_seconds: int # 8 bytes

    # 总计: ~120 bytes per session
    # 即使 100 个活动会话，也只占用 ~12 KB
```

---

## 🛡️ 错误处理

所有关键操作都有 try-except：

```python
try:
    # 获取 PID
    pid = self._get_tool_process_pid(tool_name)
except Exception as e:
    self.logger.warning(f"获取PID失败: {e}")
    pid = None  # 使用 None 继续

try:
    # 检查进程
    is_running = self._is_process_running(pid)
except Exception as e:
    self.logger.error(f"检查进程失败: {e}")
    is_running = False  # 假设已结束

try:
    # 保存配置
    self.config_manager.save_tools()
except Exception as e:
    self.logger.error(f"保存失败: {e}")
    # 不阻止程序继续运行
```

**原则**：即使某个步骤失败，也不影响整体功能运行。
