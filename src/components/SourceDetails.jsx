import { useState, useEffect } from "react";
import TopHeadlines from "./TopHeadLines";

export default function SourceDetails({ source, onBack }) {
  const [topHeadlines, setTopHeadlines] = useState([]);
  const [error, setError] = useState(null);

  const handleError = (message) => {
    setError(message);
  };

  useEffect(() => {
    const apiKey = "0b79abf6e76e48dfa741fce370a1f6b7"; 
    const url = `https://newsapi.org/v2/top-headlines?sources=${source.id}&apiKey=${apiKey}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "ok") {
          setTopHeadlines(data.articles);
        } else {
          handleError("Fehler beim Abrufen der Top Headlines.");
        }
      })
      .catch(() => handleError("Netzwerkfehler, bitte versuche es später erneut."));
  }, [source.id]);

  if (error) {
    return <div>Fehler: {error}</div>;
  }

  return (
    <div>
      <h2>{source.name}</h2>
      <p>{source.description}</p>
      <button onClick={onBack}>Zurück zu den Quellen</button>
      <TopHeadlines articles={topHeadlines} />
    </div>
  );
}
