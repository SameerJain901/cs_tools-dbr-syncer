"""
Freezes and downloads all necessary requirements.

This script is to be run on a ThoughtSpot server by ThoughtSpot in order to
ensure correct output. Upon running, all requirements will be downloaded to the
../vendor/ directory.

-------------------------------------------------------------------------------

The assumptions we are making before proceeding:

 1. The client does not have local access to a python 3.6+ environment.
 2. The client's ThoughtSpot server DOES NOT have outside internet access.

If you can answer yes to both questions, proceed below.

In order to share with a client, run this script and upload the current vendor/
directory to Egynte, then share the link to the client. The client will need to
transfer the download to their ThoughtSpot instance into the /tmp directory.

cd $HOME
mkdir .venv
python3 -m venv .venv
activate
pip install -r /tmp/vendor/offline-install.txt --find-lines=/tmp/vendor/

The client can verify their install with the following command. Running the
command below should result with the message EVIRONMENT SUCCESS.

python -c "import thoughtspot_internal;print('EVIRONMENT SUCCESS!')"
"""
import subprocess as sp
import pathlib
import shutil
import stat
import sys
import os


class _cd:
    """ Change directory. """
    def __init__(self, to: pathlib.Path):
        self.to = to.expanduser()
        self.from_ = pathlib.Path.cwd()

    def __enter__(self):
        os.chdir(self.to)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.chdir(self.from_)


def _rm_ro(function, path, exc_info):
    """
    Remove read-only files.

    Called only when shutil.rmtree errors.
    """
    os.chmod(path, stat.S_IWRITE)
    os.remove(path)


if __name__ == '__main__':
    if sys.prefix == sys.base_prefix:
        raise RuntimeError('no virtual environment detected!')

    HERE = pathlib.Path(__file__).parent
    VENDOR_DIR = HERE.parent / 'vendor'

    # remove all files from vendor/
    for fp in VENDOR_DIR.iterdir():
        fp.unlink()

    # move directories to vendor/ for cleanliness
    with _cd(VENDOR_DIR):
        offline_install = pathlib.Path('offline-install.txt')
        cs_tools = pathlib.Path('cs_tools/')
        ts_tools = pathlib.Path('ts_tools/')

        # pip freeze > offline-install.txt
        with offline_install.open('w') as fp:
            sp.run('pip freeze', stdout=fp)

        # ensure we have thoughtspot packages installed
        with offline_install.open('r') as fp:
            if not any('thoughtspot' in line for line in fp.readlines()):
                raise RuntimeError('thoughtspot or thoughtspot-internal not found in virtual environment')

        # download our pip-installed packages, remove tmp installed file
        sp.run(f'pip download -r {offline_install} -d {VENDOR_DIR}')

        # cs_tools: clone, zip, clean up cloned
        sp.run('git clone https://github.com/thoughtspot/cs_tools.git')
        shutil.make_archive('thoughtspot-internal-0.1.0', 'zip', cs_tools)  # TODO grab version number dynamically
        shutil.rmtree(cs_tools, onerror=_rm_ro)

        # ts_tools: clone, zip, clean up cloned
        sp.run('git clone https://github.com/thoughtspot/ts_tools.git')
        shutil.make_archive('thoughtspot-0.1.0', 'zip', ts_tools)  # TODO grab version number dynamically
        shutil.rmtree(ts_tools, onerror=_rm_ro)
