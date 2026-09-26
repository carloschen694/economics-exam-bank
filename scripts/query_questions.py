"""
scripts/query_questions.py
歷屆經濟學考古題庫 CLI 靈活檢索與解答查詢工具
"""

import sys
import argparse
from pathlib import Path
from sqlmodel import Session, select, col

# 將 src 加入 sys.path 以便匯入模組
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from economics_exam_bank.database import engine
from economics_exam_bank.models.entities import Exam, Question, QuestionType

sys.stdout.reconfigure(encoding='utf-8')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="經濟學題庫 CLI 查詢與解答推導工具 (economics-exam-bank)"
    )
    parser.add_argument("--id", type=int, help="依題目 ID 精確查詢")
    parser.add_argument("--year", type=int, help="依民國年份查詢 (如：113, 114, 115)")
    parser.add_argument("--school", type=str, help="依學校搜尋 (如：臺北大學)")
    parser.add_argument("--tag", type=str, help="依知識點標籤關鍵字搜尋 (如：Cournot, 納許, 效用)")
    parser.add_argument("--keyword", type=str, help="依題目內容內文關鍵字搜尋 (如：Hicksian, Nash)")
    parser.add_argument("--type", type=str, help="依題型搜尋 (multiple_choice, calculation, essay)")
    parser.add_argument("-s", "--solution", action="store_true", help="是否顯示標準答案與詳細 LaTeX 解析推導")
    parser.add_argument("--limit", type=int, default=20, help="最多顯示筆數 (預設 20)")
    return parser


def query_questions(args):
    with Session(engine) as session:
        statement = select(Question, Exam).join(Exam, isouter=True)

        if args.id:
            statement = statement.where(Question.id == args.id)
        if args.year:
            statement = statement.where(Exam.year == args.year)
        if args.school:
            statement = statement.where(col(Exam.school).contains(args.school))
        if args.type:
            statement = statement.where(col(Question.question_type).contains(args.type))
        if args.tag:
            statement = statement.where(col(Question.tags).contains(args.tag))
        if args.keyword:
            statement = statement.where(col(Question.content).contains(args.keyword))

        statement = statement.limit(args.limit)
        results = session.exec(statement).all()

        if not results:
            print("[!] 未找到符合條件的考題。")
            return

        print("=" * 80)
        print(f" 🔍 題庫檢索結果（共找到 {len(results)} 筆）：")
        print("=" * 80)

        for q, exam in results:
            exam_info = f"{exam.year}年 {exam.school} {exam.subject.value}" if exam else "未知試卷"
            print(f"\n📌 [QID: {q.id:02d}] {exam_info} | 題號: 第 {q.question_number} 題 ({q.points:.0f}分)")
            print(f"   題型: {q.question_type.value} | 難度評級: {'★' * q.difficulty}")
            print(f"   標籤: {q.tags or '無'}")
            print(f"   -----------------------------------------------------------------")
            
            # 格式化顯示內文
            lines = q.content.split("\n")
            preview_content = "\n   ".join(lines[:5])
            print(f"   內文:\n   {preview_content}")
            if len(lines) > 5:
                print("   ...")

            # 顯示選項（若有）
            if q.options:
                import json
                try:
                    opts = json.loads(q.options)
                    print("   選項:")
                    for k, v in opts.items():
                        print(f"     ({k}) {v}")
                except Exception:
                    pass

            # 顯示答案與解析
            if args.solution or args.id:
                print(f"\n   ✅ 標準答案: {q.answer or '暫無答案'}")
                print(f"   📖 詳細推導解析:")
                if q.explanation:
                    exp_lines = q.explanation.split("\n")
                    formatted_exp = "\n     ".join(exp_lines)
                    print(f"     {formatted_exp}")
                else:
                    print("     (暫無詳細解析)")
            print("-" * 80)


def main():
    parser = build_parser()
    args = parser.parse_args()
    query_questions(args)


if __name__ == "__main__":
    main()
