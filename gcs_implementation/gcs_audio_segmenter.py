from pydub import AudioSegment 
from google.cloud import storage
import logging 
import json 
import math 
import os 

client = storage.Client()

def audio_segment(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
        event (dict): Event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    file = event
    bucket = client.get_bucket(file['bucket'])
    blob = bucket.blob(file['name'])

    int_folder = file['name'][:file['name'].rfind('/')]
    print(f"Int Folder: {int_folder}")

    os.makedirs('/tmp/raw/'+int_folder, exist_ok=True)

    audio_data = '/tmp/raw/'+file['name']
    blob.download_to_filename(audio_data)
    print(f"Audio filepath: {audio_data}")

    song = AudioSegment.from_mp3(audio_data)
    
    seg_length = 10
    song = song.set_channels(1)  # enforce mono rather than stereo
    song = song.set_frame_rate(44100)  # uniformize, 44.1k is cd standard
    seg_count = math.floor(len(song) / 1000 / seg_length)

    os.makedirs('/tmp/processed/'+int_folder, exist_ok=True)

    export_path = '/tmp/processed/'+file['name']

    print(f"Export Path: {export_path}")

    bucket = client.get_bucket('birdcall-id-processed-mp3s')

    for i in range(seg_count):
        start_ts, stop_ts = seg_length * 1000 * i, seg_length * 1000 * (i + 1)
        segment = song[start_ts:stop_ts]
        export_name = export_path+ "_" + str(i * seg_length) + "_" + str((i + 1) * seg_length) + ".wav"
        segment.export(export_name, format="wav")

        gcs_export_name = export_name.replace('/tmp/processed/', '')
        print(f'GCS Export Filename: {gcs_export_name}')
        new_audio_seg = bucket.blob(gcs_export_name)   
        new_audio_seg.upload_from_filename(export_name)

    return None


if __name__=='__main__':
    ''' testing before uploading function as cloud function '''
    sample_json = json.loads('{"bucket": "birdcall-id-raw-mp3s", "contentType": "audio/mpeg", "crc32c": "dPENGw==", "etag": "CO67kcCAy+oCEAE=", "generation": "1594669951901166", "id": "birdcall-id-raw-mp3s/amebit/XC127371.mp3/1594669951901166", "kind": "storage#object", "md5Hash": "aCvKDRoFWR768FIcBspUoQ==", "mediaLink": "https://www.googleapis.com/download/storage/v1/b/birdcall-id-raw-mp3s/o/amebit%2FXC127371.mp3?generation=1594669951901166&alt=media", "metageneration": "1", "name": "amebit/XC127371.mp3", "selfLink": "https://www.googleapis.com/storage/v1/b/birdcall-id-raw-mp3s/o/amebit%2FXC127371.mp3", "size": "805212", "storageClass": "STANDARD", "timeCreated": "2020-07-13T19:52:31.901Z", "timeStorageClassUpdated": "2020-07-13T19:52:31.901Z", "updated": "2020-07-13T19:52:31.901Z"}')
    audio_segment(sample_json, None)