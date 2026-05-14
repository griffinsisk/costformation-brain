from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    ERROR = "ERROR"
    WARN = "WARN"


@dataclass
class Diagnostic:
    severity: Severity
    rule_id: str
    message: str
    path: str = ""
    line: int = 0
    column: int = 0
    dimension_id: Optional[str] = None
    rule_name: Optional[str] = None

    def human_readable(self, filename: str) -> str:
        sev = self.severity.value.ljust(5)
        loc = f"{filename}:{self.line}" if self.line else filename
        return f"{sev} {loc} — [{self.rule_id}] {self.message}"

    def to_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "rule_id": self.rule_id,
            "message": self.message,
            "path": self.path,
            "line": self.line,
            "column": self.column,
            "dimension_id": self.dimension_id,
            "rule_name": self.rule_name,
        }
