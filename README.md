# custom-ruler

A [Leptos](https://leptos.dev) app for printing **exact 1:1 measuring scales** and a
paper **caliper dial**, plus a client-side build of the matching **3D-printable**
ruler and dial caliper.

Everything is calibrated from two numbers: how many **units** you counted over how
many **millimetres** (`units per mm`), and the **max units** where the scale ends.
Tick density adapts in 1/2/5 steps, so the same page prints a metric ruler, an
inch ruler, or any custom scale.

The printable models are generated in the browser from
[build123d](https://build123d.readthedocs.io) running on
[Pyodide](https://pyodide.org) with [OCP.wasm](https://github.com/yeicor/OCP.wasm)
inside a Web Worker. Nothing is uploaded; the page hands back a single 3MF.

## Web app

Three cards:

- **Scale (exact size in print)** — landscape A4/US Letter sheet, stacked copies,
  optional ruler name, adjustable label size; prints at exact size.
- **Caliper dial (exact size in print)** — the paper dial face, derived by the same
  code the 3D model uses (`src/dial.rs`); prints at exact size.
- **3D printable models** — pick Ruler or Dial caliper, wait for the build, download
  the 3MF. For the caliper, the static hardware ships separately in
  `public/cad/caliper_static.3mf` and is combined in the slicer.

## Development

Prerequisites: Rust, the `wasm32-unknown-unknown` target, `cargo-leptos`, and Node
(for Tailwind).

```bash
rustup target add wasm32-unknown-unknown
cargo install cargo-leptos --locked
npm install
cargo leptos watch
```

Open <http://127.0.0.1:3000>. Release build: `cargo leptos build --release`.

## Layout

| path | what it is |
|---|---|
| `src/app.rs` | the UI, the scale SVG and the dial drawing |
| `src/scale.rs` | pure tick generation (1/2/5 steps, three tick levels) |
| `src/dial.rs` | dial geometry, shared by the paper dial and `cad/` |
| `src/paper.rs` | page sizes and print margins |
| `src/cad.rs` | worker wiring, `include_str!` of the Python model sources |
| `public/cad-worker.js` | Pyodide + build123d worker, emits the 3MF |
| `public/cad/`, `public/stl/` | static STEP/model assets and printed parts |
| `cad/` | the build123d sources — see [`cad/README.md`](cad/README.md) |
| `style/tailwind.css` | Tailwind + basecoat, print rules and bundled DIN lettering |

## 3D models from the command line

```bash
python -m venv .venv-cad
.venv-cad/bin/pip install -r cad/requirements.txt
.venv-cad/bin/python cad/caliper.py   # cad/out/caliper.3mf + caliper.step
.venv-cad/bin/python cad/ruler.py     # cad/out/ruler.3mf
.venv-cad/bin/python cad/check.py     # interference / mesh / solid checks
```

Parameters live at the top of `caliper.py` and `ruler.py` and can be overridden
from the environment — the same `CALIPER_*` variables the web worker passes:

```bash
CALIPER_UNITS=150 CALIPER_PER_MM=10 CALIPER_MAX_UNITS=1500 \
CALIPER_UNIT_NAME=u python cad/caliper.py
```

See [`cad/README.md`](cad/README.md) for the model, print and assembly details.

## Licence

MIT — see [LICENSE](LICENSE).

The bundled Alte DIN fonts in `public/fonts/` are licensed separately under the
GPL / SIL OFL — see [`public/fonts/AlteDIN-LICENSE.txt`](public/fonts/AlteDIN-LICENSE.txt).
The engraved stroke alphabet traced from the same letterforms is documented in
[`cad/fonts/NOTICE.md`](cad/fonts/NOTICE.md).
