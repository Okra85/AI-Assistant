import streamlit as st
from openai import OpenAI

# ✅ Create OpenAI client
client = OpenAI(api_key="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")  # ← Replace with your actual API key

st.set_page_config(page_title="Student Learning Assistant", layout="wide")
st.title("🧠 Student Learning Assistant")

# 🔁 Initialize session keys
for key in [
    "session_names", "session_data", "student_prompts", "engagement_scores",
    "session_goals", "goal_status", "session_reflection", "topic_vocab"
]:
    if key not in st.session_state:
        st.session_state[key] = {}

# ✅ Ensure session_names is a list
if "session_names" not in st.session_state or not isinstance(st.session_state.session_names, list):
    st.session_state.session_names = ["Default"]

# ✅ Initialize sessions
for name in st.session_state.session_names:
    st.session_state.session_data.setdefault(name, [{"role": "system", "content": "You are a thoughtful mentor."}])
    st.session_state.student_prompts.setdefault(name, [])
    st.session_state.engagement_scores.setdefault(name, 0)
    st.session_state.session_goals.setdefault(name, [])
    st.session_state.goal_status.setdefault(name, [])
    st.session_state.session_reflection.setdefault(name, "")
    st.session_state.topic_vocab.setdefault(name, {})

# 📂 Sidebar: Sessions + Goals + Summary
with st.sidebar:
    st.header("🧵 Session Manager")
    selected_session = st.selectbox("Choose session:", st.session_state.session_names)

    new_session = st.text_input("Start new session:")
    if new_session and new_session not in st.session_state.session_names:
        st.session_state.session_names.append(new_session)
        st.session_state.session_data[new_session] = [{"role": "system", "content": "You are a thoughtful mentor."}]
        st.session_state.student_prompts[new_session] = []
        st.session_state.engagement_scores[new_session] = 0
        st.session_state.session_goals[new_session] = []
        st.session_state.goal_status[new_session] = []
        st.session_state.session_reflection[new_session] = ""
        st.session_state.topic_vocab[new_session] = {}
        st.rerun()

    st.subheader("🎯 Goals & Score")
    goals = st.session_state.session_goals[selected_session]
    goal_status = st.session_state.goal_status[selected_session]
    for i, goal in enumerate(goals):
        st.write(f"{'✔️' if goal_status[i] else '❌'} {goal}")

    score = st.session_state.engagement_scores[selected_session]
    st.metric("Reflective Engagement Score", f"{score}/100")
    st.progress(score / 100 if isinstance(score, (int, float)) else 0)

    st.subheader("📘 Generate Summary")
    if st.button("🪞 Create Reflection Summary"):
        summary_prompt = f"""
Student Prompts:\n{st.session_state.student_prompts[selected_session]}\n
Goals:\n{goals}\n
Goal Status:\n{goal_status}\n
Engagement Score:\n{score}\n\n
Write a 3–5 sentence reflection on self-reliance, authentic learning, legacy, and ethical growth. Offer one next step.
"""
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": summary_prompt}]
            )
            st.session_state.session_reflection[selected_session] = response.choices[0].message.content.strip()
        except Exception as e:
            st.session_state.session_reflection[selected_session] = f"⚠️ Error: {str(e)}"

    if st.session_state.session_reflection[selected_session]:
        st.markdown("#### 📘 Assistant Reflection")
        st.markdown(st.session_state.session_reflection[selected_session])

# 🧠 Goal Setup
if not st.session_state.session_goals[selected_session]:
    st.subheader("🌱 Set Goals")
    g1, g2, g3 = st.text_input("Goal 1"), st.text_input("Goal 2"), st.text_input("Goal 3")
    if st.button("Save Goals"):
        new_goals = [g for g in [g1, g2, g3] if g]
        st.session_state.session_goals[selected_session] = new_goals
        st.session_state.goal_status[selected_session] = [False] * len(new_goals)
        st.rerun()

# 🧠 Layout: Chat (left) + Vocabulary (right)
chat_col, vocab_col = st.columns([3, 1])

with chat_col:
    messages = st.session_state.session_data[selected_session]
    for msg in messages[1:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask a question or reflect…")
    if prompt:
        st.chat_message("user").markdown(prompt)
        messages.append({"role": "user", "content": prompt})
        st.session_state.student_prompts[selected_session].append(prompt)

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            reply = f"⚠️ Error: {e}"

        st.chat_message("assistant").markdown(reply)
        messages.append({"role": "assistant", "content": reply})

        # 📊 Engagement Score
        try:
            score_prompt = f"Rate this question from 0 to 100 for depth, curiosity, and ethical reflection.\n\n{prompt}"
            score_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": score_prompt}]
            )
            new_score = int(score_response.choices[0].message.content.strip())
            prompts = st.session_state.student_prompts[selected_session]
            average = int((st.session_state.engagement_scores[selected_session] * (len(prompts) - 1) + new_score) / len(prompts))
            st.session_state.engagement_scores[selected_session] = average
        except:
            pass

        # ✅ Goal Check
        try:
            goal_prompt = f"Goals:\n{goals}\nPrompt:\n{prompt}\nWhich goals are achieved? Return list of indices."
            goal_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": goal_prompt}]
            )
            achieved = eval(goal_response.choices[0].message.content.strip())
            for i in achieved:
                if 0 <= i < len(goal_status):
                    st.session_state.goal_status[selected_session][i] = True
        except:
            pass

        # 📘 Topic Detection + Vocabulary Scaffold
        try:
            topic_prompt = f"What academic topic or concept is explored in this question?\n\n{prompt}"
            topic_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": topic_prompt}]
            )
            topic = topic_response.choices[0].message.content.strip()

            vocab_prompt = f"List 5 key academic vocabulary terms related to {topic}, with short beginner-friendly definitions. Return as a Python dictionary."
            vocab_response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": vocab_prompt}]
            )
            vocab_dict = eval(vocab_response.choices[0].message.content.strip())
            st.session_state.topic_vocab[selected_session] = vocab_dict
        except:
            st.session_state.topic_vocab[selected_session] = {}

with vocab_col:
    st.markdown("### 📚 Vocabulary")
    vocab = st.session_state.topic_vocab[selected_session]
    if vocab:
        for term, definition in vocab.items():
            st.markdown(f"**{term}**: {definition}")
    else:
        st.caption("Vocabulary will appear after your next prompt.")