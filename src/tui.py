from __future__ import annotations

"""
Minimal Textual TUI stub for flows dashboard.
Launch with: uv run --with textual --with textual-dev python -m src.tui
"""

from typing import Iterable

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive


class StatusLog(Static):
    lines = reactive(list[str])

    def on_mount(self) -> None:
        self.lines = []

    def write(self, text: str) -> None:
        self.lines.append(text)
        self.update("\n".join(self.lines[-200:]))


class FlowApp(App):
    CSS = """
    Screen { layout: vertical; }
    #id-status { height: 1fr; border: solid $accent 10%; padding: 1; }
    """

    BINDINGS = [
        ("p", "plan", "Plan"),
        ("v", "validate", "Validate"),
        ("r", "run", "Run"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield StatusLog(id="status")
        yield Footer()

    def action_quit(self) -> None:
        self.exit()

    def _log(self, text: str) -> None:
        self.query_one(StatusLog).write(text)

    def action_validate(self) -> None:
        self._log("validate: TODO (wire to CLI validate)")

    def action_plan(self) -> None:
        self._log("plan: TODO (wire to CLI plan)")

    def action_run(self) -> None:
        self._log("run: TODO (wire to Runner streaming)")


if __name__ == "__main__":
    FlowApp().run()

