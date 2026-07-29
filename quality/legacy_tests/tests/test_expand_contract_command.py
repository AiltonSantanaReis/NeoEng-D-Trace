import unittest
from src.models.scene import Scene
from src.core.commands import CommandManager, ExpandContractCommand

class TestExpandContractCommand(unittest.TestCase):
    def test_expand_contract_undo_redo(self):
        s = Scene()
        s.cmd = CommandManager()
        s.add_object('o1', [(0,0),(10,0),(10,10),(0,10)])
        old = list(s.objects['o1'].polygon)
        new = [( -1,-1),(11,-1),(11,11),(-1,11)]
        cmd = ExpandContractCommand('o1', old, new)
        s.cmd.execute(cmd, s)
        self.assertEqual(s.objects['o1'].polygon, new)
        s.cmd.undo(s)
        self.assertEqual(s.objects['o1'].polygon, old)

if __name__ == '__main__':
    unittest.main()