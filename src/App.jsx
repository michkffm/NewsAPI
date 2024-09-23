import { HashRouter,  Routes, Route } from 'react-router-dom';
import NewsSources from './views/NewsSources';
import './App.css';
import Header from "./components/Header";
import Home from "./views/Home";
import TopHeadlinesPage from "./views/TopHeadlinesPage"; 

function App() {
  return (
    <HashRouter>
      <Header />
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/top-headlines" element={<TopHeadlinesPage />} />
          <Route path="/news-sources" element={<NewsSources />} />
        </Routes>
      </div>
    </HashRouter>
  );
}

export default App;