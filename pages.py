import streamlit as st
import pretty_midi
import io
import convert as cv
import midi_utils as mu
import delete as dl
import numpy as np
import tempfile
import subprocess
from chord_estimate import EstimateChord
from produce_note import ProduceNote


class TempoChangerPage():
    def __init__(self, title) -> None:
        self.title = title
        st.title(title)

        if 'initialized' not in st.session_state:
            st.session_state.midi_file = None
            st.session_state.midi_data = None
            st.session_state.user_tempo = 120
            st.session_state.default_tempo = None
            st.session_state.generated_audio = None
            st.session_state.audio_playback = None
            st.session_state.start_time = 0.0
            st.session_state.end_time = 8.0
            st.session_state.full_audio = None
            st.session_state.temp_dir = tempfile.TemporaryDirectory()
            st.session_state["temp_files"] = []
            st.session_state.note_numbers = []
            st.session_state.generated_score = None
            st.session_state.initialized = True
            st.session_state.step = False
            st.session_state.audio = False


    def upload_and_convert_file(self):
        uploaded_file = st.file_uploader("MIDIファイルをアップロードしてください", type=["mid"])
        if uploaded_file:
            st.session_state.midi_file = io.BytesIO(uploaded_file.read())
            st.session_state.midi_file.seek(0)
            
            # アップロードしたMIDIファイルを全体音源としてWAVに変換
            st.session_state.midi_data = pretty_midi.PrettyMIDI(st.session_state.midi_file)
            st.session_state.full_audio = cv.convert_midi_to_wav(st.session_state.midi_data)
            st.session_state.step = True


    def play_full_audio(self):
        if st.session_state.full_audio:
            st.write("アップロードしたファイルの音源:")
            audio_file = open(st.session_state.full_audio, 'rb')
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")


    def select_range_and_tempo(self):
        user_tempo = st.number_input("テンポを指定してください", min_value=20, max_value=300, value=st.session_state.user_tempo)
        st.session_state.user_tempo = user_tempo

        if st.session_state.midi_file:
            st.session_state.midi_file.seek(0)
            midi_data = pretty_midi.PrettyMIDI(st.session_state.midi_file)
            midi_duration = midi_data.get_end_time()

            # スライダーで範囲指定
            start_time, end_time = st.slider("練習したい範囲を選択してください", 0.0, midi_duration, (0.0, min(8.0, midi_duration)))
            st.session_state.start_time = start_time
            st.session_state.end_time = end_time
            st.write(f"選択された範囲: {start_time:.2f}秒 から {end_time:.2f}秒")


    def adjust_select_range(self):
        self.select_range_and_tempo()
        closest_beats = mu.get_closeest_downbeats(st.session_state.midi_data, st.session_state.start_time, st.session_state.end_time)
        st.session_state.start_time, st.session_state.end_time = closest_beats[:2]
        print(f"start_time{st.session_state.start_time}, end_time{st.session_state.end_time}")

    
    def convert_and_store_audio(self, adjusted_midi):
        if adjusted_midi:
            wav_path = cv.convert_midi_to_wav(adjusted_midi)
            st.session_state.generated_audio = wav_path


    def display_generated_audio(self):
        if st.session_state.generated_audio:
            st.write("指定された範囲の音源:")
            audio_file = open(st.session_state.generated_audio, 'rb')
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")


    def run_pages(self):
        dl.handle_cleanup_request()
        
        self.upload_and_convert_file()
        if st.session_state.step:
            self.play_full_audio()
            self.adjust_select_range()

        if st.session_state.midi_file is not None:
            if st.button("指定された範囲の音源を生成"):
                st.session_state.default_tempo = mu.get_tempo(st.session_state.end_time, st.session_state.midi_data)
                count_in_midi = mu.run_midi_trimmed(st.session_state.midi_file, st.session_state.start_time, st.session_state.end_time, st.session_state.default_tempo)
                adjusted_midi = cv.change_tempo(count_in_midi, st.session_state.user_tempo, st.session_state.default_tempo)
                self.convert_and_store_audio(adjusted_midi)
                self.display_generated_audio()
                st.session_state.audio = True

            elif st.session_state.generated_audio:
                self.display_generated_audio()

        if st.session_state.generated_audio:
            mb = MusicscoreButton()
            es = EstimateChord(st.session_state.start_time, st.session_state.end_time, st.session_state.midi_data)
            key, chord_list = es.run(st.session_state.start_time, st.session_state.end_time, st.session_state.midi_data)

            if mb.generate_musicscore_button:
                produce_note = ProduceNote(chord_list, key, mb.progression_type)
                st.session_state.note_numbers = produce_note.run_produce_note()

                if len(st.session_state.note_numbers) > 0:
                    musicscore = MusicscorePage(key, st.session_state.note_numbers)
                    musicscore.run()

            elif st.session_state.generated_score:
                musicscore = MusicscorePage(key, st.session_state.note_numbers)
                musicscore.display_score()


class MusicscoreButton():
    def __init__(self) -> None:
        self.progression_type = st.radio("進行タイプを選んでください：", ("順次進行", "跳躍進行"))
        self.generate_musicscore_button = st.button("楽譜の生成")


class MusicscorePage():
    def __init__(self, key, notenumber_list) -> None:
        self.key = key
        self.notenumber_list = notenumber_list


    def change_notenumbers_to_lilypond(self, note_numbers, key_type):
        sharp_lilypond_notes = ["c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "b"]
        flat_lilypond_notes = ["c", "des", "d", "es", "e", "f", "ges", "g", "as", "a", "bes", "b"]
        
        if key_type == "sharp":
            lilypond_notes = sharp_lilypond_notes
        else:
            lilypond_notes = flat_lilypond_notes

        if isinstance(note_numbers, (list, np.ndarray)):
            return [
                lilypond_notes[int(note) % 12] + (
                    "'" * ((int(note) // 12) - 4) if int(note) // 12 >= 5 else "," * (4 - (int(note) // 12))
                ) + "8"
                for note in note_numbers
            ]
        else:
            note_number = int(note_numbers)
            octave = (note_number // 12) - 4
            note_name = lilypond_notes[note_number % 12]
            lily_octave = "'" * octave if octave >= 0 else "," * -octave
            return note_name + lily_octave + "8"


    def convert_to_lilypond_key(self, key):
        lilypond_key = key.replace("#", "is").replace("-", "es")
        
        if lilypond_key.endswith("m"):
            return f"\\key {lilypond_key[:-1].lower()} \\minor", lilypond_key[:-1].lower()
        else:
            return f"\\key {lilypond_key.lower()} \\major", lilypond_key.lower()
        

    def get_key_type(self, key_signature, key_name):
        sharp_major_keys = ['c', 'g', 'd', 'a', 'e', 'b', 'fis', 'cis']
        flat_major_keys = ['f', 'bes', 'ees', 'aes', 'des', 'ges', 'ces']
        sharp_minor_keys = ['a', 'e', 'b', 'fis', 'cis', 'gis', 'dis', 'ais']
        flat_minor_keys = ['d', 'g', 'c', 'f', 'bes', 'ees', 'aes']
        
        if "major" in key_signature:
            if key_name in sharp_major_keys:
                return "sharp"
            elif key_name in flat_major_keys:
                return "flat"
            else:
                raise ValueError("キーが無効です")
            
        else:
            if key_name in sharp_minor_keys:
                return "sharp"
            elif key_name in flat_minor_keys:
                return "flat"
            else:
                raise ValueError("キーが無効です")

        
    def generate_lilypond_code(self, key_signature, notes_sequence, time_signature="4/4", clef="treble"):
        return f'''
        \\version "2.24.4"
        \\paper {{
            indent = 0\mm
            paper-width = 190\\mm
            paper-height = 100\\mm
            top-margin = 5\\mm
            bottom-margin = 5\\mm
            left-margin = 5\\mm
            right-margin = 5\\mm
            ragged-right = ##t
        }}
        
        {{
            \\clef {clef}          % ト音記号
            \\time {time_signature} % 拍子
            {key_signature}         % キー設定
            {notes_sequence}    % 音符列
        }}
        '''


    def generate_score(self, lilypond_code):
        temp_dir = st.session_state.temp_dir.name
        ly_file_path = f"{temp_dir}\example.ly"
        svg_file_path = f"{temp_dir}\example.svg"
        print(f"svg_file_path{svg_file_path}")

        with open(ly_file_path, "w", encoding="utf-8") as file:
            file.write(lilypond_code)

        result = subprocess.run(
            ["lilypond", "-dbackend=svg", "-o", temp_dir, ly_file_path],
            capture_output=True,
            encoding="utf-8"
        )

        if result.returncode == 0:
            with open(svg_file_path, "rb") as f:
                st.session_state.generated_score = f.read()
                
        else:
            st.session_state.generated_score = None
            st.session_state.error_message = result.stderr


    def redisplay_score(self, lilypond_code):
        self.generate_score(lilypond_code)
        if "generated_score" in st.session_state and st.session_state.generated_score:
            self.display_score()
        elif "error_message" in st.session_state:
            st.error(f"Error generating music sheet: {st.session_state.error_message}")


    def display_score(self):
        st.components.v1.html(st.session_state.generated_score, height=500)

    
    def run(self):
        key_signature, key_name = self.convert_to_lilypond_key(self.key)
        lilypond_notes = self.change_notenumbers_to_lilypond(self.notenumber_list, self.get_key_type(key_signature, key_name))
        notes_sequence = " ".join(lilypond_notes)
        lilypond_code = self.generate_lilypond_code(key_signature, notes_sequence)
        self.redisplay_score(lilypond_code)