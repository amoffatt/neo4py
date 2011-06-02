# Copyright (c) 2011 "Aaron Moffatt"
# aaronmoffatt.com
# 
# This file is part of Neo4py.
# 
# Neo4py is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import itertools
from backend import neo4j as java

ITER_BUFFER_SIZE = 100


VALUE_METHOD_MAPPING = (
    (java.String, 'toString'),
    (java.Integer, 'intValue'),
    (java.Short, 'shortValue'),
    (java.Float, 'floatValue'),
    (java.Double, 'doubleValue')
)

PY2J_TYPE_MAP = {
    int     : java.Integer,
    long    : java.Long,
    str     : java.String,
    unicode : java.String,
    float   : java.Double,
}


#NOTE: should transaction handling take place at graph/node level or at model level.  Thinking model.
###TODO
def transactional(f, retry=False, retry_delay=5, retry_count=3):
    def inner(frame, *args, **kwargs):
        #ensure transaction
        tx, created = frame._neo.get_tx()
        try:
            retval = f(frame, *args, **kwargs)
        except:
            if created:
                tx.failure()
            raise
        finally:
            if created:
                tx.finish(True)
        return retval
        
    return inner


def fancy_property(function):     # from http://wiki.python.org/moin/PythonDecoratorLibrary
    keys = 'fget', 'fset', 'fdel'
    func_locals = {'doc':function.__doc__}
    def probe_func(frame, event, arg):
        if event == 'return':
            locals = frame.f_locals
            func_locals.update(dict((k, locals.get(k)) for k in keys))
            sys.settrace(None)
        return probe_func
    sys.settrace(probe_func)
    function()
    return property(**func_locals)

class cached_property(property):
    '''Decorator. Caches result from property getter after
    first reading.'''
    def __init__(self, f):
        self.__f = f
        super(cached_property, self).__init__(self.fget)
        
    def fget(self, frame):
        value = self.__f(frame)
        frame.__dict__[self.__f.__name__] = property(self.__f)
        return value


class BufferedIterator(object):
    def __init__(self, java_node_iter, buffer_size=ITER_BUFFER_SIZE, constructor=None):
        self._iter = java_node_iter
        self.buffer_size = buffer_size
        self.constructor = constructor
        self._finished = False
        
    def append(self, *java_node_iters):
        self._iter = itertools.chain(self._iter, *java_node_iters)
        
    def __iter__(self):
        while True:
            buffer = self._buffer_next()
            for item in buffer:
                yield item
            if len(buffer) < self.buffer_size:
                self._finished = True
                break
            
#    @transactional            #NOTE: perhaps transaction handling should be at a higher level.
    def _buffer_next(self):
        constructor = self.constructor
        return [constructor(n) for n in itertools.islice(self._iter, self.buffer_size)]
    

def java_isinstance(jvalue, *types):
    for t in types:
        if t.instance_(jvalue):
            return True
    return False

#def py_isstring(v):
#    return isinstance(v, basestring)
#
#
#def java_isstring(v):
#    return java.String.instance_(v)
#    
#def java_isfloat(v):
#    java_isinstance(v, java.Float, java.Double)
#    
#def java_isint(v):
#    java_isinstance(v, java.Integer, java.Long, java.Short)
    
    #TODO is there a better/faster way to do this?
def java_to_py(v):
    for clazz, method in VALUE_METHOD_MAPPING:
        if clazz.instance_(v):
            return getattr(clazz.cast_(v), method)()
    raise ValueError("Unknown value type:" + str(v))

def dict_to_jmap(d):
    for k,v in d.iteritems():
        try:
            key_type = PY2J_TYPE_MAP[type(k)]
            value_type = PY2J_TYPE_MAP[type(v)]
        except KeyError:
            raise ValueError("Unsupported type in dict pair: (%s, %s)" % (type(k), type(v)))
        break
    
    jmap = java.HashMap().of_(key_type, value_type)
    for k,v in d.iteritems():
        jmap.put(k,v)
        
    return jmap
    
    
    