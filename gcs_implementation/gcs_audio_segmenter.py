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

        1. Downloads the file to the cloud function instance
        2. Reads that file into pydub
        3. Splits the file into 10 second chunks
        4. Writes the collection of files to the cloud function instance
        5. Uploads those files to a separate GCS bucket.
    """

    # Getting GCS File
    file = event
    bucket = file["bucket"]
    filename = file["name"]
    bucket = client.get_bucket(bucket)
    blob = bucket.blob(filename)

    # Making a target directory and saving the file to the cloud function instance
    int_folder = filename[: filename.rfind("/")]

    temp_store_loc = "/tmp/raw/" + int_folder
    logging.info(f"Writing raw file to location: {temp_store_loc}")

    os.makedirs(temp_store_loc, exist_ok=True)

    audio_data = "/tmp/raw/" + filename  # filename includes temp_store_loc
    blob.download_to_filename(audio_data)
    logging.info(f"Raw Audio filepath: {audio_data}")

    # Reading the function into pydub and splitting into 10s chunks
    song = AudioSegment.from_mp3(audio_data)
    song = song.set_channels(1)  # enforce mono rather than stereo
    song = song.set_frame_rate(44100)  # uniformize, 44.1k is cd standard

    seg_length = 10  # hardcoded for cloud function. Maybe env var is the way to go?
    seg_count = math.floor(len(song) / 1000 / seg_length)

    # Saving the resulting files to a new location on the cloud function instance
    processed_file_loc = "/tmp/processed/" + int_folder
    logging.info(f"Writing processed file to location: {processed_file_loc}")

    os.makedirs(processed_file_loc, exist_ok=True)

    export_path = "/tmp/processed/" + filename  # filename includes processed_file_loc

    bucket = client.get_bucket("birdcall-id-processed-mp3s")

    for i in range(seg_count):
        start_ts, stop_ts = seg_length * 1000 * i, seg_length * 1000 * (i + 1)
        segment = song[start_ts:stop_ts]
        export_name = (
            export_path
            + "_"
            + str(i * seg_length)
            + "_"
            + str((i + 1) * seg_length)
            + ".wav"
        )
        segment.export(export_name, format="wav")
        logging.info(f"Processed export file #{i} in location: {export_path}")

        # Uploading the files to a separate GCS bucket.
        gcs_export_name = export_name.replace("/tmp/processed/", "")
        logging.info(f"Exporting to GCS location: {gcs_export_name}")

        new_audio_seg = bucket.blob(gcs_export_name)
        new_audio_seg.upload_from_filename(export_name)

    return None


if __name__ == "__main__":
    """ testing before uploading function as cloud function """
    sample_json = json.loads(
        '{"bucket": "birdcall-id-raw-mp3s", "contentType": "audio/mpeg", "crc32c": "dPENGw==", "etag": "CO67kcCAy+oCEAE=", "generation": "1594669951901166", "id": "birdcall-id-raw-mp3s/amebit/XC127371.mp3/1594669951901166", "kind": "storage#object", "md5Hash": "aCvKDRoFWR768FIcBspUoQ==", "mediaLink": "https://www.googleapis.com/download/storage/v1/b/birdcall-id-raw-mp3s/o/amebit%2FXC127371.mp3?generation=1594669951901166&alt=media", "metageneration": "1", "name": "amebit/XC127371.mp3", "selfLink": "https://www.googleapis.com/storage/v1/b/birdcall-id-raw-mp3s/o/amebit%2FXC127371.mp3", "size": "805212", "storageClass": "STANDARD", "timeCreated": "2020-07-13T19:52:31.901Z", "timeStorageClassUpdated": "2020-07-13T19:52:31.901Z", "updated": "2020-07-13T19:52:31.901Z"}'
    )
    audio_segment(sample_json, None)
