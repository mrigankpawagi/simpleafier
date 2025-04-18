#!/usr/bin/env python3
import argparse
import sys
import os
import re
import subprocess
import json
import random


def __process_simponly_info_object(info_object, content):
    lines = content.splitlines()
    
    start_line = info_object["pos"]["line"] - 1 # lines are 1-indexed in Lean
    start_col = info_object["pos"]["column"]
    suggestion = info_object["data"].split("Try this: ", 1)[1].strip()

    start_pos = len("\n".join(lines[:start_line])) + start_col
    if start_line > 0:
        start_pos += 1
    
    # suggestion may contain newlines
    suggestion = suggestion.replace("\n", "")
    
    # find the end position of the "simp" statement
    
    # check if the suggestion contains "at"
    if re.search(r"\bat\b", suggestion):
        # usually the suggestion will have "[...]"
        if "]" in suggestion:
            if re.search(r"\bat\b", suggestion[suggestion.rfind("]"):]):
                # and "at" appears after "[...]"
                first_at_pos_in_suggestion = re.search(r"\bat\b", suggestion[suggestion.rfind("]"):]).start() + suggestion.rfind("]")
                word_after_at = suggestion[first_at_pos_in_suggestion+2:].split()[0]
                
                # Find the first occurrence of "at" such that the next thing is `word_after_at` 
                for match in re.finditer(r"\bat\b", content[start_pos:]):
                    pos = match.start()
                    if content[start_pos + pos + 2:].split()[0] == word_after_at:
                        first_at_pos = pos + start_pos
                        break

        else:
            # the suggestion is like "simp only at ..."
            # (this simp is probably useless and may be removed...)
            first_at_pos = re.search(r"\bat\b", content[start_pos:]).start() + start_pos 
            first_at_pos_in_suggestion = re.search(r"\bat\b", suggestion).start()
            word_after_at = suggestion[first_at_pos_in_suggestion+2:].split()[0]

        # now find the first ocurrence of `word_after_at` after the first "at"
        word_after_at_pos = content.find(word_after_at, first_at_pos+2)
        end_pos = word_after_at_pos + len(word_after_at) - 1
    else:
        # we have one of "simp", "simp [...]", "simp only [...]"
        # (each of these is actually "simp?")
        
        # find the first non-whitespace character after "simp" in content
        first_non_whitespace_char = content[start_pos+5:].lstrip()[0]
        first_non_whitespace_char_pos = content.find(first_non_whitespace_char, start_pos + 5)
        
        if (
            first_non_whitespace_char == "[" or 
            content[first_non_whitespace_char_pos:first_non_whitespace_char_pos + 4] == "only"
        ):
            # find the first "]" after this
            closing_bracket_pos = content.find("]", first_non_whitespace_char_pos)
            end_pos = closing_bracket_pos
            
        else:
            # just select "simp"
            underlined_length = info_object["endPos"]["column"] - start_col
            end_pos = start_pos + underlined_length - 1

    return start_pos, end_pos, suggestion


def __get_info_objects(file_name):
    # Run the Lean file using lake
    result = subprocess.run(
        ["lake", "env", "lean", "--run", file_name, "--json"],
        capture_output=True,
        text=True,
        check=False
    )

    info_objects = []
    for line in result.stdout.splitlines():
        try:
            info_object = json.loads(line)
            if info_object["data"].startswith("Try this: simp"):
                info_objects.append(info_object)
        except json.JSONDecodeError:
            pass

    return info_objects


def __replace_simp(content):
    # Replace 'simp' with 'simp?' but it should not already be simp?
    new_content = re.sub(r"\bsimp", "simp?", content)
    new_content = re.sub(r"\bsimp\?\?", "simp?", new_content)

    # Change any "@[simp?]" back to "@[simp]"
    new_content = re.sub(r"@\[simp\?\]", "@[simp]", new_content)

    return new_content


def convert_simp_to_simponly(lean_file, fast_mode=False):
    try:
        temp_file_path = os.path.join(os.path.dirname(lean_file), f"simpleafier_temp{random.randint(10000, 99999)}.lean")
        with open(lean_file, "r", encoding="utf-8") as f:
            content = f.read()

        if not fast_mode:
            k = 0
            while True:
                new_content = __replace_simp(content)

                with open(temp_file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                
                info_objects = __get_info_objects(temp_file_path)
                
                # we will only process the k-th simp? in the file
                if len(info_objects) <= k:
                    break
                
                content = new_content

                info_object = info_objects[k]
                print(f"Applying suggestion {k+1}/{len(info_objects)}: {info_objects[k]['data']}")

                start_pos, end_pos, suggestion = __process_simponly_info_object(info_object, content)
                content = content[:start_pos] + suggestion + content[end_pos+1:]

                # replace any remaining simp? with simp
                content = re.sub(r"\bsimp\?", "simp", content)

                k += 1

            # Write the modified content to the actual Lean file
            with open(lean_file, "w", encoding="utf-8") as f:
                f.write(content)
        
        else:
            content = __replace_simp(content)

            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            info_objects = __get_info_objects(temp_file_path)            

            replacements = {}
            for k, info_object in enumerate(info_objects):
                print(f"Registering suggestion {k+1}/{len(info_objects)}: {info_object['data']}")
                start_pos, end_pos, suggestion = __process_simponly_info_object(info_object, content)
                replacements[(start_pos, end_pos)] = suggestion

            # replace in reverse order so as to not mess up indexes
            replacement_pos = list(replacements.keys())
            replacement_pos.sort(reverse=True)
            for k, (start_pos, end_pos) in enumerate(replacement_pos):
                suggestion = replacements[(start_pos, end_pos)]
                content = content[:start_pos] + suggestion + content[end_pos+1:]

            # replace any remaining simp? with simp
            content = re.sub(r"\bsimp\?", "simp", content)

            # Write the modified content to the actual Lean file
            with open(lean_file, "w", encoding="utf-8") as f:
                f.write(content)

    finally:
        # if the temp file was created, delete it before exiting
        if os.path.isfile(temp_file_path):
            try:
                os.remove(temp_file_path)
                pass
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Simpleafier: A command line tool to help improve the quality of Lean code."
    )
    parser.add_argument(
        "lean_file",
        type=str,
        help="Path to the Lean file (relative to project root). Make sure that the file compiles without errors."
    )
    parser.add_argument(
        "--simponly",
        action="store_true",
        help="Convert any simp to simp only. Warning: This is not intended to be either sound or complete. Use with caution."
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run in fast mode by reducing accuracy."
    )
    args = parser.parse_args()

    # Check if the file exists
    if not os.path.isfile(args.lean_file):
        print(f"Error: File '{args.lean_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if args.simponly:
        convert_simp_to_simponly(args.lean_file, args.fast)
    else:
        print("No feature flag provided. Use --help for help.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
