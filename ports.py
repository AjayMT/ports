
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
        self.on('unregister', self._on_unregister)
        self.on('disconnect', self._on_disconnect)
        self.on('close', self._on_close)

    def _on_register(self, who, service):
        for name, services in self.services.items():
            for s in services:
                if s == service:
                    s['_peer'] = who

        service['_peer'] = self.sockname

        peers = [p for p in self.peers if not who == p]
        self.emit('register', service, to=peers)

    def _on_bound(self, who):
        host, port = who
        self.ports.append(port)

    def _on_unregister(self, who, service):
        for name, services in self.services.items():
            if service in services:
                services.remove(service)

    def _on_close(self, *args):
        def lsum(l): return l[0] + lsum(l[1:]) if l else []

        [self.unregister(s) for s in lsum(self.services.values())
         if s['_peer'] == self.sockname]

    def _on_disconnect(self, who):
        self.ports.remove(who[1])

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

        service = {'port': port, 'id': str(uuid4()), '_peer': self.sockname}

        if not self.services.get(name):
            self.services[name] = []

        self.services[name].append(service)
        self.ports.append(port)
        self.emit('register', service)

        return service

    def unregister(self, service):
        self._on_unregister(self.sockname, service)
        self.emit('unregister', service)

    def connect(self, *who):
        if self.sockname == (None, None):
            self._bind()

        super(Ports, self).connect(*who)
