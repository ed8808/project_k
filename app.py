from flask import Flask,render_template,request,url_for,redirect
from flask_table import Table,Col
import vocal_rm
import database
import vplayer
import os
import time

SHOW_QUEUE = "SELECT name,id,state FROM queue WHERE (state IS 'QUEUED' OR state IS 'DOWNLOADED' OR state IS 'PLAYING')  ORDER BY date ASC"
PLAYED_QUEUE = "SELECT name,id,state FROM queue WHERE (state IS 'PLAYED')  ORDER BY date DESC"
INIT_QUEUE = "CREATE TABLE IF NOT EXISTS queue (name TEXT, id TEXT, state TEXT, date INTEGER)"
ADD_QUEUE = "INSERT INTO queue (name, id, state, date) VALUES(?,?,?,?)"
DELETE_QUEUE = "UPDATE queue SET state = ? WHERE (state = ? OR state = ?) AND id = ?" 
SKIP_QUEUE = "UPDATE queue SET date = ? WHERE (state = ? OR state = ?) AND id = ?"
EXIST_QUEUE = "SELECT name,id,state,date FROM queue WHERE name = ? ORDER BY date DESC LIMIT 1"

app = Flask(__name__)

class ItemTable(Table):
  idx = Col('Index')
  name = Col('Song')
  state = Col('State')

class Item(object):
  def __init__(self, idx, name, state):
    self.idx = idx
    self.name = name
    self.state = state

def show_queue(query):
  items=[]
  records=[]
  db_list = database.db_show(query)

  for i in range(len(db_list)):
    if "[" in db_list[i][0]:
      idx = db_list[i][0].rfind('[')
      name= db_list[i][0][:idx]
    else:
      name = db_list[i][0]
    records += [db_list[i][1]]
    items += [Item(i+1,name,db_list[i][2])]
  return items, records

def show_queue_old(query):
  items=[]
  records=[]
  name=[]
  db_list = database.db_show(query)

  for i in range(len(db_list)):
    name += [ db_list[i][0] ]

  names = list(set(name))
  for i in range(len(names)):
    records += [names[i]]
    items += [Item(-(i+1),names[i],'PLAYED')]
  return items, records

def init_queue():
  global cursor
  database.db_create(INIT_QUEUE)

def add_queue(data):
  t = int(time.time())
  database.db_update(ADD_QUEUE, (*data,'QUEUED',t))

def delete_queue(data):
  _, records = show_queue(SHOW_QUEUE)
  if data <= len(records):
    database.db_update(DELETE_QUEUE, ('DELETED', 'QUEUED', 'DOWNLOADED', records[data-1]))

def jump_queue(data):
  _, records = show_queue(SHOW_QUEUE)
  if data <= len(records):
    database.db_update(SKIP_QUEUE, (0, 'QUEUED', 'DOWNLOADED', records[data-1]))

def check_readd_queue(data):
  table = []
  if data[0] == '-':
    data = data[1:]
    if data.isdigit():
      _, records = show_queue_old(PLAYED_QUEUE)
      name = records[int(data)-1]
      data = database.db_find(EXIST_QUEUE, (name,))[0][1]
  return data

@app.route("/", methods=('GET','POST'))
def index():
  if request.method == 'POST':
    try:
      if request.form.get('add') == 'add':
        content = request.form['content']
        content = check_readd_queue(content)
        id,name,_ = vocal_rm.get_filename(content)
        add_queue((name,id))
      elif request.form.get('vocal') == 'vocal':
        vplayer.vocal_toggle()
      elif request.form.get('repeat') == 'repeat':
        vplayer.repeat_video()
      elif request.form.get('stop') == 'stop':
        vplayer.stop_video()
      elif request.form.get('delete') == 'delete':
        content = request.form['content']
        if content.isdigit():
          delete_queue(int(content))
      elif request.form.get('jump') == 'jump':
        content = request.form['content']
        if content.isdigit():
          jump_queue(int(content))
    except Exception as e:
      print(f'Error: {e}')
      pass

  items1,_ = show_queue(SHOW_QUEUE)
  items2,_ = show_queue_old(PLAYED_QUEUE)
  #items = items1+items2
  #table = ItemTable(items)
  table1 = ItemTable(items1)
  table2 = ItemTable(items2)
  return render_template('index.html', tStrToLoad1=table1.__html__(), tStrToLoad2=table2.__html__())

def main():
  init_queue()
  app.run(host='0.0.0.0', port=3000)

if __name__ == '__main__':
  main()
