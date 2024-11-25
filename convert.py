import tempfile
from midi2audio import FluidSynth
import midi_utils as mu
from pretty_midi import PrettyMIDI

def convert_midi_to_wav(midi_data):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as temp_midi:
        midi_data.write(temp_midi.name)
        midi_path = temp_midi.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        fs = FluidSynth()
        fs.midi_to_audio(midi_path, temp_wav.name)
        return temp_wav.name

    pass

def change_tempo(trimmed_midi:PrettyMIDI, user_tempo, default_tempo):
    if trimmed_midi:
        trimmed_midi.adjust_times(
            [0, trimmed_midi.get_end_time()],
            [0, trimmed_midi.get_end_time() * (default_tempo / user_tempo)]
        )

    return trimmed_midi