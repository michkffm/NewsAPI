import { useState, useEffect } from 'react';
import '../styles/NewsSources.css';

function NewsSources() {
  const [sources, setSources] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const apiKey = '0b79abf6e76e48dfa741fce370a1f6b7';
    const url = `https://newsapi.org/v2/top-headlines/sources?apiKey=${apiKey}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.status === 'ok') {
          setSources(data.sources);
        } else {
          setError('Fehler beim Abrufen der Quellen.');
        }
      })
      .catch(() => setError('Netzwerkfehler, bitte versuche es später erneut.'));
  }, []);

  return (
    <div>
      <h1>Nachrichtenquellen</h1>
      {error ? (
        <p>{error}</p>
      ) : (
        <ul>
          {sources.map((source) => (
            <li key={source.id}>
              {source.name}
              <p>{source.description}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default NewsSources;
