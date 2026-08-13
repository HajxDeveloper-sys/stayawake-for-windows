from preferences import DEFAULT_PREFERENCES, PreferencesStore, sanitize_preferences


def test_preferences_round_trip_in_a_user_writable_path(tmp_path):
    store = PreferencesStore(tmp_path / "StayAwake" / "preferences.json")
    choices = {
        "language": "EN",
        "keep_display": False,
        "keep_system": True,
        "virtual_heartbeat": True,
        "session_preset": "custom",
        "custom_duration_minutes": 75,
        "geometry": "640x720",
    }

    assert store.save(choices)
    assert store.load() == choices


def test_invalid_preferences_fall_back_field_by_field(tmp_path):
    store = PreferencesStore(tmp_path / "preferences.json")
    store.path.parent.mkdir(parents=True, exist_ok=True)
    store.path.write_text("not valid json", encoding="utf-8")
    assert store.load() == DEFAULT_PREFERENCES

    safe = sanitize_preferences(
        {
            "language": "nope",
            "keep_display": "yes",
            "session_preset": "forever",
            "custom_duration_minutes": 999999,
            "geometry": "20x20",
        }
    )
    assert safe["language"] == "TR"
    assert safe["keep_display"] is True
    assert safe["session_preset"] == "continuous"
    assert safe["custom_duration_minutes"] == 1440
    assert safe["geometry"] == "520x700"
