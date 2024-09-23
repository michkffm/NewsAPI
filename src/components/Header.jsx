import { Link } from 'react-router-dom';
import '../styles/Header.css';

export default function Header() {
    return (
        <header className="navbar">
          <h1>News App</h1>
          <nav>
            <Link to="/">Home</Link>
            <Link to="/top-headlines">Top Headlines</Link>
            <Link to="/news-sources">News Sources</Link>
          </nav>
        </header>
      );
    }
  