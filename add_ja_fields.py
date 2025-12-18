import io
import os

ROOT = os.path.dirname(__file__)
TARGET = os.path.join(ROOT, "frontend", "src", "pages", "header", "glossaryData.js")


def main():
    with io.open(TARGET, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for i, line in enumerate(lines):
        new_lines.append(line)

        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]

        # label_ja 추가 (없을 때만)
        if "label_ko:" in stripped and "label_ja" not in stripped:
            # 값 추출 시, 단일 인용부호 기준 간단 파싱
            try:
                value = stripped.split("label_ko:")[1].split("'")[1]
            except Exception:
                value = ""
            # 우선은 label_ko 값을 복사해서 placeholder로 사용
            new_lines.append(f"{indent}label_ja: '{value}',\n")

        # description_ja 추가 (없을 때만)
        if "description_ko:" in stripped and "description_ja" not in stripped:
            try:
                value = stripped.split("description_ko:")[1].split("'", 1)[1].rsplit("'", 1)[0]
            except Exception:
                value = ""
            new_lines.append(f"{indent}description_ja: '{value}',\n")

    with io.open(TARGET, "w", encoding="utf-8", newline="") as f:
        f.writelines(new_lines)


if __name__ == "__main__":
    main()


