import os
from datetime import datetime
import streamlit as st

from app.config import validate_api_key
from app.pdf_utils import extract_text_from_pdf
from app.text_processing import split_notes_for_display
from app.features import (
    answer_question,
    generate_quiz,
    generate_revision_plan,
    generate_revision_notes,
    summarize_notes,
    generate_flashcards,
)

st.set_page_config(
    page_title="Smart Study Assistant Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
    .hero {
        padding: 1.25rem 1.4rem;
        border-radius: 22px;
        background: linear-gradient(135deg, rgba(75,85,255,0.08), rgba(255,115,163,0.10));
        border: 1px solid rgba(120,120,255,0.18);
        margin-bottom: 1rem;
    }
    .mini-card {
        padding: 1rem 1rem;
        border-radius: 18px;
        border: 1px solid rgba(140,140,140,0.16);
        background: rgba(255,255,255,0.7);
    }
    .result-card {
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(120,120,255,0.2);
        background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(245,245,255,0.5));
        margin-top: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #111827;
    }
    .muted {
        color: #667085;
        font-size: 0.95rem;
    }
    button[data-baseweb="tab"]:active,
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #4b55ff20, #ff73a320);
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def ensure_state():
    defaults = {
        "context_text": "",
        "source_name": "",
        "quiz_items": [],
        "exam_items": [],
        "weak_topics": [],
        "quiz_result": None,
        "exam_result": None,
        "summary_text": "",
        "revision_text": "",
        "revision_plan": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

ensure_state()

if not validate_api_key():
    st.error("🚨 Google API key is missing or invalid. Please add a valid `GOOGLE_API_KEY` to your `.env` file.")
    st.stop()


st.markdown(
    """
    <div class="hero">
        <h1 style="margin-bottom: 0.25rem;">📚 Smart Study Assistant Agent</h1>
        <div class="muted">
            Upload notes or a PDF, ask questions, generate quizzes, track weak areas, and run exam mode.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Setup")
    st.caption("Use your Gemini API key from a .env file.")
    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    manual_notes = st.text_area(
        "Or paste notes",
        height=220,
        placeholder="Paste your notes here if you do not have a PDF...",
    )
    model_name = st.text_input("Model name", value=os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash"))
    quiz_count = st.slider("Quiz questions", 3, 10, 5)
    exam_count = st.slider("Exam questions", 5, 15, 8)
    retrieval_method = st.selectbox("Retrieval method", ["Keyword overlap", "Embedding (experimental)"])
    st.divider()
    beginner_mode = st.toggle("Explain Like I'm 10 Mode", value=False, help="Simplify explanations and examples")
    st.divider()
    st.caption("Tip: keep the notes concise for faster generation.")

    if st.button("🗑️ Reset all data"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

source_text = ""
source_name = ""

if uploaded is not None:
    try:
        with st.spinner("📄 Reading PDF... please wait"):
            source_text = extract_text_from_pdf(uploaded)
        source_name = uploaded.name
    except Exception as exc:
        st.error(f"Could not read the PDF: {exc}")

if manual_notes.strip():
    source_text = manual_notes.strip()
    source_name = "Pasted notes"

if source_text:
    st.session_state.context_text = source_text
    st.session_state.source_name = source_name

context = st.session_state.context_text.strip()
is_ready = bool(context)

if not is_ready:
    st.info("Upload a PDF or paste notes to start.")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="muted">Source</div>
            <div><strong>{st.session_state.source_name or "Loaded content"}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    word_count = len(context.split())
    if word_count > 10000:
        st.warning("⚠️ Large document detected. Quiz and summary generation may take longer.")
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="muted">Approx. length</div>
            <div><strong>{word_count:,} words</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="muted">Weak topics saved</div>
            <div><strong>{len(st.session_state.weak_topics)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

tabs = st.tabs(["🔍 Ask", "📝 Quiz", "🎓 Exam Mode", "🧠 Weak Areas", "📄 Summary"])

def record_weak_topics(items, selected_answers):
    for item, selected in zip(items, selected_answers):
        correct = item.get("answer_index")
        topic = item.get("topic", "General")
        if correct is not None and selected != correct:
            if topic and topic not in st.session_state.weak_topics:
                st.session_state.weak_topics.append(topic)


with tabs[0]:
    st.markdown("<div class='section-header'>Ask questions about your notes</div>", unsafe_allow_html=True)
    if not is_ready:
        st.info("Upload a PDF to start asking questions.")

    question = st.text_input("Your question", placeholder="Explain photosynthesis in simple words...", disabled=not is_ready)
    if st.button("Get answer", type="primary", disabled=not is_ready):
        if not question.strip():
            st.warning("Type a question first.")
        else:
            with st.spinner("Thinking..."):
                try:
                    answer = answer_question(context, question, model_name=model_name, beginner_mode=beginner_mode)
                    st.markdown(f"<div class='result-card'>\n\n{answer}\n\n</div>", unsafe_allow_html=True)
                except Exception as exc:
                    with st.expander("❌ Error details", expanded=True):
                        st.error(str(exc))
                        st.caption("Try using a shorter question or check your API key.")

    if is_ready:
        with st.expander("Preview the loaded notes"):
            st.code(split_notes_for_display(context), language="markdown")

with tabs[1]:
    st.markdown("<div class='section-header'>Quiz mode</div>", unsafe_allow_html=True)
    st.caption("Generate a practice quiz with answers and explanations.")

    if not is_ready:
        st.info("Upload a PDF to generate a quiz.")

    if st.button("Generate quiz", type="primary", disabled=not is_ready):
        with st.spinner("Creating quiz..."):
            try:
                st.session_state.quiz_items = generate_quiz(
                    context=context,
                    num_questions=quiz_count,
                    model_name=model_name,
                    exam_mode=False,
                )
                st.session_state.quiz_result = None
            except Exception as exc:
                with st.expander("❌ Error details", expanded=True):
                    st.error(str(exc))
                    st.caption("Try using a shorter question or check your API key.")

    quiz_items = st.session_state.quiz_items

    if quiz_items:
        selected_answers = []
        for i, item in enumerate(quiz_items):
            st.markdown(f"### Q{i+1}. {item.get('question', '')}")
            options = item.get("options", [])
            choice = st.radio(
                label=f"Answer for question {i+1}",
                options=list(range(len(options))) if options else [0],
                format_func=lambda idx, opts=options: opts[idx] if idx < len(opts) else str(idx),
                key=f"quiz_choice_{i}",
                horizontal=False,
                label_visibility="collapsed",
            )
            selected_answers.append(choice)

        if st.button("Submit quiz"):
            correct_count = 0
            wrong_items = []
            for item, selected in zip(quiz_items, selected_answers):
                correct = item.get("answer_index", -1)
                if selected == correct:
                    correct_count += 1
                else:
                    wrong_items.append(item)
            record_weak_topics(quiz_items, selected_answers)
            st.session_state.quiz_result = {
                "score": correct_count,
                "total": len(quiz_items),
                "wrong_items": wrong_items,
                "submitted_at": datetime.now().isoformat(timespec="seconds"),
            }

    if st.session_state.quiz_result:
        result = st.session_state.quiz_result

        st.markdown(f"""
        <div class="result-card">
            <h3 style="margin-top:0;">Quiz Results</h3>
            <p style="font-size:1.2rem; font-weight:bold; color:{'#2e7d32' if result['score'] > result['total']/2 else '#c62828'}">
                Score: {result['score']} / {result['total']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        import json
        result_json = json.dumps(st.session_state.quiz_result, indent=2)
        st.download_button("📥 Download quiz results", result_json, file_name="quiz_results.json")

        if result["wrong_items"]:
            st.markdown("#### Review the ones you missed")
            for item in result["wrong_items"]:
                st.markdown(f"**{item.get('question','')}**")
                options = item.get("options", [])
                answer_index = item.get("answer_index", 0)
                if options and 0 <= answer_index < len(options):
                    st.write(f"Correct answer: {options[answer_index]}")
                if item.get("explanation"):
                    st.caption(item["explanation"])
                st.divider()

with tabs[2]:
    st.markdown("<div class='section-header'>Exam mode</div>", unsafe_allow_html=True)
    st.caption("Practice like a real test: answers stay hidden until submission.")

    if not is_ready:
        st.info("Upload a PDF to practice Exam Mode.")

    if st.button("Generate exam", type="primary", disabled=not is_ready):
        with st.spinner("Creating exam..."):
            try:
                st.session_state.exam_items = generate_quiz(
                    context=context,
                    num_questions=exam_count,
                    model_name=model_name,
                    exam_mode=True,
                )
                st.session_state.exam_result = None
            except Exception as exc:
                with st.expander("❌ Error details", expanded=True):
                    st.error(str(exc))
                    st.caption("Try using a shorter question or check your API key.")

    exam_items = st.session_state.exam_items

    if exam_items:
        selected_answers = []
        for i, item in enumerate(exam_items):
            st.markdown(f"### Q{i+1}. {item.get('question', '')}")
            options = item.get("options", [])
            choice = st.radio(
                label=f"Exam answer for question {i+1}",
                options=list(range(len(options))) if options else [0],
                format_func=lambda idx, opts=options: opts[idx] if idx < len(opts) else str(idx),
                key=f"exam_choice_{i}",
                horizontal=False,
                label_visibility="collapsed",
            )
            selected_answers.append(choice)

        if st.button("Submit exam"):
            correct_count = 0
            wrong_items = []
            for item, selected in zip(exam_items, selected_answers):
                correct = item.get("answer_index", -1)
                if selected == correct:
                    correct_count += 1
                else:
                    wrong_items.append(item)
            record_weak_topics(exam_items, selected_answers)
            st.session_state.exam_result = {
                "score": correct_count,
                "total": len(exam_items),
                "wrong_items": wrong_items,
                "submitted_at": datetime.now().isoformat(timespec="seconds"),
            }

    if st.session_state.exam_result:
        result = st.session_state.exam_result

        st.markdown(f"""
        <div class="result-card">
            <h3 style="margin-top:0;">Exam Results</h3>
            <p style="font-size:1.2rem; font-weight:bold; color:{'#2e7d32' if result['score'] > result['total']/2 else '#c62828'}">
                Score: {result['score']} / {result['total']}
            </p>
        </div>
        """, unsafe_allow_html=True)

        import json
        result_json = json.dumps(st.session_state.exam_result, indent=2)
        st.download_button("📥 Download exam results", result_json, file_name="exam_results.json")

        if result["wrong_items"]:
            st.markdown("#### Answers revealed after submission")
            for item in result["wrong_items"]:
                st.markdown(f"**{item.get('question','')}**")
                options = item.get("options", [])
                answer_index = item.get("answer_index", 0)
                if options and 0 <= answer_index < len(options):
                    st.write(f"Correct answer: {options[answer_index]}")
                if item.get("explanation"):
                    st.caption(item["explanation"])
                st.divider()

with tabs[3]:
    st.markdown("<div class='section-header'>Weak areas tracker & Smart Revision Planner</div>", unsafe_allow_html=True)
    st.caption("Topics from incorrect answers are saved here. Use them to generate a structured study plan.")

    if st.session_state.weak_topics:
        st.markdown("#### Your current weak topics:")
        for topic in st.session_state.weak_topics:
            st.markdown(f"- {topic}")
    else:
        st.info("Your weak topics will appear here after you submit a quiz or exam.")

    if st.button("Generate Smart Revision Plan", type="primary", disabled=not is_ready or not st.session_state.weak_topics):
        with st.spinner("Building a structured 3-5 day revision plan..."):
            try:
                st.session_state.revision_plan = generate_revision_plan(
                    context=context,
                    weak_topics=st.session_state.weak_topics,
                    model_name=model_name,
                )
            except Exception as exc:
                with st.expander("❌ Error details", expanded=True):
                    st.error(str(exc))

    if st.session_state.revision_plan:
        st.markdown(f"<div class='result-card'>\n\n{st.session_state.revision_plan}\n\n</div>", unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate quick revision notes", disabled=not is_ready):
            with st.spinner("Building revision notes..."):
                try:
                    st.session_state.revision_text = generate_revision_notes(
                        context=context,
                        weak_topics=st.session_state.weak_topics,
                        model_name=model_name,
                    )
                except Exception as exc:
                    with st.expander("❌ Error details", expanded=True):
                        st.error(str(exc))
                        st.caption("Try using a shorter question or check your API key.")

        if st.session_state.revision_text:
            st.markdown("#### Revision notes")
            st.markdown(f"<div class='mini-card'>\n\n{st.session_state.revision_text}\n\n</div>", unsafe_allow_html=True)

    with col2:
        if st.button("📇 Create flashcards", disabled=not is_ready):
            with st.spinner("Generating flashcards..."):
                try:
                    flashcards = generate_flashcards(context, st.session_state.weak_topics, model_name)
                    if not flashcards:
                        st.warning("Could not generate flashcards.")
                    for card in flashcards:
                        with st.expander(f"📌 {card.get('front', 'Flashcard')}"):
                            st.write(card.get('back', ''))
                except Exception as exc:
                    with st.expander("❌ Error details", expanded=True):
                        st.error(str(exc))
                        st.caption("Try using a shorter question or check your API key.")

with tabs[4]:
    st.markdown("<div class='section-header'>Quick summary</div>", unsafe_allow_html=True)
    if not is_ready:
        st.info("Upload a PDF to view a quick summary.")

    if not st.session_state.summary_text:
        if st.button("Summarize notes", type="primary", disabled=not is_ready):
            with st.spinner("Summarizing..."):
                try:
                    st.session_state.summary_text = summarize_notes(context, model_name=model_name)
                except Exception as exc:
                    with st.expander("❌ Error details", expanded=True):
                        st.error(str(exc))
                        st.caption("Try using a shorter question or check your API key.")
    if st.session_state.summary_text:
        st.write(st.session_state.summary_text)

st.divider()
st.caption("Built for GenAI Academy project submission.")
