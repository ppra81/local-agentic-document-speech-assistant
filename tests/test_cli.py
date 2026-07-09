from typer.testing import CliRunner

from assistant.cli import app


def test_cli_command_works():
    result = CliRunner().invoke(app, ["search", "total"])
    assert result.exit_code == 0
    assert "results" in result.output

