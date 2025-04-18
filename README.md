# Simpleafier

Simpleafier is a command line tool to help improve the quality of Lean code by converting any `simp` to `simp only`. This can help make Lean proofs more robust and maintainable by restricting the set of lemmas used by `simp`.

## Requirements

- Python 3.6+
- Lean 4
- `lake` must be installed and available in your PATH.

## Installation

Simpleafier is available on PyPI and can be installed using `pip`.

```bash
python -m pip install Simpleafier
```

## Usage

To convert all `simp` calls in a Lean file to `simp only`:

```bash
python -m simpleafier path/to/your/file.lean --simponly --fast
```

`simpleafier` must be invoked from the root of your lake project. The lean file provided must be compilable without any errors. `simpleafier` will create a temporary file in the same directory as the original file for processing. At the end of the process, the temporary file will be deleted and the original file will be replaced with the modified version.

The `--fast` flag provides significantly faster processing, but may result in less accurate results that may need more manual fixes. However it is currently the **recommended mode** for using `simpleafier` as it is more stable and gives reasonably good results.

> [!WARNING]
> This tool is still under development and does not guarantee perfect results. You may have to manually fix the output in some cases.

## License

This project is licensed under the MIT License.

## Contributing

Contributions, bug reports, and feature requests are welcome! Please open an issue or submit a pull request on GitHub.
