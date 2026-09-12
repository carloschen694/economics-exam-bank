from enum import Enum
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel


class SubjectType(str, Enum):
    MICROECONOMICS = "microeconomics"       # 個體經濟學
    MACROECONOMICS = "macroeconomics"       # 總體經濟學
    STATISTICS = "statistics"               # 統計學
    ECONOMETRICS = "econometrics"           # 計量經濟學
    COMPREHENSIVE = "comprehensive"         # 綜合經濟學


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"       # 單選題
    MULTIPLE_CHOICE = "multiple_choice"   # 多選題
    CALCULATION = "calculation"           # 計算題
    PROOF = "proof"                       # 數學證明題
    ESSAY = "essay"                       # 申論分析題


class ExamBase(SQLModel):
    title: str = Field(index=True, description="試卷名稱，如：113學年度台大經濟所個體經濟學")
    school: str = Field(index=True, description="學校名稱，如：國立臺灣大學、國立政治大學")
    department: str = Field(default="經濟學研究所", index=True, description="報考系所")
    year: int = Field(index=True, description="考試民國年份或西元年份，如：113")
    subject: SubjectType = Field(index=True, description="考試考科")
    description: Optional[str] = Field(default=None, description="考試說明或注意事項")


class Exam(ExamBase, table=True):
    __tablename__ = "exams"

    id: Optional[int] = Field(default=None, primary_key=True)

    # 關聯題目
    questions: List["Question"] = Relationship(back_populates="exam", cascade_delete=True)


class QuestionBase(SQLModel):
    exam_id: Optional[int] = Field(default=None, foreign_key="exams.id", index=True)
    question_number: int = Field(description="題號，例如：1")
    sub_number: Optional[str] = Field(default=None, description="小題編號，例如：(a)、(1)")
    question_type: QuestionType = Field(default=QuestionType.CALCULATION, description="題型")
    content: str = Field(description="題目內容，支援 LaTeX 數學符號與 Markdown 語法")
    options: Optional[str] = Field(default=None, description="選擇題選項，以 JSON 字串格式儲存，如 {'A':'...','B':'...'}")
    answer: Optional[str] = Field(default=None, description="標準答案或簡答")
    explanation: Optional[str] = Field(default=None, description="詳細數學推導與經濟意涵解析")
    tags: Optional[str] = Field(default=None, index=True, description="知識點標籤，逗號分隔，例如：Solow模型,黃金法則")
    difficulty: int = Field(default=3, ge=1, le=5, description="難度評級 1-5")
    points: float = Field(default=10.0, description="配分")


class Question(QuestionBase, table=True):
    __tablename__ = "questions"

    id: Optional[int] = Field(default=None, primary_key=True)

    # 關聯試卷
    exam: Optional[Exam] = Relationship(back_populates="questions")


# Pydantic Schemas for API Requests & Responses
class ExamCreate(ExamBase):
    pass


class ExamRead(ExamBase):
    id: int


class QuestionCreate(QuestionBase):
    pass


class QuestionRead(QuestionBase):
    id: int


class ExamReadWithQuestions(ExamRead):
    questions: List[QuestionRead] = []


class QuestionUpdate(SQLModel):
    question_number: Optional[int] = None
    sub_number: Optional[str] = None
    question_type: Optional[QuestionType] = None
    content: Optional[str] = None
    options: Optional[str] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    tags: Optional[str] = None
    difficulty: Optional[int] = None
    points: Optional[float] = None
