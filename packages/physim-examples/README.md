# physim-examples

Runnable example scenes for [physim](https://github.com/TRC-Loop/physim).

```bash
pip install physim[examples]
python -m physim_examples                      # list them
python -m physim_examples.bouncing_ball        # render one
python -m physim_examples.escape_ring --debug  # with the stats overlay
```

Each example is a plain Python file, so it also works as a starting point for
your own scenes:

```bash
physim render $(python -c "import physim_examples.bouncing_ball as m; print(m.__file__)")
```
