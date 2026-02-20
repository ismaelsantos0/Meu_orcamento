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

from services.fence import plugin as fence_plugin
from services.fence_concertina import plugin as fence_concertina_plugin
from services.concertina_linear import plugin as concertina_linear_plugin

# Importando os novos serviços de Câmeras e Motores
from services.cftv_install import plugin as cftv_install_plugin
from services.cftv_maintenance import plugin as cftv_maintenance_plugin
from services.gate_motor_install import plugin as motor_install_plugin
from services.gate_motor_maintenance import plugin as motor_maintenance_plugin

# Registrando todos
register(fence_plugin)
register(fence_concertina_plugin)
register(concertina_linear_plugin)
register(cftv_install_plugin)
register(cftv_maintenance_plugin)
register(motor_install_plugin)
register(motor_maintenance_plugin)
