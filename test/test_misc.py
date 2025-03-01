import unittest
from unittest.mock import patch, mock_open

from src.misc import get_config, csv_to_json, log_exception, list_to_html


class TestGetConfig(unittest.TestCase):
    @patch('os.getenv')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
    def test_get_config_json(self, mock_open_file, mock_isfile, mock_getenv):
        mock_isfile.return_value = True
        mock_getenv.return_value = None

        result = get_config('key', config_file='config.json')

        mock_isfile.assert_called_once_with('config.json')
        mock_open_file.assert_called_once_with('config.json', 'r')
        self.assertEqual(result, 'value')

    @patch('os.getenv')
    @patch('os.path.isfile')
    def test_get_config_no_file(self, mock_isfile, mock_getenv):
        mock_isfile.return_value = False
        mock_getenv.return_value = None

        with self.assertRaises(FileNotFoundError):
            get_config('key', config_file='missing_config.json')

        mock_isfile.assert_called_once_with('missing_config.json')

    @patch('os.getenv')
    def test_get_config_no_env_or_file(self, mock_getenv):
        mock_getenv.return_value = None

        with self.assertRaises(RuntimeError):
            get_config('key')


class TestCsvToJson(unittest.TestCase):
    @patch('csv.reader')
    @patch('builtins.open', new_callable=mock_open)
    def test_csv_to_json(self, mock_open_file, mock_csv_reader):
        mock_csv_reader.return_value = iter([
            ['key', 'value1', 'value2'],
            ['row1', 'data1', 'data2'],
            ['row2', 'data3', 'data4']
        ])

        result = csv_to_json('test.csv', delimiter=',')

        expected = {
            'row1': {'value1': 'data1', 'value2': 'data2'},
            'row2': {'value1': 'data3', 'value2': 'data4'}
        }

        self.assertEqual(result, expected)

    @patch('csv.reader')
    @patch('builtins.open', new_callable=mock_open)
    def test_csv_to_json_duplicate_key(self, mock_open_file, mock_csv_reader):
        mock_csv_reader.return_value = iter([
            ['key', 'value1', 'value2'],
            ['row1', 'data1', 'data2'],
            ['row1', 'data3', 'data4']
        ])

        with self.assertRaises(ValueError):
            csv_to_json('test.csv', delimiter=',')


class TestHtml(unittest.TestCase):
    def test_list_to_html_with_header(self):
        data = [['Header1', 'Header2'], ['Row1Col1', 'Row1Col2'], ['Row2Col1', 'Row2Col2']]

        result = list_to_html(data)

        expected = (
            '<table border="1">'
            '<tr><th>Header1</th><th>Header2</th></tr>'
            '<tr><td>Row1Col1</td><td>Row1Col2</td></tr>'
            '<tr><td>Row2Col1</td><td>Row2Col2</td></tr>'
            '</table>'
        )

        self.assertEqual(result, expected)

    def test_list_to_html_without_header(self):
        data = [['Row1Col1', 'Row1Col2'], ['Row2Col1', 'Row2Col2']]

        result = list_to_html(data, has_header=False)

        expected = (
            '<table border="1">'
            '<tr><td>Row1Col1</td><td>Row1Col2</td></tr>'
            '<tr><td>Row2Col1</td><td>Row2Col2</td></tr>'
            '</table>'
        )

        self.assertEqual(result, expected)


class TestLogging(unittest.TestCase):
    @patch('logging.critical')
    def test_log_exception(self, mock_logging):
        exctype = ValueError
        value = ValueError('Test exception message')
        tb = value.__traceback__

        log_exception(exctype, value, tb)
        mock_logging.assert_called_once()
        log_message = mock_logging.call_args[0][0]
        assert 'type' in log_message
        assert 'description' in log_message
        assert 'traceback' in log_message
        assert 'ValueError' in log_message
        assert 'Test exception message' in log_message


if __name__ == '__main__':
    unittest.main()
