from __future__ import annotations

from textual.message import Message


class ValidateDone(Message):
    def __init__(self, ok: bool, detail: str = "") -> None:
        self.ok = ok
        self.detail = detail
        super().__init__()


class PlanDone(Message):
    def __init__(self, plan_text: str) -> None:
        self.plan_text = plan_text
        super().__init__()


class GraphDone(Message):
    def __init__(self, graph_text: str) -> None:
        self.graph_text = graph_text
        super().__init__()


class RunEvent(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class RunFinished(Message):
    def __init__(self, summary: str = "") -> None:
        self.summary = summary
        super().__init__()


class Error(Message):
    def __init__(self, error: str) -> None:
        self.error = error
        super().__init__()

