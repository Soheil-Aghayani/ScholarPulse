# 🎓 ScholarPulse — Academic Publication Suite & Citation Formatter

[![Live Website](https://img.shields.io/badge/Live%20Website-GitHub%20Pages-2563eb?style=for-the-badge&logo=github)](https://soheil-aghayani.github.io/ScholarPulse/)
[![PWA Foundation](https://img.shields.io/badge/PWA-Foundation-10b981?style=for-the-badge&logo=pwa)](https://soheil-aghayani.github.io/ScholarPulse/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-amber?style=for-the-badge)](LICENSE)

**ScholarPulse** is a modern academic publication explorer and citation management platform. It allows researchers, students, and institutions to search scholars with typo-tolerant fuzzy matching, scrape Google Scholar profiles, resolve truncated paper titles (`...`) via CrossRef, generate citations across multiple styles (APA, IEEE, Harvard, MLA, BibTeX), analyze citation trajectories, and export clean publication lists directly to **Microsoft Word (.docx)**, **BibTeX (.bib)**, and **CSV**.

---

## 🌟 Live Demo

> 🌐 **Live Website**: [https://soheil-aghayani.github.io/ScholarPulse/](https://soheil-aghayani.github.io/ScholarPulse/)

ScholarPulse is architected to work **100% serverless in the browser** on GitHub Pages (querying global open academic registries directly via CORS) while also providing an optional high-performance local Python engine for Google Scholar scraping and native `.docx` generation.

---

## ✨ Key Features

### 1. 🔍 Typo-Tolerant Scholar Search
- Search scholars worldwide by name, institution, or research field.
- **Room for Mistakes**: Built-in Levenshtein edit-distance and phonetic transliteration variant expansion (e.g., `Ali Molasalehi` ↔ `Ali Mollasalehi`, `Rodabeh` ↔ `Roudabeh`, `Naser` ↔ `Nasser`, `Hosein` ↔ `Hossein`).
- Seamlessly falls back to client-side OpenAlex querying on static hosts like GitHub Pages.

### 2. 👤 High-Res Profile Pictures (No Initials)
- Displays genuine scholar profile portraits from Google Scholar.
- For all other global researchers, generates high-quality illustrated Notionist academic portraits—never showing boring plain letter initials.

### 3. 🎯 Full Title Restoration (Zero `...`)
- Resolves truncated titles and venues from Google Scholar using CrossRef API and clean regex heuristics.
- Eliminates duplicate trailing periods, trailing dates `(2021)`, and ellipsis characters (`...` and `…`).

### 4. 📄 Multi-Format Citation & Document Export
- **Microsoft Word (`.docx` / `.doc`)**: One-click download with professional typography (Calibri, hanging indent, styled headers). Works both via local Python engine and client-side browser builder.
- **BibTeX (`.bib`)**: Formatted entries with clean citation keys, author names, venues, and years.
- **CSV Spreadsheet (`.csv`)**: Full dataset with citations, DOI links, and publication years.
- **Citation Styles**: Instant toggle between **APA 7th**, **IEEE**, **Harvard**, **MLA 9th**, and **Chicago**.

### 5. 📊 Real-Time Bibliometrics & Analytics
- Dynamic calculation of Total Papers, Total Citations, **h-index**, and **i10-index**.
- Interactive publication trajectory charts by year and citation distribution breakdown.

### 6. 📱 PWA & Offline Ready
- Configured with `manifest.json` and service worker `sw.js`.
- Responsive across desktop, tablet, and mobile devices with Dark / Light theme support.

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
- Python 3.9+ (optional for local Google Scholar scraper & python-docx engine)

### 1. Clone the Repository
```bash
git clone https://github.com/Soheil-Aghayani/ScholarPulse.git
cd ScholarPulse
```

### 2. Install Dependencies (Optional for native DOCX & scraping)
```bash
pip install python-docx
```

### 3. Run the Local Server
```bash
python server.py
```
*Or double-click `start.bat` on Windows.*

Open your browser at **`http://localhost:5000`**.

---

## 🌐 Deploying to GitHub Pages

1. Push your repository to GitHub:
   ```bash
   git remote add origin https://github.com/Soheil-Aghayani/ScholarPulse.git
   git branch -M main
   git push -u origin main
   ```
2. In your GitHub repository, go to **Settings** > **Pages** and set **Source** to **GitHub Actions**.
3. The included `.github/workflows/pages.yml` publishes the site after each push. Within minutes, it will be accessible at:
   **`https://soheil-aghayani.github.io/ScholarPulse/`**

---

## 📁 Project Structure

```
ScholarPulse/
├── index.html                  # Single-page web application (UI, charts, client search, exports)
├── server.py                   # Lightweight Python backend (Scholar scraper, DOCX bridge, fuzzy API)
├── start.bat                   # 1-click Windows launcher
├── manifest.json               # Progressive Web App (PWA) manifest
├── sw.js                       # Service Worker for offline capabilities
├── scholar_8EUCPOUAAAAJ.json   # Pre-indexed publication dataset (Prof. Nasser Mehrdadi - 353 papers)
├── scholar_bnprOf8AAAAJ.json   # Pre-indexed publication dataset
├── scholar_u1PBvywAAAAJ.json   # Pre-indexed publication dataset (Prof. Yoshua Bengio)
├── .gitignore                  # Clean repository ignore rules
└── README.md                   # Project documentation
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
