import unittest
from console import Shell


class TestShell(unittest.TestCase):
    def setUp(self):
        self.shell = Shell()

    def test_ls(self):
        self.assertEqual(self.shell.onecmd("ls test.py"), "ls: cannot access 'test.py': No such file or directory.")
        self.assertEqual(self.shell.onecmd("ls home"), "username")
        self.assertEqual(self.shell.onecmd("ls"), "bin boot dev etc home lib lib32 lib64 media mnt opt proc run sbin snap srv sys tmp usr var")

    def test_cd(self):
        self.shell.onecmd("cd home")
        self.assertEqual(self.shell.current_directory, "/home")
        self.shell.onecmd("cd /home/username/media")
        self.assertEqual(self.shell.current_directory, "/home/username/media")
        self.shell.onecmd("cd /")
        self.assertEqual(self.shell.current_directory, "/")

    def test_echo(self):
        self.assertEqual(self.shell.onecmd("echo 12345"), "12345")
        self.assertEqual(self.shell.onecmd('echo "Hello World!"'), "Hello World!")
        self.assertEqual(self.shell.onecmd("echo"), "")

    def test_cal(self):
        self.assertEqual(self.shell.onecmd("cal"), self.shell.onecmd("cal"))



if __name__ == "__main__":
    unittest.main()