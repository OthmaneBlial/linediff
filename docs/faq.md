# FAQ

## What does Linediff add to a line diff?

On development `main`, `--display structural` names changed or moved Python functions, classes, and direct class methods, with source ranges. It also prints the exact text diff. The default mode is a plain unified diff. [Try the fixture](QUICKSTART.md).

## Which languages have a structural view?

Python only. Other UTF-8 text can be compared as text and gets an explicit fallback message in structural mode. Optional Tree-sitter grammars expose parser trees for eight languages, but do not provide structural CLI views for the other seven. See [parser support](PARSER_SUPPORT.md).

## Are Tree-sitter packages required?

No. Python definition matching uses the standard library AST. The optional Python grammar can provide source ranges. The base package has no required runtime dependencies.

## Can I apply the structural output as a patch?

No. Use the default unified view for an applicable text patch. The structural view is clearly labeled human-readable and includes the exact diff for inspection.

## How does `--check-only` exit?

It returns `0` for identical content, `1` for different content, and `2` for an input or processing error. Successful display mode returns `0` for both identical and changed files.

## Does `git diff | linediff` work?

No. Standard input accepts a Linediff-specific pair of texts separated by a line containing only `---`. For Git, use the one-shot external diff commands in the [usage guide](usage.md#git-integration).

## How are binary or large files handled?

Regular binary/non-UTF-8 file inputs return an error. Git external mode reports binary status. Text operands have explicit [size and complexity limits](LIMITS.md); an expensive line alignment uses an exact whole-file replacement patch. The Python structural view has tighter limits and may fall back to text.

## Is there a current downloadable release?

The `v0.1.3` tag predates the changes on `main`. A new GitHub Release, PyPI package, or standalone executable for the current code has not been verified. Install from the checkout for now; the [roadmap](../ROADMAP.md) lists the release gates.
