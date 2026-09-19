# Terminal capture provenance

The two source fixtures in `data/move_*.py` are forced to LF on checkout so the recorded output remains reproducible on Git for Windows.

The [README image](../assets/terminal-structural-dark.svg) and its [light variant](../assets/terminal-structural-light.svg) are still frames rendered from the same real terminal recording: [`assets/casts/structural-output.cast`](../assets/casts/structural-output.cast). They show the output of this command run from the checkout after the base installation:

```bash
.venv/bin/linediff --display structural data/move_a.py data/move_b.py
```

The recording used `termtosvg-ng 1.4.1` with a 60-column, 18-row PTY. Rendering used its `gjm8` dark and `solarized_light` templates and selected the sole output frame. No output line was invented or altered. `tests/test_capture.py` compares the recorded terminal text with a fresh invocation of the installed package. The screenshots were visually reviewed at desktop and 390-pixel browser widths; the text is small on mobile but remains vector and zoomable. The final product video is a separate roadmap gate and has not been produced.

The [column view](../assets/terminal-columns-dark.svg) and [inline view](../assets/terminal-inline-dark.svg) were captured the same way from `data/move_a.py` and `data/move_b.py`, using `--color always`; their [light column](../assets/terminal-columns-light.svg) and [light inline](../assets/terminal-inline-light.svg) variants use the same recorded bytes. The raw [column](../assets/casts/columns-output.cast) and [inline](../assets/casts/inline-output.cast) casts are checked in. All three modes were visually reviewed on dark and light backgrounds. Colour supplements the `+`/`-` marks and line numbers; it does not carry the only meaning.

To recreate the cast on a POSIX host, use a virtual environment containing `termtosvg-ng==1.4.1` and the source installation of Linediff. Run `termtosvg record assets/casts/structural-output.cast -g 60x18 -c '.venv/bin/linediff --display structural data/move_a.py data/move_b.py'` in a real PTY. Then render still frames with `termtosvg render assets/casts/structural-output.cast OUTPUT_DIR --still-frames -t gjm8` or `-t solarized_light`. Capture only public fixture files; do not include private paths or credentials.
