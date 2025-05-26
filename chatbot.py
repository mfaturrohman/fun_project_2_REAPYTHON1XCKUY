import streamlit as st
import requests
from datetime import datetime
import uuid
import json
import os

# ========== Title halaman ==========
st.set_page_config(page_title="Multi Model Chatbot", page_icon="🧠")

# ========== Konstanta ==========
FILE_SESSION = "sessions_data.json"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ========== Fungsi untuk menyimpan dan memuat sesi ==========

# Menyimpan semua sesi ke file JSON
def save_sessions_to_file(sessions):
    with open(FILE_SESSION, "w", encoding="utf-8") as f:
        json.dump(sessions, f, default=str, ensure_ascii=False, indent=2)

# Memuat sesi dari file JSON jika tersedia
def load_sessions_from_file():
    if os.path.exists(FILE_SESSION):
        with open(FILE_SESSION, "r", encoding="utf-8") as f:
            data = json.load(f)
        for sid, session in data.items():
            # Konversi string timestamp ke objek datetime
            if "created" in session:
                try:
                    session["created"] = datetime.fromisoformat(session["created"])
                except Exception:
                    pass
        return data
    return {}

# ========== Inisialisasi session_state ==========

# Inisialisasi data sesi jika belum ada
if "sessions" not in st.session_state:
    st.session_state.sessions = load_sessions_from_file()

# Buat sesi baru jika tidak ada sesi sama sekali
if not st.session_state.sessions:
    sid = str(uuid.uuid4())
    st.session_state.sessions[sid] = {
        "title": "Sesi Baru",
        "created": datetime.now(),
        "messages": []
    }
    st.session_state.current_sid = sid

# Tetapkan sesi aktif pertama kali jika belum ada
if "current_sid" not in st.session_state:
    st.session_state.current_sid = list(st.session_state.sessions.keys())[0]

# Siapkan variabel api_key
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# ========== Fungsi utilitas ==========

# Menyiapkan header permintaan API
def get_headers():
    return {
        "Authorization": f"Bearer {st.session_state.api_key}",
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "AI Chatbot Streamlit",
        "Content-Type": "application/json"
    }

# Update judul sesi dengan isi pesan pertama dari user
def update_title_first_user_message(sid):
    session = st.session_state.sessions[sid]
    if session["title"] == "Sesi Baru":
        for msg in session["messages"]:
            if msg["role"] == "user":
                new_title = msg["content"][:30] + ("..." if len(msg["content"]) > 30 else "")
                session["title"] = new_title
                break

# ========== Sidebar ==========
st.sidebar.title("💬 Riwayat Chat")

# Input API Key pengguna
st.sidebar.markdown("#### 🔑 API Key OpenRouter")
st.sidebar.markdown("###### Lihat tutorial: https://youtu.be/-X9DVzzxpAA?si=I_854UoseHS8VnnH")
st.session_state.api_key = st.sidebar.text_input(
    "Masukkan API Key kamu:",
    value=st.session_state.api_key,
    type="password",
    placeholder="sk-or-..."
)

# Dropdown model AI
AVAILABLE_MODELS = {
    "Mistral 7B": "mistralai/mistral-7b-instruct:free",
    "Deepseek v3-0324": "deepseek/deepseek-chat-v3-0324:free",
}

if "selected_model" not in st.session_state:
    st.session_state.selected_model = list(AVAILABLE_MODELS.values())[0]

selected_model_name = st.sidebar.selectbox("🧠 Pilih Model AI", list(AVAILABLE_MODELS.keys()))
MODEL = AVAILABLE_MODELS[selected_model_name]
st.sidebar.markdown("---")

# Daftar sesi dengan opsi pengaturan
to_delete = None
for sid, session in st.session_state.sessions.items():
    title = session["title"]
    is_current = (sid == st.session_state.current_sid)
    with st.sidebar.container():
        col1, col2 = st.columns([8, 1])
        display_title = f"👉 {title}" if is_current else title

        # Tombol pilih sesi
        if col1.button(display_title, key="select_" + sid):
            st.session_state.current_sid = sid
            st.rerun()

        # Tombol menu opsi
        if col2.button("⋯", key="menu_" + sid):
            if st.session_state.get("open_menu_sid") == sid:
                st.session_state["open_menu_sid"] = None
            else:
                st.session_state["open_menu_sid"] = sid

        # Menu ubah judul dan hapus sesi
        if st.session_state.get("open_menu_sid") == sid:
            with st.sidebar.expander("🔧 Opsi"):
                new_title = st.text_input("Ubah Judul", value=title, key="rename_" + sid)
                if st.button("✅ Simpan", key="save_" + sid):
                    st.session_state.sessions[sid]["title"] = new_title
                    st.session_state["open_menu_sid"] = None
                    save_sessions_to_file(st.session_state.sessions)

                if st.button("🗑️ Hapus", key="delete_" + sid):
                    st.session_state["confirm_delete_sid"] = sid

                # Konfirmasi hapus
                if st.session_state.get("confirm_delete_sid") == sid:
                    st.warning("Yakin ingin menghapus sesi ini?")
                    col_c1, col_c2 = st.columns(2)
                    if col_c1.button("✅ Ya, Hapus", key="confirm_yes_" + sid):
                        to_delete = sid
                        st.session_state["confirm_delete_sid"] = None
                        st.session_state["open_menu_sid"] = None
                    if col_c2.button("❌ Batal", key="confirm_no_" + sid):
                        st.session_state["confirm_delete_sid"] = None

# Proses penghapusan sesi
if to_delete:
    del st.session_state.sessions[to_delete]
    if st.session_state.current_sid == to_delete:
        if st.session_state.sessions:
            st.session_state.current_sid = list(st.session_state.sessions.keys())[0]
        else:
            sid = str(uuid.uuid4())
            st.session_state.sessions[sid] = {
                "title": "Sesi Baru",
                "created": datetime.now(),
                "messages": []
            }
            st.session_state.current_sid = sid
    save_sessions_to_file(st.session_state.sessions)
    st.rerun()

# Tombol untuk membuat sesi baru
if st.sidebar.button("➕ Buat Sesi Baru"):
    sid = str(uuid.uuid4())
    st.session_state.sessions[sid] = {
        "title": "Sesi Baru",
        "created": datetime.now(),
        "messages": []
    }
    st.session_state.current_sid = sid
    save_sessions_to_file(st.session_state.sessions)
    st.rerun()

# ========== Halaman Utama Chatbot ==========

st.title("🧠 Chatbot AI via OpenRouter")
st.markdown(f"###### Model aktif: `{MODEL}`")

# Ambil data sesi aktif
sid = st.session_state.current_sid
if sid not in st.session_state.sessions:
    st.error("⚠️ Sesi tidak ditemukan.")
    st.stop()

session_data = st.session_state.sessions[sid]

# Tampilkan riwayat chat
for msg in session_data["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "timestamp" in msg:
            st.markdown(f"<div style='font-size: 0.75em; color: gray;'>{msg['timestamp']}</div>", unsafe_allow_html=True)
        if "model" in msg and msg["role"] == "assistant":
            st.markdown(f"<div style='font-size: 0.75em; color: gray;'>🤖 Model: `{msg['model']}`</div>", unsafe_allow_html=True)

# Input dari pengguna
user_input = st.chat_input("Ketik pesan...")

if user_input:
    # Validasi API key
    if not st.session_state.api_key.strip():
        st.error("❌ Masukkan API key OpenRouter kamu terlebih dahulu di sidebar.")
        st.stop()

    # Simpan pesan dari user
    st.chat_message("user").markdown(user_input)
    session_data["messages"].append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    update_title_first_user_message(sid)
    save_sessions_to_file(st.session_state.sessions)

    # Kirim permintaan ke API OpenRouter
    with st.spinner("Sedang memproses..."):
        payload = {
            "model": MODEL,
            "messages": [{"role": "system", "content": "You are a helpful assistant."}] + session_data["messages"]
        }

        try:
            response = requests.post(API_URL, headers=get_headers(), json=payload)
            if response.status_code == 200:
                reply = response.json()['choices'][0]['message']['content']
            elif response.status_code == 429:
                reply = "❌ Batas penggunaan model gratis harian telah tercapai.\n\nSilakan coba lagi besok atau gunakan API key lain."
            elif response.status_code == 400:
                reply = "❌ Permintaan tidak valid. Periksa kembali API Key dan model yang digunakan."
            elif response.status_code == 401:
                reply = "❌ API Key tidak valid atau sudah expired."
            else:
                reply = f"❌ Gagal: {response.status_code} - {response.text}"
        except Exception as e:
            reply = f"❌ Terjadi kesalahan: {e}"

    # Tampilkan balasan dari model
    st.chat_message("assistant").markdown(reply)
    session_data["messages"].append({
        "role": "assistant",
        "content": reply,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": MODEL
    })
    save_sessions_to_file(st.session_state.sessions)