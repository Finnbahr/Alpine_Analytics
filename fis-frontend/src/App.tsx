import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import AthleteProfile from './pages/AthleteProfile';

function App() {
  return (
    <div className="min-h-screen bg-black">
      <Header />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/athletes/:fisCode" element={<AthleteProfile />} />
      </Routes>
    </div>
  );
}

export default App;
