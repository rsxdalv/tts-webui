import subprocess
import sys

from tts_webui.utils.safe_path import DEFAULT_ROOTS, resolve_within

# open / xdg-open / explorer launch the registered handler for whatever they
# are given, not just directories, so an unvalidated path lets a remote caller
# start arbitrary local files. "data" is included for the model directories.
_OPEN_ROOTS = DEFAULT_ROOTS + ("data",)


def _validated(folder_path: str) -> str:
    return resolve_within(folder_path, _OPEN_ROOTS)


if sys.platform == "darwin":

    def open_folder(folder_path: str):
        subprocess.check_call(["open", "--", _validated(folder_path)])

elif sys.platform.startswith("linux"):

    def open_folder(folder_path: str):
        subprocess.check_call(["xdg-open", _validated(folder_path)])

elif sys.platform == "win32":

    def open_folder(folder_path: str):
        subprocess.Popen(["explorer", _validated(folder_path)])


if __name__ == "__main__":
    # open_folder("./data/models/")
    import os

    open_folder(os.path.join("data", "models"))
