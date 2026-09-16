# ScholarPulse

[![Live website](https://img.shields.io/badge/Live%20website-GitHub%20Pages-2563eb?style=for-the-badge&logo=github&logoColor=white)](https://soheil-aghayani.github.io/ScholarPulse/)
[![Latest release](https://img.shields.io/github/v/release/Soheil-Aghayani/ScholarPulse?style=for-the-badge&label=Latest%20release)](https://github.com/Soheil-Aghayani/ScholarPulse/releases/latest)
[![Pages deployment](https://img.shields.io/github/actions/workflow/status/Soheil-Aghayani/ScholarPulse/pages.yml?branch=main&style=for-the-badge&label=Pages)](https://github.com/Soheil-Aghayani/ScholarPulse/actions/workflows/pages.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-amber?style=for-the-badge)](LICENSE)

ScholarPulse is a free academic research toolkit for finding scholars, loading Google Scholar profiles, cleaning publication metadata, formatting citations, and exporting research data. It runs in a browser, as an installable PWA, as a Windows desktop app, and as an Android APK.

## Use ScholarPulse

| Edition | Best for | What it needs |
| :--- | :--- | :--- |
| [Web app](https://soheil-aghayani.github.io/ScholarPulse/) | Any modern browser | Nothing to install. Pages uses the free hosted backend for exports and exact requests, with an OpenAlex fallback when it is unavailable. |
| [Hosted app](https://scholarpulse-hfew.onrender.com/) | Exact Scholar profile and publication requests | The free Render service. It may sleep when unused and Google Scholar may still rate-limit it. |
| Windows release | A dedicated PC workspace | Download the Windows installer from [Releases](https://github.com/Soheil-Aghayani/ScholarPulse/releases/latest). |
| Android release | ScholarPulse on a phone | Download and install the APK from [Releases](https://github.com/Soheil-Aghayani/ScholarPulse/releases/latest). |

No account, paid API, or bank-card information is required by ScholarPulse. The hosted backend is optional and runs on Render’s free plan.

Word exports from the backend are real `.docx` files. If no backend is reachable, ScholarPulse uses a clearly labeled Word-compatible `.doc` fallback instead of producing a misleading or corrupted `.docx` file.

## What it does

- Searches scholars by name, institution, or research field with typo-tolerant matching and common transliteration variants.
- Imports the exact visible Google Scholar author-search results, including real profile photo URLs, with the ScholarPulse bookmarklet.
- Loads Google Scholar publication profiles and keeps author metrics, citations, years, venues, and source links together.
- Restores truncated publication titles when Crossref can verify a matching record.
- Formats references as APA, IEEE, Harvard, MLA, Chicago, BibTeX, or a custom template.
- Exports publication data as Microsoft Word, BibTeX, CSV, or JSON.
- Saves scholars locally and compares up to three profiles without an account.
- Includes a responsive PWA shell with light/dark themes and offline access to the app shell.

## Search accuracy and profile photos

Google Scholar and OpenAlex are different data sources, so a browser-side fallback can return a different ranking, citation count, or photo. ScholarPulse labels the source instead of presenting those results as identical.

For the closest match to the Google Scholar page, use the hosted app or the exact-result importer:

1. Open the web app and choose **Open import guide** in the Search tab.
2. Save the **ScholarPulse Import** link as a bookmark. On a phone, long-press it and choose the browser’s bookmark option.
3. Search for authors on Google Scholar and open the author-search results page.
4. Run the saved bookmark. ScholarPulse opens with the visible names, photos, affiliations, and citation counts.

The importer reads only the cards already visible in your browser. It does not use an API key, bypass a challenge, or scrape Google Scholar from the server. If Scholar itself shows its graduation-cap placeholder, that placeholder is retained because the profile has no public photo URL.

## Run locally

### Web and Python backend

Prerequisites: Python 3.9 or newer. `python-docx` is installed from `requirements.txt` for Word export.

```bash
git clone https://github.com/Soheil-Aghayani/ScholarPulse.git
cd ScholarPulse
python -m pip install -r requirements.txt
python server.py
```

Open `http://localhost:5000`. On Windows, `start.bat` starts the same server.

### Native desktop development

The Windows and Android editions use Tauri 2 around the same frontend. Install Node.js 20+, Rust, Python, and the platform WebView/Android tools first.

```bash
npm install
npm run native:dev
```

The native build creates a clean `dist/` bundle and points the app at the free hosted backend by default. Override it for a private or local backend with `SCHOLARPULSE_API_BASE` before running the native build.

```powershell
$env:SCHOLARPULSE_API_BASE = 'https://your-backend.example.com'
npm run native:build
```

## Free backend deployment

GitHub Pages cannot run `server.py`, so the repository also includes a Render definition for the optional live backend:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Soheil-Aghayani/ScholarPulse)

1. Open the button and sign in to Render.
2. Keep the service on the Free plan.
3. Open the generated `*.onrender.com` URL on a phone or computer.
4. Check `/api/health` to confirm the service returns `"ok": true`.

Render can sleep after inactivity, so the first request may take a little longer. Google Scholar can also block anonymous automated requests. When that happens, use the exact-result importer or the OpenAlex fallback.

## Native releases

The `native-release.yml` workflow publishes a Windows installer and Android artifacts when a tag such as `v1.0.0` is pushed:

- Windows: NSIS `.exe` installer and MSI package.
- Android: signed APK for direct installation and AAB for a future store pipeline.

The first workflow run can generate a temporary Android signing key so the APK is installable without repository secrets. For seamless Android updates and Play Store publishing, configure a stable keystore through the repository secrets `ANDROID_KEY_BASE64`, `ANDROID_KEY_ALIAS`, and `ANDROID_KEY_PASSWORD`. The private keystore is never committed.

To publish a release after making a verified change:

```bash
git add .
git commit -m "release: ScholarPulse v1.0.0"
git tag v1.0.0
git push origin main --tags
```

The GitHub Actions job creates the release and uploads the native artifacts. The Android job runs after the desktop job so all artifacts land on one release page.

## Project structure

```text
ScholarPulse/
├── index.html                  # Single-page interface and browser logic
├── server.py                   # Optional Python backend and Word export bridge
├── scripts/build-app.mjs       # Clean web/native asset bundle builder
├── scripts/                    # Android release preparation helpers
├── src-tauri/                  # Windows and Android Tauri shell
├── icon.svg                    # Big Sur-inspired application mark
├── manifest.json               # PWA metadata and install icons
├── sw.js                       # Offline app-shell cache
├── render.yaml                 # Free Render service definition
└── .github/workflows/           # Pages and native release pipelines
```

## Limitations

- Google Scholar is an access-controlled public website. Results may be delayed, challenged, or unavailable from a hosted server.
- Citation counts and author rankings are source-specific and can change over time.
- OpenAlex, Crossref, Google Scholar, DiceBear, and Chart.js are external services used for specific features.
- ScholarPulse is a research utility, not a citation database or a replacement for checking the source publication.

## License

ScholarPulse is open source under the [MIT License](LICENSE).
