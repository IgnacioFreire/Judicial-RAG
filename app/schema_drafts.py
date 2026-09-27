"""Build a QuestionSchema from unsaved editor drafts."""

from pydantic import BaseModel, ValidationError

from models.query import Category, QuestionSchema, QuestionType, UserQuestion


class CategoryDraft(BaseModel):
    """One category row in the classification editor."""

    code: str = ""
    label: str = ""


class QuestionDraft(BaseModel):
    """One question editor. Not a saved UserQuestion until build_schema succeeds."""

    label: str = ""
    question: str = ""
    question_type: QuestionType = QuestionType.EXTRACTION
    output_format: str = ""
    notes: str = ""
    categories: list[CategoryDraft] = []


class SchemaBuildError(BaseModel):
    """First validation failure when saving drafts."""

    message: str
    question_index: int | None = None


def build_schema(
    drafts: list[QuestionDraft],
) -> tuple[QuestionSchema | None, SchemaBuildError | None]:
    """Validate drafts and return a schema, or the first error."""
    questions: list[UserQuestion] = []

    for i, draft in enumerate(drafts):
        try:
            categories = None
            if draft.question_type == QuestionType.CLASSIFICATION:
                categories = [
                    Category(code=row.code, label=row.label)
                    for row in draft.categories
                    if row.code and row.label
                ] or None

            questions.append(
                UserQuestion(
                    label=draft.label.strip(),
                    question=draft.question.strip(),
                    question_type=draft.question_type,
                    categories=categories,
                    output_format=draft.output_format or None,
                    notes=draft.notes or None,
                )
            )
        except ValidationError as exc:
            return None, SchemaBuildError(
                message=exc.errors()[0]["msg"],
                question_index=i,
            )

    if not questions:
        return None, SchemaBuildError(
            message="Add at least one question before saving."
        )

    try:
        return QuestionSchema(name="User schema", questions=questions), None
    except ValidationError as exc:
        return None, SchemaBuildError(message=exc.errors()[0]["msg"])
