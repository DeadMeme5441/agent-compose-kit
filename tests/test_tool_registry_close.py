from src.tools.registry import ToolRegistry


class _DummyTool:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_tool_registry_close_all(tmp_path):
    specs = {"tools": []}
    reg = ToolRegistry(specs, base_dir=tmp_path)
    dummy = _DummyTool()
    reg._tools_by_id["x"] = dummy  # inject dummy instance
    reg.close_all()
    assert dummy.closed is True

