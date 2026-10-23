import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Welcome from './components/Welcome';
import Login from './components/Login';
import Signup from './components/Signup';
// We will create these placeholders next
import Dashboard from './components/Dashboard'; 
import Settings from './components/Settings';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* When the URL is just "/", show the Welcome page */}
        <Route path="/" element={<Welcome />} />
        
        {/* When the URL is "/login", show the Login page */}
        <Route path="/login" element={<Login />} />
        
        {/* When the URL is "/signup", show the Signup page */}
        <Route path="/signup" element={<Signup />} />
        
        {/* The Dashboard and Settings (we will build these out in Phase 3 & 4) */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;