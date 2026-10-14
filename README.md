# Bulk File Renamer

A command-line utility for applying the same naming rules to many files. It prints a preview by default and checks for filename conflicts before making changes.

## Requirements

- Python 3.10 or newer
- No third-party packages

## Usage

Open Command Prompt or PowerShell in this project folder.

Preview a rename plan:

```powershell
py bulk_file_renamer.py "C:\Photos" --prefix "Trip_"
```

The preview is the default. It does not change any files.

Apply the plan after reviewing it. The program asks you to type `YES`:

```powershell
py bulk_file_renamer.py "C:\Photos" --prefix "Trip_" --apply
```

For scripts, `--yes` skips the confirmation prompt:

```powershell
py bulk_file_renamer.py "C:\Photos" --number --start 1 --width 4 --apply --yes
```

## Arguments containing spaces

Put double quotes around any argument that contains spaces. This applies to folder paths and text passed to `--prefix`, `--suffix`, `--find`, or `--replace`. Command Prompt and PowerShell both accept these examples:

```powershell
py bulk_file_renamer.py "C:\Users\Timur\Downloads\Organized\Images" --find "Снимок экрана" --replace "photo"
```

To add a prefix containing spaces:

```powershell
py bulk_file_renamer.py "C:\Photos" --prefix "Summer trip "
```

To replace a phrase with another phrase containing spaces:

```powershell
py bulk_file_renamer.py "C:\Photos" --find "old name" --replace "new name"
```

Without quotes, Windows passes each word as a separate command-line argument. The program will then report an unrecognized argument. The `--find` match is case-sensitive, so the capitalization must match the file names exactly.

## Options

| Option | Description |
| --- | --- |
| `folder` | Folder containing files to rename (required) |
| `--prefix TEXT` | Add text to the beginning of each file name |
| `--suffix TEXT` | Add text before each file extension |
| `--find TEXT` | Find this case-sensitive text in file names |
| `--replace TEXT` | Replacement text used with `--find`; can be empty to remove the matched text |
| `--number` | Append sequential numbers before file extensions |
| `--start N` | First sequence number (default: 1) |
| `--width N` | Minimum number of digits (default: 3) |
| `--recursive` | Include files in subfolders |
| `--apply` | Apply the previewed changes after confirmation |
| `--yes` | Skip confirmation; valid only with `--apply` |

## Rename rules and safety

Rules are applied in this order: find and replace, prefix, suffix, then numbering. Numbering follows the files' sorted path order. File extensions are preserved, and files are renamed in their current folders.

The preview lists each current name, proposed name, and status. The utility refuses to apply a plan if multiple files would get the same target name or if a target already exists and is not being renamed as part of the same batch. No files are changed when conflicts are found. During application, files are staged temporarily so swaps do not overwrite one another.

Renames cannot be undone automatically. Review the preview before using `--apply`. With `--apply --yes`, changes happen without an interactive confirmation prompt.
