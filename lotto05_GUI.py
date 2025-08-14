import os
import pandas as pd
import io
import random
import time
import tkinter as tk
from tkinter import ttk, messagebox, font as tkFont

# --- Data Parsing Function ---
def parse_and_prepare_data(data_text):
    """
    Parses the raw text data into a pandas DataFrame and
    prepares it for probability calculations.
    """
    lines = data_text.strip().split('\n')
    if len(lines) < 2:
        raise ValueError("입력된 데이터가 충분하지 않습니다.")

    header_line = lines[0]
    data_lines = '\n'.join(lines[1:])
    
    raw_headers = header_line.split()
    # '숫자' 헤더를 건너뛰고, 실제 칸별 헤더부터 처리합니다.
    # raw_headers[0]은 '숫자'이므로, raw_headers[1:]부터 시작합니다.
    processed_headers = raw_headers[1:] # '숫자'를 제외한 나머지 헤더

    parsed_headers = []

    # processed_headers를 2개씩 묶어서 처리합니다.
    for i in range(0, len(processed_headers), 2):
        if i + 1 < len(processed_headers) and processed_headers[i+1].strip().lower() == '확률':
            base_name = processed_headers[i].strip()
            parsed_headers.append(f'{base_name}빈도')
            parsed_headers.append(f'{base_name}확률')
        else:
            # 오류 메시지를 더 명확하게 수정합니다.
            raise ValueError(f"헤더 형식이 '칸 확률' 패턴과 다릅니다. 문제의 부분: '{processed_headers[i]} {processed_headers[i+1] if i+1 < len(processed_headers) else ''}'")
            
    df = pd.read_csv(io.StringIO(data_lines), sep=r'\s+', header=None, engine='python', index_col=0)
    df.index.name = '번호' 

    if len(df.columns) != len(parsed_headers):
        raise ValueError(f"데이터의 열 개수({len(df.columns)})가 예상({len(parsed_headers)})과 다릅니다. 원본 데이터를 확인해주세요.")
    df.columns = parsed_headers
    
    probability_df = df[[col for col in df.columns if '확률' in col]].copy()

    for col in probability_df.columns:
        # Check for and replace 'None' string, then empty strings, then '%'
        probability_df.loc[:, col] = probability_df[col].astype(str).str.strip() \
                                        .replace('None', '0.00%') \
                                        .replace('', '0.00%') \
                                        .str.replace('%', '').astype(float)
        
    return probability_df

# --- Number Selection Function ---
def get_random_number_from_column(prob_df, column_name, selection_type, exclude_numbers=None):
    """
    Selects a random number from a given column based on selection type
    and excludes already chosen numbers.
    
    Args:
        prob_df (pd.DataFrame): The DataFrame containing probability data.
        column_name (str): The name of the column to select numbers from (e.g., '1칸확률').
        selection_type (str): The type of selection ('top', 'bottom', 'random').
        exclude_numbers (set, optional): A set of numbers to exclude from selection. Defaults to None.
    
    Returns:
        int or None: A randomly selected number, or None if no eligible numbers are found.
    """
    if exclude_numbers is None:
        exclude_numbers = set()

    if column_name not in prob_df.columns:
        return None

    eligible_numbers = []

    if selection_type == 'top':
        # Select numbers with probability > 2%
        top_prob_df = prob_df[prob_df[column_name] > 2]
        eligible_numbers = [num for num in top_prob_df.index.tolist() if num not in exclude_numbers]
    elif selection_type == 'bottom':
        # Select numbers with probability between 0.2% and 2.5%
        bottom_prob_df = prob_df[(prob_df[column_name] >= 0.2) & (prob_df[column_name] <= 2.5)]

        eligible_numbers = [num for num in bottom_prob_df.index.tolist() if num not in exclude_numbers]
    elif selection_type == 'random':
        all_non_zero_numbers = prob_df[prob_df[column_name] > 0].index.tolist()
        eligible_numbers = [num for num in all_non_zero_numbers if num not in exclude_numbers]
    else:
        return None

    if not eligible_numbers:
        return None
    
    return random.choice(eligible_numbers)

# --- GUI Application Class ---
class LottoGeneratorApp:
    def __init__(self, master):
        self.master = master
        master.title("✨ 로또 번호 각 칸별 확률 기반 랜덤 조합 생성기 ✨")
        master.geometry("850x910") 
        master.resizable(False, False)

        self.prob_df = self._load_data()
        if self.prob_df is None:
            master.destroy() 
            return 

        self.selection_type_codes = {'top': 't', 'bottom': 'b', 'random': 'r'}
        self.selection_options = ['높은 확률 (t)', '낮은 확률 (b)', '랜덤 (r)']
        self.combo_vars = []
        self.combination_results = [] 

        self._create_widgets()

    def _load_data(self):
        """
        Loads the predefined lottery data from an external file.
        """
        try:
            script_dir = os.path.dirname(__file__)
            file_path = os.path.join(script_dir, 'lotto_data.txt')

            with open(file_path, 'r', encoding='utf-8') as f:
                data_as_text = f.read()
            return parse_and_prepare_data(data_as_text)
        except FileNotFoundError:
            messagebox.showerror("파일 없음 오류", f"'{file_path}' 파일을 찾을 수 없습니다. 프로그램과 같은 디렉토리에 있는지 확인해주세요.")
            return None
        except Exception as e:
            messagebox.showerror("파일 읽기 오류", f"'lotto_data.txt' 파일을 읽는 중 오류가 발생했습니다: {e}")
            return None

    def _create_widgets(self):
        """
        Creates and arranges all GUI widgets.
        """
        input_frame = ttk.LabelFrame(self.master, text="로또 번호 생성 설정", padding="10 10 10 10")
        input_frame.pack(pady=10, padx=10, fill="x")

        # Configure columns for grid
        for i in range(6): 
            input_frame.grid_columnconfigure(i, weight=1)

        # Create labels and comboboxes for each of the 6 columns
        for i in range(6): 
            ttk.Label(input_frame, text=f"{i+1}칸:").grid(row=0, column=i, padx=5, pady=2, sticky="s") 
            
            combo_var = tk.StringVar()
            combo = ttk.Combobox(input_frame, textvariable=combo_var, values=self.selection_options, state="readonly", width=12) 
            combo.set(self.selection_options[2]) # Default to '랜덤 (r)'
            combo.grid(row=1, column=i, padx=5, pady=2, sticky="n") 
            self.combo_vars.append(combo_var)
        
        # Number of combinations input (on a new row, spans across columns)
        ttk.Label(input_frame, text="생성할 조합 개수 (1~20):").grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky="e") 
        self.num_combinations_entry = ttk.Entry(input_frame, width=7) 
        self.num_combinations_entry.insert(0, "1") 
        self.num_combinations_entry.grid(row=2, column=3, columnspan=3, padx=5, pady=10, sticky="w") 

        # Generate Button
        generate_button = ttk.Button(self.master, text="로또 번호 생성", command=self._generate_combinations)
        generate_button.pack(pady=15)

        # Output Text Area
        self.output_label = ttk.Label(self.master, text="--- 생성된 랜덤 조합 ---")
        self.output_label.pack(pady=5)
        
        # Define fonts
        default_font = tkFont.nametofont("TkDefaultFont")
        self.combination_font = tkFont.Font(family=default_font.actual("family"), 
                                        size=default_font.actual("size") + 3) 
        self.random_value_font = tkFont.Font(family=default_font.actual("family"),
                                            size=default_font.actual("size") - 2) 

        self.output_text = tk.Text(self.master, height=36, width=85, state="disabled", wrap="none", 
                                   font=default_font) 
        self.output_text.pack(pady=5, padx=10)

        # Configure tags for different font sizes
        self.output_text.tag_configure("combination_numbers", font=self.combination_font)
        self.output_text.tag_configure("random_value", font=self.random_value_font)

        # Scrollbars for output text
        scrollbar_y = ttk.Scrollbar(self.master, orient="vertical", command=self.output_text.yview)
        scrollbar_y.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(self.master, orient="horizontal", command=self.output_text.xview)
        scrollbar_x.pack(side="bottom", fill="x")
        self.output_text.config(xscrollcommand=scrollbar_x.set)


    def _generate_combinations(self):
        """
        Generates lottery combinations based on user selections and displays them.
        Ensures central alignment and clear spacing.
        """
        self_output_text = self.output_text
        self_output_text.config(state="normal")
        self_output_text.delete(1.0, tk.END) # Clear previous content
        self.combination_results = [] 

        column_selection_choices = {}
        for i, combo_var in enumerate(self.combo_vars):
            selected_text = combo_var.get()
            code = selected_text.split('(')[1][0] 
            column_selection_choices[i+1] = {v: k for k, v in self.selection_type_codes.items()}[code] 

        try:
            num_to_generate = int(self.num_combinations_entry.get())
            if not (1 <= num_to_generate <= 20):
                messagebox.showwarning("입력 오류", "생성할 조합 개수는 1에서 20 사이여야 합니다.")
                return
        except ValueError:
            messagebox.showwarning("입력 오류", "생성할 조합 개수를 숫자로 입력해주세요.")
            return

        MAX_CONTENT_WIDTH = 80 
        COMBINATION_PART_ALIGN_LEN = 48 

        header_text = "--- 생성된 랜덤 조합 ---"
        padding_for_header = (MAX_CONTENT_WIDTH - len(header_text)) // 2 
        self_output_text.insert(tk.END, " " * padding_for_header + header_text + "\n")
        
        for i in range(num_to_generate):
            final_combination_set = set()
            combination_details = {}
            random_selected_numbers = [] 

            cols_to_process = {
                'top': [k for k, v in column_selection_choices.items() if v == 'top'],
                'bottom': [k for k, v in column_selection_choices.items() if v == 'bottom'],
                'random': [k for k, v in column_selection_choices.items() if v == 'random']
            }

            for col_type in ['top', 'bottom', 'random']:
                for col_num in sorted(cols_to_process[col_type]):
                    if len(final_combination_set) >= 6: break
                    column_name = f'{col_num}칸확률'
                    
                    selected_num = get_random_number_from_column(
                        self.prob_df, 
                        column_name, 
                        col_type, 
                        final_combination_set
                    )
                    
                    if selected_num is not None:
                        final_combination_set.add(selected_num)
                        combination_details[col_num] = (selected_num, self.selection_type_codes[col_type])
                        if self.selection_type_codes[col_type] == 'r': 
                            random_selected_numbers.append(selected_num)
                    else:
                        combination_details[col_num] = (None, self.selection_type_codes[col_type])

            final_combination_list = sorted(list(final_combination_set))
            fill_message = ""
            if len(final_combination_list) < 6:
                remaining_count = 6 - len(final_combination_list)
                all_possible_numbers = set(range(1, 46))
                available_numbers_for_fill = list(all_possible_numbers - final_combination_set)
                
                if len(available_numbers_for_fill) >= remaining_count:
                    newly_added_numbers = random.sample(available_numbers_for_fill, remaining_count)
                    final_combination_list.extend(newly_added_numbers)
                    final_combination_list.sort()
                    fill_message = " (일부 숫자가 1~45 랜덤으로 채워졌습니다.)"
                else: 
                    fill_message = " (6개 숫자를 채우지 못했습니다.)"
            
            random_value_str = ""
            if random_selected_numbers:
                random_value_str = f"랜덤값: {', '.join(map(str, sorted(random_selected_numbers)))}"
            
            combination_line_prefix = f"조합 {i+1}: "
            combination_numbers_str = f"{final_combination_list}"
            
            current_comb_part_len = len(combination_line_prefix) + len(combination_numbers_str) + len(fill_message)
            
            padding_between_parts = ""
            if current_comb_part_len < COMBINATION_PART_ALIGN_LEN:
                padding_between_parts = " " * (COMBINATION_PART_ALIGN_LEN - current_comb_part_len)
            else:
                padding_between_parts = "   " 

            content_line_length = len(combination_line_prefix) + len(combination_numbers_str) + \
                                  len(fill_message) + len(padding_between_parts) + len(random_value_str)
            
            padding_for_center = (MAX_CONTENT_WIDTH - content_line_length) // 2
            if padding_for_center < 0: padding_for_center = 0 

            self_output_text.insert(tk.END, " " * padding_for_center)

            self_output_text.insert(tk.END, combination_line_prefix)
            self_output_text.insert(tk.END, combination_numbers_str, "combination_numbers")
            self_output_text.insert(tk.END, fill_message, "combination_numbers")
            
            self_output_text.insert(tk.END, padding_between_parts)

            if random_selected_numbers:
                self_output_text.insert(tk.END, random_value_str, "random_value")
            
            self_output_text.insert(tk.END, "\n") 

            if (i + 1) % 5 == 0 and (i + 1) < num_to_generate:
                empty_line_padding = (MAX_CONTENT_WIDTH - 1) // 2 
                self_output_text.insert(tk.END, " " * empty_line_padding + "\n")
                self.master.update_idletasks() 
                time.sleep(1.0) 

        self_output_text.config(state="disabled") 

# --- Main Execution Block ---
if __name__ == "__main__":
    root = tk.Tk()
    app = LottoGeneratorApp(root)
    root.mainloop()
