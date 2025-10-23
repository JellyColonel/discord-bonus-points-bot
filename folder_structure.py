#!/usr/bin/env python3
"""
Folder Structure Display Tool
Displays directory tree structure with option to ignore specific folders
"""

# bonus_points_bot/folder_structure.py
import argparse
from pathlib import Path


def print_tree(directory, prefix="", ignore_folders=None, is_last=True):
    """
    Recursively print directory tree structure

    Args:
        directory: Path to the directory
        prefix: String prefix for tree formatting
        ignore_folders: Set of folder names to ignore
        is_last: Boolean indicating if this is the last item in current level
    """
    if ignore_folders is None:
        ignore_folders = set()

    directory = Path(directory)

    # Print current directory
    connector = "└── " if is_last else "├── "
    print(f"{prefix}{connector}{directory.name}/")

    # Update prefix for children
    extension = "    " if is_last else "│   "
    new_prefix = prefix + extension

    try:
        # Get all items in directory
        items = sorted(
            directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
        )

        # Filter out ignored folders
        items = [
            item
            for item in items
            if not (item.is_dir() and item.name in ignore_folders)
        ]

        # Separate folders and files
        folders = [item for item in items if item.is_dir()]
        files = [item for item in items if item.is_file()]

        # Print folders first
        for i, folder in enumerate(folders):
            is_last_item = (i == len(folders) - 1) and len(files) == 0
            print_tree(folder, new_prefix, ignore_folders, is_last_item)

        # Print files
        for i, file in enumerate(files):
            is_last_file = i == len(files) - 1
            file_connector = "└── " if is_last_file else "├── "
            print(f"{new_prefix}{file_connector}{file.name}")

    except PermissionError:
        print(f"{new_prefix}[Permission Denied]")


def main():
    parser = argparse.ArgumentParser(
        description="Display folder structure with optional ignore patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/folder
  %(prog)s . --ignore node_modules __pycache__
  %(prog)s ~/projects --ignore .git build dist
        """,
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the folder (default: current directory)",
    )

    parser.add_argument(
        "-i",
        "--ignore",
        nargs="+",
        default=[],
        help="Folder names to ignore (e.g., node_modules .git)",
    )

    parser.add_argument(
        "--ignore-hidden",
        action="store_true",
        help="Ignore hidden folders (starting with .)",
    )

    args = parser.parse_args()

    # Prepare ignore set
    ignore_folders = set(args.ignore)

    # Add hidden folders if requested
    if args.ignore_hidden:
        # We'll handle this in the print_tree function
        pass

    # Validate path
    target_path = Path(args.path).resolve()
    if not target_path.exists():
        print(f"Error: Path '{args.path}' does not exist")
        return 1

    if not target_path.is_dir():
        print(f"Error: Path '{args.path}' is not a directory")
        return 1

    # Print header
    print(f"\nFolder structure for: {target_path}")
    if ignore_folders:
        print(f"Ignoring: {', '.join(sorted(ignore_folders))}")
    print()

    # Print tree
    print(f"{target_path.name}/")

    try:
        items = sorted(
            target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
        )

        # Filter items
        if args.ignore_hidden:
            items = [item for item in items if not item.name.startswith(".")]

        items = [
            item
            for item in items
            if not (item.is_dir() and item.name in ignore_folders)
        ]

        folders = [item for item in items if item.is_dir()]
        files = [item for item in items if item.is_file()]

        # Print folders
        for i, folder in enumerate(folders):
            is_last = (i == len(folders) - 1) and len(files) == 0
            print_tree(folder, "", ignore_folders, is_last)

        # Print files
        for i, file in enumerate(files):
            is_last_file = i == len(files) - 1
            connector = "└── " if is_last_file else "├── "
            print(f"{connector}{file.name}")

    except PermissionError:
        print("[Permission Denied]")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
