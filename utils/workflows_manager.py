"""
Workflows Manager
管理“工作流（分层集合）”的数据读写、增删改查与排序。
工作流仅为工具集合，不涉及执行编排与数据传递。
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class ToolRef:
    tool_name: str
    note: str = ""


@dataclass
class Workflow:
    id: str
    name: str
    description: str = ""
    tools: List[ToolRef] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Workflow":
        tools = [ToolRef(**t) if not isinstance(t, ToolRef) else t for t in data.get('tools', [])]
        return Workflow(
            id=data.get('id') or str(uuid.uuid4()),
            name=data.get('name', '未命名工作流'),
            description=data.get('description', ''),
            tools=tools,
            created_at=data.get('created_at') or datetime.now().isoformat(),
            updated_at=data.get('updated_at') or datetime.now().isoformat(),
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['tools'] = [asdict(t) for t in self.tools]
        return d


class WorkflowsManager:
    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_file = self.config_dir / 'workflows.json'
        self.prefs_file = self.config_dir / 'workflows_prefs.json'
        self._workflows: List[Workflow] = []
        self._prefs: Dict[str, Any] = {}
        self.load()

    # -------------------- Persistence --------------------
    def load(self):
        # Workflows
        if self.workflows_file.exists():
            try:
                data = json.load(self.workflows_file.open('r', encoding='utf-8'))
                self._workflows = [Workflow.from_dict(w) for w in data.get('workflows', [])]
            except Exception:
                self._workflows = []
        else:
            self._workflows = []
            self.save()

        # Prefs
        if self.prefs_file.exists():
            try:
                self._prefs = json.load(self.prefs_file.open('r', encoding='utf-8'))
            except Exception:
                self._prefs = {}
        else:
            self._prefs = {}
            self.save_prefs()

    def save(self):
        try:
            data = {
                'version': 1,
                'workflows': [w.to_dict() for w in self._workflows]
            }
            json.dump(data, self.workflows_file.open('w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception:
            pass

    def save_prefs(self):
        try:
            json.dump(self._prefs, self.prefs_file.open('w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception:
            pass

    # -------------------- Queries --------------------
    def list_workflows(self) -> List[Workflow]:
        return list(self._workflows)

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        for w in self._workflows:
            if w.id == workflow_id:
                return w
        return None

    # -------------------- Mutations --------------------
    def create_workflow(self, name: str, description: str = "") -> Workflow:
        wf = Workflow(id=str(uuid.uuid4()), name=name.strip() or '未命名工作流', description=description.strip())
        self._workflows.append(wf)
        self.save()
        return wf

    def rename_workflow(self, workflow_id: str, new_name: str):
        wf = self.get_workflow(workflow_id)
        if wf:
            wf.name = new_name.strip() or wf.name
            wf.updated_at = datetime.now().isoformat()
            self.save()

    def duplicate_workflow(self, workflow_id: str) -> Optional[Workflow]:
        wf = self.get_workflow(workflow_id)
        if not wf:
            return None
        copy = Workflow(
            id=str(uuid.uuid4()),
            name=f"{wf.name} (副本)",
            description=wf.description,
            tools=[ToolRef(t.tool_name, t.note) for t in wf.tools]
        )
        self._workflows.append(copy)
        self.save()
        return copy

    def delete_workflow(self, workflow_id: str):
        self._workflows = [w for w in self._workflows if w.id != workflow_id]
        self.save()

    def add_tool(self, workflow_id: str, tool_name: str, note: str = "") -> bool:
        wf = self.get_workflow(workflow_id)
        if not wf:
            return False
        wf.tools.append(ToolRef(tool_name=tool_name, note=note))
        wf.updated_at = datetime.now().isoformat()
        self.save()
        return True

    def remove_tool(self, workflow_id: str, index: int) -> bool:
        wf = self.get_workflow(workflow_id)
        if not wf:
            return False
        if 0 <= index < len(wf.tools):
            del wf.tools[index]
            wf.updated_at = datetime.now().isoformat()
            self.save()
            return True
        return False

    def move_tool(self, workflow_id: str, index: int, direction: int) -> bool:
        """direction: -1 上移, +1 下移"""
        wf = self.get_workflow(workflow_id)
        if not wf:
            return False
        new_index = index + direction
        if 0 <= index < len(wf.tools) and 0 <= new_index < len(wf.tools):
            wf.tools[index], wf.tools[new_index] = wf.tools[new_index], wf.tools[index]
            wf.updated_at = datetime.now().isoformat()
            self.save()
            return True
        return False

    # -------------------- Preferences --------------------
    def is_add_confirm_suppressed_today(self) -> bool:
        d = self._prefs.get('suppress_add_confirm_until')
        if not d:
            return False
        try:
            return date.fromisoformat(d) >= date.today()
        except Exception:
            return False

    def suppress_add_confirm_today(self):
        self._prefs['suppress_add_confirm_until'] = date.today().isoformat()
        self.save_prefs()

