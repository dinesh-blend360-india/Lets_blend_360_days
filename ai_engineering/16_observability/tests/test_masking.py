import pytest

from obs.masking import find_unmasked, mask, mask_text


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("employee E1023 asked", "employee <masked:employee_id> asked"),
        ("mail asha.rao@example.com now", "mail <masked:email> now"),
        ("call +91 9876543210", "call <masked:phone>"),
        ("key sk-abcdef0123456789", "key <redacted:api_key>"),
        ("nothing sensitive here", "nothing sensitive here"),
    ],
)
def test_each_rule_replaces_its_pattern(raw, expected):
    assert mask_text(raw) == expected


@pytest.mark.parametrize(
    "identifier",
    [
        "generated-7499265617abcd1234ef",  # Day 10 call_id: sha256 hex can hold a 10-digit run
        "SR-7499265617AB",                 # simulated service-request ID
        "trace-9876543210-part",
    ],
)
def test_identifiers_containing_digit_runs_are_not_mangled(identifier):
    """A trace is searched by these IDs; rewriting them would defeat the point."""
    assert mask_text(identifier) == identifier


def test_a_real_phone_number_is_still_masked_next_to_punctuation():
    assert mask_text("reach me on 9876543210.") == "reach me on <masked:phone>."
    assert mask_text("(9876543210)") == "(<masked:phone>)"


def test_multiple_values_in_one_string():
    masked = mask_text("E1023 / asha.rao@example.com")
    assert masked == "<masked:employee_id> / <masked:email>"


def test_nested_structures_are_masked_recursively():
    payload = {
        "message": "I am E1023",
        "items": [{"email": "a.b@example.com"}, ["E4567"]],
    }
    masked = mask(payload)
    assert masked["message"] == "I am <masked:employee_id>"
    assert masked["items"][0]["email"] == "<masked:email>"
    assert masked["items"][1][0] == "<masked:employee_id>"


def test_secret_keys_are_dropped_not_pattern_matched():
    masked = mask({"api_key": "anything-at-all", "Authorization": "Bearer xyz", "query": "ok"})
    assert masked["api_key"] == "<dropped>"
    assert masked["Authorization"] == "<dropped>"
    assert masked["query"] == "ok"


def test_field_names_are_preserved():
    assert set(mask({"employee_id": "E1023"})) == {"employee_id"}


def test_non_string_scalars_pass_through():
    assert mask({"n": 3, "flag": True, "nothing": None}) == {"n": 3, "flag": True, "nothing": None}


def test_find_unmasked_reports_then_clears():
    payload = {"m": "E1023 and a.b@example.com"}
    assert len(find_unmasked(payload)) == 2
    assert find_unmasked(mask(payload)) == []
