import { Navigate } from 'react-router-dom';
import { isAuthenticated } from './auth';

function PublicOnly({ children }) {
  return isAuthenticated() ? <Navigate to="/dashboard" replace /> : children;
}

export default PublicOnly;