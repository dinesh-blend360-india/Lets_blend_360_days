import pytest

from obs.faults import FAULTS, FaultConfig


def test_no_flag_means_no_fault():
    config = FaultConfig.from_environment()
    assert config.name is None
    assert config.active is False


@pytest.mark.parametrize("value", ["", None, "none", "off", "0", "false", "  "])
def test_falsy_values_disable_faults(value):
    assert FaultConfig.parse(value) is None


@pytest.mark.parametrize("name", FAULTS)
def test_every_documented_fault_parses(name):
    assert FaultConfig.parse(name) == name
    assert FaultConfig(name).is_on(name) is True


def test_case_and_whitespace_are_tolerated():
    assert FaultConfig.parse("  SLOW_TOOL  ") == "slow_tool"


def test_unknown_fault_is_rejected_loudly():
    with pytest.raises(ValueError, match="Unknown FAULT"):
        FaultConfig.parse("make_it_fail")


def test_faults_are_off_by_default_in_the_environment(monkeypatch):
    monkeypatch.delenv("FAULT", raising=False)
    assert FaultConfig.from_environment().active is False


def test_environment_flag_is_read(monkeypatch):
    monkeypatch.setenv("FAULT", "mcp_error")
    assert FaultConfig.from_environment().name == "mcp_error"


def test_only_the_named_fault_is_on():
    config = FaultConfig("slow_tool")
    assert config.is_on("slow_tool")
    assert not any(config.is_on(other) for other in FAULTS if other != "slow_tool")
