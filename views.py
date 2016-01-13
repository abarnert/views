from abc import abstractmethod
import builtins
from collections.abc import Iterable, Sized, Sequence#, Reversible
import itertools

class Reversible(Iterable):
    __slots__ = ()
    @abstractmethod
    def __reversed__(self):
        while False:
            yield None
    @classmethod
    def __subclasshook__(cls, C):
        if cls is Reversible:
            if (any("__iter__" in B.__dict__ for B in C.__mro__) and
                any("__reversed__" in B.__dict__ for B in C.__mro__)):
                return True
        return NotImplemented

Reversible.register(Sequence)

# Accepts any iterables
class MapIterableView(Iterable):
    def __init__(self, func, *iterables):
        self._func, self._iterables = func, iterables
    def __iter__(self):
        while True:
            values = (next(it) for it in self._iterables)
            yield self._func(*values)
    def __repr__(self):
        return '{}({}, {})'.format(type(self).__name__,
                                   self._func.__qualname__,
                                   ', '.join(str(it) for it in self._iterables))

# Accepts a single reversible iterable
class MapReversibleView(Reversible, MapIterableView):
    def __reversed__(self):
        yield from (self._func(value)
            for value in reversed(self._iterables[0]))

# Accepts any number of sized, reversible iterables
class MapSizedView(Sized, MapReversibleView):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._len = min(len(it) for it in self._iterables)
    def __len__(self):
        return self._len
    def __reversed__(self):
        revs = [itertools.islice(reversed(it), len(it) - self._len, None)
                for it in self._iterables]
        while True:
            values = (next(it) for it in revs)
            yield self._func(*values)

# Accepts any number of sequences
class MapSequenceView(Sequence, MapSizedView):
    def __getitem__(self, index):
        if isinstance(index, slice):
            return islice(self, index.start, index.stop, index.step)
        values = (it[index] for it in self._iterables)
        return self._func(*values)

def map(func, *iterables):
    if all(isinstance(it, Sequence) for it in iterables):
        return MapSequenceView(func, *iterables)
    elif (all(isinstance(it, Sized) and isinstance(it, Reversible)
              for it in iterables)):
        return MapSizedView(func, *iterables)
    elif len(iterables) == 1 and isinstance(iterables[0], Reversible):
        return MapReversibleView(func, *iterables)
    else:
        for it in iterables:
            if not isinstance(it, Iterable):
                raise TypeError("'{}' object is not iterable".format(
                    type(it).__name))
        return MapIterableView(func, *iterables)

class StarMapIterableView(Iterable):
    def __init__(self, func, iterable):
        self._func, self._iterable = func, iterable
    def __iter__(self):
        while True:
            values = next(it)
            yield self._func(*values)
    def __repr__(self):
        return '{}({}, {})'.format(type(self).__name__,
                                   self._func.__qualname__,
                                   self._iterable)

class StarMapReversibleView(Reversible, StarMapIterableView):
    def __reversed__(self):
        yield from (self._func(*value) for value in reversed(self._iterable))

class StarMapSizedView(Sized, StarMapReversibleView):
    def __len__(self):
        return len(self._iterable)

class StarMapSequenceView(Sequence, StarMapSizedView):
    def __getitem__(self, index):
        if isinstance(index, slice):
            return islice(self, index.start, index.stop, index.step)
        return self._func(*self._iterable[index])

def starmap(func, iterable):
    if isinstance(iterable, Sequence):
        return StarMapSequenceView(func, iterable)
    elif isinstance(iterable, Sized) and isinstance(iterable, Reversible):
        return StarMapSizedView(func, iterable)
    elif isinstance(iterable, Reversible):
        return StarMapReversibleView(func, iterable)
    elif isinstance(iterable, Iterable):
        return StarMapIterableView(func, iterable)
    raise TypeError("'{}' object is not iterable".format(
        type(iterable).__name__))

class FilterIterableView(Iterable):
    def __init__(self, func, iterable):
        if func is None: func = bool
        self._func, self._iterable = func, iterable
    def __iter__(self):
        for value in self._iterable:
            if self._func(value):
                yield value
    def __repr__(self):
        return '{}({}, {})'.format(type(self).__name__,
                                   self._func.__qualname__,
                                   self._iterable)

class FilterReversibleView(FilterIterableView, Reversible):
    def __reversed__(self):
        for value in reversed(self._iterable):
            if self._func(value):
                yield value

def filter(func, iterable):
    if isinstance(iterable, Reversible):
        return FilterReversibleView(func, iterable)
    elif isinstance(iterable, Iterable):
        return FilterIterableView(func, iterable)
    raise TypeError("'{}' object is not iterable".format(
        type(iterable).__name__))

class ZipIterableView(Iterable):
    def __init__(self, *iterables):
        self._iterables = iterables
    def __iter__(self):
        while True:
            yield tuple(next(it) for it in self._iterables)
    def __repr__(self):
        return '{}({})'.format(type(self).__name__,
                               ', '.join(str(it) for it in self._iterables))

class ZipReversibleView(Reversible, ZipIterableView):
    def __reversed__(self):
        yield from ((value,) for value in reversed(self._iterables[0]))

class ZipSizedView(Sized, ZipReversibleView):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._len = min(len(it) for it in self._iterables)
    def __len__(self):
        return self._len
    def __reversed__(self):
        revs = [itertools.islice(reversed(it), len(it) - self._len, None)
                for it in self._iterables]
        while True:
            yield tuple(next(it) for it in revs)

class ZipSequenceView(Sequence, ZipSizedView):
    def __getitem__(self, index):
        if isinstance(index, slice):
            return islice(self, index.start, index.stop, index.step)
        return tuple(it[index] for it in self._iterables)

def zip(*iterables):
    if all(isinstance(it, Sequence) for it in iterables):
        return ZipSequenceView(*iterables)
    elif (all(isinstance(it, Sized) and isinstance(it, Reversible)
              for it in iterables)):
        return ZipSizedView(*iterables)
    elif len(iterables) == 1 and isinstance(iterables[0], Reversible):
        return ZipReversibleView(*iterables)
    else:
        for it in iterables:
            if not isinstance(it, Iterable):
                raise TypeError("'{}' object is not iterable".format(
                    type(it).__name))
        return ZipIterableView(*iterables)

class ZipLongestIterableView(Iterable):
    def __init__(self, *iterables, fillvalue):
        self._iterables, self._fillvalue = iterables, fillvalue
    def __iter__(self):
        counter = len(self._iterables) - 1
        def sentinel():
            nonlocal counter
            if not counter:
                raise ZipExhausted
            counter -= 1
            yield self._fillvalue
        fillers = repeat(fillvalue)
        iterators = [itertools.chain(it, sentinel(), fillers)
                     for it in self._iterables]
        try:
            while iterators:
                yield tuple(next(it) for it in iterators)
        except ZipExhausted:
            pass
    def __repr__(self):
        return '{}({}, fillvalue={})'.format(
            type(self).__name__,
            ', '.join(str(it) for it in self._iterables),
            self._fillvalue)

class ZipLongestReversibleView(Reversible, ZipIterableView):
    def __reversed__(self):
        yield from ((value,) for value in reversed(self._iterables[0]))

class ZipLongestSizedView(Sized, ZipLongestReversibleView):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._len = max(len(it) for it in self._iterables)
    def __len__(self):
        return self._len
    def __reversed__(self):
        revs = [itertools.chain(repeat(self._fillvalue, self._len - len(it)),
                                reversed(it))
                for it in self._iterables]
        while True:
            yield tuple(next(it) for it in revs)

class ZipLongestSequenceView(Sequence, ZipLongestSizedView):
    def __getitem__(self, index):
        if isinstance(index, slice):
            return islice(self, index.start, index.stop, index.step)
        if index < 0:
            index += len(self)
        if index < 0 or index >= len(self):
            raise IndexError
        return tuple(it[index] if index < len(it) else self._fillvalue
                     for it in self._iterables)

def zip_longest(func, *iterables, fillvalue=None):
    if all(isinstance(it, Sequence) for it in iterables):
        return ZipLongestSequenceView(*iterables, fillvalue=fillvalue)
    elif (all(isinstance(it, Sized) and isinstance(it, Reversible)
              for it in iterables)):
        return ZipLongestSizedView(*iterables, fillvalue=fillvalue)
    elif len(iterables) == 1 and isinstance(iterables[0], Reversible):
        return ZipLongestReversibleView(func, *iterables, fillvalue=fillvalue)
    else:
        for it in iterables:
            if not isinstance(it, Iterable):
                raise TypeError("'{}' object is not iterable".format(
                    type(it).__name))
        return ZipLongestIterableView(func, *iterables)
    
class EnumerateIterableView(Iterable):
    def __init__(self, iterable, start):
        self._iterable, self._start = iterable, start
    def __iter__(self):
        yield from builtins.enumerate(self._iterable, self._start)
    def __repr__(self):
        return '{}({}, {})'.format(type(self).__name__,
                                   self._iterable, self._start)

class EnumerateSizedView(Sized, Reversible, EnumerateIterableView):
    def __len__(self):
        return len(self._iterable)
    def __reversed__(self):
        l = len(self._iterable)
        for i, value in builtins.enumerate(reversed(self._iterable)):
            yield l-i-1+self._start, value

class EnumerateSequenceView(Sequence, EnumerateSizedView):
    def __getitem__(self, index):
        if isinstance(index, slice):
            return islice(self, *slice)
        if index < 0:
            index += len(self)
        return index+self._start, self._iterable[index]

def enumerate(iterable, start=0):
    if isinstance(iterable, Sequence):
        return EnumerateSequenceView(iterable, start)
    elif isinstance(iterable, Sized) and isinstance(iterable, Reversible):
        return EnumerateSizedView(iterable, start)
    elif isinstance(iterable, Iterable):
        return EnumerateIterableView(iterable, start)
    raise TypeError("'{}' object is not iterable".format(
        type(iterable).__name__))
    
class SliceIterableView(Iterable):
    def __init__(self, iterable, start, stop, step):
        self._iterable = iterable
        self.start, self.stop, self.step = start, stop, step
    def __iter__(self):
        yield from itertools.islice(self._iterable,
                                    self.start, self.stop, self.step)
    def __repr__(self):
        return '{}({}, {}, {}, {})'.format(type(self).__name__,
                                           self._iterable, self._start,
                                           self._stop, self._step)
        
class SliceSizedView(Sized, Reversible, SliceIterableView):
    def _range(self):
        s = slice(self.start, self.stop, self.step)
        return range(*s.indices(len(self._iterable)))
    def __len__(self):
        return len(self._range())
    def __reversed__(self):
        r = self._range()
        for i, e in reversed(enumerate(self)):
            if i in r:
                yield e

class SliceSequenceView(Sequence, SliceSizedView):
    def __getitem__(self, index):
        r = self._range()
        if isinstance(index, slice):
            return type(self)(self._iterable, r.start, r.stop, r.step)
        return self._iterable[r[index]]
    def __reversed__(self):
        for i in reversed(self._range()):
            yield self._iterable[i]

_sentinel = object()
def islice(iterable, start_or_stop, stop=_sentinel, step=None):
    if stop is _sentinel:
        start, stop = 0, start_or_stop
    else:
        start = start_or_stop
    if isinstance(iterable, Sequence):
        return SliceSequenceView(iterable, start, stop, step)
    elif isinstance(iterable, Sized) and isinstance(iterable, Reversible):
        return SliceSizedView(iterable, start, stop, step)
    elif isinstance(iterable, Iterable):
        if start and start < 0 or stop and stop < 0 or step and step < 0:
            raise TypeError("'{}' object is not sized".format(
                type(iterable).__name__))
        return SliceIterableView(iterable, start, stop, step)
    raise TypeError("'{}' object is not iterable".format(
        type(iterable).__name__))

def test():
    from operator import add
    
    a = range(0, 100, 2)
    b = range(100)
    mab = map(add, a, b)
    assert list(mab) == list(range(0, 150, 3))
    iab = islice(mab, -10, None, 2)
    assert list(iab) == list(range(120, 150, 6))
    ieab = islice(enumerate(mab), -10, None, 2)
    assert list(ieab) == list(builtins.enumerate(mab))[-10::2]
    eiab = enumerate(iab)
    assert list(eiab) == list(builtins.enumerate(range(120, 150, 6)))

    fb = filter(lambda x: x%2, b)
    assert list(fb) == list(range(100)[1::2])
    
