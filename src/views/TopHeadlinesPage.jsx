import { useState, useEffect } from 'react';
import TopHeadlines from '../components/TopHeadLines';
import '../styles/TopHeadlines.css';


function TopHeadlinesPage() {
  const [topHeadlines, setTopHeadlines] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const apiKey = '0b79abf6e76e48dfa741fce370a1f6b7';
    const url = `https://newsapi.org/v2/top-headlines?country=us&apiKey=${apiKey}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.status === 'ok' && data.articles.length > 0) {
          setTopHeadlines(data.articles);
        } else if (data.articles.length === 0) {
          setError('Keine Nachrichten verfügbar.');
        } else {
          setError(data.message || 'Ein unbekannter Fehler ist aufgetreten.');
        }
      })
      .catch(() => setError('Netzwerkfehler, bitte versuche es später erneut.'));
  }, []);

  if (error) {
    return <div>Fehler: {error}</div>;
  }

  return (
    <div>
      <h1>Top Headlines</h1>
      <TopHeadlines articles={topHeadlines} />
    </div>
  );
}

export default TopHeadlinesPage;
