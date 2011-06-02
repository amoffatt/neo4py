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


from backend import neo4j
from util import cached_property
from core import Node, Relationship, NodeIterator
from index import NodeIndexFactory, RelationshipIndexFactory

__all__ = "GraphDatabase", "Transaction"

class GraphDatabase(object):
    def __init__(self, db_path):
        self.__neo__ = neo = neo4j.EmbeddedGraphDatabase(db_path)
        self._nodeshop = NodeShop(neo)
        self._relshop = RelationshipShop(neo)
        self._current_tx = None
        self._current_tx_thread = None      #use to determine if more than one thread is being used
                                            #and if so, store current transaction by thread in a dict
        self._running = True
        
    def get_tx(self):
        '''tuple of (tx, created).  created is True if a transaction was not already in progress. If
        created is True, it is this scopes responsibility to finish() this transaction'''
        created = False
        if self._current_tx is not None:
            if self._current_tx.finished:
                created = True
                self._current_tx = Transaction(self.__neo__.beginTx())
        else:
            created = True
            self._current_tx = Transaction(self.__neo__.beginTx())
        
        return self._current_tx, created
    
    def node(self, **kwargs):
        return self._nodeshop.create(**kwargs)
    
    @property
    def nodes(self):        return self._nodeshop
    
    @property
    def rels(self):         return self._relshop
    
    @property
    def read_only(self):     return self.__neo__.isReadOnly()
    
    @property
    def reference_node(self):    return Node(self.__neo__.getReferenceNode())
    
    
    def shutdown(self):
        self._running = False;
        return self.__neo__.shutdown()
    
    @property
    def store_dir(self):    return self.__neo__.getStoreDir()
    
    @property
    def running(self):      return self._running
    def __nonzero__(self):  return self._running
    
    @cached_property
    def node_indices(self):
        return NodeIndexFactory(self.__neo__.index())
    
    @cached_property
    def rel_indices(self):
        return RelationshipIndexFactory(self.__neo__.index())
    
    
class NodeShop:
    def __init__(self, java_neo):
        self.__neo__ = java_neo
        
    @cached_property
    def reference(self):        return Node(self.__neo__.getReferenceNode())
    
    def __iter__(self):         return NodeIterator(self.__neo__.getAllNodes())
    def __getitem__(self,k):    return Node(self.__neo__.getNodeById(k))
    
    def create(self, **kwargs):
        node = Node(self.__neo__.createNode())
        node.update(**kwargs)
        return node
    
    
class RelationshipShop:
    def __init__(self, jgdb):
        self.__neo__ = jgdb
        
    def __getitem__(self,k):    return Relationship(self.__neo__.getRelationshipById(k))
    
    @property
    def types(self):            return self.__neo__.relationshipTypes



class Transaction:
    def __init__(self, jtx):
        self.__jtx = jtx
        self._finished = False
        self._marked = False
        
    @property
    def finished(self):
        return self._finished
    
    def success(self):
        self._marked = True
        self.__jtx.success()
        
    def failure(self):
        self._marked = True
        self.__jtx.failure()
        
    def finish(self, success=True):
        '''success is ignored if success() or failure() previously called'''
        if not self._marked:
            if success:
                self.__jtx.success()
            else:
                self.__jtx.failure()
        
        self._finished = True 
        self.__jtx.finish()
        
    def __nonzero__(self):
        return not self._finished
    
    def __enter__(self):
        return self
    def __exit__(self):
        self.finish(True)
            
    