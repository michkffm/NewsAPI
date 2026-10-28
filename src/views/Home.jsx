import { useEffect, useState } from 'react';

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let expired = false;
    const timeout = setTimeout(() => { expired = true; controller.abort(); setLoading(false); setError('Der Abruf dauert zu lange. Bitte erneut versuchen.'); }, 20000);
    setLoading(true);
    setError('');
    fetch('/api/news', { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error('Abruf fehlgeschlagen');
        const data = await response.json();
        if (!Array.isArray(data.articles) || !data.articles.every(a =>
          typeof a.title === 'string' && typeof a.description === 'string' &&
          typeof a.url === 'string' && a.url.startsWith('https://www.br.de/') &&
          typeof a.publishedAt === 'string')) throw new Error('Ungültige Antwort');
        if (!controller.signal.aborted) setArticles(data.articles);
      })
      .catch(() => { if (!controller.signal.aborted && !expired) setError('Die Nachrichten konnten nicht geladen werden. Bitte erneut versuchen.'); })
      .finally(() => { clearTimeout(timeout); if (!controller.signal.aborted) setLoading(false); });
    return () => { clearTimeout(timeout); controller.abort(); };
  }, [attempt]);
  const filtered = articles.filter(article => `${article.title} ${article.description}`.toLocaleLowerCase('de').includes(query.trim().toLocaleLowerCase('de')));
  return <main>
    <h1>Nachrichten im Überblick</h1>
    <p>Die neuesten Meldungen aus dem BR24-Feed. Quelle: <a href="https://www.br.de/nachrichten/" target="_blank" rel="noopener noreferrer">BR24 / Bayerischer Rundfunk</a>.</p>
    <label htmlFor="search">Aktuell geladene Meldungen durchsuchen</label>
    <input id="search" type="search" maxLength={150} value={query} onChange={event => setQuery(event.target.value)} placeholder="Thema oder Stichwort …" />
    {loading ? <p role="status">Nachrichten werden geladen …</p> : error ? <div role="alert"><p>{error}</p><button onClick={() => setAttempt(value => value + 1)}>Erneut versuchen</button></div> : <>
      <p role="status">{filtered.length} Meldungen</p>
      <ul>{filtered.map(article => <li key={article.url}>
        <article><h2><a href={article.url} target="_blank" rel="noopener noreferrer">{article.title}</a></h2>
          <p>{article.description}</p><small>Quelle: BR24{Number.isFinite(Date.parse(article.publishedAt)) && <> · <time dateTime={new Date(article.publishedAt).toISOString()}>{new Date(article.publishedAt).toLocaleString('de-DE')}</time></>}</small>
        </article>
      </li>)}</ul>
      {filtered.length === 0 && <p>Keine passenden Meldungen gefunden. Versuche einen anderen Suchbegriff.</p>}
    </>}
    <footer><p>Die Suche umfasst den aktuellen Feed, kein Nachrichtenarchiv. Inhalte werden unverändert als Text angezeigt; vollständige Artikel öffnen beim BR in einem neuen Tab.</p>
      <a href="https://www.br.de/service/nutzungsbedingungen-rss-feeds-100.html" target="_blank" rel="noopener noreferrer">Nutzungsbedingungen</a> · <a href="https://www.br.de/unternehmen/service/datenschutz/index.html" target="_blank" rel="noopener noreferrer">Datenschutz beim BR</a>
      <p>Der Feed wird über unseren Server geladen. Erst beim Öffnen eines Artikels verbindet sich dein Browser mit dem BR.</p></footer>
  </main>;
}
