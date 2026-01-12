"""
Tests for Audio Management - "Alexa 2" Voice Features

Tests the SOTA voice stack:
- STT Chain: Faster-Whisper -> Vosk -> Whisper
- TTS Chain: Piper -> Edge-TTS -> pyttsx3
- Wake Word: OpenWakeWord / Vosk fallback
"""

import pytest

# Import the module to test availability flags
from tapo_camera_mcp.tools.portmanteau.audio_management import (
    AUDIO_ACTIONS,
    EDGE_TTS_AVAILABLE,
    FASTER_WHISPER_AVAILABLE,
    OPENWAKEWORD_AVAILABLE,
    PIPER_AVAILABLE,
    PYTTSX3_AVAILABLE,
    SOUNDDEVICE_AVAILABLE,
    STT_AVAILABLE,
    TTS_AVAILABLE,
    VOSK_AVAILABLE,
    WAKE_WORDS,
    WHISPER_AVAILABLE,
)


class TestAudioDependencies:
    """Test that audio dependencies are properly detected."""

    def test_stt_chain_availability(self):
        """Test STT engine availability flags."""
        # At least one STT engine should be available
        assert (FASTER_WHISPER_AVAILABLE or VOSK_AVAILABLE or WHISPER_AVAILABLE) == STT_AVAILABLE
        print("\nSTT Engines:")
        print(f"  Faster-Whisper: {FASTER_WHISPER_AVAILABLE}")
        print(f"  Vosk: {VOSK_AVAILABLE}")
        print(f"  Whisper: {WHISPER_AVAILABLE}")
        print(f"  Any available: {STT_AVAILABLE}")

    def test_tts_chain_availability(self):
        """Test TTS engine availability flags."""
        # At least one TTS engine should be available
        assert (PIPER_AVAILABLE or EDGE_TTS_AVAILABLE or PYTTSX3_AVAILABLE) == TTS_AVAILABLE
        print("\nTTS Engines:")
        print(f"  Piper: {PIPER_AVAILABLE}")
        print(f"  Edge-TTS: {EDGE_TTS_AVAILABLE}")
        print(f"  pyttsx3: {PYTTSX3_AVAILABLE}")
        print(f"  Any available: {TTS_AVAILABLE}")

    def test_wake_word_availability(self):
        """Test wake word engine availability."""
        print("\nWake Word:")
        print(f"  OpenWakeWord: {OPENWAKEWORD_AVAILABLE}")
        print(f"  Vosk (fallback): {VOSK_AVAILABLE}")

    def test_audio_io_availability(self):
        """Test audio I/O availability."""
        print("\nAudio I/O:")
        print(f"  sounddevice: {SOUNDDEVICE_AVAILABLE}")

    def test_wake_words_defined(self):
        """Test that wake words are properly defined."""
        assert len(WAKE_WORDS) > 0
        assert "hey tapo" in WAKE_WORDS
        print(f"\nWake Words: {WAKE_WORDS}")


class TestAudioActions:
    """Test audio action definitions."""

    def test_all_actions_defined(self):
        """Test that all expected actions are defined."""
        expected_actions = [
            "get_url",
            "capabilities",
            "player_url",
            "vlc_command",
            "speak",
            "announce",
            "listen",
            "voice_command",
            "wake_start",
            "wake_stop",
            "wake_status",
            "play_alarm",
            "play_file",
            "stop_audio",
            "record",
            "list_devices",
        ]
        for action in expected_actions:
            assert action in AUDIO_ACTIONS, f"Missing action: {action}"
        print(f"\nAll {len(AUDIO_ACTIONS)} actions defined correctly")

    def test_wake_actions_present(self):
        """Test that wake word actions are present."""
        assert "wake_start" in AUDIO_ACTIONS
        assert "wake_stop" in AUDIO_ACTIONS
        assert "wake_status" in AUDIO_ACTIONS


class TestAudioCapabilities:
    """Test audio capabilities reporting."""

    @pytest.mark.asyncio
    async def test_capabilities_action(self):
        """Test the capabilities action returns engine info."""
        from fastmcp import FastMCP

        from tapo_camera_mcp.tools.portmanteau.audio_management import (
            register_audio_management_tool,
        )

        mcp = FastMCP("test")
        register_audio_management_tool(mcp)

        # Find the registered tool
        tools = mcp._tool_manager._tools
        assert "audio_management" in tools

        # Get tool function
        tool = tools["audio_management"]

        # Call capabilities
        result = await tool.fn(action="capabilities")

        assert result["success"] is True
        assert "data" in result

        data = result["data"]
        assert "stt_engines" in data
        assert "tts_engines" in data
        assert "wake_word_detection" in data
        assert "install_commands" in data

        print("\nCapabilities Response:")
        print(f"  STT Primary: {data['stt_engines'].get('primary')}")
        print(f"  TTS Primary: {data['tts_engines'].get('primary')}")
        print(f"  Wake Word Primary: {data['wake_word_detection'].get('primary')}")


class TestWakeWordListener:
    """Test wake word listener functionality."""

    @pytest.mark.asyncio
    async def test_wake_status(self):
        """Test wake status action."""
        from fastmcp import FastMCP

        from tapo_camera_mcp.tools.portmanteau.audio_management import (
            register_audio_management_tool,
        )

        mcp = FastMCP("test")
        register_audio_management_tool(mcp)

        tool = mcp._tool_manager._tools["audio_management"]
        result = await tool.fn(action="wake_status")

        assert result["success"] is True
        assert "data" in result

        data = result["data"]
        assert "running" in data
        assert "engine" in data
        assert "wake_words" in data

        print("\nWake Status:")
        print(f"  Running: {data['running']}")
        print(f"  Engine: {data['engine']}")
        print(f"  Wake Words: {data['wake_words']}")


if __name__ == "__main__":
    # Run quick dependency check
    print("=" * 60)
    print("AUDIO VOICE STACK - DEPENDENCY CHECK")
    print("=" * 60)

    test = TestAudioDependencies()
    test.test_stt_chain_availability()
    test.test_tts_chain_availability()
    test.test_wake_word_availability()
    test.test_audio_io_availability()
    test.test_wake_words_defined()

    print("\n" + "=" * 60)
    print("AUDIO ACTIONS")
    print("=" * 60)
    test2 = TestAudioActions()
    test2.test_all_actions_defined()

    print("\n" + "=" * 60)
    print("SUCCESS: All dependency checks passed!")
    print("=" * 60)
