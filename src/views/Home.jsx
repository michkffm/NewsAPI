import { useEffect, useState } from 'react';
import { useLocation, useSearchParams } from 'react-router-dom';
import { usePreferences, readLocal, writeLocal } from '../lib/preferences';
import { sections, safeArticle, getFilters, toggleBookmark } from '../lib/news';

export default function Home() {
  const { t, language } = usePreferences();
  const savedView = useLocation().pathname === '/saved';
  const [params, setParams] = useSearchParams();
  const filters = getFilters(params);
  const signature = JSON.stringify(filters);
  const [query, setQuery] = useState(filters.q);
  const [result, setResult] = useState({ articles: [], page: 1, pages: 0, total: 0 });
  const [loading, setLoading] = useState(!savedView);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [notice, setNotice] = useState('');
  const [saved, setSaved] = useState(() => {
    const value = readLocal('news-bookmarks', []);
    return Array.isArray(value) ? value.filter(safeArticle).slice(0, 100) : [];
  });
  useEffect(() => { setQuery(JSON.parse(signature).q); }, [signature]);
  useEffect(() => {
    if (savedView) { setLoading(false); return; }
    const controller = new AbortController();
    const timeout = setTimeout(() => { controller.abort(); setLoading(false); setError('timeout'); }, 20000);
    setLoading(true); setError('');
    fetch(`/api/news?${new URLSearchParams(JSON.parse(signature))}`, { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error(String(response.status));
        const data = await response.json();
        if (!Array.isArray(data.articles) || !data.articles.every(safeArticle) || ![data.page, data.pages, data.total].every(Number.isInteger)) throw new Error('invalid');
        if (!controller.signal.aborted) setResult(data);
      })
      .catch(error => { if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'network'); })
      .finally(() => { clearTimeout(timeout); if (!controller.signal.aborted) setLoading(false); });
    return () => { clearTimeout(timeout); controller.abort(); };
  }, [signature, savedView, attempt]);
  function update(patch) { setNotice(''); setParams({ ...filters, ...patch }); }
  function toggle(article) {
    const exists = saved.some(item => item.url === article.url);
    const next = toggleBookmark(saved, article);
    if (next === null) { setNotice(t('Die Merkliste ist auf 100 Artikel begrenzt.', 'Bookmarks are limited to 100 articles.')); return; }
    // Store links and titles, not copies of the provider's article text.
    if (!writeLocal('news-bookmarks', next)) { setNotice(t('Speichern im Browser ist nicht möglich.', 'Browser storage is unavailable.')); return; }
    setSaved(next); setNotice(exists ? t('Artikel entfernt.', 'Bookmark removed.') : t('Artikel gemerkt.', 'Article bookmarked.'));
  }
  async function share() {
    try { await navigator.clipboard.writeText(window.location.href); setNotice(t('Suchlink kopiert.', 'Search link copied.')); }
    catch { setNotice(t('Kopieren nicht möglich. Du kannst den Link aus der Adressleiste teilen.', 'Cannot copy. Share the link from your address bar instead.')); }
  }
  const labels = [t('Alle Themen', 'All topics'), t('Welt', 'World'), t('Technologie', 'Technology'), t('Wissenschaft', 'Science'), t('Wirtschaft', 'Business'), t('Sport', 'Sport'), t('Umwelt', 'Environment')];
  const articles = savedView ? saved : result.articles;
  const errors = {
    '503': t('Die Guardian-API ist noch nicht eingerichtet.', 'The Guardian API has not been configured yet.'),
    '429': t('Das Abruflimit ist erreicht. Bitte später erneut versuchen.', 'The request limit has been reached. Please try again later.'),
    '400': t('Bitte die Suchparameter überprüfen.', 'Please check your search parameters.'),
    timeout: t('Der Abruf dauert zu lange. Bitte erneut versuchen.', 'The request took too long. Please try again.')
  };
  return <main id="main" tabIndex={-1}><section className="hero"><p className="eyebrow">THE GUARDIAN · OPEN PLATFORM</p>
    <h1>{savedView ? t('Deine Leseliste.', 'Your reading list.') : t('Neue Perspektiven.\nJeden Tag.', 'Fresh perspectives.\nEvery day.')}</h1>
    <p className="hero-description">{savedView ? t('Deine gemerkten Artikel – direkt in diesem Browser.', 'Your bookmarked articles — saved in this browser.') : t('Entdecke Geschichten aus aller Welt. Finde die Themen, die dich bewegen.', 'Discover stories from around the world. Find the topics that matter to you.')}</p>
    <span className="source-note">{t('Oberfläche auf Deutsch · Artikel im englischen Original', 'English interface · Articles in their original language')}</span>
  </section>
    {!savedView && <section className="search-panel" aria-label={t('Nachrichtensuche', 'News search')}><form onSubmit={event => { event.preventDefault(); update({ q: query.trim(), page: 1 }); }}>
      <div className="search-row"><label className="search-label" htmlFor="search">{t('Was interessiert dich?', 'What interests you?')}</label><div className="search-input"><input id="search" type="search" value={query} maxLength={150} onChange={event => setQuery(event.target.value)} placeholder={t('Thema oder Stichwort, z. B. climate …', 'Topic or keyword, e.g. climate …')} /><button className="primary" type="submit" disabled={loading}>{t('Suchen', 'Search')} <span aria-hidden="true">↗</span></button></div></div>
      <div className="filter-row"><label>{t('Zeitraum', 'Date range')}<select value={filters.period} onChange={event => update({ period: event.target.value, q: query.trim(), page: 1 })}><option value="">{t('Alle Zeiträume', 'Any time')}</option><option value="day">{t('Letzte 24 Stunden', 'Last 24 hours')}</option><option value="week">{t('Letzte 7 Tage', 'Last 7 days')}</option><option value="month">{t('Letzte 30 Tage', 'Last 30 days')}</option></select></label>
      <label>{t('Sortierung', 'Sort by')}<select value={filters.sort} onChange={event => update({ sort: event.target.value, q: query.trim(), page: 1 })}><option value="newest">{t('Neueste zuerst', 'Newest first')}</option><option value="relevance">{t('Relevanz', 'Relevance')}</option></select></label><button className="share-button" type="button" onClick={share}>{t('Suche teilen', 'Share search')} ↗</button></div>
    </form><div className="topic-tabs" role="group" aria-label={t('Thema auswählen', 'Select topic')}>{sections.map((section, index) => <button key={section} className={filters.section === section ? 'selected' : ''} aria-pressed={filters.section === section} onClick={() => update({ section, q: query.trim(), page: 1 })}>{labels[index]}</button>)}</div></section>}
    <p className="notice" role="status">{notice}</p>
    <section className="results" aria-busy={loading}><div className="section-heading"><h2>{savedView ? t('Für später gespeichert', 'Saved for later') : t('Dein Nachrichtenüberblick', 'Your news briefing')}</h2>{!loading && (savedView || !error) && <span>{savedView ? saved.length : result.total} {t('Artikel', 'articles')}</span>}</div>
    {loading ? <div className="loading" role="status"><span className="loader" aria-hidden="true" />{t('Nachrichten werden geladen …', 'Loading news …')}</div> : error && !savedView ? <div className="empty-state" role="alert"><h3>{t('Kurz keine Verbindung.', 'Unable to connect.')}</h3><p>{errors[error] || t('Nachrichten konnten nicht geladen werden. Bitte erneut versuchen.', 'News could not be loaded. Please try again.')}</p><button onClick={() => setAttempt(value => value + 1)}>{t('Erneut versuchen', 'Try again')}</button></div> : <>
      <div className="article-grid">{articles.map(article => { const bookmarked = saved.some(item => item.url === article.url); return <article className="article-card" key={article.url}><div className="card-meta"><span>{article.category}</span><button className="bookmark" aria-pressed={bookmarked} aria-label={`${bookmarked ? t('Aus Merkliste entfernen', 'Remove bookmark') : t('Artikel merken', 'Bookmark article')}: ${article.title}`} onClick={() => toggle(article)}>{bookmarked ? '★' : '☆'}</button></div>
        <h3><a href={article.url} target="_blank" rel="noopener noreferrer">{article.title}</a></h3>{article.description && <p>{article.description}</p>}
        <div className="card-bottom"><small>{Number.isFinite(Date.parse(article.publishedAt)) ? <time dateTime={article.publishedAt}>{new Date(article.publishedAt).toLocaleDateString(language === 'de' ? 'de-DE' : 'en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</time> : 'The Guardian'}</small><a href={article.url} target="_blank" rel="noopener noreferrer" aria-label={`${t('Artikel lesen', 'Read article')}: ${article.title}`}>{t('Lesen', 'Read')} ↗</a></div></article>; })}</div>
      {articles.length === 0 && <div className="empty-state"><h3>{savedView ? t('Platz für gute Geschichten.', 'Room for great stories.') : t('Keine passenden Artikel.', 'No matching articles.')}</h3><p>{savedView ? t('Mit dem Stern an einem Artikel fügst du ihn deiner Merkliste hinzu.', 'Select the star on an article to add it to your bookmarks.') : t('Versuche einen anderen Suchbegriff oder einen größeren Zeitraum.', 'Try another keyword or a wider date range.')}</p></div>}
      {!savedView && result.pages > 1 && <nav className="pagination" aria-label={t('Ergebnisseiten', 'Result pages')}><button disabled={result.page <= 1} onClick={() => update({ page: result.page - 1 })}>← {t('Zurück', 'Previous')}</button><span>{t('Seite', 'Page')} {result.page} / {Math.min(50, result.pages)}</span><button disabled={result.page >= Math.min(50, result.pages)} onClick={() => update({ page: result.page + 1 })}>{t('Weiter', 'Next')} →</button></nav>}
    </>}</section>
  </main>;
}
