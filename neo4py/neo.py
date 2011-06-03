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


import os
from graph import GraphDatabase

__all__ = "GraphDatabase", "init_graph", "get_graph"

_global_graph = None
_global_graph_dir = None

def init_graph(db_dir):
    global _global_graph, _global_graph_dir
    if not db_dir:
        raise ValueError("Must specify graph directory")
    
    abs_db_dir = os.path.abspath(db_dir)
    if _global_graph_dir != abs_db_dir:
        if _global_graph:
            _global_graph.shutdown()
        _global_graph = GraphDatabase(db_dir)
        _global_graph_dir = abs_db_dir
    elif not _global_graph.running:
        _global_graph = GraphDatabase(db_dir)
        
    return _global_graph

def get_graph():
    return _global_graph
