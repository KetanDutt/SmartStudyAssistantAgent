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
    @media (max-width: 768px) {
        .block-container {padding-top: 0.5rem; padding-left: 0.5rem; padding-right: 0.5rem;}
        div[data-baseweb="tab-list"] { overflow-x: auto; flex-wrap: nowrap; }
    }
    .hero {
        padding: 1.25rem 1.4rem;
        border-radius: 22px;
        background: var(--secondary-background-color);
        border: 1px solid var(--secondary-background-color);
        margin-bottom: 1rem;
        color: var(--text-color);
    }
    .mini-card {
        padding: 1rem 1rem;
        border-radius: 18px;
        border: 1px solid var(--secondary-background-color);
        background: var(--background-color);
        color: var(--text-color);
    }
    .result-card {
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid var(--secondary-background-color);
        background: var(--background-color);
        margin-top: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        color: var(--text-color);
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: var(--text-color);
    }
    .muted {
        color: var(--text-color);
        opacity: 0.7;
        font-size: 0.95rem;
    }
    button[data-baseweb="tab"]:active,
    button[data-baseweb="tab"][aria-selected="true"] {
        background: var(--secondary-background-color);
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

from app.handlers import (
    ensure_state,
    update_user_data,
    record_weak_topics,
    shuffle_quiz_items,
    add_score,
)

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
    model_name = st.text_input("Model name", value=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"))
    quiz_count = st.slider("Quiz questions", 3, 10, 5)
    exam_count = st.slider("Exam questions", 5, 15, 8)
    st.divider()
    beginner_mode = st.toggle("Explain Like I'm 10 Mode", value=False, help="Simplify explanations and examples")
    st.divider()
    st.caption("Tip: keep the notes concise for faster generation.")

    st.divider()
    st.header("Study Tools")
    if st.button("🗑️ Clear all weak topics"):
        st.session_state.weak_topics = []
        update_user_data()
        st.rerun()

    import json
    export_data = {
        "weak_topics": st.session_state.get("weak_topics", []),
        "score_history": st.session_state.get("score_history", []),
        "summary": st.session_state.get("summary_text", ""),
        "revision_plan": st.session_state.get("revision_plan", ""),
        "revision_notes": st.session_state.get("revision_text", ""),
    }
    st.download_button(
        label="📥 Export All Data",
        data=json.dumps(export_data, indent=2),
        file_name="study_agent_export.json",
        mime="application/json"
    )

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
    st.markdown("""
    <div class="result-card" style="text-align: center;">
        <h2>📄 Upload your notes to get started</h2>
        <p class="muted">You can:</p>
        <p>• Ask questions 🔍</p>
        <p>• Generate quizzes 📝</p>
        <p>• Track weak areas 🧠</p>
    </div>
    """, unsafe_allow_html=True)

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

tabs = st.tabs(["🔍 Ask", "📝 Quiz", "🎓 Exam Mode", "🧠 Weak Areas", "📄 Summary", "📈 Progress"])

with tabs[0]:
    st.markdown("<div class='section-header' title='Get personalized answers based on your notes'>Ask questions about your notes</div>", unsafe_allow_html=True)
    if not is_ready:
        st.info("Upload a PDF to start asking questions.")

    question = st.text_input("Your question", placeholder="Explain photosynthesis in simple words...", disabled=not is_ready)
    if st.button("Get answer", type="primary", disabled=not is_ready):
        if not question.strip():
            st.warning("Type a question first.")
        else:
            with st.spinner("🧠 Analyzing your notes..."):
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
    st.markdown("<div class='section-header' title='Test your knowledge with auto-generated quizzes'>Quiz mode</div>", unsafe_allow_html=True)
    st.caption("Generate a practice quiz with answers and explanations.")

    if not is_ready:
        st.info("Upload a PDF to generate a quiz.")

    if st.button("Generate quiz", type="primary", disabled=not is_ready):
        with st.status("📚 Creating quiz questions...", expanded=True) as status:
            try:
                raw_items = generate_quiz(
                    context=context,
                    num_questions=quiz_count,
                    model_name=model_name,
                    exam_mode=False,
                )
                st.session_state.quiz_items = shuffle_quiz_items(raw_items)
                st.session_state.quiz_result = None
                status.update(label="Quiz generated!", state="complete", expanded=False)
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
            if len(quiz_items) > 0:
                add_score(int((correct_count / len(quiz_items)) * 100), "quiz")
            update_user_data()

    if st.button("🔄 Regenerate quiz", disabled=not is_ready, key="regen_quiz"):
        with st.status("📚 Creating quiz questions...", expanded=True) as status:
            try:
                generate_quiz.clear()
                raw_items = generate_quiz(
                    context=context,
                    num_questions=quiz_count,
                    model_name=model_name,
                    exam_mode=False,
                )
                st.session_state.quiz_items = shuffle_quiz_items(raw_items)
                st.session_state.quiz_result = None
                status.update(label="Quiz regenerated!", state="complete", expanded=False)
            except Exception as exc:
                with st.expander("❌ Error details", expanded=True):
                    st.error(str(exc))
                    st.caption("Try using a shorter question or check your API key.")

    if st.session_state.quiz_result:
        result = st.session_state.quiz_result
        score_percent = int((result['score'] / result['total']) * 100) if result['total'] > 0 else 0
        weak_topic_counts = {}
        for item in result.get('wrong_items', []):
            topic = item.get('topic', 'General')
            weak_topic_counts[topic] = weak_topic_counts.get(topic, 0) + 1

        weak_topic_html = ""
        if weak_topic_counts:
            weak_topic_html = "<h4>You are weak in:</h4><ul>"
            for topic, count in weak_topic_counts.items():
                weak_topic_html += f"<li>⚠️ {topic} ({count} mistakes)</li>"
            weak_topic_html += "</ul>"

        st.markdown(f"""
        <div class="result-card">
            <h3 style="margin-top:0;">Performance Dashboard</h3>
            <p style="font-size:1.2rem; font-weight:bold; color:{'#4caf50' if score_percent >= 50 else '#e53935'}">
                Score: {result['score']} / {result['total']} ({score_percent}%)
            </p>
            {weak_topic_html}
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
    st.markdown("<div class='section-header' title='Practice real test conditions where answers stay hidden'>Exam mode</div>", unsafe_allow_html=True)
    st.caption("Practice like a real test: answers stay hidden until submission.")

    if not is_ready:
        st.info("Upload a PDF to practice Exam Mode.")

    if st.button("Generate exam", type="primary", disabled=not is_ready):
        with st.status("🎓 Generating exam...", expanded=True) as status:
            try:
                raw_items = generate_quiz(
                    context=context,
                    num_questions=exam_count,
                    model_name=model_name,
                    exam_mode=True,
                )
                st.session_state.exam_items = shuffle_quiz_items(raw_items)
                st.session_state.exam_result = None
                status.update(label="Exam generated!", state="complete", expanded=False)
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
            if len(exam_items) > 0:
                add_score(int((correct_count / len(exam_items)) * 100), "exam")
            update_user_data()

    if st.button("🔄 Regenerate exam", disabled=not is_ready, key="regen_exam"):
        with st.status("🎓 Generating exam...", expanded=True) as status:
            try:
                generate_quiz.clear()
                raw_items = generate_quiz(
                    context=context,
                    num_questions=exam_count,
                    model_name=model_name,
                    exam_mode=True,
                )
                st.session_state.exam_items = shuffle_quiz_items(raw_items)
                st.session_state.exam_result = None
                status.update(label="Exam regenerated!", state="complete", expanded=False)
            except Exception as exc:
                with st.expander("❌ Error details", expanded=True):
                    st.error(str(exc))
                    st.caption("Try using a shorter question or check your API key.")

    if st.session_state.exam_result:
        result = st.session_state.exam_result
        score_percent = int((result['score'] / result['total']) * 100) if result['total'] > 0 else 0
        weak_topic_counts = {}
        for item in result.get('wrong_items', []):
            topic = item.get('topic', 'General')
            weak_topic_counts[topic] = weak_topic_counts.get(topic, 0) + 1

        weak_topic_html = ""
        if weak_topic_counts:
            weak_topic_html = "<h4>You are weak in:</h4><ul>"
            for topic, count in weak_topic_counts.items():
                weak_topic_html += f"<li>⚠️ {topic} ({count} mistakes)</li>"
            weak_topic_html += "</ul>"

        st.markdown(f"""
        <div class="result-card">
            <h3 style="margin-top:0;">Performance Dashboard</h3>
            <p style="font-size:1.2rem; font-weight:bold; color:{'#4caf50' if score_percent >= 50 else '#e53935'}">
                Score: {result['score']} / {result['total']} ({score_percent}%)
            </p>
            {weak_topic_html}
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
    st.markdown("<div class='section-header' title='Track incorrect answers and focus your revision'>Weak areas tracker & Smart Revision Planner</div>", unsafe_allow_html=True)
    st.caption("Topics from incorrect answers are saved here. Use them to generate a structured study plan.")

    if st.session_state.weak_topics:
        st.markdown("#### Your current weak topics:")
        for i, topic in enumerate(st.session_state.weak_topics):
            col_topic, col_del = st.columns([5, 1])
            with col_topic:
                st.markdown(f"- {topic}")
            with col_del:
                if st.button("🗑️", key=f"del_topic_{i}"):
                    st.session_state.weak_topics.pop(i)
                    update_user_data()
                    st.rerun()
    else:
        st.info("Your weak topics will appear here after you submit a quiz or exam.")

    col_rp1, col_rp2 = st.columns([1, 1])
    with col_rp1:
        if st.button("Generate Smart Revision Plan", type="primary", disabled=not is_ready or not st.session_state.weak_topics):
            with st.spinner("⚡ Generating insights..."):
                try:
                    st.session_state.revision_plan = generate_revision_plan(
                        context=context,
                        weak_topics=st.session_state.weak_topics,
                        model_name=model_name,
                    )
                except Exception as exc:
                    with st.expander("❌ Error details", expanded=True):
                        st.error(str(exc))
    with col_rp2:
        if st.button("🔄 Regenerate Plan", disabled=not is_ready or not st.session_state.weak_topics):
            with st.spinner("⚡ Generating insights..."):
                try:
                    generate_revision_plan.clear()
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
        st.download_button(
            "📥 Download Revision Plan",
            st.session_state.revision_plan,
            file_name="revision_plan.md",
            mime="text/markdown"
        )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate quick revision notes", disabled=not is_ready):
            with st.spinner("⚡ Generating insights..."):
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
            st.download_button(
                "📥 Download Revision Notes",
                st.session_state.revision_text,
                file_name="revision_notes.md",
                mime="text/markdown"
            )

    with col2:
        if st.button("📇 Create flashcards", disabled=not is_ready):
            with st.spinner("Generating flashcards..."):
                try:
                    generate_flashcards.clear()
                    st.session_state.flashcards = generate_flashcards(context, st.session_state.weak_topics, model_name)
                    if not st.session_state.flashcards:
                        st.warning("Could not generate flashcards.")
                except Exception as exc:
                    with st.expander("❌ Error details", expanded=True):
                        st.error(str(exc))
                        st.caption("Try using a shorter question or check your API key.")

        if hasattr(st.session_state, 'flashcards') and st.session_state.flashcards:
            for i, card in enumerate(st.session_state.flashcards):
                st.markdown(f"**📌 {card.get('front', 'Flashcard')}**")
                if st.checkbox("Click to reveal answer", key=f"flashcard_{i}"):
                    st.markdown(f"<div style='padding: 10px; border-left: 3px solid var(--primary-color); margin-left: 10px; background: var(--secondary-background-color); border-radius: 5px; color: var(--text-color);'>{card.get('back', '')}</div>", unsafe_allow_html=True)
                st.divider()

            flashcards_json = json.dumps(st.session_state.flashcards, indent=2)
            st.download_button("📥 Download Flashcards", flashcards_json, file_name="flashcards.json", mime="application/json")

with tabs[4]:
    st.markdown("<div class='section-header' title='Get a high-level overview of your material'>Quick summary</div>", unsafe_allow_html=True)
    if not is_ready:
        st.info("Upload a PDF to view a quick summary.")

    col_sum1, col_sum2 = st.columns([1, 1])
    with col_sum1:
        if st.button("Summarize notes", type="primary", disabled=not is_ready):
            with st.spinner("⚡ Generating insights..."):
                try:
                    st.session_state.summary_text = summarize_notes(context, model_name=model_name)
                except Exception as exc:
                    with st.expander("❌ Error details", expanded=True):
                        st.error(str(exc))
                        st.caption("Try using a shorter question or check your API key.")
    with col_sum2:
        if st.button("🔄 Regenerate summary", disabled=not is_ready):
            with st.spinner("⚡ Generating insights..."):
                try:
                    summarize_notes.clear()
                    st.session_state.summary_text = summarize_notes(context, model_name=model_name)
                except Exception as exc:
                    with st.expander("❌ Error details", expanded=True):
                        st.error(str(exc))
                        st.caption("Try using a shorter question or check your API key.")
    if st.session_state.summary_text:
        st.write(st.session_state.summary_text)
        st.download_button("📥 Download summary", st.session_state.summary_text, file_name="summary.md", mime="text/markdown")

with tabs[5]:
    st.markdown("<div class='section-header' title='Track your scores over time'>Study Progress</div>", unsafe_allow_html=True)
    if not st.session_state.get("score_history"):
        st.info("Take a quiz or exam to see your progress here.")
    else:
        import pandas as pd
        df = pd.DataFrame(st.session_state.score_history)
        # Convert isoformat back to datetime for display
        df['date'] = pd.to_datetime(df['date'])

        st.markdown("#### Score History")
        st.line_chart(df.set_index("date")["score_percent"])

        st.markdown("#### Recent Results")
        st.dataframe(
            df.sort_values(by="date", ascending=False).style.format({"score_percent": "{:.0f}%"}),
            use_container_width=True,
            hide_index=True
        )

st.divider()
st.markdown("<div style='text-align: center;' class='muted'>🚀 Built with Google Gemini | GenAI Academy 2026 Project</div>", unsafe_allow_html=True)
