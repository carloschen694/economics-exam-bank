"""
scripts/import_exam_data.py
批次匯入歷屆考古題至 economics-exam-bank 資料庫 (economics_exam.db)
支援從 D:\\antigravity\\economics-test 提取之 questions_index.json 或本地 JSON 匯入。
"""

import sys
import json
import os
from pathlib import Path
from sqlmodel import Session, select

# 將 src 加入 sys.path 以便匯入模組
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from economics_exam_bank.database import engine, create_db_and_tables
from economics_exam_bank.models.entities import (
    Exam,
    Question,
    SubjectType,
    QuestionType,
)


def map_question_type(raw_type: str) -> QuestionType:
    raw = (raw_type or "").strip()
    if "單選" in raw:
        return QuestionType.SINGLE_CHOICE
    elif "複選" in raw or "多選" in raw:
        return QuestionType.MULTIPLE_CHOICE
    elif "證明" in raw:
        return QuestionType.PROOF
    elif "計算" in raw:
        return QuestionType.CALCULATION
    else:
        return QuestionType.ESSAY


def import_questions(json_path: Path):
    if not json_path.exists():
        raise FileNotFoundError(f"找不到題目資料檔: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"[*] 讀取到 {len(items)} 題題目資料：{json_path}")

    create_db_and_tables()

    with Session(engine) as session:
        exam_cache = {}
        imported_questions = 0
        updated_questions = 0

        for item in items:
            year = int(item.get("year", 113))
            school = item.get("school", "國立臺北大學")
            department = item.get("department", "經濟學系碩士班")
            subject_str = item.get("subject", "個體經濟學")

            # 考科映射
            if "個體" in subject_str or "micro" in subject_str.lower():
                subject = SubjectType.MICROECONOMICS
            elif "總體" in subject_str or "macro" in subject_str.lower():
                subject = SubjectType.MACROECONOMICS
            elif "統計" in subject_str or "stat" in subject_str.lower():
                subject = SubjectType.STATISTICS
            elif "計量" in subject_str or "econometrics" in subject_str.lower():
                subject = SubjectType.ECONOMETRICS
            else:
                subject = SubjectType.COMPREHENSIVE

            title = f"{year}學年度{school}{department}{subject_str}入學考試試題"

            exam_key = (school, year, subject.value)
            if exam_key not in exam_cache:
                stmt = select(Exam).where(
                    Exam.school == school,
                    Exam.year == year,
                    Exam.subject == subject,
                )
                exam = session.exec(stmt).first()
                if not exam:
                    exam = Exam(
                        title=title,
                        school=school,
                        department=department,
                        year=year,
                        subject=subject,
                        description=f"{school} {year}年 碩士班研究所入學考試",
                    )
                    session.add(exam)
                    session.commit()
                    session.refresh(exam)
                    print(f"  [+] 建立新試卷: [{exam.id}] {title}")
                exam_cache[exam_key] = exam.id

            exam_id = exam_cache[exam_key]
            q_num = int(item.get("question_num", 1))

            # 處理題型
            q_type = map_question_type(item.get("type", ""))

            # 處理選擇題選項
            options_raw = item.get("options", [])
            options_json = None
            if options_raw and isinstance(options_raw, list):
                opt_dict = {
                    opt.get("label", str(i + 1)): opt.get("text", "")
                    for i, opt in enumerate(options_raw)
                    if isinstance(opt, dict)
                }
                if opt_dict:
                    options_json = json.dumps(opt_dict, ensure_ascii=False)

            # 處理題目內文與子題
            content = item.get("content_text", "").strip()
            subquestions = item.get("subquestions", [])
            if subquestions and isinstance(subquestions, list):
                sub_lines = []
                for sub in subquestions:
                    if isinstance(sub, dict):
                        lbl = sub.get("label", "")
                        txt = sub.get("text", "")
                        sub_lines.append(f"({lbl}) {txt}" if lbl else txt)
                if sub_lines:
                    content += "\n\n" + "\n".join(sub_lines)

            # 標籤整理
            tags_list = []
            if item.get("topic"):
                tags_list.append(item["topic"].strip())
            if item.get("type"):
                tags_list.append(item["type"].strip())
            tags_list.append("研究所考古題")
            tags_str = ",".join(dict.fromkeys(tags_list))

            # 配分
            points = float(item.get("score_weight", 10.0))

            # 難度 (申論題設定較高難度)
            diff = 4 if q_type in (QuestionType.ESSAY, QuestionType.PROOF) else 3

            # 檢查題目是否已存在
            q_stmt = select(Question).where(
                Question.exam_id == exam_id,
                Question.question_number == q_num,
            )
            question = session.exec(q_stmt).first()

            if question:
                question.question_type = q_type
                question.content = content
                question.options = options_json
                question.tags = tags_str
                question.points = points
                question.difficulty = diff
                session.add(question)
                updated_questions += 1
            else:
                question = Question(
                    exam_id=exam_id,
                    question_number=q_num,
                    question_type=q_type,
                    content=content,
                    options=options_json,
                    answer=item.get("answer") or None,
                    explanation=item.get("explanation") or None,
                    tags=tags_str,
                    difficulty=diff,
                    points=points,
                )
                session.add(question)
                imported_questions += 1

        session.commit()

        print(f"\n[OK] 匯入完成！新增: {imported_questions} 題，更新: {updated_questions} 題。")

        # 輸出目前資料庫狀態摘要
        exams = session.exec(select(Exam)).all()
        print("\n=== 目前資料庫試卷與題目統計 ===")
        for ex in exams:
            q_count = len(ex.questions)
            total_pts = sum(q.points for q in ex.questions)
            print(f"  ID:{ex.id:<2} | {ex.year}年 | {ex.school} | {ex.title} | 題目數: {q_count} 題 | 總分: {total_pts:.0f} 分")


def main():
    default_src = Path(r"D:\antigravity\economics-test\data\database\questions_index.json")
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        target = default_src

    print(f"=== 啟動歷屆考題匯入流程 ===")
    print(f"目標檔案: {target}")
    import_questions(target)


if __name__ == "__main__":
    main()
