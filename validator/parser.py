"""YAML parser for CostFormation files with ruamel.yaml line-number support."""
from dataclasses import dataclass
from typing import Dict, Optional

from ruamel.yaml import YAML, YAMLError
from ruamel.yaml.comments import CommentedMap


class ParseError(Exception):
    """Raised when a CostFormation file cannot be parsed."""


@dataclass
class ParseResult:
    """Holds the parsed state of a CostFormation file.

    Attributes:
        dimensions: Mapping of dimension ID -> parsed YAML node (CommentedMap).
        yaml_obj:   The full parsed top-level YAML object.
        raw_text:   The original file contents as a string.
        filename:   Absolute or relative path to the source file.
        standalone: True when the file is a standalone pattern example rather
                    than part of a full org config.  Auto-detected from the
                    file path (``examples/patterns/`` prefix) when not
                    supplied explicitly.
    """

    dimensions: Dict[str, CommentedMap]
    yaml_obj: CommentedMap
    raw_text: str
    filename: str
    standalone: bool = False

    def line_of(self, node) -> int:
        """Return the 1-based line number of a ruamel.yaml node, or 0 if unknown."""
        if hasattr(node, "lc") and node.lc is not None:
            return node.lc.line + 1  # ruamel uses 0-based line numbers
        return 0

    def col_of(self, node) -> int:
        """Return the 0-based column of a ruamel.yaml node, or 0 if unknown."""
        if hasattr(node, "lc") and node.lc is not None:
            return node.lc.col
        return 0


def parse_costformation(
    filepath: str,
    standalone: Optional[bool] = None,
) -> ParseResult:
    """Parse a CostFormation YAML file and return a :class:`ParseResult`.

    Args:
        filepath:   Path to the ``.yaml`` file to parse.
        standalone: Override the standalone flag.  When ``None`` the value is
                    auto-detected: any path whose normalised form contains
                    ``examples/patterns/`` is treated as standalone.

    Returns:
        A :class:`ParseResult` with dimension nodes that carry ruamel.yaml
        ``lc`` (line/column) metadata.

    Raises:
        ParseError: If the file cannot be read as valid YAML, or if the
                    top-level value is not a YAML mapping.
    """
    with open(filepath, "r") as fh:
        raw_text = fh.read()

    yaml = YAML()
    yaml.preserve_quotes = True
    try:
        data = yaml.load(raw_text)
    except YAMLError as exc:
        raise ParseError(f"YAML parse error in {filepath}: {exc}") from exc

    if data is None or not isinstance(data, dict):
        raise ParseError(
            f"Expected a YAML mapping in {filepath}, got {type(data).__name__}"
        )

    dimensions = data.get("Dimensions") or {}

    if standalone is None:
        # Normalise path separators so the check works on Windows too
        normalised = filepath.replace("\\", "/")
        standalone = "examples/patterns/" in normalised

    return ParseResult(
        dimensions=dimensions,
        yaml_obj=data,
        raw_text=raw_text,
        filename=filepath,
        standalone=standalone,
    )
