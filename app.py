import os
import json
import random
import logging
from typing import Dict, Any

from PyPDF2 import PdfReader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import Runnable
from langchain_community.chat_message_histories import ChatMessageHistory

import streamlit as st

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ADMIN_USERNAME = "AliKhaled"
ADMIN_DATA_FILE = "admin_data.json"

GEMINI_API_KEY = "AIzaSyDa4DFQBisGwGpmHg3FJgk3wAnx4ttG3t0"  # Replace with your actual API key
if not GEMINI_API_KEY:
    GEMINI_API_KEY = "AIzaSyDa4DFQBisGwGpmHg3FJgk3wAnx4ttG3t0"
cv_text = "السيرة الذاتية غير متوفرة حاليًا. 📄"
try:
    pdf_reader = PdfReader('Ali Khalid Ali Khalid  CV_last.pdf')
    cv_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
except FileNotFoundError:
    logger.warning("CV file not found!")
except Exception as e:
    logger.error(f"Error reading CV file: {str(e)}")

llm = None
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.4,
        api_key=GEMINI_API_KEY
    )
except Exception as e:
    logger.error(f"Error setting up Gemini API: {str(e)}")

prompt = ChatPromptTemplate.from_messages([
    ("system",
     f"""انتِ اسيستنت ذكية شغالة بالنيابة عن علي خالد. 😊
مهمتك تردي على أي سؤال عن علي أو تساعدي في المهام العامة.
لو حد جديد دخل، اسأليه عن اسمه وسنه وعلاقته بعلي وسجّلي البيانات، ومتسأليهاش تاني.
وهتكلميهم بأي لغة هم يتكلموا بيها وكمان حطي إيموجي وخلّي تصرفك لطيف! 🥰
لو حد سأل عن علي، قولي إنه اسمه علي خالد وعنده سيرة ذاتية موجودة في ملف PDF.
لو حد سأل عن مكانه، قولي إنه في مكانه الحالي.
وإنتِ اسمك إليسا، يعني أنثى، فخلّيكي رقيقة. 🌸
السيرة الذاتية لعلي:\n\n{cv_text}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{user_input}")
])

chain: Runnable = prompt | llm if llm else None

def generate_user_id(relation: str):
    if relation in ["حبيبتي", "فاطمه", "امي", "ابويا", "اخويا", "زوجتي"]:
        return str(random.randint(100, 999))
    elif relation in ["خالتي", "عمي", "صديقي", "صاحبتي"]:
        return str(random.randint(1000, 9999))
    else:
        return str(random.randint(10000, 99999))

def load_user_data(username: str) -> Dict[str, Any]:
    folder = "users_data"
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{username}.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_user_data(username: str, data: Dict[str, Any]):
    folder = "users_data"
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{username}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_session_history_streamlit(session_id: str) -> ChatMessageHistory:
    if "chat_message_history" not in st.session_state:
        st.session_state.chat_message_history = {}
    if session_id not in st.session_state.chat_message_history:
        history = ChatMessageHistory()
        st.session_state.chat_message_history[session_id] = history
    return st.session_state.chat_message_history[session_id]

def save_chat_history_streamlit(session_id: str, history: ChatMessageHistory):
    pass

def load_admin_data() -> Dict[str, str]:
    if not os.path.exists(ADMIN_DATA_FILE):
        return {}
    try:
        with open(ADMIN_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def update_admin_data(key: str, value: str):
    data = load_admin_data()
    data[key] = value
    with open(ADMIN_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_user_input(user_input: str, username: str):
    if not user_input.strip():
        return "عذرًا، أرسل رسالة صحيحة لأساعدك! 😊"
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(random.randint(100000, 999999))
    session_id = st.session_state.session_id
    user_data = load_user_data(username)
    if "is_new_user" not in user_data:
        user_data["is_new_user"] = True
        save_user_data(username, user_data)
        return f"مرحبًا {username}! يسرني نتعرف. أنا إليسا، مساعدة علي خالد. ممكن تقولي اسمك وسنك وعلاقتك بعلي؟ 🤝"
    if username == ADMIN_USERNAME:
        lowered = user_input.lower()
        if lowered.startswith("مكاني:"):
            update_admin_data("location", user_input.split(":", 1)[1].strip())
            return "✅ تم تحديث مكانك الحالي."
        elif lowered.startswith("حالتي:"):
            update_admin_data("status", user_input.split(":", 1)[1].strip())
            return "✅ تم تحديث حالتك الحالية."
        elif lowered.startswith("اسمي:"):
            update_admin_data("name", user_input.split(":", 1)[1].strip())
            return "✅ تم تحديث اسمك."
    lower_input = user_input.lower()
    admin_data = load_admin_data()
    name = admin_data.get("name", "علي خالد")
    location = admin_data.get("location", "غير معروف")
    status = admin_data.get("status", "غير محددة")
    if any(x in lower_input for x in ["فين علي", "مكان علي", "علي فين", "اين علي"]):
        return f"{name} حالياً موجود في: 📍 {location}"
    elif any(x in lower_input for x in ["عامل ايه علي", "اخبار علي", "حالته ايه", "كيف حال علي"]):
        return f"{name} حالته دلوقتي: 💬 {status}"
    if not chain:
        return "عذرًا، مشكلة في الاتصال بالخدمة! 😔 حاول مرة أخرى لاحقًا."
    chat_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history_streamlit,
        input_messages_key="user_input",
        history_messages_key="history"
    )
    try:
        response = chat_with_history.invoke(
            {"user_input": user_input},
            config={"configurable": {"session_id": session_id}}
        )
        return response.content if hasattr(response, 'content') else "لا يوجد رد من الخدمة 😔"
    except Exception as e:
        return f"عذرًا، حدث خطأ: {str(e)} 😔"

st.set_page_config(page_title="Elissa AI Assistant")
st.title("🤖 Elissa AI Assistant")
st.write("مرحبًا بك! أنا إليسا، مساعدة علي خالد الشخصية. اسألني عن علي أو أي شيء آخر يمكنني المساعدة فيه! 😊")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

default_username = "Guest"
username_input = st.sidebar.text_input("Enter your username:", value=default_username)
current_username = username_input if username_input else default_username

st.sidebar.markdown("---")
st.sidebar.header("Admin Commands (if logged in as AliKhaled)")
st.sidebar.markdown(f"**Current User:** `{current_username}`")
if current_username == ADMIN_USERNAME:
    st.sidebar.markdown("- `مكاني: [المكان الجديد]`")
    st.sidebar.markdown("- `حالتي: [الحالة الجديدة]`")
    st.sidebar.markdown("- `اسمي: [الاسم الجديد]`")

if prompt := st.chat_input("كيف يمكنني مساعدتك؟"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Elissa is thinking..."):
            response = process_user_input(prompt, current_username)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

if not st.session_state.messages:
    initial_response = process_user_input("", current_username)
    st.session_state.messages.append({"role": "assistant", "content": initial_response})
    st.rerun()

