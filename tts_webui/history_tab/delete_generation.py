import shutil

from tts_webui.utils.safe_path import resolve_within


def delete_generation(directory: str):
    # Exposed as api_name="delete_generation"; the path is client supplied.
    shutil.rmtree(resolve_within(directory))
