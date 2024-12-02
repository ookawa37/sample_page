import tempfile
from midi2audio import FluidSynth
from pretty_midi import PrettyMIDI
import pretty_midi

def convert_midi_to_wav(midi_data):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as temp_midi:
        midi_data.write(temp_midi.name)
        midi_path = temp_midi.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        sound_font_path = "default_sound_font.sf2"
        fs = FluidSynth(sound_font_path)
        fs.midi_to_audio(midi_path, temp_wav.name)
        return temp_wav.name

    pass

def change_tempo(trimmed_midi:PrettyMIDI, user_tempo, default_tempo):
    change_tempo_midi = pretty_midi.PrettyMIDI()
    time_scale = default_tempo / user_tempo

    for instrument in trimmed_midi.instruments:
        new_instrument = pretty_midi.Instrument(program=instrument.program, is_drum=instrument.is_drum)
        for note in instrument.notes:

            adjusted_note = pretty_midi.Note(
                velocity=note.velocity,
                pitch=note.pitch,
                start=note.start * time_scale,
                end=note.end * time_scale
            )
            new_instrument.notes.append(adjusted_note)
        change_tempo_midi.instruments.append(new_instrument)

    return change_tempo_midi