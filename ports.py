
import nodenet
from random import randrange
from uuid import uuid4
from fnmatch import fnmatch


def _lsum(l): return l[0] + _lsum(l[1:]) if l else []


class Ports(nodenet.Node):
    def __init__(self, loop=nodenet.loop):
        super(Ports, self).__init__(loop)

        self.services = {}
        self.ports = []
        self._auto_bound = False

        self.on('connect', self._on_connect)
        self.on('register', self._on_register)
        self.on('auto-bind', self._on_auto_bind)
        self.on('unregister', self._on_unregister)
        self.on('close', self._on_close)

    def _on_connect(self, who):
        if self._auto_bound:
            self.emit('auto-bind', self.sockname[1], to=[who])

    def _on_register(self, who, service):
        service['_peer'] = tuple(service['_peer'])
        if service['name'] not in self.services:
            self.services[service['name']] = []

        self.services[service['name']].append(service)

        s = {k: v for k, v in service.items()}
        s['_peer'] = self.sockname

        peers = [p for p in self.peers if not who == p]
        self.emit('register', s, to=peers)

    def _on_auto_bind(self, who, port):
        self.ports.append(port)

        peers = [p for p in self.peers if not who == p]
        self.emit('auto-bind', port, to=peers)

    def _on_unregister(self, who, service):
        service['_peer'] = tuple(service['_peer'])
        self.services[service['name']].remove(service)

        service['_peer'] = self.sockname
        peers = [p for p in self.peers if not who == p]
        self.emit('unregister', service, to=peers)

    def _on_close(self, *args):
        [self.unregister(s) for s in _lsum(self.services.values())
         if s['_peer'] == self.sockname]

    def _on_disconnect(self, who):
        super(Ports, self)._on_disconnect(who)

        if who[1] in self.ports:
            self.ports.remove(who[1])

    def _bind(self):
        port = randrange(10000, 65535)
        while port in self.ports:
            port = randrange(10000, 65535)

        self.bind('127.0.0.1', port)
        self._auto_bound = True

    def __getitem__(self, item):
        return _lsum([ss for name, ss in self.services.items()
                      if fnmatch(name, item)])

    def __contains__(self, item):
        return bool(self[item])

    def register(self, name, **kwargs):
        if self.sockname == (None, None):
            return None

        rng = kwargs.get('range')
        port = kwargs.get('port')
        while port in self.ports or port is None:
            port = randrange(*(rng or (10000, 65535)))

        service = {'port': port, 'id': str(uuid4()), '_peer': self.sockname,
                   'name': name}

        if name not in self.services:
            self.services[name] = []

        self.services[name].append(service)
        self.ports.append(port)
        self.emit('register', service)

        return service

    def unregister(self, service):
        service['_peer'] = tuple(service['_peer'])
        self.services[service['name']].remove(service)

        self.emit('unregister', service)

    def connect(self, *who):
        if self.sockname == (None, None):
            self._bind()

        super(Ports, self).connect(*who)
