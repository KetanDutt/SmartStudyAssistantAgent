# Feature Guide & User Manual

Welcome to the **Smart Study Assistant Agent**! This guide walks you through every feature and shows how to get the most out of your study sessions.

---

## 1. Setting Up Your Material

1. **Configure Gemini API Key**:
   - In the sidebar, enter your Google Gemini API key or supply it in `.env` as `GOOGLE_API_KEY=your_key`.
   - The status badge will show `API Key Active ✅`.
2. **Upload Study Material**:
   - Drag & drop any PDF document (lecture notes, textbooks, slides).
   - Or paste raw lecture notes into the text box.
3. **Configure Model & Settings**:
   - Choose your desired Gemini model (e.g. `gemini-2.5-flash-lite`, `gemini-2.0-flash`).
   - Select quiz difficulty: `Beginner`, `Medium`, or `Hard`.
   - Toggle **Explain Like I'm 10 Mode** if you want simpler analogies.

---

## 2. Interactive Study Features

### 💬 1. Ask Tutor (Conversational Q&A)
- Have an interactive dialogue with your AI tutor.
- The tutor answers strictly from your notes to avoid hallucinations.
- Every response ends with a **Confidence Score** (High / Medium / Low).
- Chat history persists across questions during the session.

### 📝 2. Practice Quiz
- Generate 3 to 10 multiple-choice questions.
- Questions test comprehension rather than mere rote memorization.
- Submit the quiz to view your score, missed items, and clear explanations.
- Any missed topics are automatically added to your **Weak Areas Tracker**.

### 🎓 3. Timed Exam Mode
- Simulates real test conditions.
- Answers and explanations remain hidden until full submission.
- Generates 5 to 20 questions across all topics.
- Exports a complete Exam Report in JSON format.

### 🎴 4. Spaced Recall Flashcards
- Generate an active recall flashcard deck.
- The deck prioritizes your identified weak topics.
- Flip cards to reveal answers, mark cards as **Mastered**, and track retention.
- Export your deck in JSON for Anki or offline study.

### 🧠 5. Weak Areas Tracker & Smart Revision Plan
- View all topics flagged from incorrect quiz and exam answers.
- Add challenging topics manually or delete mastered ones.
- **Smart Revision Plan**: Generates a 3–5 day step-by-step timetable with daily objectives, topics, and practice tasks.
- **High-Yield Revision Notes**: Creates condensed notes with mnemonics, analogies, and checklists.

### 📄 6. Executive Summary
- Produces a structured 5-part summary of your notes: core thesis, 5 key takeaways, essential definitions, principles, and a self-check question.

### 🗺️ 7. Visual Concept Map
- Synthesizes the core hierarchy of the study material into a visual Mermaid mindmap diagram.
- Download the `.mmd` file or inspect the tree structure.

### 📈 8. Study Analytics & Progress
- Displays total tests taken, highest score, and overall average.
- Visual line chart tracking score trends over time.
- Downloadable study log as CSV.

---

## 3. Data Export & Privacy

- Click **Export Study Profile** in the sidebar to backup your weak topics, revision plan, flashcards, and quiz history.
- Everything runs locally or within your private cloud instance; no study notes are stored externally.
