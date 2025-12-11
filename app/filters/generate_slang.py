# generate_simple_slang_sql.py
import csv

INPUT_CSV = "slang.csv"
OUTPUT_SQL = "insert_slang_words.sql"

def load_words():
    words = []
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            word = row[0].strip()
            if word:
                words.append(word)
    return words

def generate_sql(words):
    sql_lines = ["INSERT IGNORE INTO slang_words (slang_word) VALUES"]

    values = []
    for w in words:
        # SQL escape
        w = w.replace("'", "''")
        values.append(f"('{w}')")

    sql_lines.append(",\n".join(values) + ";")
    return "\n".join(sql_lines)

if __name__ == "__main__":
    words = load_words()
    sql = generate_sql(words)

    with open(OUTPUT_SQL, "w", encoding="utf-8") as f:
        f.write(sql)

    print(f"✔ SQL 생성 완료: {OUTPUT_SQL}")
    print(f"✔ 총 {len(words)} 개의 단어가 변환되었습니다.")
