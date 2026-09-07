import shutil

from tts_webui.utils.safe_path import resolve_within


def delete_generation_cb(refresh):
    def delete_generation(directory: str, *args):
        shutil.rmtree(resolve_within(directory))
        return refresh(*args)

    return delete_generation
