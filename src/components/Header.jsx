import { NavLink } from 'react-router-dom';
import { usePreferences } from '../lib/preferences';
export default function Header() {
  const { language, setLanguage, theme, setTheme, t } = usePreferences();
  return <header className="navbar"><NavLink to="/" className="brand"><span className="brand-symbol" aria-hidden="true">n.</span><span>newsroom<small>THE DAILY PERSPECTIVE</small></span></NavLink>
    <nav aria-label={t('Hauptnavigation', 'Main navigation')}><NavLink to="/" end>{t('Entdecken', 'Discover')}</NavLink><NavLink to="/saved">{t('Merkliste', 'Bookmarks')}</NavLink><NavLink to="/news-sources">{t('Über die Quelle', 'About the source')}</NavLink></nav>
    <div className="preferences"><button aria-label={t('Sprache wechseln: Englisch', 'Switch language: German')} onClick={() => setLanguage(language === 'de' ? 'en' : 'de')}>{language === 'de' ? 'EN' : 'DE'}</button>
      <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} aria-label={theme === 'dark' ? t('Hellmodus aktivieren', 'Switch to light mode') : t('Dunkelmodus aktivieren', 'Switch to dark mode')}>{theme === 'dark' ? '☀' : '☾'}</button></div>
  </header>;
}
