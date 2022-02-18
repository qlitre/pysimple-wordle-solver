import PySimpleGUI as sg
from wordle_data import create_df


class Frontend:
    """GUIの見た目"""
    window_size = (800, 500)
    frame_left_size = (550, 500)
    frame_right_size = (240, 500)

    @staticmethod
    def ignore_input():
        """含まれていない文字を入力"""
        layout = [[sg.T('Ignore Chars')],
                  [sg.InputText('', size=(50, 3), key='IGNORE')]]
        return sg.Column(layout=layout,
                         justification='c')

    @staticmethod
    def input_widget(key, bg_color):
        """入力マスのwidget"""
        size = (4, 1)
        return sg.InputText('',
                            key=key,
                            size=size,
                            justification='c',
                            background_color=bg_color)

    def green_input(self):
        """位置が合っている文字を入力"""
        widgets = []
        # 位置が合っているものは最大で5個
        for col in range(1, 6):
            key = f'GREEN-C{col}'
            widget = self.input_widget(key=key, bg_color='green')
            # [widget,widget...]という一次元リストを作る
            widgets.append(widget)
        # 2次元にする
        layout = [widgets]

        return sg.Column(layout=layout,
                         justification='c',
                         # 追加
                         vertical_alignment='t')

    def orange_input(self):
        """含まれているけど位置が合っていない文字を入力"""
        layout = []
        # ターンに応じて入力できるように縦6,横5マス
        for row in range(1, 7):
            widgets = []
            for col in range(1, 6):
                key = f'ORANGE-R{row}C{col}'
                widget = self.input_widget(key=key, bg_color='orange')
                # [widget,widget...]という一次元リストを作る
                widgets.append(widget)
            # 一行ごとにlayoutに加えることで、縦に並ぶ
            layout.append(widgets)
        return sg.Column(layout=layout,
                         justification='c')

    @staticmethod
    def control():
        """guiコントロール"""
        # 入力後の確定と、初期化するREFRESHボタン
        layout = [[sg.Button('ENTER'),
                   sg.Button('REFRESH')]]
        return sg.Column(layout=layout,
                         justification='c')

    @staticmethod
    def guess_answer():
        """絞り込まれた答えの候補を表示"""
        layout = [[sg.MLine('',
                            size=(35, 20),
                            key='GUESS')]]
        return sg.Column(layout=layout, justification='c')

    def frame_left(self):
        """左側フレーム"""

        layout = [[self.ignore_input()],
                  [self.green_input(), self.orange_input()],
                  [self.control()]]

        return sg.Frame('',
                        layout=layout,
                        vertical_alignment='c',
                        size=self.frame_left_size)

    def frame_right(self):
        """右側フレーム"""
        layout = [[self.guess_answer()]]
        return sg.Frame('',
                        layout=layout,
                        vertical_alignment='c',
                        size=self.frame_right_size)

    def layout(self):
        """レイアウト"""
        layout = [
            [self.frame_left(), self.frame_right()]
        ]
        return layout

    def window(self):
        """ウィンドウ"""
        layout = self.layout()
        window_title = 'PySimpleGUI Wordle Solver'
        window_size = self.window_size
        return sg.Window(title=window_title,
                         layout=layout,
                         size=window_size,
                         finalize=True)


class Solver:
    """solverのロジック"""

    def __init__(self, file_name):
        self.file_name = file_name
        self.df = None
        self.window = Frontend().window()

    def set_df(self):
        self.df = create_df(self.file_name)

    def filter_ignore(self, chars):
        """含まれていないの絞り込み"""
        for char in chars:
            self.df = self.df[~self.df['char_full'].str.contains(char)]

    def filter_green(self, col_name, char):
        """位置が合っているの絞り込み"""
        self.df = self.df[self.df[col_name] == char]

    def filter_orange(self, col_name, char):
        """含まれているの絞り込み"""
        self.df = self.df[self.df['char_full'].str.contains(char)]
        self.df = self.df[~self.df[col_name].str.contains(char)]

    @staticmethod
    def get_optimize_words(words: list):
        """黄色のヒット率が高い単語順に並べて返す"""
        optimized_words = []
        # 単語を総当たりで調べて、黄色がヒットするか調べる
        for guess in words:
            cnt = 0
            for answer in words:
                # 同じ場合は除く
                if guess == answer:
                    continue
                # 同じ文字はカウントしない
                already = []
                for c in guess:
                    if c in already:
                        continue
                    already.append(c)
                    # 含まれていたらカウントアップ
                    if c in answer:
                        cnt += 1
            optimized_words.append({'word': guess, 'yellow_count': cnt})
        # ヒット降順で並べる
        optimized_words.sort(key=lambda x: -x['yellow_count'])

        return [f"{dic['word']}:{dic['yellow_count']}" for dic in optimized_words]

    def output_guess(self):
        """答えの候補の出力"""
        # 一旦消す
        self.window['GUESS'].update('')
        # dfから文字リストを取得
        words = list(self.df['char_full'].values)
        # 黄色の多い順で再取得
        words = self.get_optimize_words(words)
        # あんまり多すぎても迷うので、最大50単語表示
        words = words[:50]
        guess = ''
        for word in words:
            guess += word + '\n'
        self.window['GUESS'].update(guess)

    def start_solver(self):
        """スタート"""
        # dfをセット
        self.set_df()

        while True:
            event, values = self.window.read()

            if event == sg.WIN_CLOSED:
                break

            # 絞り込む処理
            if event == 'ENTER':
                # 含まれない文字で絞り込む
                chars = values['IGNORE']
                if chars:
                    self.filter_ignore(chars=chars)

                # 位置が合っている文字で絞り込む
                for c in range(1, 6):
                    key = f'GREEN-C{c}'
                    char = values[key]
                    if char:
                        col_name = f'char_{c}'
                        self.filter_green(col_name=col_name, char=char)

                # 含まれている文字で絞り込む
                for r in range(1, 7):
                    for c in range(1, 6):
                        key = f'ORANGE-R{r}C{c}'
                        char = values[key]
                        if char:
                            col_name = f'char_{c}'
                            self.filter_orange(col_name=col_name, char=char)

                # 絞り込まれた結果を表示する
                self.output_guess()

            # 初期化する処理
            if event == 'REFRESH':
                self.set_df()


def job():
    answer_file_name = 'wordle.txt'
    solver = Solver(file_name=answer_file_name)
    solver.start_solver()


if __name__ == '__main__':
    job()
