import os

import pytest

from cgviz import cli, show


def test_defaults():
    a = cli.build_parser().parse_args(["demo"])
    assert (a.cols, a.rows, a.renderer, a.fit, a.out) == (160, 48, None, False, None)
    assert cli.resolve_size(a) == (160, 48)


def test_no_terminal_read_without_fit(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("terminal size read")

    a = cli.build_parser().parse_args(["demo", "--cols", "80", "--rows", "20"])
    monkeypatch.setattr(cli.shutil, "get_terminal_size", boom)
    assert cli.resolve_size(a) == (80, 20)


def test_fit_reads_terminal(monkeypatch):
    monkeypatch.setattr(cli.shutil, "get_terminal_size", lambda *_: os.terminal_size((100, 30)))
    a = cli.build_parser().parse_args(["demo", "--fit"])
    assert cli.resolve_size(a) == (100, 29)


def test_renderer_choice_and_default():
    p = cli.build_parser()
    assert p.parse_args(["demo", "--renderer", "block"]).renderer == "block"
    with pytest.raises(SystemExit):
        p.parse_args(["demo", "--renderer", "ascii"])
    assert cli.resolve_renderer(p.parse_args(["demo"])) in show.available_renderers()


def test_available_renderers():
    r = show.available_renderers()
    assert "block" in r
    assert set(r) <= set(show.RENDERERS)


def test_draw_requires_target():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["draw"])


@pytest.mark.parametrize(
    "argv, func",
    [
        (["demo"], "demo.diamond"),
        (["time"], "measure.time_sweep"),
        (["vs-ncu"], "profile.ncu_sweep"),
    ],
)
def test_stub_reports_not_implemented(argv, func, capsys, tmp_path):
    rc = cli.main([*argv, "--out", str(tmp_path)])
    err = capsys.readouterr().err
    assert rc != 0
    assert err.strip() == f"not implemented yet: {func}"
    assert "Traceback" not in err


def test_draw_target_reaches_capture(tmp_path, capsys):
    mod = tmp_path / "wl.py"
    mod.write_text("def make():\n    return (lambda x: x), [1]\n")
    rc = cli.main(["draw", f"{mod}:make", "--out", str(tmp_path)])
    assert rc != 0
    assert capsys.readouterr().err.strip() == "not implemented yet: capture.capture"


def test_bad_target(tmp_path):
    with pytest.raises(ValueError):
        cli.load_target("nocolon")
    with pytest.raises(FileNotFoundError):
        cli.load_target(str(tmp_path / "missing.py") + ":f")


def test_env_runs(capsys):
    assert cli.main(["env"]) == 0
    assert "python" in capsys.readouterr().out
