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
from neo import get_graph
from util import cached_classproperty, cached_property, UnimplementedError

class ValidationError(Exception):
    def __init__(self, value, *errors, **kwargs):
        self.value = value
        self.errors = errors
        self.object = kwargs.get('object', "")
        
    def __str__(self):
        if self.object:
            return "Value '%s' for %s failed to validate: %s" % (
                 self.value, self.object, ', '.join(str(e) for e in self.errors))
        else:
            return "Value '%s' failed to validate: %s" % (
                 self.value, ', '.join(str(e) for e in self.errors))
        

class _PropertyContainerModel(object):
    '''
    classdocs
    '''
    __index__ = None        # NOTE not sure if this is best implementation
    __fulltext_index__ = None
    __typenode__ = None
    __section_label__ = ""
        
    def __init__(self, property_container=None, **kwargs):
        '''
        Constructor
        '''
        self._pc = None             ##Deal with None here
        if property_container is None:
            self._id = None
        elif isinstance(property_container, (int, long)):
            self._id = property_container
        else:
            self._id = property_container.id
            self._pc = property_container
            
        self.__property_dict__ = pd = {}

        for prop, def_ in self.__model_properties__:
            pmodel = PropertyModel(prop, def_)
            pd[def_] = pmodel
            
        self.update(**kwargs)
        self._validate()
        
    @property
    def id(self):
        return self._id
    
    @cached_classproperty
    def __model_properties__(cls):
        plist = []
        for k,v in cls.__dict__.iteritems():
            if isinstance(v, BaseProperty):
                plist.append((k,v))
            
        return plist
    
    @classmethod
    def __get_index__(cls):
        if cls.__index__ is None:
            neo = get_graph()
            name = "NodeModel::" + cls.__name__
            cls.__index__ = neo.node_indices.get_or_create(name)
        return cls.__index__
                ## ISSUE nodes can have fulltext and non-fulltext indexed properties,
                ## which would have to be stored in separate indices
                ## how will this affect querying?
                ##
                ## each model should also NOT have it's own index, but 
                ## instead (model_name property_name) keys
                
    @classmethod
    def __get_fulltext_index__(cls):
        ''''''
        if cls.__fulltext_index__ is None:
            neo = get_graph()
            name = "NodeModel::" + cls.__name__ + "::fulltext"
            cls.__fulltext_index__ = neo.node_indices.get_or_create(name, fulltext=True)
        return cls.__fulltext_index__
        
    @classmethod
    def __get_typenode__(cls, create=False):
        if cls.__typenode__ is None:
            neo = get_graph()
            for rel in neo.reference_node.MODEL_TYPE_NODE:
                if (rel['section'] == cls.__section_label__ and
                    rel['model'] == cls.__name__):
                    cls.__typenode__ = n = rel.end
                    return n
            else:
                if create:
                    cls.__typenode__ = n = neo.node()
                    neo.reference_node.MODEL_TYPE_NODE(n, section=cls.__section_label__, model=cls.__name__)
                    return n
        return cls.__typenode__
        
    def save(self, graph=None):
        '''graph will be ignored if this model is already attached to a node/relationship'''
        if graph is None:
            graph = get_graph()
        self._validate()
        if self._pc:
            pc = self._pc
        elif self._id:
            pc = self._get_target_by_id(graph, self._id)
        else:
            pc = self._create_new_target(graph)
            self._id = pc.id
            tnode = self.__get_typenode__(create=True)
            tnode.INSTANCE(pc)              ##TODO allow storage of create/modification time here?
        
        for def_, pmodel in self.__property_dict__.iteritems():
            if not pmodel.unsaved:
                continue
            
            idx = None
            if def_.indexed:
                if def_.indexed_fulltext:
                    print '==>fulltext'
                    idx = self.__get_fulltext_index__()
                else:
                    idx = self.__get_index__()
                    print "==>exact"
                    
            pmodel.save(pc, index=idx)
        
        #TODO save relationship updates
        
#        self._unsaved_changes = False
        
    def _get_target_by_id(self, graph, id):
        pass
    
    def _create_new_target(self, graph):
        pass

    def update(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
            
    def _validate(self):
        for pmodel in self.__property_dict__.itervalues():
            try:
                pmodel.validate()
            except ValidationError, ex:
                raise ValidationError(ex.value, *ex.errors, object="%s.%s" % (self.__class__.__name__, pmodel._name))
    

class NodeModelManager(object):
#    def __init__(self, model):       ##TODO see django implementation
#        self.__neo__ = graph
#        self.__model__ = model
    
    def __get__(self, instance, model):
        if instance is not None:
            raise ValueError("Cannot be accessed via instances")        #TODO better ex type
        return QuerySet(model)
    
    

class NodeModel(_PropertyContainerModel):
    def __init__(self, **kwargs):
        super(NodeModel, self).__init__(**kwargs)
    
    def _get_target_by_id(self, neo, id):
        return neo.nodes[id]
    
    def _create_new_target(self, neo):
        return neo.node()
    
    objects = NodeModelManager()
    

class QuerySet(object):
    def __init__(self, model, **params):
        self.__model__ = model
    
    def _clone(self):
        clone = self.__class__(self.__model__)
        return clone
        
    def __nodeiter__(self):
        tnode = self.__model__.__get_typenode__()
        if not tnode:
            return
        for rel in tnode.INSTANCE:
            yield rel.end
        
    def create(self, **kwargs):             ##TODO transactions need to be automanaged with models
        instance = self.__model__(**kwargs)
        instance.save()                         ##TODO see django implementation
        return instance
    
    def all(self):
        return self._clone()

#class RelationModel(_PropertyContainerModel):
#    def __init__(self):
#        super(NodeModel, self).__init__()
#
#    ##TODO objects(self)
#        
#    def _get_target_by_id(self, neo, id):
#        return neo.relationships[id]
#    
#    def _create_new_target(self, graph):
#        raise TypeError("Cannot create a relationship like this")
#    
#    
#    @property
#    def start(self):
#        return self._start_nodemodel
#    
#    @property
#    def end(self):
#        return self._end_nodemodel

class RelationshipModelManager():
    def __init__(self, model, graph):
        self.__neo__ = graph
        self.__model__ = model
    
    def create(self, start_node, end_node, **kwargs):
        pass
    
    def all(self):
        pass
    
    def filter(self):
        pass


#### ??? When to create node/relation for new model instances?
####   when instance created?  -- probably not
####   when first saved, before property validation? -- probably should not be created if validation fails
####   when first saved, after successful validation of all properties? -- probaably
class PropertyModel(object):
    def __init__(self, name, definition, property_container=None, index=None):
        self._name = name
        self._def = definition
        self._unsaved_value = None
        self._unsaved = False
        self._pc = property_container
        self._index = index
        
        if self._pc is None:
            self._unsaved = True
    
    @property
    def unsaved(self):
        return self._unsaved
    
    @cached_property
    def index_key(self):
#        return "%s.%s" % (self._def.im_class.__name__, self._def.__name__)
        return self._name
    
    def set(self, v):
        print "setting property model to:", v
        self._unsaved_value = self._def.clean_python_value(v)
        self._unsaved = True
        
    def get(self):
        print "getting property model with value:", self._unsaved_value
        if self._unsaved:
            return self._unsaved_value
        if self._pc is None:
            return None
        
        try:
            raw_value = self._pc[self._name]
        except KeyError:
            return None
        else:
            return self._def.from_neo(raw_value)
    
    def save(self, property_container=None, index=None):
        '''if this property model was not instantiated with a property container,
        a property_container must be given here.  Same for index, if this property
        should be indexed'''
        if self._pc is None and property_container is not None:
            self._pc = property_container
            
        if self._index is None and index is not None:
            self._index = index
            
        if self._unsaved:
            def_ = self._def
            if self._unsaved_value is None:
                self._unsaved_value = def_.default
                
            if def_.indexed and self._index:
                try:
                    previous_value = def_.from_neo(self._pc[self._name])
                except KeyError: pass
                else:
                    for v in def_.to_index_values(previous_value):      #unindex previous value if present
                        del self._index[self._pc, self.index_key, v]
                    
                if self._unsaved_value is not None:             #index new value
                    for v in def_.to_index_values(self._unsaved_value):
                        self._index[self.index_key, v] = self._pc
            
            if self._unsaved_value is None:
                try:
                    del self._pc[self._name]
                except KeyError: pass
            else:
                raw_value = def_.to_neo(self._unsaved_value)
                self._pc[self._name] = raw_value
            self._unsaved = False
            
            
    def validate(self):
        if self._unsaved:               # NOTE could potentialy keep extra 'self._unvalidated' flag, to avoid revalidating
                                        # if previously successful, but object wasn't saved for other reasons
            self._def.validate(self._unsaved_value)
        


class Relation(object):
    pass

class OneToOneRelation(Relation):
    def __init__(self, related_models, required=True):    #?include required?
        raise UnimplementedError
        
class OneToManyRelation(Relation):
    def __init__(self, related_models):
        raise UnimplementedError

class ManyToManyRelation(Relation):
    def __init__(self, related_models):
        raise UnimplementedError


class BaseProperty(object):
    def __init__(self, index=False, index_fulltext=False, null=False, default=None, **kwargs):
        self.indexed = index
        self.indexed_fulltext = index_fulltext
        if index_fulltext:
            self.indexed = True
        self.allow_none = null;
        self.default = self.clean_python_value(default)
                ##TODO should possibly validate this value too
    
    def __get__(self, instance, owner):
#        print 'Get Property: ', dir(self)
        return instance.__property_dict__[self].get()
    
    def __set__(self, instance, v):
#        print 'Set Property: ', dir(self)
        instance.__property_dict__[self].set(v)
        
    def to_neo(self, v):
        raise UnimplementedError
    
    def from_neo(self, v):
        raise UnimplementedError
    
    def clean_python_value(self, v):
        '''Convert the given value to the proper python type for this 
        property definition, except if v is None, in which case None should
        be returned'''
        raise UnimplementedError
    
    def validate(self, v):
        if v is None and self.default is None and not self.allow_none:
            raise ValidationError(None, "cannot be None")

class StringProperty(BaseProperty):
    def __init__(self, blank=False, min_length=None, max_length=None, index_icase=False, **kwargs):
        if min_length is not None:
            self.min_length = min_length
        elif not blank:
            self.min_length = 1
        self.max_length = max_length
        self.index_icase = index_icase
        if index_icase:
            kwargs['index'] = True
        super(StringProperty, self).__init__(**kwargs)
        
    def to_neo(self, v):
        return unicode(v)
    
    def from_neo(self, v):
        return unicode(v)
    
    def clean_python_value(self, v):
        if v is None: return None
        return unicode(v)
    
    def to_index_values(self, v):
        return [v]
    
    def validate(self, v):
        super(StringProperty, self).validate(v)
        if v is None:
            return          # skip other validations in this circumstance
        try:
            if self.max_length is not None and len(v) > self.max_length:
                raise ValidationError(v, "More than %d characters" % self.max_length)
            
            if self.min_length is not None and len(v) < self.min_length:
                raise ValidationError(v, "Fewer than %d characters" % self.min_length)
        except Exception, ex:
            raise ValidationError(v, ex)
    
class ArrayProperty(BaseProperty):
    def __init__(self, component_def=StringProperty()):
        if component_def is None:
            raise ValueError("ArrayProperty component definition cannot not be None")
        self._comp_def = component_def
        self._values = []
        raise UnimplementedError
    
#    def to_index_values(self, v):
#        if self._comp_def.indexed:
#        return [unicode(v) for v in self._values]
#    
#    def 


class BooleanProperty(BaseProperty):
    def __init__(self, **kwargs):
        super(BooleanProperty, self).__init__(**kwargs)
        
    def to_neo(self, v):
        return v is True
    
    def from_neo(self, v):
        return v is True
    
    def clean_python_value(self, v):
        if v is None: return None
        return v is True
    

class NumberProperty(BaseProperty):
    def __init__(self, min=None, max=None, **kwargs):
        super(NumberProperty, self).__init__(**kwargs)
        self.min = min
        self.max = max
        
    def to_index_values(self, v):
        return [str(v)]
        
    def validate(self, v):
        super(NumberProperty, self).validate(v)
        if v is None:
            return
        if self.min is not None and v < self.min:
            raise ValidationError(v, "Less than %s" % self.min)
        if self.max is not None and v > self.max:
            raise ValidationError(v, "Greater than %s" % self.max)
    
class IntegerProperty(NumberProperty):
    def to_neo(self, v):
        return int(v)
    
    def from_neo(self, v):
        return int(v)
    
    def clean_python_value(self, v):
        if v is None: return None
        return int(v)

class BigIntegerProperty(IntegerProperty):
    def to_neo(self, v):
        return long(v)
    
    def from_neo(self, v):
        return long(v)
    
    def clean_python_value(self, v):
        if v is None: return None
        return long(v)
    
class FloatProperty(NumberProperty):
    def to_neo(self, v):
        return float(v)
    
    def from_neo(self, v):
        return float(v)
    
    def clean_python_value(self, v):
        if v is None: return None
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
    def __init__(self):
        raise UnimplementedError
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
