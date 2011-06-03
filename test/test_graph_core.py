'''
Created on May 27, 2011

@author: onesaidwho
'''
import os
import unittest
import shutil
from neo4py import neo
from neo4py.traversal import Traverser
from neo4py.core import Direction

db_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test-db.neo4j'))

try:
    shutil.rmtree(db_file)      # delete any previous test databases
    shutil.rmtree(db_file+"1")
except: pass

class Plant(object):
    def __init__(self, common_names, scientific_name, lifeform, endangered=False):
        self.common_names = common_names
        self.scientific_name = scientific_name
        self.lifeform = lifeform
        self.endangered = endangered

rare_plants = [
    Plant(["Ramshaw Meadows Abronia"], "Abronia alpina", "Perennial herb"),
    Plant(["Red Sand Verbena", "Sticky Sand Verbena"], "Abronia maritima", "Perennial herb"),
    Plant(["Cushenbury oxytheca"], "Acanthoscyphus parishii var. goodmaniana", "Annual herb", endangered=True),
    Plant(["San Mateo thorn mint"], "Acanthomintha duttonii", "Annual herb", endangered=True),
    Plant(["Siskiyou iris"], "Iris bracteata", "Perennial herb"),
    Plant(["slenderleaf skyrocket", "slender leaved ipomopsis"], "Ipomopsis tenuifolia", "Perennial herb"),
    Plant(["running clubmoss", "running pine"], "Lycopodium clavatum", "Fern"),
    Plant(["Tidestrom's lupine"], "Lupinus tidestromii", "Perennial herb"),
]

class TestGraphInit(unittest.TestCase):
        
    def test_graph_db(self):
        gdb = neo.GraphDatabase(db_file)
        self.assertEqual(gdb.store_dir, db_file)
        gdb.shutdown()
        
    def test_global_graph_db(self):
        gdb = neo.init_graph(db_file)
        self.assert_(gdb is not None)
        gdb = neo.get_graph()
        self.assert_(gdb is not None)
        
        gdb.shutdown()
        self.assert_(not gdb)
        
    def test_graph_reinit(self):
        gdb1 = neo.init_graph(db_file)
        gdb2 = neo.init_graph(db_file+"1")
        
        self.assert_(not gdb1)
        self.assertEqual(gdb2.store_dir, db_file+"1")
        
        gdb2.shutdown()
        
        
class TestNodeCreation(unittest.TestCase):
    def setUp(self):
        self.gdb = neo.init_graph(db_file)
        
    def tearDown(self):
        self.gdb.shutdown()
        
    def test_node_manipulation(self):
        tx, created = self.gdb.get_tx()
        n = self.gdb.node(name="test", color="blue", number=5)
        self.assertEqual(n['name'], "test")
        self.assertEqual(n['color'], "blue")
        self.assertEqual(n['number'], 5)
        
        id = n.id
        del n
        
        n1 = self.gdb.nodes[id]
        self.assertEqual(n1['name'], "test")
        self.assertEqual(n1['color'], "blue")
        self.assertEqual(n1['number'], 5)
        
        if created: tx.finish(True)
    
    def test_node_relations(self):
        tx, created = self.gdb.get_tx()
        
        plant_nodes = []
        plant_root = self.gdb.node(name="plant")
        
        for plant in rare_plants:
            n = self.gdb.node(sciname=plant.scientific_name, endangered=plant.endangered)
            n.IS_A(plant_root, lifeform=plant.lifeform)
            plant_nodes.append(n)
        
        relations = list(plant_root.IS_A.incoming)
        relation_lifeforms = set([r['lifeform'] for r in relations])
        
        self.assertEqual(len(relations), len(rare_plants))
        self.assertEqual(relation_lifeforms, set([p.lifeform for p in rare_plants]))
        
        if created: tx.finish(True)

class TestIndices(unittest.TestCase):
    def setUp(self):
        self.gdb = gdb = neo.init_graph(db_file)
        self.tx, created = gdb.get_tx()
        
        self.node_idx = gdb.node_indices.create("plant node index")
        self.rel_idx = gdb.rel_indices.create("plant relation index")
        self.fulltext_idx = gdb.node_indices.create("plant common name", fulltext=True)
        
        self.plant_root = self.gdb.node(name="plant")
        for plant in rare_plants:
            n = self.gdb.node(common_name=plant.common_names[0], sciname=plant.scientific_name, endangered=plant.endangered)
            r = n.IS_A(self.plant_root, lifeform=plant.lifeform)
            self.node_idx['sciname', plant.scientific_name] = n
            self.rel_idx['lifeform', plant.lifeform] = r
            
            self.fulltext_idx['lifeform', plant.lifeform] = n
            for name in plant.common_names:
                self.fulltext_idx['name', name] = n
                
        self.tx.finish(True)            # commit and start new
        self.tx, created = gdb.get_tx()
            
    
    def tearDown(self):
        for idx in self.gdb.node_indices:
            print "Deleting node index:", idx.name
            idx.delete()
        for idx in self.gdb.rel_indices:
            print "Deleting rel index:", idx.name
            idx.delete()
            
        self.tx.finish(True)
        self.gdb.shutdown()
    
    def test_index_creation(self):
        pass
        def get_index(name):
            return self.gdb.node_indices[name]
        
        self.assertRaises(KeyError, get_index, 'non_existant_index')
        
        idx = self.gdb.node_indices.create("test_index")
        self.assert_(idx is not None)
            
        def create_index(name):
            self.gdb.node_indices.create("test_index")
        
        self.assertRaises(ValueError, create_index, "test_index")
        
        
        
    def test_exact_indexing(self):
        pass
        def bad_add():
            self.rel_idx['shoulnt', 'work'] = self.plant_root
            
        self.assertRaises(TypeError, bad_add)
        
        iris = self.node_idx['sciname', "Iris bracteata"].single
        self.assert_(iris is not None)
        self.assertEqual(iris.IS_A.single['lifeform'], "Perennial herb")
        
                #Relationship index get_exact is segfaulting in neoj4 1.3
        rel_hits = self.rel_idx['lifeform', "Perennial herb"]
        rels = list(rel_hits)
        self.assertEqual(len(rel_hits), 5)
        self.assertEqual(len(rels), 5)
#        rel_hits.close()
        
        print "Perennial herbs:", [r.start['sciname'] for r in rels]

        
    def test_fulltext_indexing(self):
        herbs = list(self.fulltext_idx.simple_query('lifeform', 'herb'))
        
        self.assertEqual(len(herbs), 7)
        print "Herbs: ", [n['sciname'] for n in herbs]
        
        verbena = self.fulltext_idx.query('name:verbena').single
        
        self.assert_(verbena is not None)
        self.assertEqual(verbena['sciname'], "Abronia maritima")
        print "Verbena: " + verbena['sciname']
        self.assertEqual(verbena.IS_A.single['lifeform'], 'Perennial herb')
        

class TestTraversal(unittest.TestCase):
    def setUp(self):
        self.gdb = gdb = neo.init_graph(db_file)
        tx, created = gdb.get_tx()
        self.plant_root = gdb.node(name="plant")
        self.lifeform_root = gdb.node(name="lifeform")
        self.lifeform_nodes = {}
        self.endangered_root = gdb.node(name="endangered")
        
        for n in (self.plant_root, self.lifeform_root, self.endangered_root):
            gdb.reference_node.CHILD(n)
        
        for plant in rare_plants:
            n = gdb.node(name=plant.common_names[0], scientific_name=plant.scientific_name)
            n.IS_A(self.plant_root, endangered=plant.endangered)
            
            lf = plant.lifeform.lower()
            if lf not in self.lifeform_nodes:
                self.lifeform_nodes[lf] = lf_node = gdb.node(name=plant.lifeform)
                lf_node.IS_A(self.lifeform_root)
            else:
                lf_node = self.lifeform_nodes[lf]
                
            n.IS_A(lf_node)
            
            if plant.endangered:
                n.IS(self.endangered_root)
            
        
        tx.finish(True)
        self.tx, created = gdb.get_tx()
        
    def tearDown(self):
        #[n.remove() for n in self.gdb.nodes]        #TODO
        self.tx.finish(True)
        self.gdb.shutdown()
    
    def test_traversal(self):
        class PlantFinder(Traverser):
            types = [Direction.Incoming.IS_A]
        
        plant_nodes = []
        for node in PlantFinder(self.plant_root):
            plant_nodes.append(node)
            
            print "Traversed to plant:", node   #node.get('name', "<No Name>")
            for r in node.relationships():
                print " ==> rel: ", r.type
        
        self.assertEqual(len(plant_nodes), len(rare_plants))
    
if __name__ == '__main__':
    unittest.main()
    
    
    
