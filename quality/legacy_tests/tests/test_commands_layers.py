
import unittest
from src.models.scene import Scene
from src.core.commands import CommandManager, CreateLayerCommand, RemoveLayerCommand, ToggleLayerLockCommand

class TestCommands(unittest.TestCase):
    def test_create_and_remove_layer_command(self):
        s = Scene()
        s.cmd = CommandManager()
        cmd = CreateLayerCommand('L1')
        s.cmd.execute(cmd, s)
        lid = cmd.layer_id
        self.assertTrue(any(l.id==lid for l in s.layers))
        # remove
        cmd2 = RemoveLayerCommand(lid)
        s.cmd.execute(cmd2, s)
        self.assertFalse(any(l.id==lid for l in s.layers))
        # undo remove -> layer restored
        s.cmd.undo(s)
        self.assertTrue(any(l.id==lid for l in s.layers))

    def test_toggle_lock(self):
        s = Scene()
        s.cmd = CommandManager()
        l = s.create_layer('L2')
        cmd = ToggleLayerLockCommand(l.id)
        s.cmd.execute(cmd, s)
        self.assertTrue(any(l.locked for l in s.layers if l.id==l.id))
        s.cmd.undo(s)
