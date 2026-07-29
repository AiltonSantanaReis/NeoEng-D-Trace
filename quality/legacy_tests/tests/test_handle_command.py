import unittest
from src.models.scene import Scene
from src.core.commands import CommandManager, HandleMoveCommand

class TestHandleMove(unittest.TestCase):
    def test_handle_move_undo_redo(self):
        s = Scene()
        s.cmd = CommandManager()
        # create object with simple bezier (one segment)
        s.add_object('o1', [(0,0),(10,0),(20,0)])
        # set a simple bezier for object
        beziers = [((0,0),(5,0),(15,0),(20,0))]
        s.set_object_beziers('o1', beziers)
        old = beziers[0][1]
        new = (6,1)
        cmd = HandleMoveCommand('o1', 0, 1, old, new)
        s.cmd.execute(cmd, s)
        self.assertEqual(s.objects['o1'].beziers[0][1], new)
        s.cmd.undo(s)
        self.assertEqual(s.objects['o1'].beziers[0][1], old)
        s.cmd.redo(s)
        self.assertEqual(s.objects['o1'].beziers[0][1], new)

if __name__ == '__main__':
    unittest.main()