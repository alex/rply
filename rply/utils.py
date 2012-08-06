from collections import MutableMapping


class IdentityDict(MutableMapping):
    def __init__(self):
        self._contents = {}
        self._keepalive = []

    def __getitem__(self, key):
        return self._contents[id(key)][1]

    def __setitem__(self, key, value):
        idx = len(self._keepalive)
        self._keepalive.append(key)
        self._contents[id(key)] = key, value, idx

    def __delitem__(self, key):
        raise NotImplementedError

    def __len__(self):
        raise NotImplementedError

    def __iter__(self):
        for key, _, _ in self._contents.itervalues():
            yield key
