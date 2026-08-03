"""List the available examples.

python -m physim_examples
"""

from __future__ import annotations

from . import EXAMPLES


def main() -> None:
    """Print every example and how to run it."""
    print("physim examples\n")
    width = max(len(name) for name in EXAMPLES)
    for name, description in EXAMPLES.items():
        print(f"  {name:<{width}}  {description}")
    print("\nrun one with:\n  python -m physim_examples.<name>")
    print("flags: --debug  --preview  --seconds N  --fps N  --resolution WxH  -o FILE")


if __name__ == "__main__":
    main()
