import os
import unittest
from unittest.mock import patch, MagicMock

from src.db import db


class TestDbMethods(unittest.TestCase):
    def setUp(self):
        self.connection_string = 'Driver={SQL Server};Server=server_name;Database=database_name;'

    # def tearDown(self):
    #     pass

    @patch('src.db.sa.create_engine')
    def test_init_with_connection_string(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        db_obj = db(self.connection_string)

        self.assertEqual(db_obj.connection_string, self.connection_string)
        self.assertEqual(db_obj.engine, mock_engine)
        self.assertIsNotNone(db_obj.conn)

    @patch('src.db.sa.create_engine')
    @patch('src.db.sa.engine.URL.create')
    def test_init_without_connection_string(self, mock_engine_url, mock_create_engine):
        db_obj = db()
        self.assertIsNone(db_obj.connection_string)
        self.assertIsNone(db_obj.engine)
        self.assertIsNone(db_obj.conn)

    @patch('src.db.sa.create_engine')
    def test_run_job(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = MagicMock()
        mock_engine.connect.return_value.connection = MagicMock()

        db_obj = db(self.connection_string)

        result = db_obj.run_job('TestJob')
        self.assertTrue(result)

    @patch('src.db.sa.create_engine')
    @patch('src.db.db._is_job_running')
    def test_run_job_waiting_for_completion(self, mock_is_job_running, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = MagicMock()
        mock_engine.connect.return_value.connection = MagicMock()
        mock_is_job_running.side_effect = [True, False]  # simulating job running and then finishing

        db_obj = db(self.connection_string)

        result = db_obj.run_job('TestJob', wait_for_completion=True)
        mock_is_job_running.assert_called()
        self.assertFalse(result)

    @patch('src.db.sa.create_engine')
    @patch('src.db.os.path.isdir')
    @patch('src.db.os.mkdir')
    @patch('src.db.shutil.rmtree')
    @patch('src.db.subprocess.run')
    def test_script_objects(self, mock_subprocess_run, mock_rmtree, mock_mkdir, mock_isdir, mock_create_engine):
        root_path = '/fake/path'
        server = 'server_name'
        database = 'database_name'

        mock_engine = MagicMock()
        mock_create_engine.return_value = MagicMock()
        mock_engine.connect.return_value.connection = MagicMock()
        mock_isdir.return_value = True
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        db_obj = db(self.connection_string)

        result = db_obj.script_objects(root_path, server, database)
        mock_isdir.assert_called_with(os.path.join(root_path, database))
        mock_subprocess_run.assert_called()
        self.assertEqual(result, 0)

    @patch('src.db.sa.create_engine')
    @patch('src.db.pd.read_sql')
    def test_get_last_processed_id(self, mock_read_sql, mock_create_engine):
        db_obj = db(self.connection_string)
        database = 'database_name'
        schema = 'dbo'
        table = 'TestTable'

        mock_engine = MagicMock()
        mock_create_engine.return_value = MagicMock()
        mock_engine.connect.return_value.connection = MagicMock()
        mock_read_sql.return_value = MagicMock(values=[[123]])

        result = db_obj.GetLastProcessedID(database, schema, table)

        mock_read_sql.assert_called()
        self.assertEqual(result, 123)

    @patch('src.db.sa.create_engine')
    @patch('src.db.pd.read_sql')
    def test_get_last_processed_id_no_result(self, mock_read_sql, mock_create_engine):
        db_obj = db(self.connection_string)
        database = 'database_name'
        schema = 'dbo'
        table = 'TestTable'

        mock_engine = MagicMock()
        mock_create_engine.return_value = MagicMock()
        mock_engine.connect.return_value.connection = MagicMock()
        mock_read_sql.side_effect = Exception('Query failed')

        result = db_obj.GetLastProcessedID(database, schema, table)

        self.assertEqual(result, -1)

    @patch('src.db.sa.create_engine')
    @patch('src.db.pd.read_sql')
    def test_set_last_processed_id(self, mock_read_sql, mock_create_engine):
        db_obj = db(self.connection_string)
        database = 'database_name'
        schema = 'dbo'
        table = 'TestTable'
        id_value = 123

        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_create_engine.return_value = MagicMock()
        mock_engine.connect.return_value = mock_connection
        mock_connection.__enter__.return_value.cursor.return_value = mock_cursor
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = None  # simulate no existing record

        result = db_obj.SetLastProcessedID(database, schema, table, id_value)

        self.assertTrue(result)

    @patch('src.db.sa.create_engine')
    @patch('src.db.pd.read_sql')
    def test_set_last_processed_id_update(self, mock_read_sql, mock_create_engine):
        db_obj = db(self.connection_string)
        database = 'database_name'
        schema = 'dbo'
        table = 'TestTable'
        id_value = 123

        mock_engine = MagicMock()
        mock_create_engine.return_value = MagicMock()
        mock_engine.connect.return_value.connection = MagicMock()

        mock_cursor = MagicMock()
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = [1]  # simulate record exists

        result = db_obj.SetLastProcessedID(database, schema, table, id_value)
        self.assertTrue(result)

    @patch('src.db.logging.critical')
    def test_close_without_connection(self, mock_logging_critical):
        db_obj = db()

        with self.assertRaises(UnboundLocalError):
            db_obj.close()

        mock_logging_critical.assert_called_with('connection does not exist to close')


if __name__ == '__main__':
    unittest.main()
