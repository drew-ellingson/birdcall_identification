from pydub import AudioSegment
import math
import os
import functools
import time

source_audio = "data/train_audio/"
target_audio = "data/transformed_audio/"


def timer(func):
    """timing decorator for training and testing methods"""

    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.time()
        value = func(*args, **kwargs)
        end_time = time.time()
        print(
            "Finished {} in {} seconds".format(
                func.__name__, round((end_time - start_time), 3)
            )
        )
        return value

    return wrapper_timer


def audio_chopper(input_folder, input_file, seg_length):
    song = AudioSegment.from_mp3(input_folder + "/" + input_file)
    song = song.set_channels(1)  # enforce mono rather than stereo
    song = song.set_frame_rate(44100)  # uniformize, 44.1k is cd standard
    seg_count = math.floor(len(song) / 1000 / seg_length)
    output_folder = input_folder[input_folder.rfind("/") + 1 :]
    export_path = os.path.join(os.getcwd(), target_audio + output_folder)

    try:
        os.mkdir(export_path)
    except FileExistsError:
        pass

    for i in range(seg_count):
        start_ts, stop_ts = seg_length * 1000 * i, seg_length * 1000 * (i + 1)
        segment = song[start_ts:stop_ts]
        segment.export(
            export_path
            + "/"
            + input_file[:-4]
            + "_"
            + str(i * seg_length)
            + "_"
            + str((i + 1) * seg_length)
            + ".wav",
            format="wav",
        )
    return None


@timer
def all_audio_chopper(seg_length):
    for root, _, filenames in os.walk(source_audio):
        if not any(map(lambda x: x.endswith(".mp3"), filenames)):
            continue
        bird = root[root.rfind("/") + 1 :]
        if os.path.exists(target_audio + bird):
            print(f"{bird} was skipped")
            continue
        print(f"Starting on {bird}")
        for filename in filenames:
            if not filename.endswith("mp3"):
                continue
            else:
                audio_chopper(root, filename, seg_length)
        print(f"finished directory: {root} containing {len(filenames)} files")
    return None


# grtgra issue?
# pingro issue?
# eucdov issue?
# tunswa issue?
# btbbar issue?
if __name__ == "__main__":
    all_audio_chopper(10)
