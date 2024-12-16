import json
import yt_dlp
import os, glob
import subprocess
from src import models
import torch
import audiofile
import time
import database

TEMP = 'temp/'
OUTPUT = 'output/'
vocals_path = TEMP+"vocals.mp3"
base_path = TEMP+"base.mp3"
drums_path = TEMP+"drums.mp3"
other_path = TEMP+"other.mp3"
id=''
output_filename=''
format=''
QUEUED_QUEUE = "SELECT name,id,state,date FROM queue WHERE state IS 'QUEUED' ORDER BY date ASC LIMIT 1"
UPDATE_QUEUE = "UPDATE queue SET name = ?, state = ? WHERE id = ? AND date = ?" 
EXIST_QUEUE = "SELECT name,id,state,date FROM queue WHERE (state IS 'QUEUED' OR state is 'DOWNLOADED' OR state IS 'PLAYED') AND id = ? ORDER BY date DESC LIMIT 1"

def get_uid(url):
  return url

def get_filename(url):
  with yt_dlp.YoutubeDL() as ydl:
    info_dict = ydl.extract_info(url, download=False)
    output_filename = ydl.prepare_filename(info_dict)
    idx = output_filename.rfind('.')
    format = output_filename[idx+1:]
    output_filename = output_filename[:idx]
    id = get_uid(url)
    return id, output_filename, format

def get_titlename(filename):
  idx = filename.rfind('[')
  return filename[:idx]

def extract_audio(url,format='wav'):
  ydl_opts = {
    'format': format+'/bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': format,
    }]
  }

  with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    error_code = ydl.download(url)
  subprocess.call(['mv', output_filename+'.'+format, TEMP+output_filename+'.'+format])
  return error_code

def extract_video(url):
  with yt_dlp.YoutubeDL() as ydl:
    error_code = ydl.download(url)
  subprocess.call(['mv', output_filename+'.'+format, TEMP+output_filename+'.'+format])
  return error_code

def mix_audio(infiles, outfile=TEMP+'mixed.wav'):
  param = ''
  for infile in infiles:
    if os.path.exists(infile) == False:
      print(f"Error: {infile} file doesn't exist!")
      return
    param += ' -i '+infile
  param += f' -y -filter_complex amix=inputs={len(infiles)}:duration=longest:dropout_transition=0:normalize=0 -aq 0 {outfile}'
  return os.system(f'ffmpeg {param}')

def replace_audio(video_src, video_target, audio_src=TEMP+'mixed.wav'):
  if os.path.exists(video_src) == False:
    print(f"Error: {video_src} file doesn't exist!")
    return
  if os.path.exists(audio_src) == False:
    print(f"Error: {audio_src} file doesn't exist!")
    return
  subprocess.call(['ln','-sf',video_src,'_temp'])
  param = f'-y -i _temp -i {audio_src} -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 temp.mp4'
  os.system(f'ffmpeg {param}')
  subprocess.call(['mv','temp.mp4',video_target])

def copy_vocal(audio_target, audio_src=TEMP+'vocals.mp3'):
  if os.path.exists(audio_src) == False:
    print(f"Error: {audio_src} file doesn't exist!")
  subprocess.call(['cp',audio_src,audio_target])

def vocal_remove(url):
  global id,output_filename,format

  start_time = time.time()
  id, output_filename,format = get_filename(url)
  extract_audio(url)
  extract_video(url)

  if torch.cuda.is_available(): device = "cuda"
  elif torch.backends.mps.is_available(): device = torch.device("mps")
  else: device = "cpu"
  print(f'device = {device}: vocal removal in progress ... ')
  demucs = models.Demucs(name="hdemucs_mmi", other_metadata={"segment":2, "split":True},
                        device=device, logger=None)
  res = demucs(TEMP+output_filename+'.wav')
  seperted_audio = res
  vocals = seperted_audio["vocals"]
  base = seperted_audio["bass"]
  drums = seperted_audio["drums"]
  other = seperted_audio["other"]

  audiofile.write(vocals_path, vocals, demucs.sample_rate)
  audiofile.write(base_path, base, demucs.sample_rate)
  audiofile.write(drums_path, drums, demucs.sample_rate)
  audiofile.write(other_path, other, demucs.sample_rate)

  mix_audio([base_path, drums_path, other_path])
  replace_audio(TEMP+output_filename+'.'+format, OUTPUT+output_filename+'.mp4')
  copy_vocal(OUTPUT+output_filename+'.mp3')

  e = glob.escape(TEMP+output_filename)
  dumps = glob.glob(e+'*', recursive=True)
  for dump in dumps:
    os.remove(dump)

  print(f'process finished in seconds {(time.time() - start_time)}')
  return output_filename

def check_exist(url):
  global output_filename

  db_list = database.db_find(EXIST_QUEUE, (url,))
  if len(db_list):
    output_filename = db_list[0][0]
    return os.path.exists(OUTPUT+output_filename+'.mp4')
  return False

def main():
  global output_filename

  while True:
    time.sleep(1)
    download_list = database.db_show(QUEUED_QUEUE)
    if download_list:
      id = download_list[0][1]
      date = download_list[0][3]
      try:
        if not check_exist(id):
          output_filename = vocal_remove(id)
        database.db_update(UPDATE_QUEUE, (output_filename, 'DOWNLOADED', id, date))
      except Exception as e:
        database.db_update(UPDATE_QUEUE, (id, 'ERROR', id, date))
        print(f'Error at converting {e}')
        pass

if __name__=="__main__":
  main()
