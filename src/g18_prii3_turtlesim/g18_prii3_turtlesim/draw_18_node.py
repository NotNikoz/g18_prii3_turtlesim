#!/usr/bin/env python3
"""Nodo ROS 2 (Humble) que mueve la tortuga de turtlesim dibujando el 18.

Servicios (std_srvs/Trigger):
  /stop_drawing     -> detiene el dibujo (pausa)
  /resume_drawing   -> reanuda el dibujo
  /restart_drawing  -> borra el lienzo y empieza de nuevo
"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_srvs.srv import Trigger, Empty
from turtlesim.srv import SetPen, TeleportAbsolute

DT = 0.05              # periodo del timer (s)
LIN = 1.0              # velocidad lineal (unidades/s)
ANG = math.pi / 2      # velocidad angular (rad/s) -> 90 grados por segundo
START = (3.0, 7.0, -math.pi / 2)   # x, y, theta iniciales (mira al sur)


def forward(dist):
    return ('move', LIN, 0.0, dist / LIN)


def turn(deg):
    """Giro en el sitio. Positivo = izquierda, negativo = derecha."""
    rad = math.radians(deg)
    return ('move', 0.0, math.copysign(ANG, rad), abs(rad) / ANG)


def pen(down):
    return ('pen', down)


def wait(sec):
    return ('move', 0.0, 0.0, sec)


# Secuencia de movimientos (equivale a tu lista de cmd.linear / cmd.angular + sleep)
PATH = [
    # "1": linea vertical de (3,7) a (3,3)
    forward(4.0),
    # Ir a (6,3) sin pintar
    pen(False), wait(0.2),
    turn(90), forward(3.0), turn(90),
    pen(True), wait(0.2),
    # "8": rectangulo de 2x4 con barra central
    forward(4.0),
    turn(-90), forward(2.0),
    turn(-90), forward(4.0),
    turn(-90), forward(2.0),
    turn(-90), forward(2.0),
    turn(-90), forward(2.0),
]


class Draw18Node(Node):
    def __init__(self):
        super().__init__('draw_18_node')

        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        self.pen_cli = self.create_client(SetPen, '/turtle1/set_pen')
        self.tele_cli = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute')
        self.clear_cli = self.create_client(Empty, '/clear')

        self.create_service(Trigger, 'stop_drawing', self.stop_cb)
        self.create_service(Trigger, 'resume_drawing', self.resume_cb)
        self.create_service(Trigger, 'restart_drawing', self.restart_cb)

        # Pasos precalculados: (tipo, a, b, numero_de_ticks)
        self.steps = []
        for s in PATH:
            if s[0] == 'pen':
                self.steps.append(('pen', s[1], 0, 0))
            else:
                self.steps.append(('move', s[1], s[2], max(1, round(s[3] / DT))))

        self.idx = 0
        self.ticks = 0
        self.state = 'WAITING'   # WAITING, RESETTING, PLAYING, PAUSED, FINISHED

        self.create_timer(DT, self.timer_cb)
        self.get_logger().info('Esperando a turtlesim...')

    # ---- Reinicio: pen off -> teleport -> clear -> pen on (sin bloquear) ----
    def _call(self, client, req, nxt):
        client.call_async(req).add_done_callback(lambda _f: nxt())

    def _set_pen(self, down, nxt=None):
        r = SetPen.Request()
        r.r, r.g, r.b, r.width = 255, 255, 255, 3
        r.off = 0 if down else 1
        if nxt:
            self._call(self.pen_cli, r, nxt)
        else:
            self.pen_cli.call_async(r)

    def reset_begin(self):
        self.state = 'RESETTING'
        self.idx = 0
        self.ticks = 0
        self.cmd_pub.publish(Twist())
        self._set_pen(False, self._reset_teleport)

    def _reset_teleport(self):
        r = TeleportAbsolute.Request()
        r.x, r.y, r.theta = START
        self._call(self.tele_cli, r, self._reset_clear)

    def _reset_clear(self):
        self._call(self.clear_cli, Empty.Request(), self._reset_pen_down)

    def _reset_pen_down(self):
        self._set_pen(True, self._reset_done)

    def _reset_done(self):
        self.state = 'PLAYING'
        self.get_logger().info('Dibujando el 18...')

    # ---- Servicios ----
    def stop_cb(self, request, response):
        if self.state == 'PLAYING':
            self.state = 'PAUSED'
            self.cmd_pub.publish(Twist())
            response.success, response.message = True, 'Dibujo detenido'
        else:
            response.success, response.message = False, f'No se puede detener en estado {self.state}'
        return response

    def resume_cb(self, request, response):
        if self.state == 'PAUSED':
            self.state = 'PLAYING'
            response.success, response.message = True, 'Dibujo reanudado'
        else:
            response.success, response.message = False, f'No se puede reanudar en estado {self.state}'
        return response

    def restart_cb(self, request, response):
        if self.state in ('WAITING', 'RESETTING'):
            response.success, response.message = False, 'Reinicio ya en curso'
        else:
            self.reset_begin()
            response.success, response.message = True, 'Dibujo reiniciado'
        return response

    # ---- Bucle principal ----
    def timer_cb(self):
        if self.state == 'WAITING':
            if all(c.service_is_ready() for c in (self.pen_cli, self.tele_cli, self.clear_cli)):
                self.reset_begin()
            return

        if self.state in ('RESETTING', 'FINISHED'):
            return

        if self.state == 'PAUSED':
            self.cmd_pub.publish(Twist())
            return

        if self.idx >= len(self.steps):
            self.cmd_pub.publish(Twist())
            self.state = 'FINISHED'
            self.get_logger().info('Dibujo terminado. Usa /restart_drawing para repetirlo.')
            return

        kind, a, b, n = self.steps[self.idx]
        if kind == 'pen':
            self._set_pen(a)
            self.idx += 1
            return

        msg = Twist()
        msg.linear.x = float(a)
        msg.angular.z = float(b)
        self.cmd_pub.publish(msg)
        self.ticks += 1
        if self.ticks >= n:
            self.idx += 1
            self.ticks = 0


def main(args=None):
    rclpy.init(args=args)
    node = Draw18Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

