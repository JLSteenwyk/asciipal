from __future__ import annotations

from pathlib import Path

from asciipal.app import parse_args, run


def test_parse_args_headless_max_ticks() -> None:
    args = parse_args(["--headless", "--max-ticks", "5"])
    assert args.headless is True
    assert args.max_ticks == 5


def test_parse_args_doctor() -> None:
    args = parse_args(["--doctor"])
    assert args.doctor is True


def test_parse_args_config_util_flags() -> None:
    args = parse_args(["--init-config", "--print-config"])
    assert args.init_config is True
    assert args.print_config is True


def test_run_init_config_creates_file(tmp_path: Path) -> None:
    config_path = tmp_path / "cfg.yaml"
    code = run(["--init-config", "--config", str(config_path)])
    assert code == 0
    assert config_path.exists()


def test_run_print_config_outputs_yaml(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "cfg.yaml"
    run(["--init-config", "--config", str(config_path)])
    code = run(["--print-config", "--config", str(config_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "break_interval_minutes" in captured.out


def test_parse_args_demo_duration_flags() -> None:
    args = parse_args(["--demo", "--duration-seconds", "2", "--no-summary"])
    assert args.demo is True
    assert args.duration_seconds == 2
    assert args.no_summary is True


def test_run_demo_headless_duration() -> None:
    code = run(["--headless", "--demo", "--duration-seconds", "1", "--no-summary"])
    assert code == 0
