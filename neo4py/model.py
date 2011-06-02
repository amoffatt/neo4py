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


import inspect
from __init__ import get_graph

class NodeModel(object):
    '''
    classdocs
    '''

    def __init__(self, node=None, **kwargs):
        '''
        Constructor
        '''
        self._node = None
        if node is None:
            self._id = None
        elif isinstance(node, long):
            self._id = node
            self._node = node
        else:
            self._id = node.id
            
        self._id = node.id if node else None
        self._property_models = []
        self._unsaved_changes = True
        
        for prop, def_ in self.__model_properties__:
            pmodel = PropertyModel(def_)
            self._property_models.append((prop, pmodel))
            setattr(self, prop, pmodel)
    
    
    @classmethod
    def __model_properties__(cls):
        plist = []
        for name,def_ in inspect.getmembers(cls,
                            lambda (name, value): isinstance(value, Property) ):
            plist.append(name, def_)
            
        cls.__model_properties__ = plist
        return plist
        
        
    def save(self, graph=get_graph()):
        if self._node:
            node = self._node
        elif self._id:
            node = graph.nodes[id]
        else:
            node = graph.node()
        
        for prop, pmodel in self._property_models:
            value = pmodel.get_for_neo()
            if value is None:
                del node[prop]
            else:
                node[prop] = value
        
        #TODO save relationship updates
        
        self._unsaved_changes = False



class RelationModel(object):        #TODO
    pass


class PropertyModel(object):
    def __init__(self, definition):
        self._def = definition
        self._value = None
    
    def __set__(self, v):
        print "setting property model to:", v
        self._value = self._def.clean_value(v)
        
    def __get__(self):
        print "getting property model with value:", self._value
        return self._value
    
    def get_for_neo(self):
        return self._def.to_neo(self._value)
    
    def set_from_neo(self, v):
        self._value = self._def.from_neo(v)
    


class Relation(object):
    pass

class OneToOneRelation(Relation):
    def __init__(self, related_models, required=True):    #?include required?
        pass
        
class OneToManyRelation(Relation):
    def __init__(self, related_models):
        pass

class ManyToManyRelation(Relation):
    def __init__(self, related_models):
        pass



class Property(object):
    def __init__(self, required=False, indexed=False):
        self.required = required
        self.indexed = indexed

class StringProperty(Property):
    def __init__(self, min_length=None, max_length=None, index_fulltext=False, index_icase=False, **kwargs):
        super(NumberProperty, self).__init__(**kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.index_fulltext = index_fulltext
        self.index_icase = index_icase
        
    def to_neo(self, v):
        return unicode(v)
    
    def from_neo(self, v):
        return unicode(v)
    
class ArrayProperty(Property):
    def __init__(self, component_type=StringProperty()):
        pass

class NumberProperty(Property):
    def __init__(self, min=None, max=None, **kwargs):
        super(NumberProperty, self).__init__(**kwargs)
        self.min = min
        self.max = max
    
class IntegerProperty(NumberProperty):
    def to_neo(self, v):
        return int(v)
    
    def from_neo(self, v):
        return int(v)

class BigIntegerProperty(IntegerProperty):
    def to_neo(self, v):
        return long(v)
    
    def from_neo(self, v):
        return long(v)

class FloatProperty(NumberProperty):
    def to_neo(self, v):
        return float(v)
    
    def from_neo(self, v):
        return float(v)

#class DateProperty(BigIntegerProperty):
#    def to_neo(self, v):
#        return v.
#    
#    def from_neo(self, v):
#        return float(v)
#
#class TimeProperty(FloatProperty):
#    pass

class DateTimeProperty(FloatProperty):
    def to_neo(self, v):
        return float(v)
    
    def from_neo(self, v):
        return float(v)

#class EmailProperty(StringProperty):
#    pass
#
#class UriProperty(StringProperty):
#    pass
#
#class FileProperty(StringProperty):
#    pass
