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


from itertools import chain
from backend import neo4j, JTypes
from util import cached_property
from core import Node, Relationship, Direction

class Order:
    DEPTH_FIRST = neo4j.Traverser.Order.DEPTH_FIRST
    BREADTH_FIRST = neo4j.Traverser.Order.BREADTH_FIRST

class Stop:
    DEPTH_ONE = neo4j.StopEvaluator.DEPTH_ONE
    END_OF_GRAPH = neo4j.StopEvaluator.END_OF_GRAPH
    
class Returnable:
    ALL = neo4j.ReturnableEvaluator.ALL
    ALL_BUT_START_NODE = neo4j.ReturnableEvaluator.ALL_BUT_START_NODE


class Traverser(object):
    order = Order.BREADTH_FIRST
    types = []
    is_stop = Stop.END_OF_GRAPH
    is_returnable = Returnable.ALL_BUT_START_NODE
    
    class DynamicStopEvaluator(neo4j.NativeStopEvaluator):
        def __init__(self, method):
            neo4j.NativeStopEvaluator.__init__(self)
            self.__method = method
        def isStopNode(self, pos):
            self.__method(TraversalPosition(pos))
    
    class DynamicReturnableEvaluator(neo4j.NativeReturnableEvaluator):
        def __init__(self, method):
            neo4j.NativeReturnableEvaluator.__init__(self)
            self.__method = method
        def isStopNode(self, pos):
            self.__method(TraversalPosition(pos))
    
    def __init__(self, node):
        self.__jobj__ = node.__jobj__.traverse(*self.as_arg_list())
    
    
    def as_arg_list(self):
        if neo4j.ReturnableEvaluator.instance_(self.is_returnable):
            ret_eval = self.is_returnable
        else:
            ret_eval = self.DynamicReturnableEvaluator(self.is_returnable)
            
        if neo4j.StopEvaluator.instance_(self.is_stop):
            stop_eval = self.is_stop
        else:
            stop_eval = self.DynamicStopEvaluator(self.is_stop)
        
        return [self.order, stop_eval, ret_eval] + list(chain.from_iterable(
                    ((rt.__jobj__, rt.direction.__jobj__) \
                    if hasattr(rt, 'direction') \
                    else (rt.__jobj__, Direction.Both.__jobj__) \
                    for rt in self.types) ))
    
    @property
    def current_position(self):
        return TraversalPosition(self.__jobj__.currentPosition())
    
    @cached_property
    def all_nodes(self):
        return [Node(JTypes.Node.cast_(jnode)) for jnode in self.__jobj__.getAllNodes()]
    
    def __iter__(self):
        for jnode in iter(self.__jobj__):
            yield Node(JTypes.Node.cast_(jnode))        #not sure why these need to be casted, but they do
            

#def create_traverser(types, order=None, stop_evaluator=None, return_evaluator=None):
#    class DynamicTraverser(Traverser):
#        pass
#    
#    DynamicTraverser.rel_types = types
#    if order:
#        DynamicTraverser.order = order
#    if stop_evaluator:
#        DynamicTraverser.is_stop = stop_evaluator
#    if return_evaluator:
#        DynamicTraverser.is_returnable = return_evaluator
#        
#    return DynamicTraverser


class TraversalPosition(object):
    def __init__(self, java_pos):
        self.__jobj__ = java_pos
        
    @cached_property
    def node(self):
        return Node(self.__jobj__.currentNode())
    
    @cached_property
    def depth(self):
        return self.__jobj__.depth()
    @cached_property
    def num_returned(self):
        return self.__jobj__.returnedNodesCount()
    
    @cached_property
    def is_start(self):
        return bool(self.__jobj__.isStartNode())
    
    @cached_property
    def last_relationship(self):
        if self.is_start: return None
        return Relationship(self.__jobj__.lastRelationshipTraversed())
    
    @cached_property
    def previous_node(self):
        return Node(self.__jobj__.previousNode())
    
    