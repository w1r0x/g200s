from g200s import exceptions
from bluepy import btle
from enum import Enum


class Method(Enum):
    AUTH = 255
    VERSION = 1
    TIME_SYNC = 110
    STAT_WATTS = 71
    STAT_TIMES = 80
    GET_MODE = 6
    SET_MODE = 5
    RUN = 3
    STOP = 4
    STANDBY_COLOR = 55
    SET_PALETTE = 50
    GET_PALETTE = 51


class Mode(Enum):
    BOILING = 0
    HEAT = 1
    LAMP = 3


class State(Enum):
    STOPPED = 0
    RUNNING = 2


class Teapot:
    mac = None
    key = None

    notify_uuid = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
    write_uuid = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'

    iter = 0

    connection = None
    write_handle = None

    _authorized = False
    _version = None

    _current_mode = None
    _dest_temperature = None
    _current_temperature = None
    _state = None

    def __init__(self, mac, key=b'\xff\xff\xff\xff\xff\xff\xff\xff'):
        self.mac = mac
        self.key = key
        self.connection = btle.Peripheral(deviceAddr=self.mac, addrType=btle.ADDR_TYPE_RANDOM)

        delegate = NotificationDispatcher(self)
        self.connection.setDelegate(delegate)

        self._enable_notifications()
        self._set_write_handle()
        self.auth()
        self._read_version()
        self._get_mode()

    @property
    def authorized(self):
        return self._authorized

    @authorized.setter
    def authorized(self, value):
        self._authorized = value

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

    @property
    def mode(self):
        return self._current_mode

    @mode.setter
    def mode(self, value):
        self._current_mode = value

    @property
    def temperature(self):
        return self._current_temperature

    @temperature.setter
    def temperature(self, value):
        self._current_temperature = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    def _enable_notifications(self):
        ch = self.connection.getCharacteristics(uuid=self.notify_uuid)[0]
        notify_handle = ch.getHandle() + 1
        self.connection.writeCharacteristic(notify_handle, b'\x01\x00', withResponse=True)

    def _set_write_handle(self):
        ch = self.connection.getCharacteristics(uuid=self.write_uuid)[0]
        self.write_handle = ch.getHandle()

    def _write_cmd(self, method, post_cmd=None):
        if method != Method.AUTH:
            if not self._authorized:
                raise exceptions.AuthenticationError

        cmd = bytearray(b'\x55')
        cmd.extend(self.iter.to_bytes(1, byteorder='little'))
        self._inc_iter()
        cmd.extend(method.value.to_bytes(1, byteorder='little'))

        if post_cmd is not None:
            cmd.extend(post_cmd)
        cmd.extend(b'\xaa')
        self.connection.writeCharacteristic(self.write_handle, cmd)
        self.connection.waitForNotifications(2.0)

    def _inc_iter(self):
        if self.iter == 100:
            self.iter = 0
        else:
            self.iter += 1

    def auth(self):
        cmd = bytearray(self.key)
        self._write_cmd(Method.AUTH, cmd)

    def _read_version(self):
        self._write_cmd(Method.VERSION)

    def _set_mode(self, mode, temperature=0):
        cmd = bytearray(mode.value.to_bytes(1, byteorder='little'))
        cmd.extend(b'\x00')
        cmd.extend(temperature.to_bytes(1, byteorder='little'))
        cmd.extend(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        cmd.extend(b'\x80')
        cmd.extend(b'\x00\x00')
        self._write_cmd(Method.SET_MODE, cmd)

    def _get_mode(self):
        self._write_cmd(Method.GET_MODE)

    def update_state(self):
        self._get_mode()

    def run(self):
        self._write_cmd(Method.RUN)
        self._get_mode()

    def stop(self):
        self._write_cmd(Method.STOP)
        self._get_mode()

    def boil(self):
        self.stop()
        self._set_mode(Mode.BOILING)
        self.run()

    def heat(self, temperature):
        self.stop()
        self._set_mode(Mode.HEAT, temperature)
        self.run()

    # TODO: check for working
    def lamp(self):
        self.stop()
        self._set_mode(Mode.LAMP)
        self.run()


class NotificationDispatcher(btle.DefaultDelegate):

    teapot = None

    def __init__(self, teapot):
        btle.DefaultDelegate.__init__(self)
        self.teapot = teapot

    def _handle_auth(self, data):
        if data[3] == 1:
            self.teapot.authorized = True
        else:
            self.teapot.authorized = False

    def _handle_version(self, data):
        self.teapot.version = '{0}.{1}'.format(data[3], data[4])

    @staticmethod
    def _handle_set_mode(data):
        if data[3] != 1:
            raise exceptions.SetModeError(data)

    @staticmethod
    def _handle_run(data):
        if data[3] != 1:
            raise exceptions.RunError(data)

    @staticmethod
    def _handle_stop(data):
        if data[3] != 1:
            raise exceptions.StopError(data)

    def _handle_get_mode(self, data):
        self.teapot.mode = Mode(data[3])
        self.teapot._dest_temperature = data[5]
        self.teapot.temperature = data[8]
        self.teapot.state = State(data[11])

    def handleNotification(self, cHandle, data):
        method = Method(data[2])

        if method == Method.AUTH:
            self._handle_auth(data)
        elif method == Method.VERSION:
            self._handle_version(data)
        elif method == Method.SET_MODE:
            self._handle_set_mode(data)
        elif method == Method.RUN:
            self._handle_run(data)
        elif method == Method.STOP:
            self._handle_stop(data)
        elif method == Method.GET_MODE:
            self._handle_get_mode(data)