"""Keep audio suffix rejection independent of archive directory names."""

from zipfile import ZipFile

import pytest

from tools.verify_distribution import check_privacy


@pytest.mark.parametrize("suffix", ["aac", "AAC", "wav", "mp3"])
def test_distribution_rejects_audio_outside_audio_directory(tmp_path, suffix):
    artifact = tmp_path / "candidate.whl"
    with ZipFile(artifact, "w") as archive:
        archive.writestr(f"assets/voice.{suffix}", b"private audio placeholder")
    with pytest.raises(SystemExit, match="voice"):
        check_privacy(artifact)


def test_distribution_allows_source_and_environment_example(tmp_path):
    artifact = tmp_path / "candidate.whl"
    with ZipFile(artifact, "w") as archive:
        archive.writestr("homex_nlp/example.py", "VALUE = 1\n")
        archive.writestr("docs/.env.example", "DEMO=value\n")
    check_privacy(artifact)
