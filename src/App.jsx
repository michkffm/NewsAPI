import { useEffect, useState } from 'react';
import { HashRouter, Routes, Route } from 'react-router-dom';
import NewsSources from './views/NewsSources';
import Header from './components/Header';
import Home from './views/Home';
import { Preferences, readLocal, writeLocal } from './lib/preferences';
import './App.css';

export default function App() {
  const [language, setLanguage] = useState(() => readLocal('news-language', 'de') === 'en' ? 'en' : 'de');
  const [theme, setTheme] = useState(() => {
    const stored = readLocal('news-theme', null);
    return stored === 'dark' || stored === 'light' ? stored : window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });
  const t = (de, en) => language === 'de' ? de : en;
  useEffect(() => { document.documentElement.lang = language; writeLocal('news-language', language); }, [language]);
  useEffect(() => { document.documentElement.dataset.theme = theme; writeLocal('news-theme', theme); }, [theme]);
  return <Preferences.Provider value={{ language, setLanguage, theme, setTheme, t }}>
    <HashRouter><a className="skip-link" href="#main" onClick={event => { event.preventDefault(); document.getElementById("main")?.focus(); }}>{t('Zum Inhalt', 'Skip to content')}</a><Header />
      <div className="App"><Routes>
        <Route path="/" element={<Home />} /><Route path="/top-headlines" element={<Home />} />
        <Route path="/saved" element={<Home />} /><Route path="/news-sources" element={<NewsSources />} />
      </Routes></div>
      <footer className="site-footer"><p>{t('Projekt von Michael Koch', 'A project by Michael Koch')}</p>
        <p>Powered by <a href="https://www.theguardian.com/" target="_blank" rel="noopener noreferrer">The Guardian</a> · © Guardian News &amp; Media Ltd.</p>
        <p>{t('Nichtkommerzielle Portfolio-Demo. Artikel bleiben in ihrer Originalsprache.', 'Non-commercial portfolio demo. Articles remain in their original language.')}</p>
        <a href="https://github.com/michkffm" target="_blank" rel="noopener noreferrer">{t('Autor: Michael Koch', 'Author: Michael Koch')}</a>
      </footer>
    </HashRouter>
  </Preferences.Provider>;
}
