"""Implementation of :mod:`src.exporters.profiles.generic`.

Implementation preserved in the single ``src`` source tree.
"""

from typing import Dict, Any, Union, List


def format_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formato genérico de metadados.
    Mantém a estrutura plana e simples para fácil leitura humana ou parsing simples.
    """
    # Garante acesso seguro ao Rect
    rect = metadata.get("rect", {"x": 0, "y": 0, "w": 0, "h": 0})
    
    # Normaliza o acesso ao Pivot (pode ser dict ou list dependendo da versão)
    pivot_raw = metadata.get("pivot", {"x": 0, "y": 0})
    if isinstance(pivot_raw, (list, tuple)):
        px, py = pivot_raw[0], pivot_raw[1]
    else:
        px = pivot_raw.get("x", 0)
        py = pivot_raw.get("y", 0)

    return {
        "name": metadata.get("id", "unknown"),
        "dimensions": {
            "x": rect.get("x", 0),
            "y": rect.get("y", 0),
            "w": rect.get("w", 0),
            "h": rect.get("h", 0),
        },
        "pivot": {"x": px, "y": py},
        "properties": {
            "layer": metadata.get("layer", "default"),
            "group": metadata.get("group", None),
            "is_trimmed": metadata.get("trimmed", False),
            "vertex_count": len(metadata.get("polygon", [])),
        },
    }
