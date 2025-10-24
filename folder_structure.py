#!/usr/bin/env python3
"""
Folder Structure Display Tool
Displays directory tree structure with option to ignore specific folders
"""

# bonus_points_bot/folder_structure.py
import argparse
from datetime import datetime
from pathlib import Path


def print_tree(
    directory, prefix="", ignore_folders=None, is_last=True, output_file=None
):
    """
    Recursively print directory tree structure

    Args:
        directory: Path to the directory
        prefix: String prefix for tree formatting
        ignore_folders: Set of folder names to ignore
        is_last: Boolean indicating if this is the last item in current level
        output_file: File handle to write output (None for console)
    """
    if ignore_folders is None:
        ignore_folders = set()

    directory = Path(directory)

    # Print current directory
    connector = "└── " if is_last else "├── "
    line = f"{prefix}{connector}{directory.name}/"

    if output_file:
        output_file.write(line + "\n")
    else:
        print(line)

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
            print_tree(folder, new_prefix, ignore_folders, is_last_item, output_file)

        # Print files
        for i, file in enumerate(files):
            is_last_file = i == len(files) - 1
            file_connector = "└── " if is_last_file else "├── "
            line = f"{new_prefix}{file_connector}{file.name}"

            if output_file:
                output_file.write(line + "\n")
            else:
                print(line)

    except PermissionError:
        line = f"{new_prefix}[Permission Denied]"
        if output_file:
            output_file.write(line + "\n")
        else:
            print(line)


def main():
    parser = argparse.ArgumentParser(
        description="Display folder structure with optional ignore patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/folder
  %(prog)s . --ignore node_modules build
  %(prog)s ~/projects --ignore-hidden
  %(prog)s . -o structure.txt
  %(prog)s . --no-defaults -i __pycache__
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
        help="Additional folder names to ignore (e.g., node_modules .git)",
    )

    parser.add_argument(
        "--ignore-hidden",
        action="store_true",
        help="Ignore hidden folders (starting with .)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output file path (default: folder_structure_TIMESTAMP.txt)",
    )

    parser.add_argument(
        "--no-defaults",
        action="store_true",
        help="Don't use default ignore folders (__pycache__, .git, venv)",
    )

    args = parser.parse_args()

    # Prepare ignore set with defaults
    DEFAULT_IGNORES = {"__pycache__", ".git", "venv"}

    if args.no_defaults:
        ignore_folders = set(args.ignore)
    else:
        ignore_folders = DEFAULT_IGNORES | set(args.ignore)

    # Validate path
    target_path = Path(args.path).resolve()
    if not target_path.exists():
        print(f"Error: Path '{args.path}' does not exist")
        return 1

    if not target_path.is_dir():
        print(f"Error: Path '{args.path}' is not a directory")
        return 1

    # Determine output file
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"folder_structure_{timestamp}.txt")

    # Generate header
    header_lines = [
        "=" * 80,
        "Folder Structure",
        f"Path: {target_path}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    if ignore_folders:
        header_lines.append(f"Ignoring: {', '.join(sorted(ignore_folders))}")

    header_lines.extend(["=" * 80, ""])

    # Write to file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            # Write header
            for line in header_lines:
                f.write(line + "\n")

            # Write root directory
            f.write(f"{target_path.name}/\n")

            # Get items
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
                print_tree(folder, "", ignore_folders, is_last, f)

            # Print files
            for i, file in enumerate(files):
                is_last_file = i == len(files) - 1
                connector = "└── " if is_last_file else "├── "
                f.write(f"{connector}{file.name}\n")

        print(f"✅ Folder structure saved to: {output_path}")
        print(f"📊 Total size: {output_path.stat().st_size} bytes")

        # Also print to console
        print("\n" + "=" * 80)
        print("Preview:")
        print("=" * 80)
        with open(output_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Print first 30 lines as preview
            for line in lines[:30]:
                print(line.rstrip())
            if len(lines) > 30:
                print(f"\n... ({len(lines) - 30} more lines in file)")

        return 0

    except PermissionError:
        print(f"❌ Error: Permission denied writing to {output_path}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
