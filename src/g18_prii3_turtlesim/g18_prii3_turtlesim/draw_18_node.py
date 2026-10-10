#!/usr/bin/env python3
"""Nodo ROS 2 (Humble) con control en Lazo Cerrado (Odometría)."""
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from std_srvs.srv import Trigger, Empty
from turtlesim.srv import SetPen, TeleportAbsolute

START = (3.0, 7.0, -math.pi / 2)

# Trayectoria exacta: ('move', distancia) o ('turn', radianes) o ('pen', True/False)
PATH = [
    ('move', 4.0),
    ('pen', False),
    ('turn', math.pi/2),
    ('move', 3.0),
    ('turn', math.pi/2),
    ('pen', True),
    ('move', 4.0),
    ('turn', -math.pi/2),
    ('move', 2.0),
    ('turn', -math.pi/2),
    ('move', 4.0),
    ('turn', -math.pi/2),
    ('move', 2.0),
    ('turn', -math.pi/2),
    ('move', 2.0),
    ('turn', -math.pi/2),
    ('move', 2.0)
]

class Draw18Node(Node):
    def __init__(self):
        super().__init__('draw_18_node')

        # Publicador de velocidad y Suscriptor de coordenadas (Lazo Cerrado)
        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.pose_sub = self.create_subscription(Pose, '/turtle1/pose', self.pose_cb, 10)
        
        self.pen_cli = self.create_client(SetPen, '/turtle1/set_pen')
        self.tele_cli = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute')
        self.clear_cli = self.create_client(Empty, '/clear')

        self.create_service(Trigger, 'stop_drawing', self.stop_cb)
        self.create_service(Trigger, 'resume_drawing', self.resume_cb)
        self.create_service(Trigger, 'restart_drawing', self.restart_cb)

        self.idx = 0
        self.state = 'WAITING'
        self.start_pose = None
        self.step_in_progress = False

        self.get_logger().info('Esperando a turtlesim...')
        self.startup_timer = self.create_timer(0.5, self.check_services)

    def check_services(self):
        if self.state == 'WAITING':
            if all(c.service_is_ready() for c in (self.pen_cli, self.tele_cli, self.clear_cli)):
                self.startup_timer.cancel()
                self.reset_begin()

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
        self.step_in_progress = False
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
        self.get_logger().info('Dibujando el 18 (Modo Odometría)...')

    def stop_cb(self, request, response):
        if self.state == 'PLAYING':
            self.state = 'PAUSED'
            self.cmd_pub.publish(Twist())
            response.success, response.message = True, 'Dibujo detenido'
        else:
            response.success = False
        return response

    def resume_cb(self, request, response):
        if self.state == 'PAUSED':
            self.state = 'PLAYING'
            response.success, response.message = True, 'Dibujo reanudado'
        else:
            response.success = False
        return response

    def restart_cb(self, request, response):
        if self.state not in ('WAITING', 'RESETTING'):
            self.reset_begin()
            response.success, response.message = True, 'Dibujo reiniciado'
        else:
            response.success = False
        return response

    def pose_cb(self, msg):
        if self.state != 'PLAYING':
            return

        if self.idx >= len(PATH):
            if self.state != 'FINISHED':
                self.cmd_pub.publish(Twist())
                self.state = 'FINISHED'
                self.get_logger().info('Dibujo terminado. Usa /restart_drawing para repetirlo.')
            return

        step_type, value = PATH[self.idx]

        if step_type == 'pen':
            self._set_pen(value)
            self.idx += 1
            self.step_in_progress = False
            return

        if not self.step_in_progress:
            self.start_pose = msg
            self.step_in_progress = True

        cmd = Twist()
        done = False

        if step_type == 'move':
            # Mide la distancia euclidiana exacta
            dist = math.hypot(msg.x - self.start_pose.x, msg.y - self.start_pose.y)
            if dist >= value:
                done = True
            else:
                cmd.linear.x = 1.0

        elif step_type == 'turn':
            # Mide la diferencia de ángulo exacta
            diff = msg.theta - self.start_pose.theta
            diff = math.atan2(math.sin(diff), math.cos(diff))
            
            if abs(diff) >= abs(value):
                done = True
            else:
                cmd.angular.z = math.copysign(1.0, value)

        if done:
            self.cmd_pub.publish(Twist())
            self.idx += 1
            self.step_in_progress = False
        else:
            self.cmd_pub.publish(cmd)

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
