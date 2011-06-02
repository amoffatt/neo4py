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


import neo4jcc as neo4j
neo4j.initVM()

_rel_types = {}

def rel_type(name):
    global _rel_types
    if name not in _rel_types:
        rtype = neo4j.DynamicRelationshipType.withName(name)
        _rel_types[name] = rtype
        return rtype
    return _rel_types[name]
    


class JTypes:
    Node = neo4j.Node
    Relationship = neo4j.Node
    JavaError = neo4j.JavaError
    String  = neo4j.String
