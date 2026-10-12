import os
import json
from types import SimpleNamespace
from typing import Literal

try:
    import ollama
except ModuleNotFoundError:  # pragma: no cover - handling missing optional dependency
    class _OllamaResponseError(Exception):
        def __init__(self, message="", status_code=None, error=None):
            super().__init__(message)
            self.status_code = status_code
            self.error = error

    class _OllamaClient:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "The 'ollama' package is not installed. "
                "Install it before starting the model client."
            )

    ollama = SimpleNamespace(
        ResponseError=_OllamaResponseError,
        Client=_OllamaClient,
    )

try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover - app only runs with Streamlit installed
    st = None

from dotenv import load_dotenv
from pydantic import BaseModel, Field, StrictStr, ValidationError
import httpx


#adding test cases 

from reliability import (
    AIResponse,
    MAX_ATTEMPTS,
    generate_validated_response,
    response_to_dict,
)

# Load configuration from .env
load_dotenv()

# Read configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MAX_ATTEMPTS = 2

#------day2-----
BASE_URL = os.getenv("LLM_BASE_URL")
API_KEY = os.getenv("LLM_API_KEY")
MODEL = os.getenv("LLM_MODEL")


# Create Ollama client only when the dependency is available.
# client = ollama.Client(host=OLLAMA_HOST)

client = None
if ollama is not None and hasattr(ollama, "Client"):
    try:
        client = ollama.Client(
            host=OLLAMA_HOST,
            timeout=60.0,
        )
    except RuntimeError:
        client = None
#---output json structure class
#-------output contract or schema-----

class AIResponse(BaseModel):
    status: Literal["success", "needs_clarification"]
    answer: StrictStr = Field(min_length=1)

    class Config:
        extra = "forbid"

def get_response_schema():
    """Support Pydantic v1 and v2."""
    if hasattr(AIResponse, "model_json_schema"):
        return AIResponse.model_json_schema()

    return AIResponse.schema()


def validate_response(raw_output):
    """Parse JSON and validate its structure and field types."""
    parsed = json.loads(raw_output)

    if hasattr(AIResponse, "model_validate"):
        return AIResponse.model_validate(parsed)

    return AIResponse.parse_obj(parsed)


def response_to_dict(result):
    """Convert a validated Pydantic object into a dictionary."""
    if hasattr(result, "model_dump"):
        return result.model_dump()

    return result.dict()


#-contract instructions

CONTRACT_INSTRUCTIONS = """
    You are an AI assistant helping employees.

    Return exactly one JSON object matching the supplied schema.
    Do not include Markdown code fences or text outside the JSON.

    Use status="success" when you have enough information to answer.
    Use status="needs_clarification" when more information is required.

    The answer field must contain the user-facing answer or a
    concise clarification question.

    Do not invent facts. If supplied context lacks the information
    needed to answer, do not guess. Ask for clarification or explain
    what information is missing.
    """



if st is not None and __name__ == "__main__":
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



def client_build(
    model,
    system_instructions,
    user_input,
    context=None,
    version_name="AI Response",):

    if st is None:
        raise RuntimeError(
            "Streamlit is required to run this app. Install streamlit and launch it in a browser."
        )

    if not user_input.strip():
        st.warning("Please enter a prompt.")
        return

    # Every version follows the same structured output contract.
    combined_instructions = CONTRACT_INSTRUCTIONS

    if system_instructions and system_instructions.strip():
        combined_instructions += (
            "\n\nAdditional instructions:\n"
            + system_instructions
        )

    messages = [
        {
            "role": "system",
            "content": combined_instructions,
        }
    ]

    #messages = []

    # if system_instructions:
    #     messages.append({
    #         "role": "system",
    #         "content": system_instructions,
    #     })

    if context and context.strip():
        user_message = f"""
            Context:
                {context}

                Question:
                {user_input}

                Use the supplied context for your answer.
                If the answer is missing from the context, say you do not know.
                Follow the JSON output contract. 
                """
    else:
        user_message = user_input

    messages.append({
        "role": "user",
        "content": user_message,
    })

    # a corrective follow-up before the next attempt.
    working_messages = list(messages)
    last_error = "No response was produced."

    st.subheader(version_name)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with st.spinner(
                f"Generating response: attempt {attempt}/{MAX_ATTEMPTS}"
            ):
                response = client.chat(
                    model=model,
                    messages=working_messages,
                    format=get_response_schema(),
                    stream=False,
                    options={
                        "temperature": 0,
                        "num_ctx": 2048,
                    },
                )

            raw_output = response.message.content or ""

           # raw_output = '{"status": "success",'  # temo replacement
            # Parse and validate the completed response.
            try:
                result = validate_response(raw_output)

            except (
                json.JSONDecodeError,
                ValidationError,
                TypeError,
                ValueError,
            ) as exc:
                last_error = (
                    f"{type(exc).__name__}: {exc}"
                )

                if attempt < MAX_ATTEMPTS:
                    # Retry once with explicit corrective feedback.
                    working_messages.extend([
                        {
                            "role": "assistant",
                            "content": raw_output,
                        },
                        {
                            "role": "user",
                            "content": (
                                "Your previous response failed JSON "
                                "parsing or schema validation. Return "
                                "one corrected JSON object matching "
                                "the required schema. Do not add "
                                "surrounding text."
                            ),
                        },
                    ])
                    continue

                break

            # Only display the answer after successful validation.
            with st.expander("Validated JSON output", expanded=True):
                st.json(response_to_dict(result))

            if result.status == "success":
                st.success("Response passed schema validation.")
                st.markdown(result.answer)
            else:
                st.info(result.answer)

            return result

        # Retry only selected transient connection/timeout failures.
        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            ConnectionError,
        ) as exc:
            last_error = f"{type(exc).__name__}: {exc}"

            if attempt < MAX_ATTEMPTS:
                continue

            break

        # Retry server errors or rate limits, but not permanent errors
        # such as a model-not-found response.
        except ollama.ResponseError as exc:
            status_code = getattr(exc, "status_code", None)

            last_error = (
                f"Ollama response error "
                f"(HTTP {status_code}): {exc.error}"
            )

            retryable = (
                status_code == 429
                or (
                    status_code is not None
                    and status_code >= 500
                )
            )

            if retryable and attempt < MAX_ATTEMPTS:
                continue

            break

        # Unknown/unexpected errors are not retried automatically.
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            break

    # Safe fallback after failure or exhausted retries.
    st.error(
        "The AI could not produce a valid response. "
        "Please try again later."
    )
    with st.expander("Developer diagnostics (local testing)"):
        st.code(last_error)

    return None

    # Useful for your Day 03 local testing evidence.
    # In production, keep technical details in server-side logs.
    # with st.expander("Developer diagnostics (local testing)"):
    #     st.code(last_error)

    # return None

    # st.subheader(version_name)

    # try:
    #     with st.spinner(f"Generating {version_name}..."):
    #         # response = client.chat(
    #         #     model=model,
    #         #     messages=messages,
    #         #     stream=True,
    #         #     options={"num_ctx": 2048},
    #         # )

    #         answer = st.write_stream(
    #             chunk.message.content
    #             for chunk in response
    #             if chunk.message.content
    #         )

    # except ollama.ResponseError as e:
    #     st.error(f"Ollama error: {e.error}")

    # except Exception as e:
    #     st.error(f"Unable to connect to Ollama: {e}")

    # return None

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

if st is not None and __name__ == "__main__":
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

    # --------------------------------------------------
    # Run the application
    # --------------------------------------------------

    st.subheader("Choose a version to test")

    # col1, col2, col3 = st.columns(3)
    col3, = st.columns(1)

    # Version A: Baseline
    # with col1:
    #     if st.button("Run Version A", use_container_width=True):
    #         if not prompt.strip():
    #             st.warning("Please enter a question.")
    #         else:
    #             version1(prompt)

    # # Version B: Improved instructions
    # with col2:
    #     if st.button("Run Version B", use_container_width=True):
    #         if not prompt.strip():
    #             st.warning("Please enter a question.")
    #         else:
    #             version2(prompt)

    # Version C: Instructions + context
    with col3:
        if st.button("Run Version C", use_container_width=True):
            if not prompt.strip():
                st.warning("Please enter a question.")
            else:
                version3(prompt, context)