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
    """Triggered by a change to a cloud storage bucket
    Args:
        event (dict): Event payload.
        context (google.cloud.functions.Context): Metadata for the event.

        1. Downloads the .wav file to the cloud function instance
        2. Creates a spectrogram image using librosa
        3. Saves the image to the cloud function instance
        5. Uploads the image to a separate GCS bucket.
    """

    # Getting GCS File
    file = event
    bucket = file["bucket"]
    filename = file["name"]
    bucket = client.get_bucket(bucket)
    blob = bucket.blob(filename)

    # Downloading file to a new location on the cloud function instance
    int_folder = filename[: filename.rfind("/")]
    temp_store_loc = "/tmp/raw/" + int_folder
    os.makedirs(temp_store_loc, exist_ok=True)

    audio_data = "/tmp/raw/" + filename  # filename includes temp_store_loc

    logging.info(f"Writing raw file to location: {temp_store_loc}")
    blob.download_to_filename(audio_data)
    logging.info(f"Raw Audio filepath: {audio_data}")

    # Creating a location to the store the processed spectrogram
    processed_file_loc = "/tmp/processed/" + int_folder
    os.makedirs(processed_file_loc, exist_ok=True)
    export_path = "/tmp/processed/" + filename  # filename includes processed_file_loc

    # Creating the spectrogram
    y, sr = librosa.load("/tmp/raw/" + filename)
    n_fft = 2048
    hop_length = 256

    D = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    D = librosa.amplitude_to_db(D, ref=np.max)

    librosa.display.specshow(D, sr=sr, x_axis="time", y_axis="log")

    logging.info(f"Writing processed image to location: {processed_file_loc}")

    # Writing to a location on the cloud function instance
    export_path = "/tmp/processed/" + filename.replace(".wav", ".png")
    plt.axis("off")
    plt.savefig(export_path, pad_inches=0, bbox_inches="tight")
    plt.close()

    # Uploading to a separate GCS bucket.
    target_bucket = client.get_bucket("birdcall-id-spectrograms")

    gcs_export_path = export_path.replace("/tmp/processed/", "")
    logging.info(f"Exporting to GCS location: {gcs_export_path}")

    new_audio_seg = target_bucket.blob(gcs_export_path)
    new_audio_seg.upload_from_filename(export_path)

    return None


if __name__ == "__main__":
    """ testing for sample event before pushing to a cloud function """
    event_string = '{"bucket": "birdcall-id-processed-mp3s", "contentType": "audio/x-wav", "crc32c": "j08FGg==", "etag": "CNPYwKLYy+oCEAE=", "generation": "1594693512080467", "id": "birdcall-id-processed-mp3s/amebit/XC127371.mp3_0_10.wav/1594693512080467", "kind": "storage#object", "md5Hash": "Oa1F2iA0y/nX7TNpyWsn8A==", "mediaLink": "https://www.googleapis.com/download/storage/v1/b/birdcall-id-processed-mp3s/o/amebit%2FXC127371.mp3_0_10.wav?generation=1594693512080467&alt=media", "metageneration": "1", "name": "amebit/XC127371.mp3_0_10.wav", "selfLink": "https://www.googleapis.com/storage/v1/b/birdcall-id-processed-mp3s/o/amebit%2FXC127371.mp3_0_10.wav", "size": "882044", "storageClass": "STANDARD", "timeCreated": "2020-07-14T02:25:12.080Z", "timeStorageClassUpdated": "2020-07-14T02:25:12.080Z", "updated": "2020-07-14T02:25:12.080Z"}'
    event = json.loads(event_string)
    make_spectrogram(event, None)
