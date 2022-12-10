from pathlib import Path


ROOT_PATH = Path(__file__).parent.parent

CODE_PATHS = [
    str(p)
    for p in [
        ROOT_PATH / "bodkin",
    ]
]


def test_black():
    import runpy
    import sys

    old_args = sys.argv[:]
    format_changes = False
    try:
        sys.argv = ["black", "--check", *CODE_PATHS]
        runpy.run_module("black")
    except SystemExit as exit_:
        format_changes = exit_.code != 0
    finally:
        sys.argv = old_args
    assert not format_changes
