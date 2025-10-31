import time
from vosk import Model, KaldiRecognizer
import sounddevice
import soundfile
import queue
from pathlib import Path
import webbrowser

MODEL_PATH = Path(__file__).parent / "vosk-model"
SAMPLE_RATE = 16000

model = Model(str(MODEL_PATH))

recognizer = KaldiRecognizer(model, SAMPLE_RATE)


def build_audio_path(relative_path):
    return str(Path(__file__).parent / relative_path)


commands_audio = {
    "просыпайся": build_audio_path("sounds/welcome-back.wav"),
    "работаем": build_audio_path("sounds/start-diagnostics.wav"),
}

commands_action = {
    "открой браузер": lambda: webbrowser.open("https://www.google.com"),
}

queue = queue.Queue()

last_command_time = 0
cooldown = 2.0


def audio_callback(indata, frames, time, status):
    queue.put(bytes(indata))


def play_sound(filename):
    data, samplerate = soundfile.read(filename)
    sounddevice.play(data, samplerate)

    print("play sound")


with sounddevice.RawInputStream(
    samplerate=SAMPLE_RATE,
    blocksize=8000,
    dtype="int16",
    channels=1,
    callback=audio_callback,
):
    print("Джарвис слушает...")

    while True:
        data = queue.get()
        if recognizer.AcceptWaveform(data):
            result = recognizer.Result()
            text = result.lower()

            print("RESULT", text)
        else:
            result = recognizer.PartialResult()
            text = result.lower()

        if text:
            print(f"Распознано: {text}")
            for command in commands_audio.keys():
                if command in text:
                    now = time.time()

                    if now - last_command_time > cooldown:
                        print(f"Executing command: {command}")
                        play_sound(commands_audio[command])
                        last_command_time = now

            for command in commands_action.keys():
                if command in text:
                    now = time.time()

                    if now - last_command_time > cooldown:
                        print(f"Executing action: {command}")
                        commands_action[command]()
                        last_command_time = now
