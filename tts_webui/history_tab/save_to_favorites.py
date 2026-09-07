import os
import shutil

import gradio as gr

from tts_webui.utils.safe_path import resolve_within


def save_to_favorites(directory: str):
    source = resolve_within(directory)
    shutil.copytree(
        source, os.path.join("favorites", os.path.basename(source)), symlinks=False
    )
    return gr.Button(value="Saved")


def save_to_collection(directory: str, collection: str):
    # Both arguments come from the client, so the destination needs the same
    # containment check as the source.
    source = resolve_within(directory)
    destination = resolve_within(collection)
    shutil.copytree(
        source, os.path.join(destination, os.path.basename(source)), symlinks=False
    )
    return gr.Dropdown(value="Saved")
