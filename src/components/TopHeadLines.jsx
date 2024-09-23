import { useState } from 'react';
import '../styles/TopHeadlines.css';

export default function TopHeadlines({ articles }) {
  const [selectedArticle, setSelectedArticle] = useState(null);

  const handleArticleClick = (article) => {
    setSelectedArticle(article);
  };

  const handleBack = () => {
    setSelectedArticle(null);
  };

  if (selectedArticle) {
    return (
      <div>
        <h2>{selectedArticle.title}</h2>
        <p>{selectedArticle.description}</p>
        <p>
          <strong>Quelle:</strong> {selectedArticle.source.name}
        </p>
        <button onClick={handleBack}>Zurück zu den Headlines</button>
      </div>
    );
  }

  return (
    <div>
      <ul className="headlines-list">
        {articles.map((article) => (
          <li key={article.url} onClick={() => handleArticleClick(article)}>
            {article.title}
          </li>
        ))}
      </ul>
    </div>
  );
}


