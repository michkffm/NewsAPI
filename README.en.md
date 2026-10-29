# News App · The Guardian

[Deutsch](README.md) | **English**

A project by Michael Koch

**[Open the live demo](https://newsroom-michkffm.onrender.com/)**

The app is deployed on Render. News retrieval, search, topic and date filters, pagination and bookmarks have been verified in the browser using the Guardian API.

A news application built with React and a custom Python API. The Guardian Open Platform provides articles that can be searched by keyword and topic.

## Features

- Load news from an external JSON API
- Keyword search, topic and date filters, sorting by date or relevance
- Shareable search links with filters and page number
- German/English interface and persistent light/dark mode
- Local bookmarks for up to 100 article links without an account
- Responsive news cards and keyboard support
- Colour accents, hover effects and subtle animations with reduced-motion support
- Pagination with ten articles per page
- Loading indicators, clear error messages and retry controls
- Open original articles in a new tab
- Keep the API key exclusively on the server

Articles are mainly in English. The interface supports German and English; article content is not translated.

## Interface

![Published Guardian search in the apricot theme](docs/newsroom-live.png)

Bookmarks store only article titles, links, sections and publication dates in the browser, not article bodies. Use the star to add or remove entries. The initial appearance follows the system theme; a manual choice is remembered. Clearing browser data removes bookmarks and preferences.

## Technologies

| Area | Technology |
| --- | --- |
| Frontend | React 18, React Router 7, CSS |
| Build | Vite 8, npm |
| Backend | Python 3, standard library |
| News | The Guardian Open Platform |
| Hosting | Render web service |

## API integration

```text
React → GET /api/news → Python backend → Guardian Content API
```

The app sends the search term, topic and page to its own backend. The backend validates parameters, calls the fixed Guardian endpoint and returns a normalized JSON response. The API key is read from an environment variable and is neither sent to the browser nor stored in the repository.

`GET /api/news?q=climate&section=science&page=1&period=week&sort=relevance` searches articles. `GET /health` checks server availability. Searches run when the form is submitted, rather than on every keystroke.

Results are cached in memory for five minutes. New provider requests are limited within the process to one per 1.1 seconds and 450 per UTC day. Server restarts reset these local counters; the provider's actual limit still applies to the API key. The free Guardian tier is intended for non-commercial use and provides up to 500 requests daily. [Provider information](https://open-platform.theguardian.com/access/)

## Running locally

Requirements: Node.js 22.12 or later within version 22, npm and Python 3.

```sh
git clone https://github.com/michkffm/NewsAPI.git
cd NewsAPI
npm ci
npm run build
```

Set `GUARDIAN_API_KEY` in your terminal to your own key, keeping it out of files and command examples. Then run:

```sh
python3 server/app.py
```

Open **http://localhost:8766/**. Without a key, the app displays a configuration message. For frontend development, also run `npm run dev`; Vite proxies `/api` to the local Python server.

## Configuration and deployment

| Variable | Purpose |
| --- | --- |
| `GUARDIAN_API_KEY` | Secret Guardian API key, backend only |
| `PORT` | Server port; defaults to 8766 locally, set automatically by Render |

`render.yaml` describes a free Python web service. Build: `npm ci && npm run build`. Start: `python3 server/app.py`. Store the key as a secret environment variable in the Render dashboard. A Render Static Site cannot run the backend. Free web services may sleep when inactive and take some time to start on the next request.

The previous RSS integration has been replaced. Earlier NewsAPI keys may remain in Git history or old builds and must be revoked with the previous provider.

## Tests

```sh
python3 -m unittest discover -s server
npm run lint
npm run build
npm audit
```

Backend tests cover search parameters, data validation, safe article links, caching, missing keys and request limits. They use synthetic responses and do not require a real API key.

## Source

Powered by [The Guardian](https://www.theguardian.com/). News content © Guardian News & Media Ltd or the respective rights holders. This is a non-commercial portfolio demo, not an official Guardian product.

## Author

[Michael Koch](https://github.com/michkffm)
