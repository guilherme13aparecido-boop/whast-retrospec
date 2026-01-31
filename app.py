import streamlit as st
import pandas as pd
import zipfile
import re

st.set_page_config(page_title="WhatsApp Wrapped", page_icon="💬", layout="wide")

st.title("💬 WhatsApp Wrapped")
st.caption("Sua conversa como você nunca viu antes")

uploaded_file = st.file_uploader(
    "📤 Envie o arquivo .txt ou .zip exportado do WhatsApp",
    type=["txt", "zip"]
)

# ---------------- EXTRAIR TXT DO ZIP ---------------- #
def extract_txt_from_zip(zip_file):
    try:
        with zipfile.ZipFile(zip_file) as z:
            for name in z.namelist():
                if name.endswith(".txt"):
                    return z.open(name).read().decode("utf-8")
    except:
        return None
    return None


# ---------------- PARSER WHATSAPP ---------------- #
def parse_whatsapp(text):
    # Suporta:
    # 31/12/2024, 23:59 - Nome: Mensagem
    # [31/12/2024, 23:59] Nome: Mensagem
    pattern = r"\[?(\d{1,2}/\d{1,2}/\d{2,4}), (\d{2}:\d{2})\]? - (.*?): (.*)"
    data = []

    for line in text.split("\n"):
        match = re.match(pattern, line)
        if match:
            date, time, sender, message = match.groups()
            data.append([f"{date} {time}", sender, message])

    if not data:
        return pd.DataFrame(columns=["datetime", "sender", "message"])

    df = pd.DataFrame(data, columns=["datetime", "sender", "message"])

    # Converte datas com tolerância a erros
    df["datetime"] = pd.to_datetime(
        df["datetime"],
        errors="coerce",
        dayfirst=True
    )

    df = df.dropna(subset=["datetime"])

    return df


# ---------------- EMOÇÃO ---------------- #
def emotion(msg):
    pos = ["amo", "feliz", "kkk", "haha", "lindo", "😍", "❤️"]
    neg = ["triste", "raiva", "ódio", "chato", "droga", "merda", "😢"]
    msg = str(msg).lower()
    if any(p in msg for p in pos): return "Positiva 😊"
    if any(n in msg for n in neg): return "Negativa 😔"
    return "Neutra 😐"


# ---------------- EXECUÇÃO PRINCIPAL ---------------- #
if uploaded_file:

    if uploaded_file.name.endswith(".zip"):
        content = extract_txt_from_zip(uploaded_file)
    else:
        content = uploaded_file.read().decode("utf-8")

    if not content:
        st.error("Não consegui ler o arquivo 😢")
        st.stop()

    df = parse_whatsapp(content)

    if df.empty:
        st.error("Não encontrei mensagens válidas no arquivo 😢")
        st.stop()

    # Segurança extra
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"])

    if df.empty:
        st.error("As datas das mensagens não puderam ser interpretadas 😢")
        st.stop()

    # Métricas
    df["emotion"] = df["message"].apply(emotion)
    df["hour"] = df["datetime"].dt.hour
    df["length"] = df["message"].str.len()
    df["laugh"] = df["message"].str.contains(r"kkk|haha|rs|hehe", case=False, na=False)

    st.metric("💬 Total de mensagens", len(df))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 Mensagens por pessoa")
        st.bar_chart(df["sender"].value_counts())

        st.subheader("😊 Emoções")
        st.bar_chart(df["emotion"].value_counts())

    with col2:
        st.subheader("⏰ Horários mais ativos")
        st.bar_chart(df["hour"].value_counts().sort_index())

    longest = df.loc[df["length"].idxmax()]
    st.subheader("🧾 Mensagem mais longa")
    st.write(longest["message"])
