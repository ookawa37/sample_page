import numpy as np
from music21 import *
from midi_utils import get_tempo
import matplotlib.pyplot as plt
import constans

class EstimateChord():
    def __init__(self, start_time, end_time, midi_data):
        self.start_time = start_time
        self.end_time = end_time
        self.midi_data = midi_data
        pass


    def calc_double_length(self, end_time, midi_data):
        tempo_bpm = get_tempo(end_time, midi_data)
        beat_length = 60 / tempo_bpm
        double_length = beat_length * 2

        return double_length


    def get_chromagram(self, midi_data, double_length, start_time, end_time):
        chroma = midi_data.get_chroma()
        fs = 100
        start_frame = int(start_time * fs)
        end_frame = int(end_time * fs)

        # 指定された時間範囲のクロマグラムを抽出
        chroma = chroma[:, start_frame:end_frame]

        frames_per_second = int(double_length * fs)
        aggregated_chroma = []
        
        for i in range(0, chroma.shape[1], frames_per_second):
            segment = chroma[:, i:i + frames_per_second]
            if segment.shape[1] > 0:  # フレームが存在する場合
                segment_mean = segment.mean(axis=1)  # 平均化して1つのデータポイントに
                aggregated_chroma.append(segment_mean)
        
        # リストを配列に変換
        aggregated_chroma = np.array(aggregated_chroma).T  # 転置して元の形に合わせる
        
        return aggregated_chroma
    

    def display_chroma(self, aggregated_chroma, start_time, end_time):
        plt.figure(figsize=(10, 4))
        plt.imshow(aggregated_chroma, aspect='auto', origin='lower', cmap='coolwarm', extent=[start_time, end_time, 0, aggregated_chroma.shape[0]])
        plt.xlabel("Times(frames)")
        plt.ylabel("Pitch Class")
        plt.colorbar(label="Intensity")
        plt.title("Chromagram from MIDI")
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        plt.yticks(range(len(notes)), notes)  # y軸のラベルを音名に変更
        plt.show()


    def get_key_signature(self, midi_data, start_time):
        key_signature = None

        for key_sig in midi_data.key_signature_changes:
            if key_sig.time <= start_time:
                key_signature = key_sig
            else:
                break

        print(f"Key signature at or before start_time ({start_time}): {key_signature}")
        return key_signature
    

    def setKey(self, key_signature):
        major_key_signature = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'F', 'B-', 'E-', 'A-', 'D-', 'G-', 'C-']
        minor_key_signature = ['A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'D', 'G', 'C', 'F', 'B-', 'E-', 'A-']

        if key_signature:
            key_signature_str = str(key_signature)
            key_signature_info = f"{key_signature_str}"
        else:
            raise ValueError(f"キーシグネチャが取得できませんでした")
        
        key_name = key_signature_info.split(' ')[0]
        key_name = key_name.replace("b", "-")
        key_type = key_signature_info.split(' ')[1]
        if key_type == 'Major' or key_type == 'major':
            if key_name in major_key_signature:
                return key_name
            else:
                raise ValueError(f"'{key_name}' はキーリスト内に見つかりませんでした")
            
        elif key_type == 'Minor' or key_type == 'minor':
            if key_name in minor_key_signature:
                return key_name+'m'
            else:
                raise ValueError(f"'{key_name}' はキーリスト内に見つかりませんでした")
        else:
            raise ValueError(f"キータイプ '{key_type}' は無効です")


    def generate_chroma_vector(self, indices):
        vector = np.zeros(12)  # 12次元のベクトルを初期化
        for index in indices:
            vector[index] = 1  # コード構成音の場所に1をセット
        return vector
    

    def include_top3(self, possible_chords_full, possible_chords_partial, major_or_minor, sorted_indices):
        if major_or_minor == "minor":
            m = "m"
        else:
            m = ""
        for root_note, intervals in constans.CHORD_ID[major_or_minor].items():
            # トップ3の音がコード構成音に含まれているかをチェック
            matched_notes = [note for note in sorted_indices[:3] if note in intervals]
            if len(matched_notes) == 3:
                possible_chords_full.append(root_note + m)
            elif len(matched_notes) == 2:
                possible_chords_partial.append(root_note + m)


    # クロマグラムからコードを推定する関数
    def estimate_chords_from_chromagram(self, chroma_matrix, key):
        chord_names = []
        print(f"key:{key}")

        for i in range(chroma_matrix.shape[1]):
            chroma_column = chroma_matrix[:, i]
            # 音量の高い順に音階をソート（演奏されている可能性が高い音）
            sorted_indices = np.argsort(chroma_column)[::-1]
            
            top3_names = []
            for idx in sorted_indices[:3]:
                top3_name = note.Note(idx).name
                top3_names.append(top3_name)

            # コードのルート音と構成音の推定
            possible_chords_full = []
            possible_chords_partial = []
            self.include_top3(possible_chords_full, possible_chords_partial, "major", sorted_indices)
            self.include_top3(possible_chords_full, possible_chords_partial, "minor", sorted_indices)

            # 3つ一致するコードがあればそれを優先的に出力
            if possible_chords_full:
                chord_names.append(", ".join(possible_chords_full))
            # 3つ一致するコードがない場合
            elif possible_chords_partial:
                #キーと一致するものを優先
                if key in possible_chords_partial:
                    chord_names.append(key)
                else:
                    #クロマベクトルに基づき1つに絞る
                    max_score = -1
                    best_chord = None

                    for chord in possible_chords_partial:
                        chord_without_m = chord.rstrip("m")
                        if chord_without_m in constans.CHORD_ID["major"]:
                            indices = constans.CHORD_ID["major"][chord_without_m]
                        elif chord_without_m in constans.CHORD_ID["minor"]:
                            indices = constans.CHORD_ID["minor"][chord_without_m]
                        else:
                            raise ValueError(f"適するコードがありません{chord}, {chord_without_m}")

                        chord_vector = self.generate_chroma_vector(indices)#コードベクトル作成
                        score = np.dot(chroma_column, chord_vector)#内積計算

                        # 最大値を更新
                        if score > max_score:
                            max_score = score
                            best_chord = chord
                    chord_names.append(best_chord)

            # それでもなければkeyを入れる
            else:
                chord_names.append(key)

        return chord_names


    # 推定されたコードを表示し、返す
    def display_estimated_chords(self, chroma_matrix, key):
        chords = self.estimate_chords_from_chromagram(chroma_matrix, key)
        for i, chord in enumerate(chords):
            print(f"Time step {i+1} beats: {chord}")
        return chords


    def run(self, start_time, end_time, midi_data):
        key_signature = self.get_key_signature(midi_data, start_time)
        key = self.setKey(key_signature)
        chromagram = self.get_chromagram(midi_data, self.calc_double_length(end_time, midi_data), start_time, end_time)
        chord_list = self.display_estimated_chords(chromagram, key)
        return key, chord_list