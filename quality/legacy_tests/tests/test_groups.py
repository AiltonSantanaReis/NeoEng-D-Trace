
import unittest
from src.models.scene import Scene
from src.core.commands import CommandManager, CreateGroupCommand, RemoveGroupCommand, AddToGroupCommand, RemoveFromGroupCommand

class TestGroups(unittest.TestCase):
    def test_create_and_remove_group(self):
        s = Scene(); s.cmd = CommandManager()
        cmd = CreateGroupCommand('G1'); s.cmd.execute(cmd, s)
        gid = cmd.group_id
        self.assertTrue(any(g.id==gid for g in getattr(s,'groups',[])))
        cmd2 = RemoveGroupCommand(gid); s.cmd.execute(cmd2, s)
        self.assertFalse(any(g.id==gid for g in getattr(s,'groups',[])))
        s.cmd.undo(s)
        self.assertTrue(any(g.id==gid for g in getattr(s,'groups',[])))

    def test_add_remove_member(self):
        s = Scene(); s.cmd = CommandManager()
        # create object and group
        s.add_object('o1', [(0,0),(1,0),(1,1)])
        cmd = CreateGroupCommand('G2'); s.cmd.execute(cmd, s); gid = cmd.group_id
        cmd2 = AddToGroupCommand(gid, 'o1'); s.cmd.execute(cmd2, s)
        g = next((x for x in getattr(s,'groups',[]) if x.id==gid), None)
        self.assertIsNotNone(g)
        self.assertIn('o1', g.members)
        cmd3 = RemoveFromGroupCommand(gid, 'o1'); s.cmd.execute(cmd3, s)
        self.assertNotIn('o1', g.members)
        s.cmd.undo(s)
        g2 = next((x for x in getattr(s,'groups',[]) if x.id==gid), None)
        self.assertIn('o1', g2.members)

if __name__ == '__main__':
    unittest.main()
