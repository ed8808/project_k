import sqlite3

DB_QUEUE = 'queue.db'
connection = sqlite3.connect(DB_QUEUE, check_same_thread=False)

def db_create(cmd):
  global connection
  with connection:
    cursor = connection.cursor()
    cursor.execute(cmd)

def db_find(cmd, param):
  global connection
  with connection:
    cursor = connection.cursor()
    return cursor.execute(cmd, param).fetchall()

def db_show(cmd):
  global connection
  with connection:
    cursor = connection.cursor()
    return cursor.execute(cmd).fetchall()

def db_update(cmd, param):
  global connection
  with connection:
    cursor = connection.cursor()
    cursor.execute(cmd, param)
    connection.commit()
