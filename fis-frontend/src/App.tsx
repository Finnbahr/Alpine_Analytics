import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Home from './pages/Home';
import Leaderboards from './pages/Leaderboards';
import AthleteProfile from './pages/AthleteProfile';
import Courses from './pages/Courses';
import Analytics from './pages/Analytics';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/leaderboards" element={<Leaderboards />} />
        <Route path="/leaderboards/:discipline" element={<Leaderboards />} />
        <Route path="/athletes" element={<ComingSoon title="Athletes" />} />
        <Route path="/athletes/:fisCode" element={<AthleteProfile />} />
        <Route path="/races" element={<ComingSoon title="Races" />} />
        <Route path="/courses" element={<Courses />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </div>
  );
}

function ComingSoon({ title }: { title: string }) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">{title}</h1>
      <p className="text-xl text-gray-600">Coming soon...</p>
    </div>
  );
}

export default App;
