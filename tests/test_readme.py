from pathlib import Path

from pytest import CaptureFixture
from pytest import MonkeyPatch

from check_markdown_links import entry_point

project_root_path = Path(__file__).parent.parent


def test_readme_contains_usage(
    capsys: CaptureFixture[str], monkeypatch: MonkeyPatch
) -> None:
    """
    Run the `check-markdown-links --help' and check that the output
    is contained verbatim in the readme.
    """
    readme_path = project_root_path / "readme.md"
    monkeypatch.setenv("COLUMNS", "80")
    monkeypatch.setattr("sys.argv", ["check-markdown-links", "--help"])

    try:
        entry_point()
    except SystemExit:
        pass

    usage_block = f"```\n" f"{capsys.readouterr().out.strip()}\n" f"```"

    print(f"Expecting {readme_path} the following block:\n" f"\n" f"{usage_block}")

    assert usage_block in readme_path.read_text()
