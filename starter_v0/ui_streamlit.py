from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return slug.strip("_") or "run"


def json_text(value: Any, *, max_chars: int | None = None) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars] + "\n...<truncated>"
    return text


def trim_history(history: list[dict[str, str]], window: int) -> list[dict[str, str]]:
    if window <= 0:
        return []
    return history[-window * 2 :]


def execute_tool_call(call: ToolCall) -> dict[str, Any]:
    func = TOOL_FUNCTIONS.get(call.name)
    if not func:
        return {
            "tool": call.name,
            "args": call.args,
            "result": {"error": "unknown_tool", "message": f"No local implementation for {call.name}"},
        }
    try:
        result = func(**call.args)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"tool": call.name, "args": call.args, "result": result}


def tool_results_message(events: list[dict[str, Any]]) -> dict[str, str]:
    return {
        "role": "user",
        "content": (
            "TOOL_RESULTS_JSON:\n"
            f"{json_text(events, max_chars=24000)}\n\n"
            "Use only these tool results. If the user asked for a digest and the items are ready, "
            "call the formatting tool. Otherwise answer the user directly with cited sources when available."
        ),
    }


def assistant_tool_message(response_text: str | None, calls: list[ToolCall]) -> dict[str, str]:
    call_summary = [{"name": call.name, "args": call.args} for call in calls]
    content = response_text or "I will call the selected tool(s)."
    return {
        "role": "assistant",
        "content": f"{content}\n\nTOOL_CALLS_JSON:\n{json_text(call_summary)}",
    }


def run_model_tool_loop(
    *,
    provider: Any,
    messages: list[dict[str, str]],
    tools: list[dict[str, Any]],
    model: str | None,
    max_tool_rounds: int,
) -> dict[str, Any]:
    working_messages = list(messages)
    rounds: list[dict[str, Any]] = []
    all_tool_events: list[dict[str, Any]] = []

    for round_index in range(1, max_tool_rounds + 1):
        response = provider.complete(working_messages, tools, model=model, temperature=0.0)
        calls = response.tool_calls
        round_record: dict[str, Any] = {
            "round": round_index,
            "assistant_text": response.text,
            "tool_calls": [{"name": call.name, "args": call.args} for call in calls],
            "tool_results": [],
        }

        if not calls:
            rounds.append(round_record)
            return {
                "status": "answered",
                "assistant_text": response.text or "",
                "rounds": rounds,
                "tool_events": all_tool_events,
            }

        working_messages.append(assistant_tool_message(response.text, calls))
        non_clarification_events: list[dict[str, Any]] = []

        for call in calls:
            event = execute_tool_call(call)
            round_record["tool_results"].append(event)
            all_tool_events.append(event)

            # Detect the clarification/pause tool by its output flag (rename-proof),
            # not by a hard-coded tool name.
            result = event.get("result", {})
            if isinstance(result, dict) and result.get("awaiting_user"):
                question = result.get("question") or call.args.get("question") or "Bạn bổ sung thêm thông tin nhé."
                rounds.append(round_record)
                return {
                    "status": "waiting_for_user",
                    "assistant_text": question,
                    "rounds": rounds,
                    "tool_events": all_tool_events,
                }

            non_clarification_events.append(event)

        rounds.append(round_record)
        working_messages.append(tool_results_message(non_clarification_events))

    return {
        "status": "max_tool_rounds",
        "assistant_text": f"Stopped after {max_tool_rounds} tool rounds. Inspect the transcript for details.",
        "rounds": rounds,
        "tool_events": all_tool_events,
    }


def write_transcript(path: Path, transcript: dict[str, Any]) -> None:
    transcript["updated_at"] = now_iso()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def ensure_session() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []
    if "transcript_path" not in st.session_state:
        st.session_state.transcript_path = None
    if "transcript" not in st.session_state:
        st.session_state.transcript = None


def start_new_transcript(*, version: str, provider_name: str, model: str | None, system_prompt_path: Path, tools_path: Path, history_window: int, max_tool_rounds: int) -> None:
    artifact_version = build_artifact_version(version, system_prompt_path, tools_path)
    selected_model = model or getattr(make_provider(provider_name), "default_model", None)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), timestamp])
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"

    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": selected_model,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }

    st.session_state.history = []
    st.session_state.transcript_path = transcript_path
    st.session_state.transcript = transcript
    write_transcript(transcript_path, transcript)


def main() -> None:
    st.set_page_config(page_title="Research Agent UI", layout="wide")
    ensure_session()

    with st.sidebar:
        st.title("Research Agent")
        provider_name = st.selectbox("Provider", options=["openrouter", "openai", "anthropic", "gemini"], index=0)
        version = st.text_input("Version label", value="v0")
        model = st.text_input("Model (optional)", value="").strip() or None
        history_window = st.number_input("History window (pairs)", min_value=0, max_value=20, value=5, step=1)
        max_tool_rounds = st.number_input("Max tool rounds", min_value=1, max_value=10, value=4, step=1)

        system_prompt_path = st.text_input("system_prompt path", value=str(ARTIFACTS_DIR / "system_prompt.md"))
        tools_path = st.text_input("tools.yaml path", value=str(ARTIFACTS_DIR / "tools.yaml"))

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("New transcript", use_container_width=True):
                start_new_transcript(
                    version=version,
                    provider_name=provider_name,
                    model=model,
                    system_prompt_path=Path(system_prompt_path),
                    tools_path=Path(tools_path),
                    history_window=int(history_window),
                    max_tool_rounds=int(max_tool_rounds),
                )
        with col_b:
            if st.button("Clear chat", use_container_width=True):
                st.session_state.history = []

        st.divider()
        st.caption("Transcript file")
        st.code(str(st.session_state.transcript_path or ""), language=None)

    if st.session_state.transcript is None:
        start_new_transcript(
            version=version,
            provider_name=provider_name,
            model=model,
            system_prompt_path=Path(system_prompt_path),
            tools_path=Path(tools_path),
            history_window=int(history_window),
            max_tool_rounds=int(max_tool_rounds),
        )

    st.subheader("Chat")
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_text = st.chat_input("Nhập yêu cầu…")
    if not user_text:
        return

    st.session_state.history.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    provider = make_provider(provider_name)
    selected_model = model or getattr(provider, "default_model", None)
    system_prompt = Path(system_prompt_path).read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(Path(tools_path))
    openai_tools = to_openai_tools(tool_declarations)

    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history[:-1], int(history_window)),
        {"role": "user", "content": user_text},
    ]

    turn_index = len(st.session_state.transcript["turns"]) + 1
    turn_record: dict[str, Any] = {
        "turn_index": turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    try:
        result = run_model_tool_loop(
            provider=provider,
            messages=messages,
            tools=openai_tools,
            model=selected_model,
            max_tool_rounds=int(max_tool_rounds),
        )
        turn_record.update(result)
        assistant_text = result["assistant_text"]
    except Exception as exc:
        assistant_text = f"ERROR: {type(exc).__name__}: {str(exc)}"
        turn_record.update({"status": "provider_error", "error": assistant_text})

    turn_record["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn_record)
    write_transcript(Path(st.session_state.transcript_path), st.session_state.transcript)

    st.session_state.history.append({"role": "assistant", "content": assistant_text})
    with st.chat_message("assistant"):
        st.markdown(assistant_text)


if __name__ == "__main__":
    main()

