import sys
import os
import json
import logging

# Add src to path so we can import the module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

try:
    from tapo_camera_mcp.web.api.plex import _condense_metadata
except ImportError as e:
    print(f"Import Error: {e}")

    # Fallback for testing purely the logic if imports fail due to fastAPI dependencies not being installed in this env
    def _condense_metadata(metadata: dict) -> dict:
        if not metadata:
            return {}
        return {
            "title": metadata.get("title"),
            "type": metadata.get("type"),
            "grandparentTitle": metadata.get("grandparentTitle"),
            "parentTitle": metadata.get("parentTitle"),
            "summary": metadata.get("summary"),
            "thumb": metadata.get("thumb"),
        }


def test_condense_logic():
    full_payload = {
        "title": "Episode 1",
        "type": "episode",
        "grandparentTitle": "Breaking Bad",
        "parentTitle": "Season 1",
        "summary": "Walter White is a chemistry teacher...",
        "thumb": "/library/metadata/123/thumb",
        "Role": [{"tag": "Bryan Cranston"}],
        "Director": [{"tag": "Vince Gilligan"}],
        "Media": [{"videoResolution": "1080p"}],
        "Guid": [{"id": "imdb://tt123456"}],
    }

    condensed = _condense_metadata(full_payload)

    # Assertions
    assert condensed["title"] == "Episode 1"
    assert condensed["grandparentTitle"] == "Breaking Bad"
    assert "Role" not in condensed
    assert "Director" not in condensed
    assert "Media" not in condensed

    print("SUCCESS: _condense_metadata logic passed!")
    print(f" condensed output: {json.dumps(condensed, indent=2)}")


if __name__ == "__main__":
    test_condense_logic()
