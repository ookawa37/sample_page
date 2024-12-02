
import pretty_midi

def get_tempo(start_time, end_time, midi_data: pretty_midi.PrettyMIDI):
    # テンポを取得
    tempo_times, tempo_bpms = midi_data.get_tempo_changes()
    tempo_times = tempo_times[1:]
    tempo_bpms = tempo_bpms[1:]

    if tempo_times.size == 0:
        raise ValueError("テンポが正常に取得できませんでした")
    
    prev_tempo_time = 0.0
    for tempo_time in tempo_times:
        if tempo_time > start_time:
            break
        prev_tempo_time = tempo_time
    
    total_bpm = 0
    count = 0
    if len(tempo_bpms) > 0:
        for time, bpm in zip(tempo_times, tempo_bpms):
            if time > end_time:
                break
            elif prev_tempo_time > time:
                continue
            else:
                total_bpm += bpm
                count += 1
        
        tempo_bpm = total_bpm / count
    else:
        tempo_bpm = 120

    return tempo_bpm, tempo_times[0]


def cut_midi(midi_file, start_time, end_time):
    midi_file.seek(0)
    midi_data = pretty_midi.PrettyMIDI(midi_file)
    trimmed_midi = pretty_midi.PrettyMIDI()
    for instrument in midi_data.instruments:
        new_instrument = pretty_midi.Instrument(program=instrument.program)
        for note in instrument.notes:
            if note.end > start_time and note.start < end_time:
                trimmed_note = pretty_midi.Note(
                    velocity=note.velocity,
                    pitch=note.pitch,
                    start=max(note.start, start_time) - start_time,
                    end=min(note.end, end_time) - start_time
                )
                new_instrument.notes.append(trimmed_note)
        trimmed_midi.instruments.append(new_instrument)

    return trimmed_midi


def get_first_key_signature(midi_data):
    key_signature = None
    if midi_data.key_signature_changes:
        key_signature = midi_data.key_signature_changes[0]
    print(f"key_signature{key_signature}")
    return key_signature


def trim_silence_from_start(midi_data: pretty_midi.PrettyMIDI, start_time, tempo_times_one):
    if start_time >= tempo_times_one:
        return midi_data
    
    else:
        midi_data.adjust_times(
        [tempo_times_one, midi_data.get_end_time()],
        [0, midi_data.get_end_time() - tempo_times_one]
        )
        return midi_data


def get_closeest_downbeats(midi_data, start_time, end_time):
    downbeats = midi_data.get_downbeats()
    target_times = [start_time, end_time]
    closest_beats = [min(downbeats, key=lambda x: abs(x - target)) for target in target_times]
    closest_beats = [float(value) for value in closest_beats]

    return closest_beats


def generate_count_in(default_tempo, start_time=0, count=4):
    count_in_midi = pretty_midi.PrettyMIDI()
    click_instrument = pretty_midi.Instrument(program=0, is_drum=True)

    beat_duration = 60.0 / default_tempo

    for i in range(count):
        note = pretty_midi.Note(
            velocity=127,            # 音量
            pitch=37,                # スネアドラム音
            start=start_time + i * beat_duration, # 開始時間
            end=start_time + (i + 0.5) * beat_duration  # 半拍分の長さ
        )
        click_instrument.notes.append(note)

    count_in_midi.instruments.append(click_instrument)
    return count_in_midi


def combine_midi(midi_data, count_in_midi, default_tempo, count_in_interval=4):
    count_in_duration = 4 * (60 / default_tempo)
    midi_data.adjust_times(
        [0, midi_data.get_end_time()], 
        [count_in_duration, midi_data.get_end_time() + count_in_duration]
    )

    total_duration = midi_data.get_end_time()
    combined_midi = pretty_midi.PrettyMIDI()

    combined_midi.instruments.extend(count_in_midi.instruments)
    combined_midi.instruments.extend(midi_data.instruments)

    # カウントインを曲の終わりまで繰り返し追加
    current_time = count_in_interval * (60.0 / default_tempo)
    while current_time < total_duration:
        # 現在の位置にカウントインを追加
        count_in_midi_with_offset = generate_count_in(default_tempo, start_time=current_time)
        combined_midi.instruments.extend(count_in_midi_with_offset.instruments)

        # 次のカウントインの開始位置を計算
        current_time += count_in_interval * (60.0 / default_tempo)  # 次のカウントインを入れる時刻
        
    return combined_midi


def run_midi_trimmed(midi_file, start_time, end_time, default_tempo, tempo_times_one):
    trimmed_midi = cut_midi(midi_file, start_time, end_time)
    new_midi_data = trim_silence_from_start(trimmed_midi, start_time, tempo_times_one)
    count_in_midi = combine_midi(new_midi_data, generate_count_in(default_tempo), default_tempo)

    return count_in_midi

