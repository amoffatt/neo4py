from __future__ import with_statement
import os
import sys
from os.path import join, dirname, exists
import platform
import runpy
import shutil

from distutils.core import setup
import neo4py as __info__

try:
        from jcc import cpp
except ImportError:
        print """
Could not find jcc. It must be installed first:

easy_install jcc
"""
        sys.exit(1)

NEO4J_JARS = {
	"1.3" : [
		"neo4j-kernel-1.3.jar",
		"neo4j-community-1.3.jar",
		"geronimo-jta_1.1_spec-1.1.1.jar",
		"neo4j-lucene-index-1.3.jar",
		"org.apache.servicemix.bundles.lucene-3.0.1_2.jar"
	]
}

NEO4J_SUPPORTED_VERSIONS = ', '.join(NEO4J_JARS.keys())

def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

def find_neo4j_version(neo4j_home):
	readme = join(neo4j_home, 'README.txt')
	if not exists(readme):
		return None

	with open(readme) as readme:
		parts = readme.readline().split()
		if len(parts) != 2:
				return None
		return parts[1]
		

setup(
	name="neo4py",
	version=__info__.__version__,
	author=__info__.__author__,
	author_email=__info__.__author_email__,
	url=__info__.__url__,
	description=__info__.__description__,
	long_description=read('README.txt'),
	license=__info__.__license__,
	keywords='neo4j graph graphdb graphdatabase database native cpython',
	classifiers=[
		'Intended Audience :: Developers',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
	],
	packages=[
		__info__.__name__,
	],
	requires=[
		"jcc",
	]
)


build_wrappers = True
if len(sys.argv) < 2:
	cmd = None

cmd = sys.argv[1]

if cmd not in ("install", "build"):
	build_wrappers = False
else:
	if cmd == "install":
		try:
			import neo4jcc
	
			neo4jcc_path = dirname(dirname(neo4jcc.__file__))
	
			print
			print "Previously built Neo4j C++ wrappers found at '%s'" %neo4jcc_path
			ans = raw_input("Remove and install new? (Y/n): ")
			
			if not ans or ans.lower().startswith('y'):
				try:
						shutil.rmtree(dirname(dirname(neo4jcc.__file__)))
				except Exception, ex:
						print
						print "Error removing previous install of neo4jcc: %s" %ex
						sys.exit(1)
			else:
				print "Using previous build of C++ wrappers"
				build_wrappers = False
	
		except ImportError:
			pass
		

if build_wrappers:
	build_info_file = join('build', "NEO4J_HOME.txt")
	
	if cmd == 'build':
		try:
			NEO4J_HOME = os.environ['NEO4J_HOME']
		except KeyError:
			print """
*** NEO4J_HOME environment variable must be set ***
For example: export NEO4J_HOME=~/downloads/neo4j-community-1.x

Note that if you are using sudo, the environment variable must be
set within the sudo scope:

$ sudo -s		# enter password if needed
$ export NEO4J_HOME=~/downloads/neo4j-community-1.x
$ python setup.py ...

Supported Neo4j versions: %s""" %NEO4J_SUPPORTED_VERSIONS
			sys.exit(1)
		
		NEO4J_VER = find_neo4j_version(NEO4J_HOME)
	
		if NEO4J_VER not in NEO4J_JARS:
			print "Unsupported version of Neo4j at '%s'" %NEO4J_HOME
			print "Supported versions: %s" %NEO4J_SUPPORTED_VERSIONS
			sys.exit(1)
		
	else:
		if not exists(build_info_file):
			print """
Cannot complete installation: Neo4j C++ wrappers have not been built.
Run 'setup.py build' first
"""
			sys.exit(1)
		try:
			with open(build_info_file) as f:
				NEO4J_HOME = f.readline().strip()
				NEO4J_VER = f.readline().strip()
		except Exception, ex:
			print "Error reading build info file:", ex
			sys.exit(1)

	
	jcc_args = [
		cpp.__file__,
		"--debug",
		"--shared",
	
		"--jar", join("java", "lib", "neo4j-neo4py-exts.jar"),
		"--package", "java.lang",
		"--package", "java.util",
		"--package", "javax.transaction",
		"--package", "org.neo4j.kernel",
		"--package", "org.neo4j.graphdb",
		"--package", "org.neo4j.graphdb.index",
		"--package", "org.neo4j.index.impl.lucene",
	
		"org.neo4j.kernel.EmbeddedGraphDatabase",
		"org.neo4j.graphdb.DynamicRelationshipType",
		"org.neo4j.graphdb.index.IndexManager",
		"org.neo4j.index.impl.lucene.LuceneIndexProvider",
		"java.util.HashMap",
	
		"--exclude", "RelationshipIndex",
	
		"--version", NEO4J_VER,
		"--python", "neo4jcc",
	]
	
	for jar in NEO4J_JARS[NEO4J_VER]:
		jcc_args.extend((
			'--include',
			join(NEO4J_HOME, 'lib', jar)
		))
	
	if cmd == "install":
		jcc_args.append("--install")
	elif cmd == "build":
		jcc_args.append("--build")
	
	cpp.jcc(jcc_args)
	
	if cmd == 'build':
		with open(build_info_file, 'w') as f:
			f.write(NEO4J_HOME+'\n')
			f.write(NEO4J_VER+'\n')
			
			

