from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"

@dataclass
class Document:
    path: Path
    title: str
    department: str
    allowed_roles: set[str]
    version: str
    keywords: list[str]
    body: str


def _parse(path: Path) -> Document:
    text = path.read_text(encoding="utf-8")
    meta, _, body = text.partition("---\n")
    info = {}
    for line in meta.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip()] = v.strip()
    return Document(
        path=path,
        title=info.get("title", path.stem),
        department=info.get("department", "general"),
        allowed_roles={x.strip() for x in info.get("allowed_roles", "all").split(",")},
        version=info.get("version", "v1"),
        keywords=[x.strip().lower() for x in info.get("keywords", "").split(",") if x.strip()],
        body=body.strip(),
    )


def load_documents() -> list[Document]:
    return [_parse(p) for p in KNOWLEDGE.rglob("*.md")]


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[가-힣A-Za-z0-9]+", text.lower()) if len(t) >= 2}


def search(question: str, employee_department: str = "일반", role: str = "employee", top_k: int = 2) -> list[tuple[Document, int]]:
    q = question.lower()
    q_tokens = _tokens(question)
    scored = []
    for doc in load_documents():
        if "all" not in doc.allowed_roles and role not in doc.allowed_roles and employee_department not in doc.allowed_roles:
            continue
        score = sum(3 for kw in doc.keywords if kw and kw in q)
        score += len(q_tokens & _tokens(doc.title + " " + doc.body[:500]))
        if score > 0:
            scored.append((doc, score))
    return sorted(scored, key=lambda x: x[1], reverse=True)[:top_k]


def rag_answer(question: str, employee_department: str = "일반", role: str = "employee") -> dict | None:
    results = search(question, employee_department, role)
    if not results or results[0][1] < 3:
        return None
    doc, score = results[0]
    excerpt = doc.body.split("\n\n")[0].strip()
    return {
        "answer": f"사내 문서 **{doc.title}**에서 관련 내용을 찾았습니다.\n\n{excerpt}\n\n※ 데모에서는 검색 결과를 그대로 보여주며, 실제 운영에서는 이 문서 일부만 LLM Context로 전달합니다.",
        "knowledge_version": doc.version,
        "document": str(doc.path.relative_to(ROOT)),
        "score": score,
    }
