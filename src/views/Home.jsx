import { useState } from 'react';

function Home() {
  const [searchTerm, setSearchTerm] = useState('');
  const [articles, setArticles] = useState([]);
  const [error, setError] = useState(null);

  const handleSearch = () => {
    const apiKey = '0b79abf6e76e48dfa741fce370a1f6b7';
    const url = `https://newsapi.org/v2/everything?q=${searchTerm}&apiKey=${apiKey}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.status === 'ok') {
          setArticles(data.articles);
        } else {
          setError('Ein Fehler ist aufgetreten.');
        }
      })
      .catch(() => setError('Netzwerkfehler, bitte erneut versuchen.'));
  };

  return (
    <div>
      <h1>Willkommen zur News App</h1>
      <p>Wähle eine der folgenden Optionen:</p>
      <input
        type="text"
        placeholder="Suche nach Nachrichten..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <button onClick={handleSearch}>Suchen</button>
      {error && <p>{error}</p>}
      <ul>
        {articles.map((article) => (
          <li key={article.url}>{article.title}</li>
        ))}
      </ul>
    </div>
  );
}

export default Home;

