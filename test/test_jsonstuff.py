import os
import unittest
from unittest.mock import patch, mock_open
# import json
from src.jsonstuff import reformat_json


class TestReformatJson(unittest.TestCase):
    def setUp(self):
        self.fake_path = os.path.normpath('/fake/path')

    @patch('os.path.isdir')
    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dump')
    def test_reformat_json_all_files(
        self, mock_json_dump, mock_json_load, mock_open_file, mock_isfile, mock_listdir, mock_isdir
    ):
        # set up the mocking
        mock_isdir.return_value = True
        mock_listdir.return_value = ['file1.json', 'file2.json', 'other.txt']
        mock_isfile.side_effect = lambda filepath: filepath.endswith('.json') and '_reformat' not in filepath
        mock_json_load.return_value = {'key': 'value'}

        # perform the actual test and validate results
        expected_result = [
            os.path.normpath(f'{self.fake_path}/file1_reformat.json'),
            os.path.normpath(f'{self.fake_path}/file2_reformat.json'),
        ]

        result = reformat_json(self.fake_path)
        self.assertEqual(result, expected_result)
        mock_isdir.assert_called_once_with(self.fake_path)
        mock_listdir.assert_called_once_with(self.fake_path)
        self.assertEqual(mock_open_file.call_count, 4)  # 2 reads and 2 writes
        self.assertEqual(mock_json_dump.call_count, 2)

    @patch('os.path.isdir')
    def test_reformat_json_invalid_path(self, mock_isdir):
        # set up the mocking
        mock_isdir.return_value = False

        # perform the actual test and validate results
        with self.assertRaises(FileNotFoundError):
            reformat_json('/invalid/path')

        mock_isdir.assert_called_once_with('/invalid/path')

    @patch('os.path.isdir')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dump')
    def test_reformat_json_specific_files(
        self, mock_json_dump, mock_json_load, mock_open_file, mock_isfile, mock_isdir
    ):
        # set up the mocking
        mock_isdir.return_value = True
        mock_isfile.side_effect = lambda filepath: filepath in [
            os.path.join(self.fake_path, 'file1.json'),
            os.path.join(self.fake_path, 'file2.json')
        ]
        mock_json_load.return_value = {'key': 'value'}

        expected_result = [
            os.path.normpath(f'{self.fake_path}/file1_reformat.json'),
            os.path.normpath(f'{self.fake_path}/file2_reformat.json'),
        ]

        # perform the actual test and validate results
        result = reformat_json(self.fake_path, files=['file1.json', 'file2.json'])
        self.assertEqual(result, expected_result)
        mock_isdir.assert_called_once_with(self.fake_path)
        self.assertEqual(mock_open_file.call_count, 4)  # 2 reads and 2 writes
        self.assertEqual(mock_json_dump.call_count, 2)

    @patch('os.path.isdir')
    @patch('os.path.isfile')
    def test_reformat_json_file_not_found(self, mock_isfile, mock_isdir):
        # set up the mocking
        mock_isdir.return_value = True
        mock_isfile.return_value = False

        # perform the actual test and validate results
        with self.assertRaises(FileNotFoundError):
            reformat_json(self.fake_path, files=['missing_file.json'])

        mock_isdir.assert_called_once_with(self.fake_path)

    @patch('os.path.isdir')
    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    def test_reformat_json_skips_existing_reformatted_files(
        self, mock_json_load, mock_open_file, mock_isfile, mock_listdir, mock_isdir
    ):
        # set up the mocking
        mock_isdir.return_value = True
        mock_listdir.return_value = ['file1.json', 'file1_reformat.json', 'file2.json']

        def isfile_mock(filepath):
            if filepath == os.path.join(self.fake_path, 'file1_reformat.json'):
                return True
            return filepath in [
                os.path.join(self.fake_path, 'file1.json'),
                os.path.join(self.fake_path, 'file2.json')
            ]
        mock_isfile.side_effect = isfile_mock

        mock_json_load.return_value = {'key': 'value'}

        # perform the actual test and validate results
        result = reformat_json(self.fake_path)
        self.assertEqual(result, [os.path.join(self.fake_path, 'file2_reformat.json')])
        mock_isdir.assert_called_once_with(self.fake_path)
        mock_listdir.assert_called_once_with(self.fake_path)
        self.assertEqual(mock_open_file.call_count, 2)  # 1 read and 1 write
