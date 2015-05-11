
import nodenet
from random import randrange
from uuid import uuid4


class Ports(nodenet.Node):
    def __init__(self, loop=nodenet.loop):
        super(Ports, self).__init__(loop)

        self.services = {}
        self.on('register', self.on_register)

    def on_register(self, who, service):
        peers = [p for p in self.peers if not who == p]
        self.emit('register', service, to=peers)

    def register(self, name, **kwargs):
        if not self.sockname[0]:
            return None

        ports = []
        for s in self.services.values():
            ports += [p['port'] for p in s]

        rng = kwargs.get('range')
        port = kwargs.get('port')
        while port in ports or port is None:
            port = randrange(*(rng or (10000, 65535)))

        service = {'port': port, 'id': str(uuid4())}

        if not self.services.get(name):
            self.services[name] = []

        self.services[name].append(service)
        self.emit('register', service)

        return port
