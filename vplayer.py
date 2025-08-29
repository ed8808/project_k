import database
import mpv
from pygame import mixer
import os
import subprocess
import time

OUTPUT = 'output/'
PLAY_QUEUE = "SELECT name,id,state,date FROM queue WHERE (state IS 'DOWNLOADED' OR state IS 'PLAYING') ORDER BY date ASC LIMIT 1"
UPDATE_QUEUE = "UPDATE queue SET state = ? WHERE id = ? AND date = ?" 
DELETE_QUEUE = "UPDATE queue SET state = ? WHERE (state = ? OR state = ?) AND id = ?" 

player = 0
repeat = 0
stop = 0
pause = False
mixer_vol = 0
vocal_exist = 0
mixer.init()
player = mpv.MPV(fullscreen=True)

def play_media(file):
  global player,mixer,mixer_vol,vocal_exist
  mixer_vol = 0
  player.volume = 100
  player.play(file+'.mp4')
  vocal_exist = os.path.exists(file+'.wav')
  if vocal_exist:
    #time.sleep(0.5)
    mixer.music.load(file+'.wav')
    mixer.music.set_volume(mixer_vol)
    mixer.music.play()
  player.wait_for_playback()
  #del player
  if vocal_exist:
    mixer.music.stop()
    #mixer.quit()

def vocal_toggle():
  global player,mixer,mixer_vol,vocal_exist
  if vocal_exist:
    if mixer_vol:
      mixer_vol=0
      mixer.music.set_volume(0)
      player.volume = 100

    else:
      mixer_vol=1
      mixer.music.set_volume(0.3)
      player.volume = 0

def repeat_video():
  global player, mixer, repeat, vocal_exist
  repeat = True
  if player:
    player.stop()
  if vocal_exist:
    mixer.music.stop()

def stop_video():
  global player, mixer, stop, vocal_exist
  stop = True
  if player:
    player.stop()
  if vocal_exist:
    mixer.music.stop()

def pause_video():
  global pause
  pause = not pause

def main():
  global repeat, stop, pause

  while True:
    time.sleep(1)
    repeat=0
    stop=0
    if True:
      play_list = database.db_show(PLAY_QUEUE)
      if play_list and not pause:
        id = play_list[0][1]
        date = play_list[0][3]
        output_filename = OUTPUT + play_list[0][0]
        if os.path.exists(output_filename+'.mp4') == False:
          database.db_update(UPDATE_QUEUE, ('ERROR', id, date))
          print(f"Error: {output_filename+'.mp4'} file doesn't exist!")
        else:
          database.db_update(UPDATE_QUEUE, ('PLAYING', id, date))
          play_media(output_filename)
          if repeat:
            pass
          elif stop:
            database.db_update(UPDATE_QUEUE, ('PLAYED', id, date))
          else:
            database.db_update(UPDATE_QUEUE, ('PLAYED', id, date))

if __name__ == '__main__':
  main()
