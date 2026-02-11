from services.fence import plugin as fence
from services.fence_concertina import plugin as fence_concertina
from services.concertina_linear import plugin as concertina_linear
from services.cftv_install import plugin as cftv_install
from services.cftv_maintenance import plugin as cftv_maintenance
from services.gate_motor_install import plugin as motor_install
from services.gate_motor_maintenance import plugin as motor_maintenance


SERVICE_REGISTRY = {
    fence.id: fence,
    fence_concertina.id: fence_concertina,
    concertina_linear.id: concertina_linear,
    cftv_install.id: cftv_install,
    cftv_maintenance.id: cftv_maintenance,
    motor_install.id: motor_install,
    motor_maintenance.id: motor_maintenance,
}
