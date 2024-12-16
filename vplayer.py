import database
import mpv
from pygame import mixer
import os
import time

OUTPUT = 'output/'
PLAY_QUEUE = "SELECT name,id,state,date FROM queue WHERE state IS 'DOWNLOADED' ORDER BY date ASC LIMIT 1"
UPDATE_QUEUE = "UPDATE queue SET state = ? WHERE id = ? AND date = ?" 
DELETE_QUEUE = "UPDATE queue SET state = ? WHERE (state = ? OR state = ?) AND id = ?" 

player = 0
repeat = 0
stop = 0
mixer_vol = 0
mixer.init()

def play_media(file):
  global player,mixer,mixer_vol
  player = mpv.MPV(fullscreen=True)
  player.play(file+'.mp4')
  vocal_exist = os.path.exists(file+'.mp3')
  if vocal_exist:
    mixer.music.load(file+'.mp3')
    mixer.music.set_volume(mixer_vol)
    mixer.music.play()
  player.wait_for_playback()
  del player
  if vocal_exist:
    mixer.music.stop()

def vocal_toggle():
  global mixer,mixer_vol
  if mixer_vol:
    mixer_vol=0
  else:
    mixer_vol=1
  mixer.music.set_volume(mixer_vol)

def repeat_video():
  global player,repeat
  repeat = True
  if player:
    player.stop()

def stop_video():
  global player,stop
  stop = True
  if player:
    player.stop()

def main():
  global repeat, stop

  while True:
    time.sleep(1)
    repeat=0
    stop=0
    play_list = database.db_show(PLAY_QUEUE)
    if play_list:
      id = play_list[0][1]
      date = play_list[0][3]
      output_filename = OUTPUT + play_list[0][0]
      if os.path.exists(output_filename+'.mp4') == False:
        database.db_update(UPDATE_QUEUE, ('ERROR', id, date))
        print(f"Error: {output_filename+'.mp4'} file doesn't exist!")
      else:
        play_media(output_filename)
        if repeat:
          pass
        elif stop:
          database.db_update(UPDATE_QUEUE, ('PLAYED', id, date))
        else:
          database.db_update(UPDATE_QUEUE, ('PLAYED', id, date))

if __name__ == '__main__':
  main()
