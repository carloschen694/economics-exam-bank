import random
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, col, select
from ...database import get_session
from ...models.exam import Exam, SubjectType
from ...models.question import Question, QuestionRead, QuestionType

router = APIRouter(prefix="/practice", tags=["Practice 練習與測驗"])

SessionDep = Annotated[Session, Depends(get_session)]


class AnswerSubmission(BaseModel):
    question_id: int
    user_answer: str


class AnswerResult(BaseModel):
    question_id: int
    user_answer: str
    correct_answer: str | None
    is_correct: bool | None
    explanation: str | None


@router.get("/random", response_model=QuestionRead)
def get_random_question(
    session: SessionDep,
    subject: SubjectType | None = Query(default=None, description="依考科篩選"),
    question_type: QuestionType | None = Query(default=None, description="依題型篩選"),
    tag: str | None = Query(default=None, description="依知識點標籤篩選"),
    difficulty: int | None = Query(default=None, ge=1, le=5, description="依難度篩選"),
) -> Question:
    statement = select(Question)
    
    if subject:
        statement = statement.join(Exam).where(Exam.subject == subject)
    if question_type:
        statement = statement.where(Question.question_type == question_type)
    if tag:
        statement = statement.where(col(Question.tags).contains(tag))
    if difficulty:
        statement = statement.where(Question.difficulty == difficulty)

    results = list(session.exec(statement).all())
    if not results:
        raise HTTPException(status_code=404, detail="無符合條件的題目")
        
    return random.choice(results)


@router.post("/submit", response_model=AnswerResult)
def submit_answer(
    submission: AnswerSubmission,
    session: SessionDep,
) -> AnswerResult:
    question = session.get(Question, submission.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="題目不存在")

    is_correct: bool | None = None
    if question.answer:
        # 單選題或大小寫不拘比對
        cleaned_user = submission.user_answer.strip().upper()
        cleaned_std = question.answer.strip().upper()
        is_correct = (cleaned_user == cleaned_std)

    return AnswerResult(
        question_id=question.id or 0,
        user_answer=submission.user_answer,
        correct_answer=question.answer,
        is_correct=is_correct,
        explanation=question.explanation,
    )
