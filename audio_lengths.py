from pydub import AudioSegment
import math
import os
import pandas as pd 

def audio_length(input_folder, input_file):
    song = AudioSegment.from_mp3(input_folder+'/'+input_file)
    song_length = math.floor(len(song)/1000)
    return song_length

def all_audio_lengths():
    for root, _, filenames in os.walk('data/train_audio'):
        if not any(map(lambda x: x.endswith('.mp3'), filenames)):
            continue
        bird = root[root.rfind('/')+1:]
        lengths = []
        for filename in filenames:
            if not filename.endswith('mp3'):
                continue
            else:
                lengths.append(audio_length(root, filename))
        df = pd.DataFrame(lengths)
        with open('audio_lengths.txt', 'a') as myfile:
            myfile.write(f'Bird: {bird}')
            myfile.write(str(df.describe()))
            myfile.write('\n\n')
        
        print(f'Finished bird: {bird}')
    return None

if __name__ == '__main__':
    all_audio_lengths()