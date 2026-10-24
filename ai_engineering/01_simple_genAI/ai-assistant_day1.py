import os
import ollama
import streamlit as st
from dotenv import load_dotenv

# Load configuration from .env
load_dotenv()

# Read configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Create Ollama client
client = ollama.Client(host=OLLAMA_HOST)

st.set_page_config(
    page_title="Local GenAI",
    page_icon="🤖",
)

st.title("🤖 Local GenAI Playground")
st.caption("Powered by Ollama — runs on your computer")


inbox_title = "Ask the AI assistant"
prompt = st.text_area(
    inbox_title,
    placeholder="Enter your employee query here...",
    help="Ask a question for the AI assistant.",
)

st.caption(f"Model: {OLLAMA_MODEL}")

instructions =  """ You are an AI assistant who helps 
                                employees with their queries. 
                                Give clear, accurate, and helpful answers. """



def simple_employee_ai_assistant(OLLAMA_MODEL, instructions, prompt):

    if st.button("Generate response", type="primary", use_container_width=True):
        if not prompt.strip():
            st.warning("Please enter a prompt.")
        else:
            try:
                with st.spinner("Generating response..."):
                    response = client.chat(
                        model=OLLAMA_MODEL,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    instructions
                                ),
                            },
                            {
                                "role": "user",
                                "content": prompt.strip(),
                            },
                        ],
                        options={"num_ctx": 2048}, ##setting context window to 2048 so i'm trying to limit memory usage.
                    )

                st.subheader("AI Response")
                st.markdown(response.message.content)

            except ollama.ResponseError as e:
                st.error(f"Ollama error: {e.error}")

            except Exception as e:
                st.error(f"Unable to connect to Ollama: {e}")
                st.info(
                    "Check that Ollama is running, the server URL is "
                    "correct, and the selected model is available."
                )


if  __name__=="__main__":
    simple_employee_ai_assistant(OLLAMA_MODEL, instructions, prompt)