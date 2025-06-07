import sys

def docopt(docstring=None, argv=None, **kwargs):
    if argv is None:
        argv = sys.argv[1:]
    result = {"--large": False, "--no-sudo": False, "<command>": []}
    for arg in argv:
        if arg == "--large":
            result["--large"] = True
        elif arg == "--no-sudo":
            result["--no-sudo"] = True
        else:
            result["<command>"].append(arg)
    return result

__all__ = ["docopt"]
