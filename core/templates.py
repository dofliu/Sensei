"""
Sensei · Visual Templates Schema
================================
Pydantic schemas defining the 7 visualization templates Sensei supports
(enumeration / comparison / flow / hierarchy / SWOT / pyramid / quiz_card).

Design principle: LLM picks the template, fills the slots. Templates are
fixed — this prevents the model from inventing new layouts every utterance,
which would make the classroom screen jumpy and unreadable.

Adding a new template:
1. Define the Pydantic class here.
2. Register it in `TEMPLATE_REGISTRY` (bottom of file).
3. Add an example to prompts/classifier.txt.
4. Add a renderer in frontend/renderers.py and register it in RENDERERS.
5. Add the tool description in core/llm.py::TOOL_DESCRIPTIONS and a
   dropdown label in frontend/app.py::_list_template_hints + frontend/i18n.py.
6. Smoke-test on a representative transcript before merging.
"""

from typing import Literal
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# 1. Enumeration cards: parallel items
#    "Control isn't only PID — also optimal, neural, nonlinear, robust"
# ──────────────────────────────────────────────
class CardItem(BaseModel):
    name: str = Field(description="Item name in Traditional Chinese")
    name_en: str = Field(default="", description="Optional English name (kept in history, not rendered on /display)")
    icon: str = Field(description="Lucide icon slug, e.g. 'trending-up'")
    desc: str = Field(description="Short caption ≤10 Chinese chars, displayed as a small subtitle under the name")
    tag: str = Field(default="", description="Optional short label, kept in history but not rendered on /display")


class EnumerationCards(BaseModel):
    template: Literal["enumeration_cards"] = "enumeration_cards"
    title: str
    subtitle: str = ""
    items: list[CardItem] = Field(min_length=2, max_length=6)


# ──────────────────────────────────────────────
# 2. Comparison table: A vs B
#    "Open-loop vs closed-loop control"
# ──────────────────────────────────────────────
class ComparisonRow(BaseModel):
    aspect: str = Field(description="Comparison dimension")
    a_value: str
    b_value: str


class ComparisonTable(BaseModel):
    template: Literal["comparison_table"] = "comparison_table"
    title: str
    a_name: str
    b_name: str
    rows: list[ComparisonRow] = Field(min_length=2, max_length=8)


# ──────────────────────────────────────────────
# 3. Flow diagram: ordered steps
#    "First measure, then compare, then actuate"
# ──────────────────────────────────────────────
class FlowStep(BaseModel):
    name: str
    desc: str = Field(default="", description="Short caption ≤10 Chinese chars, displayed under the step name")
    icon: str = ""


class FlowDiagram(BaseModel):
    template: Literal["flow_diagram"] = "flow_diagram"
    title: str
    steps: list[FlowStep] = Field(min_length=2, max_length=8)


# ──────────────────────────────────────────────
# 4. Hierarchy tree: classification
#    "Control: linear { proportional, PID }, nonlinear { sliding-mode, ... }"
# ──────────────────────────────────────────────
class HierarchyNode(BaseModel):
    name: str
    children: list["HierarchyNode"] = Field(default_factory=list)


HierarchyNode.model_rebuild()


class HierarchyTree(BaseModel):
    template: Literal["hierarchy_tree"] = "hierarchy_tree"
    title: str
    root: HierarchyNode


# ──────────────────────────────────────────────
# 5. SWOT analysis: strategic 2x2 grid
#    "Let's SWOT Taiwan offshore wind: strengths..., weaknesses..., ..."
# ──────────────────────────────────────────────
class SWOTItem(BaseModel):
    name: str = Field(description="Item label in Traditional Chinese, ≤10 chars ideal")
    desc: str = Field(default="", description="Optional ≤10-char sub-caption")


class SWOT(BaseModel):
    template: Literal["swot"] = "swot"
    title: str
    subject: str = Field(default="", description="Optional: what is being analyzed")
    strengths:     list[SWOTItem] = Field(min_length=1, max_length=6)
    weaknesses:    list[SWOTItem] = Field(min_length=1, max_length=6)
    opportunities: list[SWOTItem] = Field(min_length=1, max_length=6)
    threats:       list[SWOTItem] = Field(min_length=1, max_length=6)


# ──────────────────────────────────────────────
# 6. Pyramid: linear hierarchy with weight from base→apex
#    "Maslow's hierarchy: physiological at base, self-actualization at apex"
# ──────────────────────────────────────────────
class PyramidLayer(BaseModel):
    name: str = Field(description="Layer label in Traditional Chinese, ≤10 chars ideal")
    desc: str = Field(default="", description="Optional ≤10-char sub-caption")


class Pyramid(BaseModel):
    template: Literal["pyramid"] = "pyramid"
    title: str
    subject: str = Field(default="", description="Optional: what is being structured")
    # Order convention: layers[0] = apex (top, narrowest); layers[-1] = base (bottom, widest)
    layers: list[PyramidLayer] = Field(min_length=2, max_length=7)


# ──────────────────────────────────────────────
# 7. Quiz card: in-lecture formative-check multiple choice (4-option)
#    "Quick check — which of the following is NOT a control method?
#     (A) PID  (B) Fuzzy  (C) Linear regression  (D) Robust"
#    Designed for the demo flow where the teacher asks the question,
#    students answer by hand-raise, and the teacher reveals the key verbally.
# ──────────────────────────────────────────────
class QuizCard(BaseModel):
    template: Literal["quiz_card"] = "quiz_card"
    title: str = Field(description="Short topic label for the projector (≤16 chars ideal)")
    question: str = Field(description="Question stem in Traditional Chinese (≤60 chars ideal)")
    # Exactly 4 options; renderer auto-labels them A/B/C/D in order.
    options: list[str] = Field(min_length=4, max_length=4)
    answer: Literal["A", "B", "C", "D"] = Field(description="The single correct option label")
    explanation: str = Field(default="", description="Short rationale (≤40 chars), shown small for teacher-led reveal")
    difficulty: Literal["easy", "medium", "hard"] = Field(default="medium")


# ──────────────────────────────────────────────
# Registry — used by llm.py for schema validation
# ──────────────────────────────────────────────
TEMPLATE_REGISTRY: dict[str, type[BaseModel]] = {
    "enumeration_cards": EnumerationCards,
    "comparison_table":  ComparisonTable,
    "flow_diagram":      FlowDiagram,
    "hierarchy_tree":    HierarchyTree,
    "swot":              SWOT,
    "pyramid":           Pyramid,
    "quiz_card":         QuizCard,
}
