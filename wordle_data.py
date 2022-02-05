import pandas as pd


def generate_df_row(file_name):
    """dfの行を作成して返す"""
    with open(file_name, "r") as f:
        for word in f:
            word = word.strip()
            yield [word[0], word[1], word[2], word[3], word[4], word]


def create_df(file_name):
    """dfを作成"""
    cols = ['char_1', 'char_2', 'char_3', 'char_4', 'char_5', 'char_full']
    values = [row for row in generate_df_row(file_name)]
    return pd.DataFrame(values, columns=cols)


def job():
    answer_file = 'wordle.txt'
    df = create_df(answer_file)

    # a,b,cの３文字が含まれない単語
    ignore_chars = 'abc'
    for char in ignore_chars:
        df = df[~df['char_full'].str.contains(char)]
    print(df)

    # 含まれている文字の絞り込み
    char = 'd'
    # 全文字の中に含まれているの絞り込み
    df = df[df['char_full'].str.contains(char)]
    # 特定の位置に含まれていないの絞り込み
    pos = 1
    col_name = f'char_{pos}'
    df = df[df[col_name] != char]
    print(df)

    # 位置が合っている文字の絞り込み
    char = 'n'
    pos = 2
    col_name = f'char_{pos}'
    df = df[df[col_name] == char]
    print(df)


if __name__ == '__main__':
    job()
