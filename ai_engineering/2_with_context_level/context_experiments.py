import os
import ollama
import streamlit as st
from dotenv import load_dotenv

# Load configuration from .env
load_dotenv()

# Read configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

#------day2-----
BASE_URL = os.getenv("LLM_BASE_URL")
API_KEY = os.getenv("LLM_API_KEY")
MODEL = os.getenv("LLM_MODEL")


# Create Ollama client
client = ollama.Client(host=OLLAMA_HOST)

#streamlit page config
st.set_page_config(
    page_title="Local GenAI",
    page_icon="🤖",
)

#title
st.title("🤖 Local GenAI Playground")
st.caption("Powered by Ollama — runs on your computer")

#prompt area
inbox_title = "Ask the AI assistant" #box head label
prompt = st.text_area(
    inbox_title,
    placeholder="Enter your employee query here...",
    help="Ask a question for the AI assistant.",
)

st.caption(f"Model: {OLLAMA_MODEL}")


# def client_build(OLLAMA_MODEL, system_instructions, prompt):
#     if st.button(
#         "Generate response",
#         type="primary",
#         use_container_width=True,
#     ):
#         if not prompt.strip():
#             st.warning("Please enter a prompt.")
#             return

#         messages = [
#             {
#                 "role": "system",
#                 "content": system_instructions,
#             },
#             {
#                 "role": "user",
#                 "content": prompt.strip(),
#             },
#         ]

#         try:
#             st.subheader("AI Response")

#             with st.spinner("Connecting to Ollama..."):
#                 response = client.chat(
#                     model=OLLAMA_MODEL,
#                     messages=messages,
#                     stream=True,
#                     options={"num_ctx": 2048},
#                 )

#             # Display tokens progressively in Streamlit
#             answer = st.write_stream(
#                 chunk["message"]["content"]
#                 for chunk in response
#                 if chunk["message"]["content"]
#             )

#         except ollama.ResponseError as e:
#             st.error(f"Ollama error: {e.error}")

#         except Exception as e:
#             st.error(f"Unable to connect to Ollama: {e}")
#             st.info(
#                 "Check that Ollama is running, the server URL "
#                 "is correct, and the selected model is downloaded."
#             )

def client_build(
    model,
    system_instructions,
    user_input,
    context=None,
    version_name="AI Response",
):
    if not user_input.strip():
        st.warning("Please enter a prompt.")
        return

    messages = []

    if system_instructions:
        messages.append({
            "role": "system",
            "content": system_instructions,
        })

    if context and context.strip():
        user_message = f"""
Context:
{context}

Question:
{user_input}

Use the supplied context for your answer.
If the answer is missing from the context, say you do not know.
"""
    else:
        user_message = user_input

    messages.append({
        "role": "user",
        "content": user_message,
    })

    st.subheader(version_name)

    try:
        with st.spinner(f"Generating {version_name}..."):
            response = client.chat(
                model=model,
                messages=messages,
                stream=True,
                options={"num_ctx": 2048},
            )

            answer = st.write_stream(
                chunk.message.content
                for chunk in response
                if chunk.message.content
            )

    except ollama.ResponseError as e:
        st.error(f"Ollama error: {e.error}")

    except Exception as e:
        st.error(f"Unable to connect to Ollama: {e}")
def sys_inst(whoknows):
    if whoknows:
        return """
    You are an AI assistant who helps employees with their queries.

    - Give clear, accurate, and helpful answers.
    - Do not invent facts or present guesses as confirmed information.
    - If you do not know an answer, clearly say so.
    - wrong answer might cause global warming.
    - If a question is ambiguous, ask for clarification.
    - Keep answers concise but sufficiently detailed.
    - Use only supplied context for internal company information.
    - If the context does not contain the answer, say so.
    """
    return ""

def adding_layered_prompt_instructions():
    pass

def adding_detailed_context():
    pass

#--------contextual versions---------#

# def version1(context,user_input):
#     client_build(OLLAMA_MODEL, sys_inst(user_input), prompt)

# def version1(user_input):
#     client_build(
#         OLLAMA_MODEL,
#         system_instructions="",
#         user_input=user_input,
#     )

# def version2(context,user_input):
#     client_build(OLLAMA_MODEL, sys_inst(user_input), prompt)

# def version3():
#     pass

# def version2(user_input):
#     client_build(
#         OLLAMA_MODEL,
#         system_instructions=sys_inst(True),
#         user_input=user_input,
#     )


# # Version 3: System instructions + supplied context
# def version3(user_input, context):
#     client_build(
#         OLLAMA_MODEL,
#         system_instructions=sys_inst(True),
#         user_input=user_input,
#         context=context,
#     )

# Version A: Baseline
def version1(user_input):
    client_build(
        model=OLLAMA_MODEL,
        system_instructions="",
        user_input=user_input,
        version_name="Version A — Baseline",
    )


# Version B: Improved instructions
def version2(user_input):
    client_build(
        model=OLLAMA_MODEL,
        system_instructions=sys_inst(True),
        user_input=user_input,
        version_name="Version B — Improved Instructions",
    )

context = st.text_area(
    "Relevant Context (Version C only)",
    placeholder="Paste context here when the test case provides it...",
    help="This context will only be given to Version C.",
)
# Version C: Instructions + relevant context
def version3(user_input, context):
    client_build(
        model=OLLAMA_MODEL,
        system_instructions=sys_inst(True),
        user_input=user_input,
        context=context,
        version_name="Version C — Instructions + Context",
    )

if  __name__=="__main__":

    # # client_build(OLLAMA_MODEL, system_instructions, prompt)
    # st.write("----------- Version 1: Baseline -----------")
    # if st.button("Run Version 1", key="version1"):
    #     version1(prompt)

    # st.write("----------- Version 2: Instructions -----------")
    # if st.button("Run Version 2", key="version2"):
    #     version2(prompt)

    # st.write("----------- Version 3: Instructions + Context -----------")
    # if st.button("Run Version 3", key="version3"):
    #     sample_context = """
    #     Employees receive 12 sick leave days per year.
    #     Leave requests must be submitted to their manager.
    #     """
    #     version3(prompt, sample_context)


    if st.button(
        "Send — Compare All 3 Versions",
        type="primary",
        use_container_width=True,
    ):

        if not prompt.strip():
            st.warning("Please enter a question.")

        else:
            st.write("## Comparison Results")

            # Run all three versions for the same question
            version1(prompt)

            st.divider()

            version2(prompt)

            st.divider()

            version3(prompt, context)
