import sys
from pathlib import Path


def print_section(title):
    pass


def main():
    # Print Python environment info
    print_section("Python Environment")

    # Add src to path
    src_dir = str(Path(__file__).parent.absolute() / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    # Test importing base_tool
    print_section("Testing base_tool Import")
    try:
        pass

    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
