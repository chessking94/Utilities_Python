import os
import unittest
from unittest.mock import patch

from src.cmd import cmd


class TestCmd(unittest.TestCase):
    def setUp(self):
        self.cmd_instance = cmd()
        self.fake_path = os.path.normpath('/fake/path')

    @patch('os.path.isdir')
    @patch('os.path.isfile')
    @patch('os.getcwd')
    @patch('os.chdir')
    @patch('os.system')
    def test_run_script_success(self, mock_system, mock_chdir, mock_getcwd, mock_isfile, mock_isdir):
        mock_isdir.return_value = True
        mock_isfile.return_value = True
        mock_getcwd.return_value = self.fake_path
        mock_system.return_value = 0

        result = self.cmd_instance.run_script(
            program_name='python',
            script_path=self.fake_path,
            script_name='test_script.py',
            parameters='--arg value'
        )

        mock_isdir.assert_called_once_with(self.fake_path)
        mock_isfile.assert_called_once_with(os.path.join(self.fake_path, 'test_script.py'))
        mock_chdir.assert_called_once_with(self.fake_path)
        mock_system.assert_called_once_with('cmd /C python test_script.py --arg value')
        self.assertEqual(result, 0)

    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_run_script_invalid_path(self, mock_isfile, mock_isdir):
        invalid_path = '/invalid/path'
        mock_isdir.return_value = False

        with self.assertRaises(FileNotFoundError):
            self.cmd_instance.run_script(
                program_name='python',
                script_path=invalid_path,
                script_name='test_script.py'
            )

        mock_isdir.assert_called_once_with(invalid_path)
        mock_isfile.assert_not_called()

    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_run_script_invalid_file(self, mock_isfile, mock_isdir):
        mock_isdir.return_value = True
        mock_isfile.return_value = False

        with self.assertRaises(FileNotFoundError):
            self.cmd_instance.run_script(
                program_name='python',
                script_path=self.fake_path,
                script_name='invalid_script.py'
            )

        mock_isdir.assert_called_once_with(self.fake_path)
        mock_isfile.assert_called_once_with(os.path.join(self.fake_path, 'invalid_script.py'))

    @patch('os.path.isdir')
    @patch('os.getcwd')
    @patch('os.chdir')
    @patch('os.system')
    def test_run_command_success(self, mock_system, mock_chdir, mock_getcwd, mock_isdir):
        mock_isdir.return_value = True
        mock_getcwd.return_value = self.fake_path
        mock_system.return_value = 0

        result = self.cmd_instance.run_command(command='echo test', command_path=self.fake_path)

        mock_isdir.assert_called_once_with(self.fake_path)
        mock_chdir.assert_called_once_with(self.fake_path)
        mock_system.assert_called_once_with('cmd /C echo test')
        self.assertEqual(result, 0)

    @patch('os.path.isdir')
    def test_run_command_invalid_path(self, mock_isdir):
        invalid_path = '/invalid/path'
        mock_isdir.return_value = False

        with self.assertRaises(FileNotFoundError):
            self.cmd_instance.run_command(command='echo Hello', command_path=invalid_path)

        mock_isdir.assert_called_once_with(invalid_path)

    def test_run_command_missing_command(self):
        with self.assertRaises(RuntimeError):
            self.cmd_instance.run_command(command='')


if __name__ == '__main__':
    unittest.main()
