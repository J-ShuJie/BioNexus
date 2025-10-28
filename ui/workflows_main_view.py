from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal
from .card_grid_container import CardScrollArea
from .workflow_card_v3 import WorkflowCardV3, NewWorkflowPlusCardV3


class WorkflowsMainView(QWidget):
    new_workflow_requested = pyqtSignal()
    open_workflow_requested = pyqtSignal(str)
    rename_workflow_requested = pyqtSignal(str)
    duplicate_workflow_requested = pyqtSignal(str)
    delete_workflow_requested = pyqtSignal(str)

    def __init__(self, workflows_manager, parent=None):
        super().__init__(parent)
        self.workflows_manager = workflows_manager
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.cards = CardScrollArea()
        outer.addWidget(self.cards)

    def refresh(self):
        # 基于 CardGridContainer 重建卡片，保持与“全部工具”相同的网格/边距
        gc = self.cards.grid_container
        for card in getattr(gc, 'cards', [])[:]:
            card.deleteLater()
        gc.cards = []

        # 工作流卡（先放工作流，再把“新建”放到最后）
        workflows = [w.to_dict() if hasattr(w, 'to_dict') else w for w in self.workflows_manager.list_workflows()]
        for wf in workflows:
            card = WorkflowCardV3(wf, gc)
            card.open_requested.connect(self.open_workflow_requested.emit)
            card.rename_requested.connect(self.rename_workflow_requested.emit)
            card.duplicate_requested.connect(self.duplicate_workflow_requested.emit)
            card.delete_requested.connect(self.delete_workflow_requested.emit)
            gc.cards.append(card)
            card.show()

        # 新建工作流卡排在末尾
        plus = NewWorkflowPlusCardV3(gc)
        plus.create_requested.connect(self.new_workflow_requested.emit)
        gc.cards.append(plus)
        plus.show()

        gc._relayout_cards()
