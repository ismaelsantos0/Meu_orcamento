# services/registry.py
from __future__ import annotations

from typing import Dict

from services.base import ServicePlugin

REGISTRY: Dict[str, ServicePlugin] = {}


def register(plugin: ServicePlugin) -> ServicePlugin:
    REGISTRY[plugin.id] = plugin
    return plugin


def get_plugins() -> Dict[str, ServicePlugin]:
    return REGISTRY


# =========================
# Importa e registra plugins
# =========================
# Ajuste os imports conforme os nomes reais dos seus arquivos em services/
# (pelo seu print você tem fence.py, fence_concertina.py, concertina_linear.py)
from services.fence import plugin as fence_plugin
from services.fence_concertina import plugin as fence_concertina_plugin
from services.concertina_linear import plugin as concertina_linear_plugin

register(fence_plugin)
register(fence_concertina_plugin)
register(concertina_linear_plugin)
