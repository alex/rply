import sys

if sys.version_info >= (3, 3):
    from collections.abc import MutableMapping
else:
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
        del self._contents[id(key)]
        for idx, obj in enumerate(self._keepalive):
            if obj is key:
                del self._keepalive[idx]
                break

    def __len__(self):
        return len(self._contents)

    def __iter__(self):
        for key, _, _ in itervalues(self._contents):
            yield key


class Counter(object):
    def __init__(self):
        self.value = 0

    def incr(self):
        self.value += 1


if sys.version_info >= (3,):
    def itervalues(d):
        return d.values()

    def iteritems(d):
        return d.items()
else:
    def itervalues(d):
        return d.itervalues()

    def iteritems(d):
        return d.iteritems()
