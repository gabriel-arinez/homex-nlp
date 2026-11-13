from tools.experiment_real_voice_asr import configurations, signal_profile


def test_experiment_settings_do_not_include_reference_scripts_or_codes():
    settings = configurations()
    assert set(settings) == {
        "temperature_zero",
        "no_previous",
        "vad_no_previous",
        "wider_beam",
        "context_no_previous",
    }
    assert settings["no_previous"]["condition_on_previous_text"] is False
    assert settings["vad_no_previous"]["vad_filter"] is True
    assert settings["wider_beam"]["beam_size"] == 8
    assert settings["context_no_previous"]["beam_size"] == 5
    assert not any(key in str(settings) for key in ["MP-", "SIL-", "PIS-", "OTR-", "NF-", "NA9"])
    assert all(isinstance(s["temperature"], float) for s in settings.values())


def test_signal_profile_distinguishes_silence_and_clipping():
    quiet = signal_profile([0] * 32000, 16000)
    assert quiet["duration_seconds"] == 2
    assert quiet["silence_seconds"] == 2
    assert quiet["clipped_samples"] == 0
    loud = signal_profile([32767] * 16000, 16000)
    assert loud["silence_seconds"] == 0
    assert loud["clipped_samples"] == 16000
