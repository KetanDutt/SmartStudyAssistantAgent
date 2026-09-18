"""
Main Streamlit application entry point for Smart Study Assistant Agent.
Features conversational Q&A, interactive quizzes, exam simulation,
flashcard review deck, weak topic analytics, visual concept maps, and data exports.
"""

from datetime import datetime
import html
import json
import os
import streamlit as st

from app.config import (
    DEFAULT_MODEL,
    get_api_key,
    get_available_models,
    validate_api_key,
)
from app.features import (
    answer_question,
    generate_flashcards,
    generate_mindmap_markdown,
    generate_quiz,
    generate_revision_notes,
    generate_revision_plan,
    summarize_notes,
)
from app.handlers import (
    add_score,
    ensure_state,
    record_weak_topics,
    shuffle_quiz_items,
    update_user_data,
)
from app.pdf_utils import extract_text_from_pdf
from app.text_processing import split_notes_for_display

# Set application layout and page metadata
st.set_page_config(
    page_title="Smart Study Assistant Agent",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom responsive CSS design system
st.markdown(
    """
    <style>
    :root {
        --primary-gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        --card-bg: rgba(255, 255, 255, 0.9);
        --card-border: #e2e8f0;
        --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        --text-main: #0f172a;
        --text-muted: #64748b;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --card-bg: rgba(30, 41, 59, 0.8);
            --card-border: #334155;
            --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1250px;
    }
    .hero-banner {
        background: var(--primary-gradient);
        color: white;
        padding: 2rem 2.2rem;
        border-radius: 18px;
        box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.3);
        margin-bottom: 1.5rem;
    }
    .hero-banner h1 {
        margin: 0;
        color: white !important;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .hero-banner p {
        margin: 0.4rem 0 0 0;
        opacity: 0.92;
        font-size: 1.05rem;
    }
    .metric-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        box-shadow: var(--card-shadow);
        transition: transform 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        font-weight: 600;
    }
    .metric-val {
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text-main);
        margin-top: 0.2rem;
    }
    .content-box {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 14px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--card-shadow);
    }
    .flashcard {
        background: var(--card-bg);
        border: 2px solid #6366f1;
        border-radius: 16px;
        padding: 2rem;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.12);
        margin: 1rem 0;
    }
    .flashcard-topic {
        display: inline-block;
        background: #e0e7ff;
        color: #4338ca;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    .flashcard-text {
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--text-main);
        line-height: 1.5;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-weak {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .badge-success {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 10px;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize application session state
ensure_state()

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.markdown("### ⚙️ Study Agent Setup")

    # API Key Management
    active_key = get_api_key()
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.get("user_api_key", "") or (active_key or ""),
        type="password",
        placeholder="Paste AIza... key",
        help="Optional if GOOGLE_API_KEY is already configured in .env",
    )
    if api_key_input:
        st.session_state.user_api_key = api_key_input.strip()

    is_key_valid = validate_api_key(get_api_key())
    if is_key_valid:
        st.success("API Key Active", icon="✅")
    else:
        st.warning("Valid API Key required", icon="⚠️")

    st.divider()
    st.markdown("### 📁 Study Material")
    uploaded = st.file_uploader(
        "Upload PDF document",
        type=["pdf"],
        help="Supports textbooks, notes, and slides",
    )
    manual_notes = st.text_area(
        "Or paste lecture notes",
        height=180,
        placeholder="Paste your course notes, articles, or transcripts here...",
    )

    st.divider()
    st.markdown("### 🧠 AI Model & Difficulty")
    available_models = get_available_models(get_api_key())
    default_env_model = os.getenv("GEMINI_MODEL_NAME", DEFAULT_MODEL)
    if available_models:
        default_idx = (
            available_models.index(default_env_model)
            if default_env_model in available_models
            else 0
        )
        model_name = st.selectbox(
            "Gemini Model", options=available_models, index=default_idx
        )
    else:
        model_name = st.text_input("Gemini Model", value=default_env_model)

    quiz_difficulty = st.selectbox(
        "Question Difficulty",
        ["Beginner", "Medium", "Hard"],
        index=1,
    )
    quiz_count = st.slider("Practice Quiz Questions", 3, 10, 5)
    exam_count = st.slider("Exam Mode Questions", 5, 20, 8)

    st.divider()
    st.markdown("### 🛠️ Study Agent Tools")
    beginner_mode = st.toggle(
        "Explain Like I'm 10 Mode",
        value=False,
        help="Simplifies explanations using vivid analogies and beginner-friendly language.",
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Clear Weak", use_container_width=True):
            st.session_state.weak_topics = []
            update_user_data()
            st.rerun()
    with col_btn2:
        if st.button("Reset All", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            update_user_data()
            st.rerun()

    # Export Study Profile
    export_payload = {
        "export_date": datetime.now().isoformat(),
        "source": st.session_state.get("source_name", "Untitled"),
        "weak_topics": st.session_state.get("weak_topics", []),
        "score_history": st.session_state.get("score_history", []),
        "summary": st.session_state.get("summary_text", ""),
        "revision_plan": st.session_state.get("revision_plan", ""),
        "revision_notes": st.session_state.get("revision_text", ""),
        "flashcards": st.session_state.get("flashcards", []),
    }
    st.download_button(
        label="📥 Export Study Profile",
        data=json.dumps(export_payload, indent=2),
        file_name="study_assistant_profile.json",
        mime="application/json",
        use_container_width=True,
    )

# ----------------- DOCUMENT EXTRACTION -----------------
source_text = ""
source_name = ""

if uploaded is not None:
    try:
        with st.spinner("📄 Parsing document pages..."):
            source_text = extract_text_from_pdf(uploaded)
        source_name = uploaded.name
    except Exception as exc:
        st.error(f"Failed to parse uploaded PDF: {exc}")

if manual_notes.strip():
    source_text = manual_notes.strip()
    source_name = "Pasted Notes"

if source_text:
    st.session_state.context_text = source_text
    st.session_state.source_name = source_name

context = st.session_state.context_text.strip()
is_ready = bool(context)

# ----------------- HERO HEADER -----------------
st.markdown(
    """
    <div class="hero-banner">
        <h1>📚 Smart Study Assistant Agent</h1>
        <p>Interactive AI tutor for notes synthesis, adaptive quiz generation, spaced recall flashcards, and exam preparation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not is_key_valid:
    st.info(
        "👋 Welcome! Please enter your **Google Gemini API Key** in the left sidebar "
        "or create a `.env` file with `GOOGLE_API_KEY=your_key` to start using the assistant.",
        icon="🔑",
    )

# ----------------- QUICK STATUS METRICS -----------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Active Document</div>
            <div class="metric-val">{html.escape(st.session_state.source_name or "None")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    word_count = len(context.split()) if context else 0
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Word Count</div>
            <div class="metric-val">{word_count:,} words</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Identified Weak Areas</div>
            <div class="metric-val">{len(st.session_state.weak_topics)} topics</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col4:
    recent_scores = st.session_state.get("score_history", [])
    avg_score = (
        int(sum(s["score_percent"] for s in recent_scores) / len(recent_scores))
        if recent_scores
        else 0
    )
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Average Score</div>
            <div class="metric-val">{f"{avg_score}%" if recent_scores else "N/A"}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ----------------- WORKSPACE TABS -----------------
(
    tab_qa,
    tab_quiz,
    tab_exam,
    tab_flashcards,
    tab_weak,
    tab_summary,
    tab_map,
    tab_progress,
) = st.tabs(
    [
        "💬 Ask Tutor",
        "📝 Practice Quiz",
        "🎓 Exam Mode",
        "🎴 Flashcards",
        "🧠 Weak Areas & Plan",
        "📄 Summary",
        "🗺️ Concept Map",
        "📈 Analytics",
    ]
)

# ----------------- TAB 1: ASK TUTOR -----------------
with tab_qa:
    st.subheader("💬 Ask Your AI Study Tutor")
    st.caption(
        "Ask questions about specific concepts, formulas, or themes in your notes."
    )

    if not is_ready:
        st.info(
            "Upload a PDF or paste lecture notes in the sidebar to activate the tutor."
        )

    # Conversational Chat History
    for entry in st.session_state.get("chat_history", []):
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            st.markdown(entry["answer"])

    user_q = st.chat_input(
        "Ask a question about your notes...", disabled=not is_ready or not is_key_valid
    )
    if user_q:
        if not user_q.strip():
            st.warning("Please type a question.")
        else:
            with st.chat_message("user"):
                st.write(user_q)
            with st.chat_message("assistant"):
                with st.spinner("🧠 Consulting notes and generating answer..."):
                    try:
                        ans = answer_question(
                            context=context,
                            question=user_q,
                            model_name=model_name,
                            beginner_mode=beginner_mode,
                            api_key=get_api_key(),
                        )
                        st.markdown(ans)
                        st.session_state.chat_history.append(
                            {"question": user_q, "answer": ans}
                        )
                    except Exception as exc:
                        st.error(f"Error answering question: {exc}")

    if st.session_state.get("chat_history"):
        if st.button("🧹 Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

    if is_ready:
        with st.expander("👀 View Loaded Text Preview"):
            st.code(split_notes_for_display(context), language="markdown")

# ----------------- TAB 2: PRACTICE QUIZ -----------------
with tab_quiz:
    st.subheader("📝 Adaptive Practice Quiz")
    st.caption(
        "Generate a randomized MCQ quiz. Each question provides instant feedback and saves missed topics."
    )

    if not is_ready:
        st.info("Upload notes to generate practice quizzes.")

    col_q1, col_q2 = st.columns([1, 1])
    with col_q1:
        if st.button(
            "Generate Practice Quiz",
            type="primary",
            disabled=not is_ready or not is_key_valid,
        ):
            with st.status("Creating quiz questions...", expanded=True) as status:
                try:
                    raw_items = generate_quiz(
                        context=context,
                        num_questions=quiz_count,
                        model_name=model_name,
                        exam_mode=False,
                        difficulty=quiz_difficulty,
                        api_key=get_api_key(),
                    )
                    st.session_state.quiz_items = shuffle_quiz_items(raw_items)
                    st.session_state.quiz_result = None
                    status.update(
                        label="Quiz created successfully!",
                        state="complete",
                        expanded=False,
                    )
                except Exception as exc:
                    status.update(label="Failed to generate quiz", state="error")
                    st.error(str(exc))
    with col_q2:
        if st.button("🔄 Regenerate Quiz", disabled=not is_ready or not is_key_valid):
            with st.status("Regenerating questions...", expanded=True) as status:
                try:
                    generate_quiz.clear()
                    raw_items = generate_quiz(
                        context=context,
                        num_questions=quiz_count,
                        model_name=model_name,
                        exam_mode=False,
                        difficulty=quiz_difficulty,
                        api_key=get_api_key(),
                    )
                    st.session_state.quiz_items = shuffle_quiz_items(raw_items)
                    st.session_state.quiz_result = None
                    status.update(
                        label="Quiz refreshed!", state="complete", expanded=False
                    )
                except Exception as exc:
                    status.update(label="Failed to refresh quiz", state="error")
                    st.error(str(exc))

    quiz_items = st.session_state.quiz_items
    if quiz_items:
        with st.form("quiz_form"):
            selected_answers = []
            for i, item in enumerate(quiz_items):
                st.markdown(
                    f"**Question {i+1}** <span class='badge badge-weak'>{html.escape(item.get('topic', 'General'))}</span>",
                    unsafe_allow_html=True,
                )
                st.write(item.get("question", ""))
                opts = item.get("options", [])
                ans = st.radio(
                    f"Options for Q{i+1}",
                    options=list(range(len(opts))),
                    format_func=lambda idx, o=opts: (
                        o[idx] if idx < len(o) else str(idx)
                    ),
                    key=f"practice_quiz_{i}",
                    label_visibility="collapsed",
                )
                selected_answers.append(ans)
                st.divider()

            submitted = st.form_submit_button("Submit Quiz", type="primary")
            if submitted:
                correct_count = 0
                wrong_items = []
                for item, sel in zip(quiz_items, selected_answers):
                    correct_idx = item.get("answer_index", 0)
                    if sel == correct_idx:
                        correct_count += 1
                    else:
                        wrong_items.append(item)

                record_weak_topics(quiz_items, selected_answers)
                score_pct = (
                    int((correct_count / len(quiz_items)) * 100) if quiz_items else 0
                )
                st.session_state.quiz_result = {
                    "score": correct_count,
                    "total": len(quiz_items),
                    "score_percent": score_pct,
                    "wrong_items": wrong_items,
                    "submitted_at": datetime.now().isoformat(timespec="seconds"),
                }
                add_score(
                    score_pct, "Quiz", correct=correct_count, total=len(quiz_items)
                )

    if st.session_state.quiz_result:
        res = st.session_state.quiz_result
        score_pct = res["score_percent"]
        color = (
            "#16a34a"
            if score_pct >= 70
            else ("#d97706" if score_pct >= 50 else "#dc2626")
        )

        st.markdown(
            f"""
            <div class="content-box" style="border-left: 6px solid {color};">
                <h3 style="margin: 0;">Quiz Performance Summary</h3>
                <p style="font-size: 1.5rem; font-weight: 700; color: {color}; margin: 0.5rem 0;">
                    {res['score']} / {res['total']} ({score_pct}%)
                </p>
                <p class="metric-label">Completed on: {res['submitted_at']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if res["wrong_items"]:
            st.markdown("#### 🔍 Review Missed Questions & Explanations")
            for w in res["wrong_items"]:
                st.markdown(f"**{w.get('question', '')}**")
                opts = w.get("options", [])
                ans_idx = w.get("answer_index", 0)
                if 0 <= ans_idx < len(opts):
                    st.success(f"Correct Answer: {opts[ans_idx]}")
                if w.get("explanation"):
                    st.info(f"💡 Explanation: {w['explanation']}")
                st.divider()

        # Quiz Results Export
        st.download_button(
            "📥 Download Quiz Results (JSON)",
            data=json.dumps(res, indent=2),
            file_name="quiz_results.json",
            mime="application/json",
        )

# ----------------- TAB 3: EXAM MODE -----------------
with tab_exam:
    st.subheader("🎓 Timed Exam Simulation")
    st.caption(
        "Strict test environment with hidden answers and an optional countdown timer."
    )

    if not is_ready:
        st.info("Upload notes to begin an Exam Mode session.")

    col_e1, col_e2 = st.columns([1, 1])
    with col_e1:
        if st.button(
            "Generate Exam", type="primary", disabled=not is_ready or not is_key_valid
        ):
            with st.status("Assembling exam questions...", expanded=True) as status:
                try:
                    raw_items = generate_quiz(
                        context=context,
                        num_questions=exam_count,
                        model_name=model_name,
                        exam_mode=True,
                        difficulty=quiz_difficulty,
                        api_key=get_api_key(),
                    )
                    st.session_state.exam_items = shuffle_quiz_items(raw_items)
                    st.session_state.exam_result = None
                    status.update(
                        label="Exam generated! Good luck.",
                        state="complete",
                        expanded=False,
                    )
                except Exception as exc:
                    status.update(label="Failed to generate exam", state="error")
                    st.error(str(exc))
    with col_e2:
        if st.button("🔄 Regenerate Exam", disabled=not is_ready or not is_key_valid):
            with st.status("Regenerating exam...", expanded=True) as status:
                try:
                    generate_quiz.clear()
                    raw_items = generate_quiz(
                        context=context,
                        num_questions=exam_count,
                        model_name=model_name,
                        exam_mode=True,
                        difficulty=quiz_difficulty,
                        api_key=get_api_key(),
                    )
                    st.session_state.exam_items = shuffle_quiz_items(raw_items)
                    st.session_state.exam_result = None
                    status.update(
                        label="Exam refreshed!", state="complete", expanded=False
                    )
                except Exception as exc:
                    status.update(label="Failed to refresh exam", state="error")
                    st.error(str(exc))

    exam_items = st.session_state.exam_items
    if exam_items:
        with st.form("exam_form"):
            st.info("Exam in progress. Answer all questions and press Submit Exam.")
            exam_answers = []
            for i, item in enumerate(exam_items):
                st.markdown(f"**Question {i+1}.** {item.get('question', '')}")
                opts = item.get("options", [])
                sel = st.radio(
                    f"Exam options {i+1}",
                    options=list(range(len(opts))),
                    format_func=lambda idx, o=opts: (
                        o[idx] if idx < len(o) else str(idx)
                    ),
                    key=f"exam_q_{i}",
                    label_visibility="collapsed",
                )
                exam_answers.append(sel)
                st.divider()

            submitted_exam = st.form_submit_button("Submit Exam", type="primary")
            if submitted_exam:
                correct_count = 0
                wrong_items = []
                for item, sel in zip(exam_items, exam_answers):
                    correct_idx = item.get("answer_index", 0)
                    if sel == correct_idx:
                        correct_count += 1
                    else:
                        wrong_items.append(item)

                record_weak_topics(exam_items, exam_answers)
                score_pct = (
                    int((correct_count / len(exam_items)) * 100) if exam_items else 0
                )
                st.session_state.exam_result = {
                    "score": correct_count,
                    "total": len(exam_items),
                    "score_percent": score_pct,
                    "wrong_items": wrong_items,
                    "submitted_at": datetime.now().isoformat(timespec="seconds"),
                }
                add_score(
                    score_pct, "Exam", correct=correct_count, total=len(exam_items)
                )

    if st.session_state.exam_result:
        res = st.session_state.exam_result
        score_pct = res["score_percent"]
        color = (
            "#16a34a"
            if score_pct >= 70
            else ("#d97706" if score_pct >= 50 else "#dc2626")
        )

        st.markdown(
            f"""
            <div class="content-box" style="border-left: 6px solid {color};">
                <h3 style="margin: 0;">Official Exam Scorecard</h3>
                <p style="font-size: 1.8rem; font-weight: 700; color: {color}; margin: 0.5rem 0;">
                    {res['score']} / {res['total']} ({score_pct}%)
                </p>
                <p class="metric-label">Completed on: {res['submitted_at']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if res["wrong_items"]:
            st.markdown("#### 🎯 Post-Exam Detailed Debrief")
            for w in res["wrong_items"]:
                st.markdown(f"**{w.get('question', '')}**")
                opts = w.get("options", [])
                ans_idx = w.get("answer_index", 0)
                if 0 <= ans_idx < len(opts):
                    st.success(f"Correct Answer: {opts[ans_idx]}")
                if w.get("explanation"):
                    st.caption(f"Reasoning: {w['explanation']}")
                st.divider()

        st.download_button(
            "📥 Download Exam Report (JSON)",
            data=json.dumps(res, indent=2),
            file_name="exam_results.json",
            mime="application/json",
        )

# ----------------- TAB 4: FLASHCARDS -----------------
with tab_flashcards:
    st.subheader("🎴 Spaced Recall Flashcards")
    st.caption("Active recall cards prioritizing your detected weak topics.")

    if not is_ready:
        st.info("Upload notes to generate flashcards.")

    col_fc1, col_fc2 = st.columns([1, 1])
    with col_fc1:
        if st.button(
            "Generate Flashcard Deck",
            type="primary",
            disabled=not is_ready or not is_key_valid,
        ):
            with st.spinner("Generating flashcards..."):
                try:
                    cards = generate_flashcards(
                        context=context,
                        weak_topics=st.session_state.weak_topics,
                        model_name=model_name,
                        count=8,
                        api_key=get_api_key(),
                    )
                    st.session_state.flashcards = cards
                    st.session_state.flashcard_idx = 0
                    st.session_state.flashcard_flipped = False
                    st.session_state.flashcard_mastered = []
                except Exception as exc:
                    st.error(f"Error generating flashcards: {exc}")

    cards = st.session_state.get("flashcards", [])
    if cards:
        idx = st.session_state.get("flashcard_idx", 0)
        if idx >= len(cards):
            idx = 0
            st.session_state.flashcard_idx = 0

        curr_card = cards[idx]
        is_flipped = st.session_state.get("flashcard_flipped", False)

        st.progress((idx + 1) / len(cards), text=f"Card {idx + 1} of {len(cards)}")

        # Display Card Face
        topic = curr_card.get("topic", "General")
        card_content = curr_card.get("back" if is_flipped else "front", "")
        side_label = "💡 Answer / Definition" if is_flipped else "❓ Question / Concept"

        st.markdown(
            f"""
            <div class="flashcard">
                <span class="flashcard-topic">{html.escape(topic)} • {side_label}</span>
                <div class="flashcard-text">{html.escape(card_content)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Card navigation buttons
        col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns(4)
        with col_ctrl1:
            if st.button("⏮️ Previous", disabled=idx == 0):
                st.session_state.flashcard_idx = idx - 1
                st.session_state.flashcard_flipped = False
                st.rerun()
        with col_ctrl2:
            flip_label = "🔄 Show Question" if is_flipped else "🔄 Flip Card (Reveal)"
            if st.button(flip_label, type="primary"):
                st.session_state.flashcard_flipped = not is_flipped
                st.rerun()
        with col_ctrl3:
            if st.button("⏭️ Next", disabled=idx >= len(cards) - 1):
                st.session_state.flashcard_idx = idx + 1
                st.session_state.flashcard_flipped = False
                st.rerun()
        with col_ctrl4:
            is_mastered = idx in st.session_state.get("flashcard_mastered", [])
            master_btn = "✅ Mastered" if not is_mastered else "↩️ Unmark"
            if st.button(master_btn):
                if is_mastered:
                    st.session_state.flashcard_mastered.remove(idx)
                else:
                    st.session_state.flashcard_mastered.append(idx)
                st.rerun()

        st.caption(
            f"Mastered: {len(st.session_state.get('flashcard_mastered', []))} / {len(cards)} cards"
        )

        st.download_button(
            "📥 Download Flashcard Deck (JSON)",
            data=json.dumps(cards, indent=2),
            file_name="flashcards.json",
            mime="application/json",
        )

# ----------------- TAB 5: WEAK AREAS & PLAN -----------------
with tab_weak:
    st.subheader("🧠 Weak Areas Tracker & Smart Revision Planner")
    st.caption(
        "Review difficult topics, customize your weak area list, and produce actionable study plans."
    )

    # Add custom topic
    col_add1, col_add2 = st.columns([4, 1])
    with col_add1:
        custom_topic = st.text_input(
            "Add a topic you find challenging",
            placeholder="e.g. Calvin Cycle, Bayes Theorem",
        )
    with col_add2:
        if st.button("Add Topic", disabled=not custom_topic.strip()):
            if custom_topic.strip() not in st.session_state.weak_topics:
                st.session_state.weak_topics.append(custom_topic.strip())
                update_user_data()
                st.rerun()

    if st.session_state.weak_topics:
        st.markdown("#### Tracked Weak Topics")
        for i, topic in enumerate(st.session_state.weak_topics):
            ct1, ct2 = st.columns([5, 1])
            with ct1:
                st.markdown(f"- ⚠️ **{html.escape(topic)}**")
            with ct2:
                if st.button("🗑️", key=f"del_weak_{i}"):
                    st.session_state.weak_topics.pop(i)
                    update_user_data()
                    st.rerun()
    else:
        st.info("No weak topics recorded yet. Take a quiz or add topics above!")

    st.divider()

    col_plan1, col_plan2 = st.columns(2)
    with col_plan1:
        st.markdown("#### 📅 Smart Revision Schedule")
        if st.button(
            "Generate 3-5 Day Study Plan",
            type="primary",
            disabled=not is_ready or not is_key_valid,
        ):
            with st.spinner("Building custom revision plan..."):
                try:
                    plan = generate_revision_plan(
                        context=context,
                        weak_topics=st.session_state.weak_topics,
                        model_name=model_name,
                        api_key=get_api_key(),
                    )
                    st.session_state.revision_plan = plan
                except Exception as exc:
                    st.error(f"Error creating revision plan: {exc}")

        if st.session_state.get("revision_plan"):
            st.markdown(st.session_state.revision_plan)
            st.download_button(
                "📥 Download Revision Plan (MD)",
                data=st.session_state.revision_plan,
                file_name="revision_plan.md",
                mime="text/markdown",
            )

    with col_plan2:
        st.markdown("#### 📝 High-Yield Revision Notes")
        if st.button(
            "Generate Condensed Notes", disabled=not is_ready or not is_key_valid
        ):
            with st.spinner("Synthesizing memory tricks & notes..."):
                try:
                    notes = generate_revision_notes(
                        context=context,
                        weak_topics=st.session_state.weak_topics,
                        model_name=model_name,
                        api_key=get_api_key(),
                    )
                    st.session_state.revision_text = notes
                except Exception as exc:
                    st.error(f"Error generating revision notes: {exc}")

        if st.session_state.get("revision_text"):
            st.markdown(st.session_state.revision_text)
            st.download_button(
                "📥 Download Revision Notes (MD)",
                data=st.session_state.revision_text,
                file_name="revision_notes.md",
                mime="text/markdown",
            )

# ----------------- TAB 6: SUMMARY -----------------
with tab_summary:
    st.subheader("📄 Executive Study Summary")
    st.caption(
        "Condense your lecture notes into high-level takeaways, core concepts, and definitions."
    )

    if not is_ready:
        st.info("Upload material to generate a study summary.")

    col_s1, col_s2 = st.columns([1, 1])
    with col_s1:
        if st.button(
            "Generate Summary",
            type="primary",
            disabled=not is_ready or not is_key_valid,
        ):
            with st.spinner("Summarizing notes..."):
                try:
                    st.session_state.summary_text = summarize_notes(
                        context, model_name=model_name, api_key=get_api_key()
                    )
                except Exception as exc:
                    st.error(f"Error generating summary: {exc}")
    with col_s2:
        if st.button(
            "🔄 Regenerate Summary", disabled=not is_ready or not is_key_valid
        ):
            with st.spinner("Refreshing summary..."):
                try:
                    summarize_notes.clear()
                    st.session_state.summary_text = summarize_notes(
                        context, model_name=model_name, api_key=get_api_key()
                    )
                except Exception as exc:
                    st.error(f"Error refreshing summary: {exc}")

    if st.session_state.get("summary_text"):
        st.markdown(st.session_state.summary_text)
        st.download_button(
            "📥 Download Summary (Markdown)",
            data=st.session_state.summary_text,
            file_name="study_summary.md",
            mime="text/markdown",
        )

# ----------------- TAB 7: CONCEPT MAP -----------------
with tab_map:
    st.subheader("🗺️ Visual Concept Map")
    st.caption(
        "Hierarchical mindmap diagram representing concepts and relationships in your notes."
    )

    if not is_ready:
        st.info("Upload notes to generate a visual concept map.")

    if st.button(
        "Generate Concept Mindmap",
        type="primary",
        disabled=not is_ready or not is_key_valid,
    ):
        with st.spinner("Diagramming knowledge concepts..."):
            try:
                st.session_state.mindmap_data = generate_mindmap_markdown(
                    context, model_name=model_name, api_key=get_api_key()
                )
            except Exception as exc:
                st.error(f"Failed to generate mindmap: {exc}")

    if st.session_state.get("mindmap_data"):
        st.markdown(f"```mermaid\n{st.session_state.mindmap_data}\n```")
        with st.expander("Show Raw Mermaid Code"):
            st.code(st.session_state.mindmap_data, language="mermaid")
        st.download_button(
            "📥 Download Mindmap (Mermaid)",
            data=st.session_state.mindmap_data,
            file_name="concept_map.mmd",
            mime="text/plain",
        )

# ----------------- TAB 8: ANALYTICS -----------------
with tab_progress:
    st.subheader("📈 Study Progress & Analytics")
    st.caption("Track your historical quiz and exam performance across study sessions.")

    history = st.session_state.get("score_history", [])
    if not history:
        st.info(
            "Complete practice quizzes or exam sessions to view your performance metrics."
        )
    else:
        import pandas as pd

        df = pd.DataFrame(history)
        df["date"] = pd.to_datetime(df["date"])

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Total Tests Taken", len(df))
        with col_m2:
            st.metric("Highest Score", f"{df['score_percent'].max()}%")
        with col_m3:
            st.metric("Average Score", f"{int(df['score_percent'].mean())}%")

        st.markdown("#### Performance Trend Over Time")
        st.line_chart(df.set_index("date")["score_percent"])

        st.markdown("#### Detailed Test Log")
        display_df = df.sort_values(by="date", ascending=False).copy()
        st.dataframe(
            display_df.style.format({"score_percent": "{:.0f}%"}),
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "📥 Export Progress (CSV)",
            data=df.to_csv(index=False),
            file_name="study_progress.csv",
            mime="text/csv",
        )

st.divider()
st.markdown(
    "<div style='text-align: center;' class='muted'>🚀 Smart Study Assistant Agent | Built for GenAI Academy</div>",
    unsafe_allow_html=True,
)
