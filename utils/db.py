"""
Run operations on a sqlite3 database for updating Telegram user IMDb title alerts.
"""

import sqlite3
import functools
import logging


# Setup logger
LOG = logging.getLogger(__name__)


def _catch_and_log(func):
    """
    Decorator function for catching and logging sqlite3 exceptions
    """

    @functools.wraps(func)
    def try_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except sqlite3.Error as db_err:
            LOG.error('Sqlite3 exception in %s: "%s"', func.__qualname__, db_err)
            return 'Internal database error occured.'
    return try_func


class Database():
    """
    sqlite3 Database class for IMDb alert bot
    """


    def __init__(self, db_location):
        """
        Create database and connect
        """

        self.con = sqlite3.connect(db_location,
                                   check_same_thread=False,
                                   detect_types=sqlite3.PARSE_DECLTYPES)
        self.cur = self.con.cursor()


    def __del__(self):
        self.con.close()


    @_catch_and_log
    def create_table(self):
        """
        Create IMDb bot alert table
        """

        self.cur.execute('''CREATE TABLE IF NOT EXISTS imdb_alerts
                            (user_id TEXT,
                             user_name TEXT,
                             title_id TEXT,
                             title_name TEXT,
                             title_episode_id TEXT,
                             title_release TIMESTAMP)''')
        return True


    @_catch_and_log
    def query_title_name(self, user_id):
        """
        Return all IMDb title names from user's alerts
        """

        query = self.cur.execute('''SELECT title_name FROM imdb_alerts
                                    WHERE user_id=?''', (user_id, ))
        rows = query.fetchall()
        results = [row[0] for row in rows if rows]
        return results


    @_catch_and_log
    def query_title_id(self, user_id):
        """
        Return all IMDb title IDs from user's alerts
        """

        query = self.cur.execute('''SELECT title_id FROM imdb_alerts
                                    WHERE user_id=?''', (user_id, ))
        rows = query.fetchall()
        results = [row[0] for row in rows if rows]
        return results


    @_catch_and_log
    def query_user_alert(self, user_id, title_id):
        """
        Check if alert is already enabled for user
        """

        values = (user_id, title_id)
        query = self.cur.execute('''SELECT title_name FROM imdb_alerts
                                    WHERE user_id=? AND title_id=?''', (values))
        result = query.fetchone()
        return result


    @_catch_and_log
    def query_released(self, today):
        """
        Return all user_id, title_id and title_episode_id where title_release
        is today's date
        """

        query = self.cur.execute('''SELECT user_id, title_id, title_episode_id
                                    FROM imdb_alerts
                                    WHERE title_release=?''', (today, ))
        results = query.fetchall()
        return results


    @_catch_and_log
    def insert(self, values):
        """
	    Insert the new values in the database

        values = (user_id, user_name, title_id, title_name,
                  title_episode_id, title_release)
        """

        self.cur.execute('''INSERT INTO imdb_alerts
                            VALUES(?, ?, ?, ?, ?, ?)''', values)
        self.con.commit()
        message = 'Alert enabled.'
        return message


    @_catch_and_log
    def update(self, values):
        """
        Update existing values with new episode ID
        """

        self.cur.execute('''UPDATE imdb_alerts
                            SET title_episode_id=?,
                                title_release=?
							WHERE
                                user_id=?
                            AND
                                title_id=?''', values)
        self.con.commit()


    @_catch_and_log
    def delete(self, user_id, title_id):
        """
        Delete the title ID belonging to user ID from the database
        """

        self.cur.execute('''DELETE FROM imdb_alerts WHERE
                            user_id=? AND title_id=?''', (user_id, title_id))
        self.con.commit()
        message = 'Alert disabled.'
        return message


    @_catch_and_log
    def close(self):
        """
        Close the database connection
        """

        self.con.close()
