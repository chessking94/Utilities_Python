import logging
import os
import shlex
import shutil
import subprocess
import time

import pandas as pd
import sqlalchemy as sa

from . import BOOLEANS


class db:
    """Class to handle processes related to databases

    Can be used directly or as a context manager

    Attributes
    ----------
    conn : Connection
        Object representing database connection

    Notes
    -----
    Only has been tested with SQL Server

    TODO
    ----
    Add general query execution stuff, will need injection defenses
    Is it possible to stop using pandas in _is_job_running and GetLastProcessedID?

    """
    def __init__(self, connection_string: str = None):
        """Inits db class

        Parameters
        ----------
        connection_string : str, optional (default None)
            Connection string of the database to connect to. Will skip connection if not provided.

        """
        self.engine = None
        self.conn = None
        self.connection_string = connection_string
        if self.connection_string:
            self.connection_url = sa.engine.URL.create(
                drivername='mssql+pyodbc',
                query={"odbc_connect": connection_string}
            )

            self.engine = sa.create_engine(self.connection_url)
            self.conn = self.engine.connect().connection

    def close(self):
        """Closes a db object"""
        if self.conn:
            self.conn.close()
            self.engine.dispose()
        else:
            err_msg = 'connection does not exist to close'
            logging.critical(err_msg)
            raise UnboundLocalError(err_msg)

    def __enter__(self):
        """Opens a db object from a context manager"""
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Closes a db object opened with a context manager"""
        if self.conn:
            self.conn.close()
            self.engine.dispose()

    def _is_job_running(self, job_name: str) -> bool:
        """Determines if a SQL Server job is still running

        Parameters
        ----------
        job_name : str
            Name of job to check if is running

        Returns
        -------
        bool : Whether or not the job is running

        Raises
        ------
        TypeError
            If no engine exists

        """
        if not self.engine:
            err_msg = 'connection does not exist'
            logging.critical(err_msg)
            raise TypeError(err_msg)

        qry_text = f"""
SELECT
CASE WHEN act.stop_execution_date IS NULL THEN 1 ELSE 0 END AS is_running

FROM msdb.dbo.sysjobs job
INNER JOIN msdb.dbo.sysjobactivity act ON job.job_id = act.job_id
INNER JOIN msdb.dbo.syssessions sess ON sess.session_id = act.session_id
INNER JOIN (
    SELECT MAX(agent_start_date) AS max_agent_start_date FROM msdb.dbo.syssessions
) sess_max ON sess.agent_start_date = sess_max.max_agent_start_date

WHERE job.name = '{job_name}'
    """
        logging.debug(qry_text)
        return bool(int(pd.read_sql(qry_text, self.engine).values[0][0]))

    def run_job(self, job_name: str, wait_for_completion: bool = False) -> bool:
        """Executes a SQL Server job

        Starts a SQL Server job and optionally waits for it to finish

        Parameters
        ----------
        job_name : str
            Name of job to run
        wait_for_completion : bool, optional (default False)
            Indicates if the script should pause executing until the job completes

        Returns
        -------
        bool : Whether the job is still running at the time the script ends

        Raises
        ------
        TypeError
            If no engine exists

        """
        if not self.engine:
            err_msg = 'connection does not exist'
            logging.critical(err_msg)
            raise TypeError(err_msg)

        wait_for_completion = wait_for_completion if wait_for_completion in BOOLEANS else False
        csr = self.conn.cursor()
        csr.execute(f"EXEC msdb.dbo.sp_start_job @job_name = '{job_name}'")

        logging.debug(f'SQL job "{job_name}" started')
        is_running = True
        if wait_for_completion:
            while is_running:
                time.sleep(5)
                is_running = self._is_job_running(job_name)
            logging.debug(f'SQL job "{job_name}" ended')

        return is_running

    def script_objects(self, root_path: str, server: str, database: str) -> int:
        """Scripts SQL Server objects using mssql-scripter

        Starts a SQL Server job and optionally waits for it to finish

        Parameters
        ----------
        root_path : str
            Primary directory in which objects are scripted to. Actual scripting directory will be root/database
        server : str
            Name of server objects will be scripted from
        database : str
            Name of database objects will be scripted from

        Returns
        -------
        int : the same return value as os.system()

        Raises
        ------
        FileNotFoundError
            If root_path directory does not exists
            If mssql-script is not installed in the environment

        """
        if not os.path.isdir(root_path):
            err_msg = f"path '{root_path}' does not exist"
            logging.critical(err_msg)
            raise FileNotFoundError(err_msg)

        try:
            subprocess.run(['mssql-scripter', '--version'], shell=True)
        except FileNotFoundError:
            err_msg = 'mssql-scripter is not installed in the environment'
            logging.critical(err_msg)
            raise FileNotFoundError(err_msg)

        output_path = os.path.join(root_path, database)
        if os.path.isdir(output_path):
            shutil.rmtree(output_path)

        # apparently rmtree doesn't release the directory rights immediately, need to keep trying
        ct = 0
        while True:
            try:
                os.mkdir(output_path)
                break
            except PermissionError:
                time.sleep(1)
                ct += 1
                if ct == 10:
                    logging.critical(f"unable to create directory '{output_path}'")
                    raise PermissionError
                else:
                    continue

        cmd_text = f'mssql-scripter -S "{server}" -d "{database}"'
        cmd_text = cmd_text + ' --file-per-object'
        cmd_text = cmd_text + ' --script-create'
        cmd_text = cmd_text + ' --collation'
        cmd_text = cmd_text + ' --exclude-headers'
        cmd_text = cmd_text + ' --display-progress'
        cmd_text = cmd_text + f' -f {output_path}'
        cmd = shlex.split(cmd_text, posix=False)
        r = subprocess.run(cmd, shell=True, cwd=root_path)

        return r.returncode

    def GetLastProcessedID(self, database: str, schema: str, table: str) -> int:
        """Obtain a Last_ID value from the table HuntHome.dbo.LastProcessed

        Parameters
        ----------
        database : str
            Name of the database for the ID, maps to HuntHome.dbo.LastProcessed.Database_Name
        schema : str
            Name of the schema for the ID, maps to HuntHome.dbo.LastProcessed.Schema_Name
        table : str
            Name of the table for the ID, maps to HuntHome.dbo.LastProcessed.Table_Name

        Returns
        -------
        int : the last ID value for the passed database, schema, and table

        """
        query = 'SELECT LastID FROM HuntHome.dbo.LastProcessed WHERE [Database_Name] = ? AND [Schema_Name] = ? AND [Table_Name] = ?'
        try:
            last_id = int(pd.read_sql(query, self.engine, coerce_float=False, params=(database, schema, table)).values[0][0])
            return last_id
        except Exception:
            logging.error(f'unable to get ID value: {database}.{schema}.{table}')
            return -1

    def SetLastProcessedID(self, database: str, schema: str, table: str, id: int) -> bool:
        """Sets a Last_ID value in table HuntHome.dbo.LastProcessed

        If the record does not exist, it will be created. If it does, it will be updated.

        Parameters
        ----------
        database : str
            Name of the database for the ID, maps to HuntHome.dbo.LastProcessed.Database_Name
        schema : str
            Name of the schema for the ID, maps to HuntHome.dbo.LastProcessed.Schema_Name
        table : str
            Name of the table for the ID, maps to HuntHome.dbo.LastProcessed.Table_Name
        id : int
            Value of the ID

        Returns
        -------
        bool : if the Set action succeeded

        """
        csr = self.conn.cursor()

        check_query = 'SELECT 1 FROM HuntHome.dbo.LastProcessed WHERE [Database_Name] = ? AND [Schema_Name] = ? AND [Table_Name] = ?'
        try:
            csr.execute(check_query, database, schema, table)
            exists = csr.fetchone()  # returns None if no record is found
        except Exception:
            logging.error(f'unable to set ID value: {database}.{schema}.{table} = {id}')
            return False

        if exists is None:
            query = 'INSERT INTO HuntHome.dbo.LastProcessed ([Last_ID], [Database_Name], [Schema_Name], [Table_Name]) VALUES (?, ?, ?, ?)'
        else:
            query = 'UPDATE HuntHome.dbo.LastProcessed SET Last_ID = ? WHERE [Database_Name] = ? AND [Schema_Name] = ? AND [Table_Name] = ?'

        try:
            csr.execute(query, id, database, schema, table)
            self.conn.commit()
            return True
        except Exception:
            logging.error(f'unable to set ID value: {database}.{schema}.{table} = {id}')
            return False
