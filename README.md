# Word poster generator

`poster.py` turns a topic into a portrait typographic poster: a large title, then the words that belong to it.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python3 poster.py                  # ocean, the built-in example
python3 poster.py coffee
python3 poster.py forest --style bloom -o output/forest.png
python3 poster.py "night shift" --words lamp,quiet,radio,window,ink,street
python3 poster.py --list
```

Built-in topics: ocean, forest, city, coffee, space, music, winter, garden, mountain, night, rain, library, desert, summer, cinema, kitchen, jazz.

`--style` can be `auto`, `cream`, `press`, `ink`, `sea`, `forest`, or `bloom`. `auto` picks a palette from the topic. `--seed` repeats the same layout. Images are written to `output/<topic>.png` unless `-o` is set.

For a topic that is not built in, pass `--words` as a comma-separated list, or `--words-file` for a text file (commas or one word per line).
