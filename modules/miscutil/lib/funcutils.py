import functools


"""Taken from http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize"""


class memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args, **kwargs):
        if (args, kwargs) in self.cache:
            return self.cache[(args, kwargs)]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        return repr(self.func)

    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)
