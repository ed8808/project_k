from flask import Flask,render_template,request,url_for,redirect, jsonify, Response
from flask_table import Table,Col
import vocal_rm
import database
import vplayer
import os
import time
import queue
import threading

SHOW_QUEUE = "SELECT name,id,state,date FROM queue WHERE (state IS 'QUEUED' OR state IS 'CONVERTING' OR state IS 'DOWNLOADED' OR state IS 'PLAYING')  ORDER BY date ASC"
PLAYED_QUEUE = "SELECT name,id,state FROM queue WHERE (state IS 'PLAYED')  ORDER BY date"
CONVERT_QUEUE = "SELECT name,id,state,date FROM queue WHERE (state IS 'CONVERTING')  ORDER BY date DESC"
INIT_QUEUE = "CREATE TABLE IF NOT EXISTS queue (name TEXT, id TEXT, state TEXT, date INTEGER)"
ADD_QUEUE = "INSERT INTO queue (name, id, state, date) VALUES(?,?,?,?)"
DELETE_QUEUE = "UPDATE queue SET state = ? WHERE (state = ? OR state = ? OR state = ?) AND id = ? AND date = ?" 
SKIP_QUEUE = "UPDATE queue SET date = ? WHERE (state = ? OR state = ?) AND id = ?"
EXIST_QUEUE = "SELECT name,id,state,date FROM queue WHERE name = ? ORDER BY date DESC LIMIT 1"

app = Flask(__name__)
# List to hold all connected clients (EventSource connections)
clients = []
_queue = 0

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
  states=[]
  ts=[]
  db_list = database.db_show(query)

  for i in range(len(db_list)):
    if "[" in db_list[i][0]:
      idx = db_list[i][0].rfind('[')
      name= db_list[i][0][:idx]
    else:
      name = db_list[i][0]
    records += [db_list[i][1]]
    states += [db_list[i][2]]
    ts += [db_list[i][3]]
    items += [Item(i+1,name,db_list[i][2])]
  return items, records, states, ts

def show_queue_old(query):
  items=[]
  records=[]
  name=[]
  db_list = database.db_show(query)
  
  for i in range(len(db_list)):
    name += [ db_list[i][0] ]

  #names = list(set(name))
  names = list(dict.fromkeys(name))
  for i in range(len(names)):
    records += [names[i]]
    if "[" in names[i]:
      idx = names[i].rfind("[")
      names[i] = names[i][:idx]
    items = [Item(-(i+1),names[i],'PLAYED')] + items
  return items, records

def init_queue():
  global cursor
  database.db_create(INIT_QUEUE)

def tidy_queue():
  db_list = database.db_show(CONVERT_QUEUE)
  for i in range(len(db_list)):
    if i == 0:
      database.db_update(DELETE_QUEUE, ('QUEUED', 'CONVERTING', 'CONVERTING', 'CONVERTING', db_list[i][1], db_list[i][3]))
    else:
      database.db_update(DELETE_QUEUE, ('PLAYED', 'CONVERTING', 'CONVERTING', 'CONVERTING', db_list[i][1], db_list[i][3]))

def add_queue(data):
  t = int(time.time())
  database.db_update(ADD_QUEUE, (*data,'QUEUED',t))

def delete_queue(data):
  _, records, _, ts = show_queue(SHOW_QUEUE)
  if data <= len(records):
    database.db_update(DELETE_QUEUE, ('DELETED', 'QUEUED', 'CONVERTING', 'DOWNLOADED', records[data-1], ts[data-1]))

def jump_queue(data):
  _, records, states, ts = show_queue(SHOW_QUEUE)
  if data <= len(records):
    for i in range(len(records)): #find first queued records and skip to its front
      if states[i] == 'QUEUED' or states[i] == 'DOWNLOADED':
        new_ts = ts[i]-1
        database.db_update(SKIP_QUEUE, (new_ts, 'QUEUED', 'DOWNLOADED', records[data-1]))
        break

def check_readd_queue(data):
  table = []
  if data[0] == '-':
    data = data[1:]
    if data.isdigit():
      _, records = show_queue_old(PLAYED_QUEUE)
      name = records[int(data)-1]
      data = database.db_find(EXIST_QUEUE, (name,))[0][1]
  return data

# Background function to send a forced refresh signal to all clients
def send_refresh_to_all():
  global clients
  while True:
    time.sleep(3)  # Wait for 10 seconds (or any interval you want)

    # Send refresh signal to all connected clients
    for client in clients:
      client.put("data: refresh\n\n")

@app.route("/")
def index():
  return render_template('index.html')

@app.route("/stream")
def stream():
  def generate():
    global _queue, clients
    _queue = queue.Queue()
    clients.append(_queue)  # Add the client to the list of connected clients

    try:
        while True:
            message = _queue.get()  # Wait for a message from the server
            yield message  # Send the message to the client (via SSE)

    finally:
        clients.remove(_queue)  # Remove the client when they disconnect

  return Response(generate(), content_type='text/event-stream')

@app.route("/get_table")
def get_table():
  items1,_,_,_ = show_queue(SHOW_QUEUE)
  items2,_ = show_queue_old(PLAYED_QUEUE)
  return render_template('table.html', songs=items1+[Item('','','') for i in range(1)]+items2)

@app.route("/process", methods=['POST', 'GET'])
def process_parser():
  if request.method == 'POST':
    try:
      command = ''
      param = ''
      server_data = request.get_json()
      if 'cmd' in server_data:
        command = server_data['cmd']
      if 'param' in server_data:
        content = server_data['param']

      if command == 'add':
        content = check_readd_queue(content)
        id,name,_ = vocal_rm.get_filename(content)
        add_queue((name,id))
      elif command == 'vocal':
        vplayer.vocal_toggle()
      elif command == 'repeat':
        vplayer.repeat_video()
      elif command == 'stop':
        vplayer.stop_video()
      elif command == 'pause':
        vplayer.pause_video()
      elif command == 'delete':
        if content.isdigit():
          delete_queue(int(content))
      elif command == 'jump':
        if content.isdigit():
          jump_queue(int(content))
      
      return jsonify({'processed':'true'})

    except Exception as e:
      print(f'Error: {e}')
      pass


def main():
  init_queue()
  tidy_queue()
  # Start the background thread to periodically send refresh signal to clients
  thread = threading.Thread(target=send_refresh_to_all)
  thread.daemon = True  # Ensure the thread will stop when the server stops
  thread.start()
  app.run(host='0.0.0.0', port=3000)

if __name__ == '__main__':
  main()
