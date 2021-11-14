import json
import os
import pkgutil
import subprocess
import sys

from importlib import import_module

from mapclient.core.utils import is_frozen
from mapclient.settings.definitions import PLUGINS_PACKAGE_NAME, FROZEN_PROVENANCE_INFO_FILE


def _strip_pip_list_output(output_stream):
    output = {}
    content = output_stream.decode()
    lines = content.split('\n')
    lines.pop(0)
    lines.pop(0)
    for line in lines:
        parts = line.split()
        if len(parts) > 1:
            output[parts[0]] = {'version': parts[1]}
            if len(parts) > 2:
                if os.path.isdir(parts[2]):
                    output[parts[0]]['location'] = 'locally-acquired'
                else:
                    output[parts[0]]['location'] = parts[2]

    return output


def _determine_capabilities():
    print('here 1', flush=True)
    try:
        import mapclientplugins
        mapclientplugins_present = True
    except ModuleNotFoundError:
        mapclientplugins_present = False

    print('here 2', flush=True)
    my_env = os.environ.copy()
    python_executable = sys.executable

    print('here 3', flush=True)
    result = subprocess.run([python_executable, "-m", "pip", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env)

    print('here 4', flush=True)
    output_info = _strip_pip_list_output(result.stdout)

    print('here 5', flush=True)
    mapclientplugins_info = {}
    if mapclientplugins_present:
        print('here 6', flush=True)
        print(mapclientplugins.__path__, flush=True)
        for loader, module_name, is_pkg in pkgutil.walk_packages(mapclientplugins.__path__):
            if is_pkg:
                package_name = PLUGINS_PACKAGE_NAME + '.' + module_name
                print('here 6a', flush=True)
                print(package_name, flush=True)
                try:
                    banned_list = [
                        'mapclientplugins.argonsceneexporterstep',
                        'mapclientplugins.argonviewerstep',
                        'mapclientplugins.dataembedderstep'
                    ]
                    if package_name in banned_list:
                        print('skipping this package.', flush=True)
                    else:
                        module = import_module(package_name)
                        print('here 6b', flush=True)
                        print(module.__version__, flush=True)
                        mapclientplugins_info[package_name] = {
                            "version": module.__version__ if hasattr(module, '__version__') else "X.Y.Z",
                            "location": module.__location__ if hasattr(module, '__location__') else "",
                        }
                except Exception as e:
                    print('exception happened.', flush=True)
                    print(e, flush=True)

    print('here 7', flush=True)
    print(output_info, flush=True)

    return {**output_info, **mapclientplugins_info}


def reproducibility_info():
    print('arrived', flush=True)
    if is_frozen():
        info_file = os.path.join(sys._MEIPASS, FROZEN_PROVENANCE_INFO_FILE)
        with open(info_file) as f:
            content = f.read()
        r = json.loads(content)
    else:
        r = _determine_capabilities()

    return r
