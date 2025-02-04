import streamlit as st
import subprocess

subprocess.run(["pip", "install", "google-generativeai"])
import google.generativeai as genai
import pdfplumber
import textwrap

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pyperclip

# Configure Gemini API
genai.configure(api_key="API_KEY")


# Function to generate AI responses
def generate_response(text):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(text)
    return response.text


# Function to summarize text
def summarize_text(text, summary_type="detailed"):
    model = genai.GenerativeModel("gemini-pro")

    if summary_type == "short":
        prompt = f"Summarize this in 2-3 sentences:\n\n{text}"
    elif summary_type == "bullet":
        prompt = f"Summarize this into bullet points:\n\n{text}"
    else:
        prompt = f"Summarize this in a detailed way:\n\n{text}"

    response = model.generate_content(prompt)
    return response.text


# Function to split long text into smaller chunks
def split_text(text, max_length=4000):
    return textwrap.wrap(text, max_length, break_long_words=False, replace_whitespace=False)


# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    return text if text.strip() else None


# Function to perform web search
def web_search_duckduckgo(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=3)
    return results


# Function to export chat history to a text file
def export_chat_as_text():
    chat_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state["messages"]])
    return chat_history


# Function to export chat history as a PDF
def export_chat_as_pdf():
    chat_history = export_chat_as_text()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 12)
    y_position = 750
    for line in chat_history.split("\n"):
        pdf.drawString(50, y_position, line)
        y_position -= 20
        if y_position < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y_position = 750
    pdf.save()
    buffer.seek(0)
    return buffer


# ---- Streamlit UI ----
st.set_page_config(page_title="Summarizer AI Chatbot", page_icon="📝", layout="centered")

st.title("💬 AI Chatbot & Summarizer")
st.write("Chat with the AI! Upload a PDF or enter text for summarization.")

# Sidebar for PDF Summarizer
with st.sidebar:
    st.subheader("📂 Upload a PDF to Summarize")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded_file:
        with st.spinner("Extracting text from PDF... ⏳"):
            pdf_text = extract_text_from_pdf(uploaded_file)
        if pdf_text:
            if st.button("Summarize PDF 📑"):
                with st.spinner("Summarizing PDF content... ⏳"):
                    if len(pdf_text) > 4000:
                        text_chunks = split_text(pdf_text)
                        pdf_summary = "\n\n".join([summarize_text(chunk, "detailed") for chunk in text_chunks])
                    else:
                        pdf_summary = summarize_text(pdf_text, "detailed")
                st.subheader("📌 PDF Summary:")
                st.write(pdf_summary)
        else:
            st.error("❌ Could not extract text from the PDF. It may be scanned or empty.")

# Add a 'New Chat' button to clear session state
if st.button("🆕 New Chat"):
    st.session_state["messages"] = []
    st.rerun()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display chat history
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if st.button("📋 Copy", key=f"copy_{message['content']}"):
            pyperclip.copy(message["content"])
        if st.button("🔗 Share", key=f"share_{message['content']}"):
            st.write("Sharing functionality coming soon!")

# User input in chat format
user_input = st.chat_input("Ask anything...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    with st.spinner("Thinking..."):
        if "search" in user_input.lower():
            search_results = web_search_duckduckgo(user_input)
            response = "\n".join([f"- {res['title']}: {res['href']}" for res in search_results])
        elif len(user_input) > 100:
            response = summarize_text(user_input, "detailed")
        else:
            response = generate_response(user_input)

    with st.chat_message("assistant"):
        st.write(response)

    # Store chat history
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.session_state["messages"].append({"role": "assistant", "content": response})

# Chat Export Options
st.subheader("📥 Export Chat")
col1, col2 = st.columns(2)
with col1:
    st.download_button("Download as TXT", export_chat_as_text(), "chat_history.txt")
with col2:
    st.download_button("Download as PDF", export_chat_as_pdf(), "chat_history.pdf")
