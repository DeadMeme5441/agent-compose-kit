from __future__ import annotations

"""
Textual TUI for flows dashboard. Launch with:
  uv run --with textual --with textual-dev python -m src.tui
"""

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive

from .tui.messages import ValidateDone, PlanDone, GraphDone, RunEvent, RunFinished, Error
from .tui import controller


DEFAULT_CONFIG = Path("configs/app.yaml")


class StatusLog(Static):
    lines = reactive(list[str])

    def on_mount(self) -> None:
        self.lines = []

    def write(self, text: str) -> None:
        self.lines.append(text)
        self.update("\n".join(self.lines[-400:]))


class FlowApp(App):
    CSS = """
    Screen { layout: vertical; }
    #id-status { height: 1fr; border: solid $accent 10%; padding: 1; }
    """

    BINDINGS = [
        ("p", "plan", "Plan"),
        ("v", "validate", "Validate"),
        ("g", "graph", "Graph"),
        ("r", "run", "Run"),
        ("q", "quit", "Quit"),
    ]

    config_path = reactive(DEFAULT_CONFIG)

    def compose(self) -> ComposeResult:
        yield Header()
        yield StatusLog(id="status")
        yield Footer()

    def _log(self, text: str) -> None:
        self.query_one(StatusLog).write(text)

    def action_quit(self) -> None:
        self.exit()

    def action_validate(self) -> None:
        ok, detail = controller.validate_config(self.config_path)
        self.post_message(ValidateDone(ok=ok, detail=detail))

    def action_plan(self) -> None:
        try:
            plan_text = controller.plan_config(self.config_path)
            self.post_message(PlanDone(plan_text))
        except Exception as e:  # pragma: no cover
            self.post_message(Error(str(e)))

    def action_graph(self) -> None:
        try:
            graph_text = controller.graph_ascii(self.config_path)
            self.post_message(GraphDone(graph_text))
        except Exception as e:  # pragma: no cover
            self.post_message(Error(str(e)))

    def action_run(self) -> None:
        async def _runner():
            try:
                async for line in controller.run_stream(self.config_path):
                    self.post_message(RunEvent(line))
                self.post_message(RunFinished())
            except Exception as e:  # pragma: no cover
                self.post_message(Error(str(e)))

        asyncio.create_task(_runner())

    # Handlers
    def on_validate_done(self, msg: ValidateDone) -> None:
        self._log(f"validate: {'OK' if msg.ok else 'FAIL'} {msg.detail}")

    def on_plan_done(self, msg: PlanDone) -> None:
        self._log(msg.plan_text)

    def on_graph_done(self, msg: GraphDone) -> None:
        self._log(msg.graph_text)

    def on_run_event(self, msg: RunEvent) -> None:
        self._log(msg.text)

    def on_run_finished(self, msg: RunFinished) -> None:
        self._log("run finished")

    def on_error(self, msg: Error) -> None:
        self._log(f"error: {msg.error}")


if __name__ == "__main__":
    FlowApp().run()
