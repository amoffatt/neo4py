#!/bin/sh

#
#Creates a _neo4jcc package and installs it
#

if [ $# \< 1 ]; then
	echo You must specify the path to an unpacked download of Neo4j
	echo Example: $0 '~/downloads/neo4j-community-1.3'
	exit 1
fi

NEO4J_PATH=$1
PY_VER=`python -c "import platform as pt; print pt.python_version()[:3]"`
JCC_MOD=jcc

if [ $PY_VER == 2.6 ]; then
	JCC_MOD=jcc.__main__
fi

echo "Neo4j path: $NEO4J_PATH"

mkdir -p build/java-classes
mkdir lib
javac -d build/java-classes -classpath "${NEO4J_PATH}/lib/neo4j-kernel-1.3.jar" @classes.txt
jar cf lib/neo4j-python-exts.jar -C build/java-classes org


exit 0

#not currently in use
python -m $JCC_MOD	\
        --debug		\
        --shared	\
        --include ${NEO4J_PATH}/lib/neo4j-kernel-1.3.jar	\
        --include ${NEO4J_PATH}/lib/neo4j-community-1.3.jar	\
        --include ${NEO4J_PATH}/lib/geronimo-jta_1.1_spec-1.1.1.jar	\
        --include ${NEO4J_PATH}/lib/neo4j-lucene-index-1.3.jar	\
        --include ${NEO4J_PATH}/lib/org.apache.servicemix.bundles.lucene-3.0.1_2.jar	\
        --jar lib/neo4j-python-exts.jar		\
        --package java.lang			\
        --package java.util			\
        --package javax.transaction		\
        --package org.neo4j.kernel		\
        --package org.neo4j.graphdb		\
        --package org.neo4j.graphdb.index	\
        --package org.neo4j.index.impl.lucene	\
        org.neo4j.kernel.EmbeddedGraphDatabase		\
        org.neo4j.graphdb.DynamicRelationshipType	\
        org.neo4j.graphdb.index.IndexManager		\
        org.neo4j.index.impl.lucene.LuceneIndexProvider	\
        java.util.HashMap			\
        --exclude RelationshipIndex		\
        --version 1.3				\
        --python neo4jcc			\
        --build					\



