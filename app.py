from flask import Flask,render_template,request,url_for,redirect
from flask_table import Table,Col
import vocal_rm
import database
import vplayer
import os
import time

records = []
table = []
SHOW_QUEUE = "SELECT name,id,state FROM queue WHERE state IS 'QUEUED' OR state IS 'DOWNLOADED'  ORDER BY date ASC"
INIT_QUEUE = "CREATE TABLE IF NOT EXISTS queue (name TEXT, id TEXT, state TEXT, date INTEGER)"
ADD_QUEUE = "INSERT INTO queue (name, id, state, date) VALUES(?,?,?,?)"
DELETE_QUEUE = "UPDATE queue SET state = ? WHERE (state = ? OR state = ?) AND id = ?" 
SKIP_QUEUE = "UPDATE queue SET date = ? WHERE (state = ? OR state = ?) AND id = ?"

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

def show_queue():
  global table,records
  items=[]
  records=[]
  db_list = database.db_show(SHOW_QUEUE)
  for i in range(len(db_list)):
    if "[" in db_list[i][0]:
      idx = db_list[i][0].rfind('[')
      name= db_list[i][0][:idx]
    else:
      name = db_list[i][0]
    records += [db_list[i][1]]
    items += [Item(i+1,name,db_list[i][2])]
  table = ItemTable(items)

def init_queue():
  global cursor
  database.db_create(INIT_QUEUE)

def add_queue(data):
  t = int(time.time())
  database.db_update(ADD_QUEUE, (*data,'QUEUED',t))

def delete_queue(data):
  global records
  if data <= len(records):
    database.db_update(DELETE_QUEUE, ('DELETED', 'QUEUED', 'DOWNLOADED', records[data-1]))

def jump_queue(data):
  global records
  if data <= len(records):
    database.db_update(SKIP_QUEUE, (0, 'QUEUED', 'DOWNLOADED', records[data-1]))

@app.route("/", methods=('GET','POST'))
def index():
  global table

  if request.method == 'POST':
    if request.form.get('convert') == 'convert':
      content = request.form['content']
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
  show_queue()

  if table:
    return render_template('index.html', tStrToLoad=table.__html__())
  return render_template('index.html')

def main():
  init_queue()
  app.run(host='0.0.0.0', port=3000)

if __name__ == '__main__':
  main()
