'''
Created on June 21, 2011

@author: onesaidwho
'''
import os
import unittest
import shutil
from neo4py import neo
from models import PlantModel

db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test-db.neo4j'))

try:
    shutil.rmtree(db_file)      # delete any previous test databases
    shutil.rmtree(db_file+"1")
except: pass


class TestBasicModels(unittest.TestCase):
        
    def setUp(self):
        self.gdb = neo.init_graph(db_file)
        self.tx, created = self.gdb.get_tx()
        
    def tearDown(self):
        self.tx.finish(True)
        self.gdb.shutdown()
        
    def test_simple_creation(self):
        p1 = PlantModel(scientific_name="Abronia alpina", lifeform="Perennial herb")
        self.assertEqual(p1.id, None)
        p1.save()
        pid = p1.id
        self.assert_(pid > 0)
        print "Saved plant id:", pid
        
        self.assertEqual(p1.scientific_name, "Abronia alpina")

        for n in PlantModel.objects.all().__nodeiter__():
            print "Plant Node: ", n# n['scientific_name']

if __name__ == '__main__':
    unittest.main()
    
    
    
