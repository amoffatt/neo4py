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


from backend import JTypes
from core import Node, Relationship
from util import dict_to_jmap


class _IndexFactory(object):
    def __init__(self, java_index_manager):
        self.__imanager__ = java_index_manager
        self._item_constructor = None       #Override
        self._item_type = None
    
    def create(self, name, fulltext=False, provider="lucene"):
        if name in self:
            raise ValueError("Index [%s] already exists" % (name))      #TODO better ex type...
        
        itype = 'fulltext' if fulltext else 'exact'
        params = dict_to_jmap({
                    'provider'  : provider,
                    'type'      : itype
                })
        
        return self._make(name, params)
    
    def _exists(self, name):       #Override
        pass
    def _names(self):
        pass
    def _make(self, name, params):
        pass
    def _get(self, name):
        pass
    
    def __getitem__(self, k):
        if not self._exists(k):
            raise KeyError("Index [%s] does not exist" % (k))
        return self._get(k)
    
    def __contains__(self, k):
        return self._exists(k)
    
    def __iter__(self):
        for name in self._names():
            yield self[name]
    
    @property 
    def names(self):
        return [n for n in self._names()]
        
        
class NodeIndexFactory(_IndexFactory):
    def __init__(self, java_index_manager):
        super(NodeIndexFactory, self).__init__(java_index_manager)
        self._item_constructor = Node
        self._item_type = Node
    
    def _exists(self, name):
        return self.__imanager__.existsForNodes(name)
    
    def _names(self):
        return self.__imanager__.nodeIndexNames()
    
    def _get(self, name):
        return NodeIndex(self.__imanager__.forNodes(name))
    
    def _make(self, name, params):
        return NodeIndex(self.__imanager__.forNodes(name, params))
    
        
    
class RelationshipIndexFactory(_IndexFactory):
    def __init__(self, java_index_manager):
        super(RelationshipIndexFactory, self).__init__(java_index_manager)
        self._item_constructor = Relationship
        self._item_type = Relationship
    
    def _exists(self, name):
        return self.__imanager__.existsForRelationships(name)
    
    def _names(self):
        return self.__imanager__.relationshipIndexNames()
    
    def _get(self, name):
        return RelationshipIndex(self.__imanager__.forRelationships(name))
    
    def _make(self, name, params):
        return RelationshipIndex(self.__imanager__.forRelationships(name, params))
    

class _Index(object):
    def __init__(self, java_index):
        self.__jobj__ = java_index
    
    @property
    def name(self):
        return self.__jobj__.getName()
    
    @property
    def entity_type(self):
        pass
            
    def __setitem__(self, (key, value), entity):
        self._verify_entity_type(entity)
        self.__jobj__.add(entity.__jobj__, key, value)
        
    def __delitem__(self, args):
        if not isinstance(args, tuple):
            entity = args
            args = []
        else:
            entity = args[0]
            args = args[1:]
           
        self._verify_entity_type(entity)
        self.__jobj__.remove(entity.__jobj__, *args)
        
    def _verify_entity_type(self, entity):
        if not isinstance(entity, self.entity_type):
            raise TypeError("Entity [%s] not of type [%s]" % (entity, self.entity_type))
        
    def delete(self):
        self.__jobj__.delete()



class NodeIndex(_Index):
    def __init__(self, java_index):
        super(NodeIndex, self).__init__(java_index)
        self._item_constructor = Node
    
    def simple_query(self, key, value):
        hits = self.__jobj__.query(key, value)
        return IndexHits(hits, self._item_constructor)
    
    def query(self, query):
        try:
            hits = self.__jobj__.query(query)
        except JTypes.JavaError, ex:                                ##TODO better ex type
            raise ValueError("A JavaError occured while querying.  Make sure query syntax is correct. Error:\n\n" + str(ex))
            
        return IndexHits(hits, self._item_constructor)
    
    def get(self, key, value):
        hits = self.__jobj__.get(key, value)
        return IndexHits(hits, self._item_constructor)
    
    def __getitem__(self, (key, value)):
        return self.get(key, value)
    
    @property
    def entity_type(self):
        return Node

class RelationshipIndex(_Index):
    def __init__(self, java_index):
        super(RelationshipIndex, self).__init__(java_index)
        self._item_constructor = Relationship
        
    def simple_query(self, key, value, start_node=None, end_node=None):
        hits = self.__jobj__.query(key, value, start_node, end_node)
        return IndexHits(hits, self._item_constructor)
    
    def query(self, query, start_node=None, end_node=None):
        try:
            hits = self.__jobj__.query(query, start_node, end_node)
        except JTypes.JavaError, ex:                                ##TODO better ex type
            raise ValueError("A JavaError occured while querying.  Make sure query syntax is correct. Error:\n\n" + str(ex))
            
        return IndexHits(hits, self._item_constructor)
    
    def get(self, key, value, start_node=None, end_node=None):
        hits = self.__jobj__.get(key, value, start_node, end_node)
        return IndexHits(hits, self._item_constructor)
    
    def __getitem__(self, (key, value)):
        return self.get(key, value, None, None)
    
    @property
    def entity_type(self):
        return Relationship


class IndexHits(object):
    '''User must close this if not using all items (attempts to close itself when garbage collected)'''
    def __init__(self, java_indexhits, item_constructor):
        self.__jobj__ = java_indexhits
        self._constructor = item_constructor
        self.__single = None
        
    @property
    def single(self):
        '''Assumes user will ignore remaining hits and closes iterator'''
        jentity = self.__jobj__.getSingle()
        entity = self._constructor(jentity) if jentity else None
        self.__dict__['single'] = entity
        self.close()
        return entity
   
    def __len__(self):
        return self.__jobj__.size()
    
    def __iter__(self):
        for item in self.__jobj__:
            yield self._constructor(item)
            
    def __del__(self):
        self.close()
     
    def withscore(self):
        hits = self.__jobj__
        for item in hits:
            yield self._constructor(item), hits.currentScore()
            
    def close(self):
        self.__jobj__.close()
        
    
