"""
Tests for OrcaRouter Cloud TTS extension.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so 'extensions' is importable
# This must be before any project imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from extensions.builtin.extension_orcarouter_cloud_tts.main import (
    ORCAROUTER_API_URL,
    ORCAROUTER_MODELS,
    ORCAROUTER_VOICES,
    _get_api_key,
    _save_audio,
    extension__tts_generation_webui,
    generate_orcarouter_tts,
)


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------
class TestConstants:
    """Test that constants are correctly defined."""

    @pytest.mark.unit
    def test_api_url(self):
        assert ORCAROUTER_API_URL == "https://api.orcarouter.ai/v1/audio/speech"

    @pytest.mark.unit
    def test_models_not_empty(self):
        assert len(ORCAROUTER_MODELS) >= 3

    @pytest.mark.unit
    def test_models_contain_tts_1(self):
        assert "openai/tts-1" in ORCAROUTER_MODELS

    @pytest.mark.unit
    def test_models_contain_tts_1_hd(self):
        assert "openai/tts-1-hd" in ORCAROUTER_MODELS

    @pytest.mark.unit
    def test_models_contain_gpt_4o_mini_tts(self):
        assert "openai/gpt-4o-mini-tts" in ORCAROUTER_MODELS

    @pytest.mark.unit
    def test_voices_not_empty(self):
        assert len(ORCAROUTER_VOICES) == 6

    @pytest.mark.unit
    def test_voices_contain_alloy(self):
        assert "alloy" in ORCAROUTER_VOICES

    @pytest.mark.unit
    def test_voices_contain_shimmer(self):
        assert "shimmer" in ORCAROUTER_VOICES


class TestGetApiKey:
    """Test API key resolution."""

    @pytest.mark.unit
    def test_explicit_key_takes_priority(self):
        os.environ["ORCAROUTER_API_KEY"] = "env_key"
        result = _get_api_key("explicit_key")
        assert result == "explicit_key"

    @pytest.mark.unit
    def test_env_key_fallback(self):
        os.environ["ORCAROUTER_API_KEY"] = "env_key"
        result = _get_api_key("")
        assert result == "env_key"

    @pytest.mark.unit
    def test_empty_when_no_key(self):
        os.environ.pop("ORCAROUTER_API_KEY", None)
        result = _get_api_key("")
        assert result == ""

    @pytest.mark.unit
    def test_whitespace_stripped(self):
        result = _get_api_key("  my_key  ")
        assert result == "my_key"

    @pytest.mark.unit
    def test_none_like_empty(self):
        os.environ.pop("ORCAROUTER_API_KEY", None)
        result = _get_api_key("")
        assert result == ""


class TestSaveAudio:
    """Test audio saving functionality."""

    @pytest.mark.unit
    def test_save_audio_creates_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "outputs", exist_ok=True)

        audio_path, metadata, folder_root = _save_audio(
            b"fake audio data", "Hello world", "openai/tts-1", "alloy"
        )

        assert os.path.exists(audio_path)
        assert audio_path.endswith(".mp3")
        assert os.path.exists(folder_root)

        with open(audio_path, "rb") as f:
            assert f.read() == b"fake audio data"

    @pytest.mark.unit
    def test_save_audio_metadata(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "outputs", exist_ok=True)

        audio_path, metadata, folder_root = _save_audio(
            b"test", "Test text", "openai/tts-1-hd", "echo"
        )

        assert metadata["text"] == "Test text"
        assert metadata["model"] == "openai/tts-1-hd"
        assert metadata["voice_id"] == "echo"
        assert metadata["provider"] == "orcarouter"

    @pytest.mark.unit
    def test_save_audio_json_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "outputs", exist_ok=True)

        audio_path, metadata, folder_root = _save_audio(
            b"test", "Test", "openai/tts-1", "nova"
        )

        json_path = audio_path.replace(".mp3", ".json")
        assert os.path.exists(json_path)
        with open(json_path) as f:
            saved_meta = json.load(f)
        assert saved_meta["provider"] == "orcarouter"
        assert saved_meta["voice_id"] == "nova"

    @pytest.mark.unit
    def test_save_audio_special_chars_in_text(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "outputs", exist_ok=True)

        audio_path, metadata, folder_root = _save_audio(
            b"test", "Hello! @#$% world", "openai/tts-1", "alloy"
        )

        assert os.path.exists(audio_path)
        assert "@" not in audio_path
        assert "#" not in audio_path

    @pytest.mark.unit
    def test_save_audio_empty_text(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "outputs", exist_ok=True)

        audio_path, metadata, folder_root = _save_audio(
            b"test", "", "openai/tts-1", "alloy"
        )

        assert os.path.exists(audio_path)
        assert "orcarouter_tts" in audio_path


class TestGenerateOrcaRouterTTS:
    """Test the main generation function."""

    @pytest.mark.unit
    def test_no_api_key_raises_error(self):
        os.environ.pop("ORCAROUTER_API_KEY", None)
        with pytest.raises(Exception, match="API key"):
            generate_orcarouter_tts("Hello", "openai/tts-1", "alloy", "")

    @pytest.mark.unit
    def test_empty_text_raises_error(self):
        os.environ["ORCAROUTER_API_KEY"] = "test_key"
        with pytest.raises(Exception, match="text"):
            generate_orcarouter_tts("", "openai/tts-1", "alloy", "")

    @pytest.mark.unit
    def test_whitespace_text_raises_error(self):
        os.environ["ORCAROUTER_API_KEY"] = "test_key"
        with pytest.raises(Exception, match="text"):
            generate_orcarouter_tts("   ", "openai/tts-1", "alloy", "")

    @pytest.mark.unit
    def test_successful_generation(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "outputs", exist_ok=True)

        fake_audio = b"fake mp3 audio content here"
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_audio
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            audio_path, metadata, folder_root = generate_orcarouter_tts(
                "Hello world",
                "openai/tts-1",
                "alloy",
                "test_api_key",
            )

        assert os.path.exists(audio_path)
        assert metadata["text"] == "Hello world"
        assert metadata["model"] == "openai/tts-1"
        assert metadata["voice_id"] == "alloy"

        with open(audio_path, "rb") as f:
            assert f.read() == fake_audio

    @pytest.mark.unit
    def test_empty_audio_response(self):
        os.environ["ORCAROUTER_API_KEY"] = "test_key"

        mock_resp = MagicMock()
        mock_resp.read.return_value = b""
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(Exception, match="no audio data"):
                generate_orcarouter_tts(
                    "Hello", "openai/tts-1", "alloy", "test_api_key"
                )

    @pytest.mark.unit
    def test_http_error(self):
        import urllib.error

        os.environ["ORCAROUTER_API_KEY"] = "test_key"

        mock_error = urllib.error.HTTPError(
            url="https://api.orcarouter.ai/v1/audio/speech",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=MagicMock(read=MagicMock(return_value=b"Unauthorized")),
        )

        with patch("urllib.request.urlopen", side_effect=mock_error):
            with pytest.raises(Exception, match="401"):
                generate_orcarouter_tts(
                    "Hello", "openai/tts-1", "alloy", "test_api_key"
                )

    @pytest.mark.unit
    def test_request_payload_structure(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "outputs", exist_ok=True)

        fake_audio = b"test"
        mock_resp = MagicMock()
        mock_resp.read.return_value = fake_audio
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        captured_request = {}

        def capture_request(req, **kwargs):
            captured_request["url"] = req.full_url
            captured_request["data"] = json.loads(req.data.decode("utf-8"))
            captured_request["headers"] = dict(req.headers)
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=capture_request):
            generate_orcarouter_tts(
                "Test text",
                "openai/tts-1-hd",
                "echo",
                "my_api_key",
            )

        assert captured_request["url"] == ORCAROUTER_API_URL
        assert captured_request["data"]["model"] == "openai/tts-1-hd"
        assert captured_request["data"]["input"] == "Test text"
        assert captured_request["data"]["voice"] == "echo"
        assert "Bearer my_api_key" in captured_request["headers"].get(
            "Authorization", ""
        )


class TestExtensionMetadata:
    """Test extension entry point metadata."""

    @pytest.mark.unit
    def test_extension_function_exists(self):
        assert callable(extension__tts_generation_webui)

    @pytest.mark.unit
    def test_metadata_fields(self):
        # We can't call the function (requires gradio context),
        # but we can import and check the module structure
        from extensions.builtin.extension_orcarouter_cloud_tts import main

        assert hasattr(main, "extension__tts_generation_webui")
        assert hasattr(main, "generate_orcarouter_tts")
        assert hasattr(main, "orcarouter_cloud_tts_tab")
        assert hasattr(main, "ORCAROUTER_MODELS")
        assert hasattr(main, "ORCAROUTER_VOICES")


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------
class TestOrcaRouterTTSIntegration:
    """Integration tests for the full generation pipeline."""

    @pytest.mark.integration
    @pytest.mark.requires_network
    def test_real_api_call(self, tmp_path, monkeypatch):
        """Test with real OrcaRouter API. Requires ORCAROUTER_API_KEY env var."""
        api_key = os.environ.get("ORCAROUTER_API_KEY", "")
        if not api_key:
            pytest.skip("ORCAROUTER_API_KEY not set")

        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "outputs", exist_ok=True)

        audio_path, metadata, folder_root = generate_orcarouter_tts(
            "Hello, this is a test of OrcaRouter Cloud TTS.",
            "openai/tts-1",
            "alloy",
            api_key,
        )

        assert os.path.exists(audio_path)
        assert os.path.getsize(audio_path) > 0
        assert metadata["provider"] == "orcarouter"
        assert metadata["model"] == "openai/tts-1"

        json_path = audio_path.replace(".mp3", ".json")
        assert os.path.exists(json_path)

    @pytest.mark.integration
    @pytest.mark.requires_network
    def test_hd_model(self, tmp_path, monkeypatch):
        """Test with openai/tts-1-hd model."""
        api_key = os.environ.get("ORCAROUTER_API_KEY", "")
        if not api_key:
            pytest.skip("ORCAROUTER_API_KEY not set")

        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "outputs", exist_ok=True)

        audio_path, metadata, folder_root = generate_orcarouter_tts(
            "Testing high-definition speech model.",
            "openai/tts-1-hd",
            "echo",
            api_key,
        )

        assert os.path.exists(audio_path)
        assert os.path.getsize(audio_path) > 0
        assert metadata["model"] == "openai/tts-1-hd"
        assert metadata["voice_id"] == "echo"

    @pytest.mark.integration
    @pytest.mark.requires_network
    def test_gpt_4o_mini_tts_model(self, tmp_path, monkeypatch):
        """Test with openai/gpt-4o-mini-tts model."""
        api_key = os.environ.get("ORCAROUTER_API_KEY", "")
        if not api_key:
            pytest.skip("ORCAROUTER_API_KEY not set")

        monkeypatch.chdir(tmp_path)
        os.makedirs(tmp_path / "outputs", exist_ok=True)

        audio_path, metadata, folder_root = generate_orcarouter_tts(
            "Testing gpt-4o-mini-tts model.",
            "openai/gpt-4o-mini-tts",
            "nova",
            api_key,
        )

        assert os.path.exists(audio_path)
        assert os.path.getsize(audio_path) > 0
        assert metadata["model"] == "openai/gpt-4o-mini-tts"
        assert metadata["voice_id"] == "nova"
