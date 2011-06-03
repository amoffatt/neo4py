Neo4j Python Bindings
========================

:synopsis: Access Neo4j graph database functionality from python code

Only tested with Neo4j 1.3 on OSX Snow Leopard, Python 2.6


Notice
------
This is a work in progress.  Please let me know if stuff in this document fails or doesn't seem to be true.

Thanks much.


Installation
------------

Install JCC:

$ easy_install jcc

Download and unpack neo4j somewhere (http://neo4j.org/download/)
Currently only version 1.3 is supported

Set NEO4J_HOME environment variable to this download of Neo4j:

$ export NEO4J_HOME=~/downloads/neo4j-community-1.3


Enter the Neo4py package directory:

$ cd the/directory/with/this/readme

Build C++ wrappers with JCC:

$ python setup.py build

Install (may require sudo-ness):

$ python setup.py install


Run some tests:
$ python test/test_graph_core.py

Hopefully no errors!  If there are, send me the tracebacks :)


Getting started
---------------

Simplest way is to use the 'global' graph.
  >>> from neo4py import neo
  >>> gdb = neo.init_graph('test-graph.neo4j')
  >>> gdb.shutdown()

This global graph may be accessed from anywhere after being initialized with
  >>> gdb = neo.get_graph()


Transactions
------------

Transactions are handled differently than in neo4j.py

  >>> tx, created = gdb.get_tx()

If created is True, it is the responsibility of this scope to commit the transaction when done it:

  >>> tx.finish(True)	# success - commit changes to database
  >>> tx.finish(False)	# failure - rollback changes

  >>> tx.success()		# or .failure()
  >>> tx.finish()		# it doesn't matter if True of False is passed here -- it will be ignored


Nodes, Relationships and Properties (Beginning of fun stuff)
----------------------------------

** Not all syntax is neo4j.py compatible **


Creating a node::			(must be within a transaction!)

  >>> n = gdb.node()

Specify properties for new node::

  >>> n = gdb.node(petals=5, color="Red", height=5.5)			#support for number or string array properties is not yet added

Accessing node by id:

  >>> n = gdb.nodes[14]
  

Accessing properties:

  >>> value = n['key'] # Get property value
  
  >>> n['key'] = value # Set property value
  
  >>> del n['key']     # Remove property value
  
  # Or, with a default
  >>> value = n.get('key', 'default')

  >>> for prop in n: do_something(prop)
  >>> for prop, value in n.iteritems(): do_someting(prop,value)		# loop through node properties
  
  >>>more_props = { "name" : "Jack", "occupation" : "Pilot" }
  >>>n1.update(more_props)
  >>>n2.update(name="Sarah", occupation="Astronaut")
  

  >>> n.id	# Node id
  

Create relationship::

  >>> n1.Knows(n2, since="A long time ago")
  
  # Or
  >>> n1.relationships("Likes")(n2, how_much="A lot") 	# Usefull when the name of
                                          			# relationship is stored in a variable.
					  			# This syntax may change though... seems obscure?


The creation returns a Relationship object, which has properties accessible like nodes.

  >>> rel = n1.Knows(n2, since=123456789)
  >>> rel['since']
123456789
  
Additional attributes:

  >>> rel.start		# start node (n1)
  >>> rel.end		# end node (n2)
  
  >>> rel.type
  'Knows'



Others functions over 'relationships' attribute are possible. Like get all,
incoming or outgoing relationships (typed or not):

  >>> rels = list(n1.relationships())

  
  >>> rels = list(n1.relationships("Knows", "Likes").incoming)
  
  >>> rel = n1.Knows.outgoing.single


Traversals
----------

In progress.  Much like neo4j.py
See tests (neo4py/testing/graph_core.py)

  >>> from neo4py.core import Direction
  >>> from neo4py.traversal import Traverser, Stop, Returnable, Order

  class MyTraverser(Traverser):						
      types = [Direction.Incoming.Knows, Direction.Undirected.Likes]
      is_stop = lambda pos: pos.node == my_node		#can use a python method		####  LARGELY UNTESTED  ####
							#pos is a TraversalPosition object
      is_returnable = Returnable.ALL			#or a java defined ReturnableEvaluator/StopEvaluator
							# (these are faster)
      order = Order.DEPTH_FIRST


Indices
-------

See tests (neo4py/testing/graph_core.py)

  >>> node_idx = gdb.node_indices.create("My node index", fulltext=True)		#create an new fulltext index
											#Will fail index with name already exists
  >>> node_idx = gdb.node_indices["My node index"]			#retrieve already created index

  >>> "That index" in gdb.node_indices					#test if index exists
False
  >>> "My node index" in gdb.node_indices
True
  
  >>> rel_idx = gdb.rel_indices.create("Relationship index")		# works the same, but for relationships

  >>> node_idx['name', "Jack"] = n1
  >>> node_idx['name', "Jack"] = n500			# two nodes indexed under 'name' => "Jack"

  >>>nodes = list(node_idx['name', 'Jack'])		# Returns iterator over both nodes (exact matching using this syntax)

  >>>nodes = list(node_idx.simple_query('name', 'jack')	# fulltext query by single key/value
  >>>nodes = list(node_idx.query('name:jack'))		# Run lucene query (supports multiple keys)

Relationship indices same, but with a couple extra options (See Neo4j Docs):
  >>> rels = list(rel_idx.simple_query('key', 'value', start_node=n1)		#limit query, for efficiency (can also be end_node)
  >>> rels = list(rel_idx.query('key:value', end_node=some_other_node)


Models, Django support, QuerySets, Aggregates
------

In Progress




