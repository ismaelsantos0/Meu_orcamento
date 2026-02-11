from dataclasses import dataclass
from typing import Callable, Dict, Any


@dataclass
class ServicePlugin:
    id: str
    label: str
    render_fields: Callable[[], Dict[str, Any]]
    compute: Callable[[Any, Dict[str, Any]], Dict[str, Any]]  # (conn, inputs) -> dict
