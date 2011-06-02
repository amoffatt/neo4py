import os

from distutils.core import setup
import neo4py as np

def read(fname):
        return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
        name="neo4py",
        version=np.__version__,
        author=np.__author__,
        url=np.__url__,
        description=np.__description__,
        long_description=read('README.txt'),
        license=np.__license__,
        keywords='neo4j graph graphdb graphdatabase database native cpython',
        classifiers=[
                'Intended Audience :: Developers',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
        ],
        packages=[
                'neo4py',
        ],
)

