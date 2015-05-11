
import nodenet
from random import randrange
from uuid import uuid4


class Ports(nodenet.Node):
    def __init__(self, loop=nodenet.loop):
        super(Ports, self).__init__(loop)

        self.services = {}
        self.ports = []
        self.on('register', self._on_register)
        self.on('bound', self._on_bound)

    def _on_register(self, who, service):
        peers = [p for p in self.peers if not who == p]
        self.emit('register', service, to=peers)

    def _on_bound(self, who):
        host, port = who
        self.ports.append(port)

    def _bind(self):
        port = randrange(10000, 65535)
        while port in self.ports:
            port = randrange(10000, 65535)

        self.bind('127.0.0.1', port)
        self.emit('bound')

    def register(self, name, **kwargs):
        if self.sockname == (None, None):
            return None

        rng = kwargs.get('range')
        port = kwargs.get('port')
        while port in self.ports or port is None:
            port = randrange(*(rng or (10000, 65535)))

        service = {'port': port, 'id': str(uuid4())}

        if not self.services.get(name):
            self.services[name] = []

        self.services[name].append(service)
        self.ports.append(port)
        self.emit('register', service)

        return port

    def connect(self, *who):
        if self.sockname == (None, None):
            self._bind()

        super(Ports, self).connect(*who)
