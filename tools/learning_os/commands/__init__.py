"""Command implementations for the `los` CLI.

Each module owns one domain. `los.py` keeps only argparse wiring and the
command registry, so finding a behaviour means opening the module named after
it rather than searching one long file.
"""
