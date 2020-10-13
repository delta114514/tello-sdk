import threading
import enum
import socket
import datetime

import cv2

class Direction(enum.Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    FORWARD = "forward"
    BACK = "back"

    @property
    def reverse(self):
        return (Direction.LEFT, Direction.RIGHT,
                Direction.FORWARD, Direction.BACK,
                Direction.UP, Direction.DOWN)[
                    (Direction.RIGHT, Direction.LEFT,
                    Direction.BACK, Direction.FORWARD,
                    Direction.DOWN, Direction.UP).index(self)
                ]
class Coordinate:
    def __init__(self, x: int, y: int, z: int):
        if not isinstance(x, int) or not isinstance(y, int) or not isinstance(z, int):
            raise ValueError("not all the value is ")
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other: "Coordinate"):
        return Coordinate(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Coordinate"):
        return Coordinate(self.x - other.x, self.y - other.y, self.z - other.z)

    @property
    def is_valid(self):
        for val in (self.x, self.y, self.z):
            if not -500 <= val <= 500:
                return False
        if all(lambda x: abs(x) <= 20, (self.x, self.y, self.z)):
            return False
        return True

    @property
    def invalid_reason(self):
        for val in (self.x, self.y, self.z):
            if not -500 <= val <= 500:
                return "all of arguments must be an instance of int"
        if all(lambda x: abs(x) <= 20, (self.x, self.y, self.z)):
            return "all of coordinates must be between -500 and 500"
        return False

    def __repr__(self):
        return "<Coordinate; x: {}, y: {}, z: {}>".format(self.x, self.y, self.z)

    @property
    def _cords(self):
        return "{} {} {}".format(self.x, self.y, self.z)

class TelloVideo:
    def __init__(self):
        self.lcal_addr = "0.0.0.0"
        self.video_port = 11111

        self.udp_video_address = "udp://@{}:{}".format(self.lcal_addr, self.video_port)

        self.stream = None
        self.receiver = None
        self.is_open = False

    def start(self):
        self.stream = cv2.VideoCapture(self.udp_video_address)
        if not self.stream.isOpened():
            self.stream.open(self.udp_video_address)
        self.is_open = True

        self.receiver = threading.Thread(target=self.update)
        self.receiver.daemon = True
        self.receiver.start()

    def update(self):
        while True:
            ret, frame = self.udp_video_address.read()
            cv2.imshow('Tello', frame)
            if cv2.waitKey(1) & 0xFF == ord('q') or not self.is_open:
                break

    def close(self):
        self.is_open = False
        self.receiver.join()
        self.udp_video_address.release()
        cv2.destroyAllWindows()


class Tello:
    def __init__(self):
        self.local_addr = "0.0.0.0"
        self.tello_addr = "192.168.10.1"
        self.sender_port = 8889
        self.receiver_port = 8890
        self.video_port = 11111

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.local_addr, self.receiver_port))

        self.response = []

        self.receiver = threading.Thread(target=self._receive)
        self.receiver.daemon = True
        self.receiver.start()

        self.timeout = 5

    def _send_command(self, command):
        self.socket.sendto(command.encode("utf-8"), (self.tello_addr, self.sender_port))

    def command(self):
        """
        command
        """
        self._send_command("command")
        return "{}: {}".format(self._whoami(), self._get_resp)


    def takeoff(self):
        """
        takeoff
        """
        self._send_command("takeoff")
        return "{}: {}".format(self._whoami(), self._get_resp)

    def land(self):
        """
        land
        """
        self._send_command("land")
        return "{}: {}".format(self._whoami(), self._get_resp)

    def stream_on(self):
        """
        turn on stream
        """
        self._send_command("streamon")
        return "{}: {}".format(self._whoami(), self._get_resp)

    def stream_off(self):
        """
        turn off stream
        """
        self._send_command("streamoff")
        return "{}: {}".format(self._whoami(), self._get_resp)

    def emergency(self):
        """
        turn off mortors
        """
        self._send_command("emergency")
        return "{}: {}".format(self._whoami(), self._get_resp)

    def move(self, direction: Direction, distance: int):
        """
        move to direction distance cm
        direction: Direction to move.
        distance: distance to move.
        """
        if not isinstance(direction, Direction):
            raise TypeError("Only Direction is acceptable for `direction`")

        if distance < 0:
            direciton = direction.reverse
            distance *= -1
        if not 20 <= distance <= 500:
            raise ValueError("value `{}` is not acceptable for `distance`."
                              "needs to be between 20 and 500".format(distance))

        self._send_command("{} {}".format(direction.value, distance))
        return "{}: {}".format(self._whoami(), self._get_resp)

    def rotate(self, degrees: int, clockwise=True):
        """
        rotate degrees clockwise if `clockwise` is True. If not, rotate counterclockwise
        degrees: degrees of rotate
        clockwise: whether rotate clockwise
        """
        if not 1 <= degrees <= 360:
            raise ValueError("value `{}` is not acceptable for `degrees`."
                              "needs to be between 1 and 360".format(degrees))

        self._send_command("{} {}".format("cw" if clockwise else "ccw", degrees))
        return "{}: {}".format(self._whoami(), self._get_resp)

    def flip(self, direction: Direction):
        """
        flip in direction
        """
        if direction not in (Direction.LEFT, Direction.RIGHT, Direction.FORWARD, Direction.BACK):
            raise ValueError("value `{}` is not acceptable for `direction`."
                              "needs to be one of Direction.LEFT, Direction.RIGHT, Direction.FORWARD or Direction.BACK".format(direction))
        self._send_command("flip {}".format(direction.value))
        return "{}: {}".format(self._whoami(), self._get_resp)

    def go(self, coordinate: Coordinate):
        """
        go to given coordinate
        """
        if not coodinate.is_valid:
            raise ValueError(coodinate.invalid_reason)
        self._send_command("go {} {}".format(coodinate._cords, speed))
        return "{}: {}".format(self._whoami(), self._get_resp)


    def stop(self):
        """
        hover at air. works anytime
        """
        self._send_command("stop")
        return "{}: {}".format(self._whoami(), self._get_resp)


    def curve(self, from_coordinate: Coordinate, to_coordinate: Coordinate, speed: int):
        """
        curve according to two given coordinates
        """
        if not from_coodinate.is_valid:
            raise ValueError("`from_coordinate` is invalid. "from_coodinate.invalid_reason)
        if not to_coodinate.is_valid:
            raise ValueError("`to_coordinate` is invalid. "to_coodinate.invalid_reason)
        if not 10 <= speed <= 60:
            raise ValueError("speed value is invalid. Needs to be between 10 and 60")
        self._send_command("curve {} {} {}".format(from_coodinate._cords, to_coodinate._cords, speed))
        return "{}: {}".format(self._whoami(), self._get_resp)


    def set_speed(self, speed: int):
        """
        set Speed
        """
        if not 10 <= speed <= 100:
            raise ValueError("speed value is invalid. Needs to be between 10 and 100")
        self._send_command("speed {}".format(speed))
        return "{}: {}".format(self._whoami(), self._get_resp)


    def set_wifi_password(self, ssid: str, password: str):
        """
        set ssid and wifi password
        """
        with open("tello_password.log", "a", encoding="utf-8") as f:
            f.write("{}: ssid set to `{}`; password set to `{}`".format(datetime.datetime.now(), ssid, password))
        self._send_command("wifi {} {}".format(ssid, password))
        return "{}: {}".format(self._whoami(), self._get_resp)

    @property
    def speed(self):
        self._send_command("speed?")
        return self._get_resp

    @property
    def battery(self):
        self._send_command("battery?")
        return self._get_resp

    @property
    def time(self):
        self._send_command("time?")
        return self._get_resp

    @property
    def snr(self):
        self._send_command("wifi?")
        return self._get_resp

    @property
    def sdk_version(self):
        self._send_command("sdk?")
        return self._get_resp

    @property
    def serial_number(self):
        self._send_command("sn?")
        return self._get_resp

    def _get_resp(self):
        start = datetime.datetime.now()
        while 1:
            if datetime.timedelta(seconds=self.timeout) + self.start < datetime.datetime.now():
                break
            if self.response:
                return self.response.pop(0)
        return "timeout"

    def _receive(self):
        while True:
            try:
                resp, ip = self.socket.recvfrom(1024)
                if "temph" not in resp.decode():
                    self.response.append(resp)
            except socket.error as e:
                print("error:", e)

    def _whoami():
        return inspect.stack()[1][3]
