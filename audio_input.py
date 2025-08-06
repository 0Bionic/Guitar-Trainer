# pitch_detector.py

import sounddevice as sd
import numpy as np
import queue
import threading
import math

SAMPLE_RATE = 44100
BLOCK_SIZE = 8192
CHANNELS = 2

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F',
              'F#', 'G', 'G#', 'A', 'A#', 'B']

def freq_to_note(frequency):
    if frequency <= 0:
        return None
    midi = 69 + 12 * math.log2(frequency / 440.0)
    midi = round(midi)
    note_name = NOTE_NAMES[midi % 12]
    octave = midi // 12 - 1
    return f"{note_name}{octave}"

def note_to_freq(note):
    """Returns the frequency of the given note name like A4, E2, etc."""
    name = note[:-1]
    octave = int(note[-1])
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F',
                  'F#', 'G', 'G#', 'A', 'A#', 'B']
    if name not in NOTE_NAMES:
        return None
    midi = NOTE_NAMES.index(name) + (octave + 1) * 12
    freq = 440 * 2**((midi - 69) / 12)
    return freq


def detect_pitch_autocorrelation(block, sample_rate):
    block = block - np.mean(block)
    corr = np.correlate(block, block, mode='full')
    corr = corr[len(corr)//2:]
    d = np.diff(corr)
    try:
        start = np.nonzero(d > 0)[0][0]
    except IndexError:
        return None
    peak = np.argmax(corr[start:]) + start
    if peak == 0:
        return None
    pitch = sample_rate / peak
    return pitch

class PitchDetector:
    def __init__(self, input_device=None, callback=None, gain=10.0):
        self.q = queue.Queue()
        self.device = input_device
        self.gain = gain
        self.running = False
        self.callback = callback  # Called with (note, frequency)

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.q.put(indata[:, 0])

    def _process_audio(self):
        last_note = None
        while self.running:
            try:
                block = self.q.get(timeout=0.1)
                block *= self.gain
                if np.max(np.abs(block)) > 0:
                    block = block / np.max(np.abs(block))

                pitch = detect_pitch_autocorrelation(block, SAMPLE_RATE)
                if pitch and 40 < pitch < 1200:
                    note = freq_to_note(pitch)
                    if note != last_note:
                        if self.callback:
                            self.callback(note, pitch)
                        last_note = note
            except queue.Empty:
                continue

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._process_audio, daemon=True)
        self.thread.start()

        self.stream = sd.InputStream(
            device=self.device,
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            callback=self._audio_callback
        )
        self.stream.start()

    def stop(self):
        self.running = False
        self.stream.stop()
        self.stream.close()
