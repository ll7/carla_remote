from src.cli import remote_carla_start


def test_prompt_sequence_and_dry_run(monkeypatch, capsys):
    recorded_actions: list[str] = []

    def record_event(component, action, **kwargs):
        recorded_actions.append(action)
        return None

    monkeypatch.setattr(remote_carla_start, "log_event", record_event)

    answers = iter(["remote.example.com", "ubuntu", "y", "n", "y"])
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": (print(prompt, end="") or next(answers)),
    )

    exit_code = remote_carla_start.main(["--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 0
    for prompt in [
        "Enter remote host",
        "Enter SSH username",
        "Is CARLA already installed?",
        "If not installed, proceed with download?",
        "Use persistent tmux session?",
    ]:
        assert prompt in captured.out

    assert "dry_run_complete" in recorded_actions
