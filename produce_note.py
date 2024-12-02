import constans
import numpy as np
import random
import math

class ProduceNote:
    #初期化
    def __init__(self, chord_list, key, type_button) -> None:
        self.chord_list = chord_list
        self.chord_length = len(chord_list)
        self.key = key
        self.type_button = type_button
        self.up_or_down_array = self.generate_up_or_down_array()
        self.pattern = self.get_type_button()
        self.count_id_AB = 0
        self.count_id_C = 0
        self.A =  [np.zeros((constans.NUM*constans.NUM, constans.NUM*constans.NUM)) for _ in range(self.chord_length*2)]#1音目の確率行列
        self.B = [np.zeros((constans.NUM*constans.NUM, constans.NUM*constans.NUM)) for _ in range(self.chord_length*2)]#2音目の確率行列
        self.C = [np.zeros((constans.NUM*constans.NUM, constans.NUM*constans.NUM)) for _ in range(self.chord_length)]#3, 4音目の確率行列
        self.notes_in_one_chord = 4 #1コードに対する音数
        self.notes_in_one_measure = 8 #1小節の音数
        self.total_num = self.notes_in_one_chord * self.chord_length
        self.scale_change = 0
        self.E = 10**(-20)
        self.Tr = np.zeros((self.total_num, constans.NUM*constans.NUM)) + np.log(self.E)
        self.BP = np.zeros((self.total_num, constans.NUM*constans.NUM))
    

    #1小節に1つ上昇（0）と下降（1）の設定
    def generate_up_or_down_array(self):
        elements = math.ceil(self.chord_length / 2)
        array = np.resize([0, 1], elements)

        return array


    def get_type_button(self):
        if self.type_button == "順次進行":
          return 0
        elif self.type_button == "跳躍進行":
          return 1
        else:
          return ValueError("進行がありません")
          

    #各コードに対応するスケールを決定
    def get_scale(self):
        key_id = constans.NOTE[self.key]
        key_name = constans.NOTE_ID[key_id%12]
        adjusted_chord = []
        input_chord_id = []
        for note in self.chord_list:
           input_chord_id.append(constans.NOTE[note])#区別あり
        for i in range(len(input_chord_id)):
           adjusted_chord.append(constans.NOTE_ID[input_chord_id[i]%12])#区別なし
        
        key_scale = "major" if "m" not in self.key else "minor"
        key_scale_type = "major" if key_scale == "major" else "natural"

        select_scale = [[] for _ in range(self.chord_length)]
        major_Nminor_Hminor = [[] for _ in range(self.chord_length)]
        major_or_minor_of_chord = []

        for i in range (self.chord_length):
            chord_M_or_m = "major" if "m" not in self.chord_list[i] else "minor"
            major_or_minor_of_chord.append(chord_M_or_m)
            if all(note in constans.SCALE_DICT[key_scale][key_scale_type][key_name] for note in constans.CHORD_ID[chord_M_or_m][adjusted_chord[i]]):
               select_scale[i] = key_name
               major_Nminor_Hminor[i] = key_scale_type

            elif key_scale == "minor" and all(note in constans.SCALE_DICT[key_scale]["harmonic"][key_name] for note in constans.CHORD_ID[chord_M_or_m][adjusted_chord[i]]):
               select_scale[i] = key_name
               major_Nminor_Hminor[i] = "harmonic"

            else:
                max_count = 0
                most_common_scale = (None, None)
                chord_type = "major" if chord_M_or_m == "major" else "natural"
                chord_scale = "major" if chord_type == "major" else "minor"
                for key, value in constans.NOTE_ID.items():

                  if all(note in constans.SCALE_DICT[chord_scale][chord_type][value] for note in constans.CHORD_ID[chord_M_or_m][adjusted_chord[i]]):
                    common_notes = set(constans.SCALE_DICT[key_scale][key_scale_type][key_name]) & set(constans.SCALE_DICT[chord_M_or_m][chord_type][value])
                    common_count = len(common_notes)

                    if common_count > max_count:
                      max_count = common_count
                      most_common_scale = (value, chord_type)
                
                select_scale[i] = most_common_scale[0]
                major_Nminor_Hminor[i] = most_common_scale[1]
                
        print(f"select_scale{select_scale}, major_Nminor_Hminor:{major_Nminor_Hminor}")
        return adjusted_chord, select_scale, major_Nminor_Hminor, major_or_minor_of_chord


    #スケールとコードの組み合わせを表示し、返す
    def output_scale_and_chord(self, select_scale, major_Nminor_Hminor):
        select_pitch_name = []
        for i in range(len(select_scale)):
           select_pitch_name.append([str(select_scale[i]) + str(major_Nminor_Hminor[i]), self.chord_list[i]])#[[スケール, コード]]
        print(select_pitch_name)
        return select_pitch_name
    

    #スケールがmajorかminorかを格納したリストを返す
    def get_major_or_minor_scale(self, major_Nminor_Hminor):
      result = []
      for i in range(len(major_Nminor_Hminor)):
        if major_Nminor_Hminor[i] == "major":
          result.append("major")
        else:
          result.append("minor")

      print(f"result:{result}")
      return result
    

    #スケールがharmonicのときに0, それ以外の場合に1を格納したリストを返す
    def get_harmonic_scale(self, list1, variable):
        result= []
        for i in range(len(list1)):
            if list1[i] == variable:
                result.append(0)
            else:
                result.append(1)
        return result
    

    #音符がtargetに含まれていた時、遷移確率を1とする共通のメソッド
    def _commom_matrix_process(self, target):
       matrix = np.zeros((constans.NUM*constans.NUM))
       for i in range(constans.NUM):
          for j in range(constans.NUM):
            if (j+constans.LOWEST)%12 in target:
                matrix[i*constans.NUM+j] = 1.0
       return matrix
       
    
    #次の音符がコード構成音であるときに遷移確率を1とした遷移確率行列を返す
    def get_chord_cons_matrix(self, major_or_minor_of_chord, adjusted_chord):
        target_chord = constans.CHORD_ID[major_or_minor_of_chord][adjusted_chord]
        matrix = self._commom_matrix_process(target_chord)
        return matrix


    #次の音符がコード構成音であるときに遷移確率を1とした遷移確率行列を返す
    def get_in_scale_matrix(self, scale):
        matrix = self._commom_matrix_process(scale)
        return matrix


    #順次進行の遷移確率行列の作成（特定の差分のときに確率を高くする）
    def get_difference_seq_matrix(self, harmonic):
        difference_matrix = np.zeros((2*constans.NUM-1,2*constans.NUM-1))
        plus_exception = 3 #ハーモニック,マイナースケールで登場する跳躍
        minus_exception = plus_exception * -1
        up_range = [1, 2]
        down_range = [-1, -2]

        for i in range(-constans.NUM+1, constans.NUM):
          for j in range(-constans.NUM+1, constans.NUM):
            if i in up_range and j in up_range or i in down_range and j in down_range:
              difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.9
            elif harmonic == 0:#yes
              if i in up_range and j == plus_exception or j in up_range and i == plus_exception or i in down_range and j == minus_exception or j in down_range and i == minus_exception:
                difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.3#変えるかも
            else:
              if i in up_range and j in down_range or i in down_range and j in up_range:
                difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.1
        return difference_matrix


    #跳躍進行の遷移確率行列の作成（特定の差分のときに確率を高くする）
    def get_difference_jump_matrix(self):
      difference_matrix = np.zeros((2*constans.NUM-1, 2*constans.NUM-1))
      up_range_first = [3, 4]
      up_range_second = [-2, -1]
      down_range_first = [-4, -3]
      down_range_second = [1, 2]

      for i in range(-constans.NUM+1, constans.NUM):
        for j in range(-constans.NUM+1, constans.NUM):
          if i in up_range_first:#①
            if j == up_range_second[1]:
              difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.95
            elif j == up_range_second[0]:
              difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.85
                  
          elif i in up_range_second:#②
            if j == up_range_first[0]:
              difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.95
            elif j == up_range_first[1]:
              difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.85
            else:
              if j == down_range_first[0]:
                difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.15
              elif j == down_range_first[1]:
                difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.1

          elif i in down_range_first:#③
            if j == down_range_second[0]:
              difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.95
            elif j == down_range_second[1]:
              difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.85

          elif i in down_range_second:#④
            if j == down_range_first[0]:
              difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.95
            elif j == down_range_first[1]:
              difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.85
            else:
              if j == up_range_first[0]:
                difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.15
              elif j == up_range_first[1]:
                difference_matrix[i+(constans.NUM-1)][j+(constans.NUM-1)] = 0.1

      return difference_matrix


    #ddifference_matrixを行に(i, j), 列に(j, k)をとるような配列に変換する
    def change_matrix(self, difference_matrix):
      all_pitch_matrix = np.zeros((constans.NUM*constans.NUM, constans.NUM*constans.NUM))
      for i in range(constans.NUM):
        for j in range(constans.NUM):
          for k in range(constans.NUM):
            if difference_matrix[j-i+(constans.NUM-1)][k-j+(constans.NUM-1)] != 0:
              all_pitch_matrix[constans.NUM*i+j][constans.NUM*j+k] = difference_matrix[j-i+(constans.NUM-1)][k-j+(constans.NUM-1)]
      return all_pitch_matrix
    

    #行列の正規化
    def normalize_matrix(self, list1, list2, result):
      length = len(list1)
      for i in range(length):
        result[i, :] = list1[i, :] * list2
        sum_of_row = np.sum(result[i, :])
        if sum_of_row > 0:
          result[i, :] /= sum_of_row
        else:
          pass

    #小節の頭の音を決定する遷移確率行列の作成
    def get_top_of_measure_matrix(self, up_or_down):
      max_jump = 6
      difference_matrix = np.zeros((constans.NUM*constans.NUM, constans.NUM*constans.NUM))
      for i in range(constans.NUM):
        for j in range(constans.NUM):
          for k in range(constans.NUM):
            if up_or_down == 0:#上昇
              if 0 < k-j <= max_jump:
                difference_matrix[i*constans.NUM+j][j*constans.NUM+k] = 1.0
            else:#下降
              if 0 < j-k <= max_jump:
                difference_matrix[i*constans.NUM+j][j*constans.NUM+k] = 1.0

      return difference_matrix
    

    #小節の2番目の音を決定する遷移確率行列の作成
    def get_secondpitch_matrix(self, harmonic, up_or_down):
      secondpitch_matrix = np.zeros((constans.NUM*constans.NUM, constans.NUM*constans.NUM))
      for i in range(constans.NUM):
        for j in range(constans.NUM):
          for k in range(constans.NUM):
            if self.pattern == 0:#順次
              if up_or_down == 0:#上昇
                if k-j in [1, 2]:
                  secondpitch_matrix[i*constans.NUM+j][j*constans.NUM+k] = 1.0
                elif harmonic == 0:
                  if k-j == 3: #ハーモニックマイナーを考慮
                    secondpitch_matrix[i*constans.NUM+j][j*constans.NUM+k] = 1.0
              else:
                if k-j in [-1, -2]:
                  secondpitch_matrix[i*constans.NUM+j][j*constans.NUM+k] = 1.0
                elif harmonic == 0:
                  if k-j == -3:#ハーモニックマイナーを考慮
                    secondpitch_matrix[i*constans.NUM+j][j*constans.NUM+k] = 1.0

            else:#跳躍
              if up_or_down == 0:#上昇
                if k-j in [3, 4]:
                  secondpitch_matrix[i*constans.NUM+j][j*constans.NUM+k] = 1.0
              else:
                if k-j in [-3, -4]:
                  secondpitch_matrix[i*constans.NUM+j][j*constans.NUM+k] = 1.0

      return secondpitch_matrix
    

    #1小節目の2音目を決定
    def get_first_measure_second_note(self, z_first, scale, harmonic):
      result = -1
      for i in range(constans.NUM):
        if self.pattern == 0:
          if self.up_or_down_array[0] == 0:
            if i - (z_first-constans.LOWEST) in [1, 2] and (i+constans.LOWEST) % 12 in scale:
              result = i
              break
            elif harmonic == 0:
              if i - (z_first-constans.LOWEST) == 3 and (i+constans.LOWEST) % 12 in scale: #ハーモニックマイナーを考慮
                result = i
                break
          else:
            if i - (z_first-constans.LOWEST) in [-1, -2] and (i+constans.LOWEST) % 12 in scale:
              result = i
              break
            elif harmonic == 0:
              if i - (z_first-constans.LOWEST) == -3 and (i+constans.LOWEST) % 12 in scale: #ハーモニックマイナーを考慮
                result = i
                break
        else:
          if self.up_or_down_array[0] == 0:
            if i - (z_first-constans.LOWEST) in [3, 4] and (i+constans.LOWEST) % 12 in scale:
              result = i
              break
          else:
            if i - (z_first-constans.LOWEST) in [-3, -4] and (i+constans.LOWEST) % 12 in scale:
              result = i
              break

      if result == -1:
        raise ValueError("2音目が決定できませんでした")
      
      return result + constans.LOWEST
    
    
    #1小節目の1, 2音目を決定
    def get_first_measure_notes(self, adjusted_chord, major_or_minor_of_chord, select_scale, harmonic, major_or_minor_of_scale, major_Nminor_Hminor):
      start_tone=[60,61,62,63,64,65,66,67,68,69,70,71]

      chord_list = constans.CHORD_ID[major_or_minor_of_chord][adjusted_chord]
      random_index = random.randint(0, len(chord_list)-1)
      z_first = start_tone[chord_list[random_index]]
      z_second = self.get_first_measure_second_note(z_first, constans.SCALE_DICT[major_or_minor_of_scale][major_Nminor_Hminor][select_scale], harmonic)

      return z_first, z_second

    
    #count_idを増やす
    def increment_count(self):
        self.count_id_AB += 2
        self.count_id_C += 1


    #あるコードとスケールに対する遷移確率行列の生成
    def get_probability_matrix(self, harmonic, select_scale, major_or_minor_of_chord, adjusted_chord, major_or_minor_of_scale, major_Nminor_Hminor):
      #条件：スケール内の音である(2音前も考慮)
      scale_matrix = self.get_in_scale_matrix(constans.SCALE_DICT[major_or_minor_of_scale][major_Nminor_Hminor][select_scale])

      #条件：跳躍
      calc_difference_func = (
          lambda x: self.get_difference_seq_matrix(x) if self.pattern == 0 else self.get_difference_jump_matrix()
      )
      interval_matrix = self.change_matrix(calc_difference_func(harmonic))

      #コード構成音
      cons_matrix = self.get_chord_cons_matrix(major_or_minor_of_chord, adjusted_chord)

      #1番目
      up_or_down = 0
      up_first_note_matrix = self.get_top_of_measure_matrix(up_or_down)
      up_or_down = 1
      down_first_note_matrix = self.get_top_of_measure_matrix(up_or_down)

      #2番目
      up_or_down = 0
      up_second_note_matrix = self.get_secondpitch_matrix(harmonic, up_or_down)
      up_or_down = 1
      down_second_note_matrix = self.get_secondpitch_matrix(harmonic, up_or_down)

      #正規化
      self.normalize_matrix(up_first_note_matrix, cons_matrix, self.A[self.count_id_AB])#1音目の確率行列（上昇の場合）
      self.normalize_matrix(down_first_note_matrix, cons_matrix, self.A[self.count_id_AB+1])#1音目の確率行列（下降の場合）
      self.normalize_matrix(up_second_note_matrix, scale_matrix, self.B[self.count_id_AB])#2音目の確率行列（上昇の場合）
      self.normalize_matrix(down_second_note_matrix, scale_matrix, self.B[self.count_id_AB+1])#2音目の確率行列（下降の場合）
      self.normalize_matrix(interval_matrix, scale_matrix, self.C[self.count_id_C])#3, 4音目の確率行列

      #countの更新
      self.increment_count()


    #重複なしの[[スケール,コード]]分の遷移確率行列を作成
    def get_all_matries(self, harmonic_list, major_or_minor_of_scale, select_pitch_name, adjusted_chord, select_scale, major_Nminor_Hminor, major_or_minor_of_chord):
      no_duplication_select_pitch_name = []
      for i in range(len(select_pitch_name)):
        current_element = select_pitch_name[i]
        if current_element not in select_pitch_name[:i]:
          no_duplication_select_pitch_name.append(current_element)
          self.get_probability_matrix(harmonic_list[i], select_scale[i], major_or_minor_of_chord[i], adjusted_chord[i], major_or_minor_of_scale[i], major_Nminor_Hminor[i])

      return no_duplication_select_pitch_name
    
    
    #scale_changeのカウントを増やし、返す
    def increment_scale_change(self):
        self.scale_change += 1
        return self.scale_change
    

    #ビタビアルゴリズムの実行
    def excute_viterbi(self, n, select_matrix):
      valid_columns = np.any(select_matrix != 0, axis=0)
      for k in np.where(valid_columns)[0]:
          logP = self.Tr[n-1, :] + np.log(select_matrix[:, k] + self.E)
          max_logP = np.max(logP)
          max_index = np.argmax(logP)
          self.Tr[n, k] = max_logP
          self.BP[n, k] = max_index


    #1小節目の確率を計算
    def calc_prob_pre(self, select_pitch_name, no_duplication_select_pitch_name):
      select_matrix_CD_index = 0
      if len(select_pitch_name) == 1:
        end = self.notes_in_one_chord
      else:
        end = self.notes_in_one_measure

      for n in range(2, end):
        if n % self.notes_in_one_chord == 0:#スケール（コード）の変更
          self.scale_change = self.increment_scale_change()
          select_matrix_CD_index = no_duplication_select_pitch_name.index(select_pitch_name[self.scale_change])

        select_matrix = self.C[select_matrix_CD_index]
        self.excute_viterbi(n, select_matrix)


    #2小節目以降の確率を計算
    def calc_prob(self, count, select_pitch_name, no_duplication_select_pitch_name):
      select_matrix_AB_index = 0
      select_matrix_CD_index = 0

      end = min(self.notes_in_one_measure * (count+1), self.total_num)
      for n in range(self.notes_in_one_measure * count, end):
        if n % self.notes_in_one_chord == 0:#スケール（コード）の変更
          self.scale_change = self.increment_scale_change()
          select_matrix_CD_index = no_duplication_select_pitch_name.index(select_pitch_name[self.scale_change])

        if n == self.notes_in_one_measure * count:
          select_scale_index = no_duplication_select_pitch_name.index(select_pitch_name[self.scale_change])
          select_matrix_AB_index = int(2 * select_scale_index + self.up_or_down_array[count])
          select_matrix = self.A[select_matrix_AB_index]
        elif n == self.notes_in_one_measure * count + 1:
          select_matrix = self.B[select_matrix_AB_index]
        else:
          select_matrix = self.C[select_matrix_CD_index]

        self.excute_viterbi(n, select_matrix)


    #結果のindexを返す
    def calc_result_notes(self, z_first, z_second, select_pitch_name, no_duplication_select_pitch_name):
        Z = np.zeros(self.total_num)
        self.Tr[0, 0] = 0
        self.Tr[1, (z_first-constans.LOWEST)*constans.NUM + (z_second-constans.LOWEST)] = 0
        Z[0] = z_first-constans.LOWEST
        Z[1] = z_second-constans.LOWEST
        
        for i in range(len(self.up_or_down_array)):
          if i == 0:
            self.calc_prob_pre(select_pitch_name, no_duplication_select_pitch_name)
          else:
            self.calc_prob(i, select_pitch_name, no_duplication_select_pitch_name)

        final_state_index = np.argmax(self.Tr[-1]) #最終ステップで最も確率が高い音符を最後の音に設定
        Z[self.total_num-1] = final_state_index

        for n in range(self.total_num-1, 2, -1):
          Z[n-1] = (self.BP[n, int(Z[n])])

        for n in range(2, self.total_num):
          Z[n] = Z[n] % constans.NUM

        return Z
    

    #得られたindexをノートナンバー（音符列）に変換し、音符列を返す
    def get_result_notes(self, z_first, z_second, select_pitch_name, no_duplication_select_pitch_name):
       result_notes = self.calc_result_notes(z_first, z_second, select_pitch_name, no_duplication_select_pitch_name)
       decided_notes =np.array([])
       decided_notes = np.concatenate([decided_notes, result_notes + constans.LOWEST])
       print(f"decided_notes{decided_notes}")
       return decided_notes
    

    #実行をまとめたメソッド
    def run_produce_note(self):
       adjusted_chord, select_scale, major_Nminor_Hminor, major_or_minor_of_chord = self.get_scale()
       select_pitch_name = self.output_scale_and_chord(select_scale, major_Nminor_Hminor)
       major_or_minor_of_scale = self.get_major_or_minor_scale(major_Nminor_Hminor)
       harmonic_list = self.get_harmonic_scale(major_Nminor_Hminor, "harmonic")
       no_duplication_select_pitch_name = self.get_all_matries(harmonic_list, major_or_minor_of_scale, select_pitch_name, adjusted_chord, select_scale, major_Nminor_Hminor, major_or_minor_of_chord)
       z_first, z_second = self.get_first_measure_notes(adjusted_chord[0], major_or_minor_of_chord[0], select_scale[0], harmonic_list[0], major_or_minor_of_scale[0], major_Nminor_Hminor[0])
       decided_notes = self.get_result_notes(z_first, z_second, select_pitch_name, no_duplication_select_pitch_name)

       return decided_notes