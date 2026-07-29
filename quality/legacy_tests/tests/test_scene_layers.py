
import unittest
from src.models.scene import Scene, Layer

class TestSceneLayers(unittest.TestCase):
    def test_create_remove_layer(self):
        s = Scene()
        initial = len(s.layers)
        l = s.create_layer('Extra')
        self.assertEqual(len(s.layers), initial+1)
        s.remove_layer(l.id)
        self.assertEqual(len(s.layers), initial)

    def test_render_list_respects_visibility(self):
        s = Scene()
        # create object in default layer
        s.add_object('o1', [(0,0),(1,0),(1,1)])
        # create new invisible layer and object
        l = s.create_layer('Hidden')
        s.set_layer_visibility(l.id, False)
        s.add_object('o2', [(0,0),(2,0),(2,2)], layer_id=l.id)
        # render_list should not include object in hidden layer
        ids = [o.id for o in s.render_list()]
        self.assertIn('o1', ids)
        self.assertNotIn('o2', ids)

if __name__ == '__main__':
    unittest.main()
