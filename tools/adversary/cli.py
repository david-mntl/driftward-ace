"""Command-line setup shared by the scripts, so every one gets `--help` from its own docstring."""

import argparse


def parser(doc):
    """An ArgumentParser whose help text is the script's docstring, line breaks kept."""
    return argparse.ArgumentParser(description=doc, formatter_class=argparse.RawDescriptionHelpFormatter)
