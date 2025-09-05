from src.main import main


def test_main_prints(capsys):
    main()
    captured = capsys.readouterr()
    assert "Hello from template-agent-builder!" in captured.out

