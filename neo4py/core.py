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


from itertools import islice
from backend import neo4j, rel_type, JTypes
from util import transactional, fancy_property, cached_property, BufferedIterator, java_to_py
#from helpers import create_traverser

__all__ = 'Direction', 'DirectedRelationshipType' 'PropertyContainer', 'Node', 'Relationship', 'NodeIterator', 'RelationshipIterator'

        
class _Direction(object):
    def __init__(self, java_direction):
        self.__jobj__ = java_direction
    def __call__(self, type):
        return DirectedRelationshipType(self, type)
    def __getattr__(self, attr):
        return self(attr)
    
    @cached_property
    def name(self):     return self.__jobj__.name()
    def __str__(self):  return self.name


class Direction:
    Incoming = _Direction(neo4j.Direction.INCOMING)
    Outgoing = _Direction(neo4j.Direction.OUTGOING)
    Both = _Direction(neo4j.Direction.BOTH)
    Undirected = Both

class RelationshipType(object):
    def __init__(self, type):
        if neo4j.RelationshipType.instance_(type):
            self.__jobj__ = type
            self._name = type.name()
        else:
            self.__jobj__ = rel_type(type)
            self._name = type
            
    @property
    def name(self):     return self._name
    def __str__(self):  return self._name


class DirectedRelationshipType(RelationshipType):
    def __init__(self, direction, type):
        super(DirectedRelationshipType, self).__init__(type)
        self.direction = direction
        
    def __str__(self):
        return "<%s (%s)>" % (self.name, self.direction.name)
        

class PropertyContainer(object):
    def __init__(self, java_container):
        self.__jobj__ = java_container

    @cached_property
    def id(self):               return self.__jobj__.getId()
    
    @cached_property
    def __neo__(self):          return self.__jobj__.getGraphDatabase()
        
    def __getitem__(self, k):
        try:
            return java_to_py(self.__jobj__.getProperty(k))     #TODO support array types
        except:
            raise KeyError(k)
        
    def __setitem__(self, k,v):
        try:
            self.__jobj__.setProperty(k,v)     #TODO support array types
        except:
            raise TypeError("Value of unsupported type: %s" % (v))
        
    def __contains__(self, k):
        return self.__jobj__.hasProperty(k)
    
    def __delitem__(self, k):
        self.__jobj__.removeProperty(k)
        
    def __iter__(self):
        return iter(self.__jobj__.propertyKeys)
    
    def get(self, k, default=None):
        try:
            return self[k]
        except KeyError:
            return default
    
    def update(self, *args, **kwargs):
        for d in args:
            if d:
                for k,v in d.iteritems():
                    self[k] = v
        
        for k,v in kwargs.iteritems():
            self[k] = v
            
    def iteritems(self):
        for k in self:
            yield k, self[k]
            
    def __len__(self):      ##NOTE not efficient, but caching would also cause issues
        cnt = 0
        i = iter(self)
        for x in i:
                cnt += 1
        return cnt
    
    def __str__(self):
            return "{%d properties}" % len(self)
    
class Node(PropertyContainer):
    def __init__(self, java_node):
        super(Node, self).__init__(java_node)

    def delete(self):           return self.__jobj__.delete()     #TODO may need to add relationship deletion here
    
    #def remove(self):            #method to remove relationships AND delete?
    
    def relationships(self, *types):
        rel_types = [RelationshipType(t) for t in types]
        return RelationshipFactory(self.__jobj__, Direction.Both, rel_types)

    def __hash__(self): return self.id
    
    def __eq__(self, other):
        return isinstance(other, Node) and other.id == self.id
    
    def __getattr__(self, attr):
        try:
            return super(Node, self).__getattr__(attr)
        except AttributeError:
            return self.relationships(attr)
        
    def __str__(self):
        return "Node(%s)" % super(Node, self).__str__()
    
#    def traverse(self, types, order=None, stop_evaluator=None, return_evaluator=None):
#        '''Alternative to subclassing Traverser, though slightly less efficient'''
#        t = create_traverser(types, order, stop_evaluator, return_evaluator)
#        return t(self)
        
         
        
class Relationship(PropertyContainer):
    def __init__(self, java_relationship):
        super(Relationship, self).__init__(java_relationship)
    
    @cached_property
    def type(self):     return self.__jobj__.getType().name()
    
    @cached_property
    def start(self):    return Node(self.__jobj__.getStartNode())
    
    @cached_property
    def end(self):      return Node(self.__jobj__.getEndNode())
    
    @cached_property
    def other(self):    return Node(self.__jobj__.getOtherNode())
    
    @cached_property
    def nodes(self):    return (self.start, self.end)
    
    def istype(self, tp_name):
        return self.__jobj__.isType(rel_type(tp_name))
    
    def delete(self):   self.__jobj__.delete()
    
    def __hash__(self): return self.id
    
    def __eq__(self, other):
        return isinstance(other, Relationship) and other.id == self.id
    
    def __str__(self):
        return "Relationship(%s)" % super(Node, self).__str__()
    

class RelationshipFactory(object):
    def __init__(self, java_node, dir, types):
        self.__jn__ = java_node
        self.__jdir = dir.__jobj__
        self.__types = types
        if len(types) == 1:
            self.__jsingle_type = self.__types[0].__jobj__
        else:
            self.__jsingle_type = None
    def _get_relationships(self):
        if not self.__types:
            for rel in self.__jn__.getRelationships(self.__jdir):
                yield rel
        elif len(self.__types) > 1:
            for type in self.__types:
                for rel in self.__jn__.getRelationships(type, self.__jdir):
                    yield rel
        else:
            for rel in self.__jn__.getRelationships(self.__jsingle_type,
                                                    self.__jdir):
                yield rel
    def _has_relationship(self):
        if not self.__types:
            return self.__jn__.hasRelationship(self.__jdir)
        elif len(self.__types) > 1:
            for type in self.__types:
                if self.__jn__.hasRelationship(type, self.__jdir):
                    return True
            return False
        else:
            return self.__jn__.hasRelationship(self.__jsingle_type,
                                               self.__jdir)
    def __single(self):
        if not self.__jsingle_type:
            raise TypeError("No single relationship type!")
        return self.__jn__.getSingleRelationship(self.__jsingle_type,
                                                 self.__jdir)

    def __call__(self, node, **attributes):
        if isinstance(node, JTypes.Node):
            jnode = node
        elif isinstance(node, Node):
            jnode = node.__jobj__
        else:
            raise TypeError("Invalid type for node [%s]" % type(node))
        
        if self.__jdir is Direction.Incoming:
            relationship = jnode.createRelationshipTo(
                self.__jn__, self.__jsingle_type)
        else:
            relationship = self.__jn__.createRelationshipTo(
                jnode, self.__jsingle_type)
        relationship = Relationship(relationship)
        relationship.update(attributes)
        return relationship
    
    def __iter__(self):
        return iter(RelationshipIterator(self._get_relationships()))
    
    def __nonzero__(self):
        return self._has_relationship()

    
    @fancy_property
    def single():
        def fget(self):
            single = self.__single()
            if single:
                return Relationship(single)
    
        def fset(self, node):
            del self.single
            self(node)

        def fdel(self):
            single = self.__single()
            if single: single.delete()
        
    @property
    def incoming(self):
        return RelationshipFactory(self.__jn__,
                                   Direction.Incoming, self.__types)
    @property
    def outgoing(self):
        return RelationshipFactory(self.__jn__,
                                   Direction.Outgoing, self.__types)

    
class NodeIterator(BufferedIterator):
    def __init__(self, *java_node_iters, **kwargs):
        super(NodeIterator, self).__init__(constructor=Node, *java_node_iters, **kwargs)

class RelationshipIterator(BufferedIterator):
    def __init__(self, *java_rel_iters, **kwargs):
        super(RelationshipIterator, self).__init__(constructor=Relationship, *java_rel_iters, **kwargs)
    
        
