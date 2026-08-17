import json
import os
import urllib.request
import urllib.error
from datetime import datetime

import gradio as gr


ORCAROUTER_API_URL = "https://api.orcarouter.ai/v1/audio/speech"

ORCAROUTER_MODELS = [
    "openai/tts-1",
    "openai/tts-1-hd",
    "openai/gpt-4o-mini-tts",
]

ORCAROUTER_VOICES = [
    "alloy",
    "echo",
    "fable",
    "onyx",
    "nova",
    "shimmer",
]


def _get_api_key(api_key_input: str) -> str:
    if api_key_input and api_key_input.strip():
        return api_key_input.strip()
    return os.environ.get("ORCAROUTER_API_KEY", "")


def _save_audio(audio_bytes: bytes, text: str, model: str, voice_id: str) -> tuple:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_text = "".join(c if c.isalnum() or c in " _-" else "" for c in text[:50])
    safe_text = safe_text.strip().replace(" ", "_") or "orcarouter_tts"
    folder_name = f"{timestamp}_{safe_text}"

    output_dir = os.path.join("outputs", folder_name)
    os.makedirs(output_dir, exist_ok=True)

    audio_path = os.path.join(output_dir, f"{safe_text}.mp3")
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)

    metadata = {
        "text": text,
        "model": model,
        "voice_id": voice_id,
        "provider": "orcarouter",
        "_type": "orcarouter_cloud_tts",
        "_version": "0.1.0",
    }

    metadata_path = audio_path.replace(".mp3", ".json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return audio_path, metadata, output_dir


def generate_orcarouter_tts(
    text: str,
    model: str,
    voice_id: str,
    api_key: str,
    **kwargs,
) -> tuple:
    key = _get_api_key(api_key)
    if not key:
        raise gr.Error(
            "OrcaRouter API key is required. Set ORCAROUTER_API_KEY environment variable "
            "or enter it in the API Key field."
        )

    if not text or not text.strip():
        raise gr.Error("Please enter text to synthesize.")

    payload = {
        "model": model,
        "input": text.strip(),
        "voice": voice_id,
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(
        ORCAROUTER_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            audio_bytes = resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise gr.Error(f"OrcaRouter API error ({e.code}): {body}")
    except urllib.error.URLError as e:
        raise gr.Error(f"Network error: {e.reason}")

    if not audio_bytes:
        raise gr.Error(
            "OrcaRouter API returned no audio data. "
            "Check your API key and request parameters."
        )

    audio_path, metadata, folder_root = _save_audio(audio_bytes, text, model, voice_id)
    return audio_path, metadata, folder_root


def orcarouter_cloud_tts_tab():
    with gr.Column():
        gr.Markdown(
            "Generate speech using [OrcaRouter](https://www.orcarouter.ai) Cloud TTS API. "
            "Requires an OrcaRouter API key (set `ORCAROUTER_API_KEY` env var or enter below)."
        )

        with gr.Row():
            with gr.Column(scale=2):
                text_input = gr.Textbox(
                    label="Text",
                    placeholder="Enter text to synthesize...",
                    lines=4,
                )

            with gr.Column(scale=1):
                model_dropdown = gr.Dropdown(
                    label="Model",
                    choices=ORCAROUTER_MODELS,
                    value="openai/tts-1",
                )
                voice_dropdown = gr.Dropdown(
                    label="Voice",
                    choices=ORCAROUTER_VOICES,
                    value="alloy",
                )
                api_key_input = gr.Textbox(
                    label="API Key (optional if ORCAROUTER_API_KEY is set)",
                    placeholder="Enter OrcaRouter API key...",
                    type="password",
                )

        generate_btn = gr.Button("Generate", variant="primary")
        audio_output = gr.Audio(label="Generated Audio", type="filepath")
        metadata_output = gr.JSON(label="Metadata")

        generate_btn.click(
            fn=generate_orcarouter_tts,
            inputs=[text_input, model_dropdown, voice_dropdown, api_key_input],
            outputs=[audio_output, metadata_output, gr.Textbox(visible=False)],
            api_name="orcarouter_cloud_tts",
        )


def extension__tts_generation_webui():
    orcarouter_cloud_tts_tab()
    return {
        "package_name": "extensions.builtin.extension_orcarouter_cloud_tts",
        "name": "OrcaRouter Cloud TTS",
        "requirements": "",
        "description": "Cloud-based text-to-speech using the OrcaRouter gateway (OpenAI TTS models) behind a single API key",
        "extension_type": "interface",
        "extension_class": "text-to-speech",
        "author": "OrcaRouter",
        "extension_author": "XiaoHuo888-hue",
        "license": "MIT",
        "website": "https://www.orcarouter.ai",
        "extension_website": "https://github.com/XiaoHuo888-hue/TTS-WebUI",
        "extension_platform_version": "0.0.1",
    }
