import matplotlib.pyplot as plt
import librosa
import librosa.display
import numpy as np
import json
import os
import logging
from google.cloud import storage 

client = storage.Client()

def make_spectrogram(event, context):
    file = event
    bucket = file["bucket"]
    filename = file["name"]
    bucket = client.get_bucket(bucket)
    blob = bucket.blob(filename)

    int_folder = filename[: filename.rfind("/")]
    temp_store_loc = "/tmp/raw/" + int_folder
    os.makedirs(temp_store_loc, exist_ok=True)

    audio_data = "/tmp/raw/" + filename  # filename includes temp_store_loc
    
    logging.info(f"Writing raw file to location: {temp_store_loc}")
    blob.download_to_filename(audio_data)
    logging.info(f"Raw Audio filepath: {audio_data}")

    processed_file_loc = "/tmp/processed/" + int_folder
    os.makedirs(processed_file_loc, exist_ok=True)
    export_path = "/tmp/processed/" + filename  # filename includes processed_file_loc
    
    y, sr = librosa.load('/tmp/raw/' + filename)
    n_fft = 2048
    hop_length = 256
    D = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))

    D = librosa.amplitude_to_db(D, ref=np.max)

    librosa.display.specshow(D, sr=sr, x_axis="time", y_axis="log")

    logging.info(f"Writing processed image to location: {processed_file_loc}")

    export_path = '/tmp/processed/'+ filename.replace('.wav', '.png')
    plt.axis("off")
    plt.savefig(export_path, pad_inches=0, bbox_inches="tight")
    plt.close()

    target_bucket = client.get_bucket("birdcall-id-spectrograms")
    
    gcs_export_path = export_path.replace("/tmp/processed/", "")
    logging.info(f"Exporting to GCS location: {gcs_export_path}")

    new_audio_seg = target_bucket.blob(gcs_export_path)
    new_audio_seg.upload_from_filename(export_path)

    return None

if __name__=='__main__':
    ''' testing for sample event before pushing to a cloud function '''
    event_string = '{"bucket": "birdcall-id-processed-mp3s", "contentType": "audio/wav", "crc32c": "sEc31Q==", "etag": "CO/yorvTy+oCEAE=", "generation": "1594692221843823", "id": "birdcall-id-processed-mp3s/aldfly/XC141320_60_70.wav/1594692221843823", "kind": "storage#object", "md5Hash": "+olcpnNygm/NTHh87P0csg==", "mediaLink": "https://www.googleapis.com/download/storage/v1/b/birdcall-id-processed-mp3s/o/aldfly%2FXC141320_60_70.wav?generation=1594692221843823&alt=media", "metageneration": "1", "name": "aldfly/XC141320_60_70.wav", "selfLink": "https://www.googleapis.com/storage/v1/b/birdcall-id-processed-mp3s/o/aldfly%2FXC141320_60_70.wav", "size": "882044", "storageClass": "STANDARD", "timeCreated": "2020-07-14T02:03:41.843Z", "timeStorageClassUpdated": "2020-07-14T02:03:41.843Z", "updated": "2020-07-14T02:03:41.843Z"}'
    event = json.loads(event_string)
    make_spectrogram(event, None)