# Screenshot Capture Guide

The four images referenced in the project README live here. Capture them with
Sensei running locally; aim for **1920 × 1080** crops with the operator browser
fully zoomed (Ctrl+0 to reset).

| Filename | What to capture | Suggested setup |
|---|---|---|
| `display-flow-paper.png`   | `/display` fullscreen showing a flow_diagram card | Theme = **Paper**, F11 fullscreen, run the wind-turbine flow example |
| `operator-console.png`     | Operator UI in English with the Live tab focused | UI Language = **English**, Theme = **Paper**, click into 🔴 Live tab |
| `live-recording.png`       | Operator UI mid-recording (red status, "⏹ Stop & Generate") | Press F8, screenshot during the recording state |
| `extend-card.png`          | Side-by-side: an enumeration card + the cursor over "Extend Last" button | Generate enumeration, hover (or click) Extend Last |

## Capture tips

- Use Windows **Snipping Tool** (`Win+Shift+S`) → "Window" mode for clean borders
- Or browser `F12` → Device Toolbar → set viewport size, then the in-DevTools "capture full size screenshot"
- Save as PNG (lossless), under 500 KB each ideally
- If the file is too large, run through tinypng.com or `pngquant`

## Once you have them

Drop the PNGs in this directory with the exact filenames above. The README will
pick them up automatically. Then commit and push:

```powershell
git add docs/screenshots/*.png
git commit -m "Add README screenshots"
git push
```

## Backup plan if you don't have time

The four image references in README.md will show as broken links. To hide them
gracefully, comment out or remove the `## Screenshots` section in `README.md`
(lines around 14-22) until you have the captures.
