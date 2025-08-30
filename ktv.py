import threading
import app
import vocal_rm
import vplayer
from signal import signal,SIGINT
import os

def exit_handler(signal_received, frame):
  print('exit')
  os._exit(0)

def main():
  signal(SIGINT, exit_handler)
  t3 = threading.Thread(target=vocal_rm.main)
  t2 = threading.Thread(target=vplayer.main)
  t1 = threading.Thread(target=app.main)
  t1.start()
  t2.start()
  t3.start()

if __name__=="__main__":
  main()
