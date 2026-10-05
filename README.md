# Grupo 18 - Proyecto RII 3 (Sprint 1)

## Instrucciones de ejecución
Para ejecutar el nodo de control de turtlesim que dibuja el número 18, sigue estos pasos:

1. Sitúate en la raíz del workspace y compila el paquete:
   `colcon build --packages-select g18_prii3_turtlesim`
2. Carga el entorno:
   `source install/setup.bash`
3. Ejecuta el fichero launch (abrirá el simulador y el nodo simultáneamente):
   `ros2 launch g18_prii3_turtlesim draw_18.launch.py`

## Control de servicios
En una terminal nueva (recordando ejecutar `source install/setup.bash`), puedes usar los siguientes servicios:
- Pausar: `ros2 service call /stop_drawing std_srvs/srv/Trigger`
- Reanudar: `ros2 service call /resume_drawing std_srvs/srv/Trigger`
- Reiniciar: `ros2 service call /restart_drawing std_srvs/srv/Trigger`
