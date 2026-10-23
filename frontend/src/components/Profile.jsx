import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from './AppLayout';
import { getUser, apiMe, isAuthenticated } from '../lib/auth';
import './Profile.css';

function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(getUser());
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const [draft, setDraft] = useState({
    name: user?.name || '',
    email: user?.email || '',
    bio: user?.bio || '',
    location: user?.location || '',
    phone: user?.phone || '',
  });

  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login', { replace: true });
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const fresh = await apiMe();
        if (!cancelled) setUser((prev) => ({ ...prev, ...fresh }));
      } catch {
        navigate('/login', { replace: true });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  if (!user) return null;

  const startEdit = () => {
    setDraft({
      name: user.name || '',
      email: user.email || '',
      bio: user.bio || '',
      location: user.location || '',
      phone: user.phone || '',
    });
    setEditing(true);
    setMessage({ type: '', text: '' });
  };

  const cancelEdit = () => {
    setEditing(false);
    setMessage({ type: '', text: '' });
  };

  const handleChange = (field) => (e) => {
    setDraft((d) => ({ ...d, [field]: e.target.value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });

    if (!draft.name.trim()) {
      setMessage({ type: 'error', text: 'Name cannot be empty' });
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(draft.email)) {
      setMessage({ type: 'error', text: 'Please enter a valid email' });
      return;
    }

    setSaving(true);
    try {
      await new Promise((r) => setTimeout(r, 500));
      const updated = {
        ...user,
        name: draft.name.trim(),
        email: draft.email.trim().toLowerCase(),
        bio: draft.bio.trim(),
        location: draft.location.trim(),
        phone: draft.phone.trim(),
      };
      setUser(updated);
      setEditing(false);
      setMessage({ type: 'success', text: 'Profile updated successfully' });
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Update failed' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppLayout>
      <div className="profile-main">
        <div className="panel-header">
          <div>
            <h2>Profile Information</h2>
            <p>Manage your personal details</p>
          </div>
          {!editing && (
            <button className="btn-small" onClick={startEdit}>
              ✏️ Edit
            </button>
          )}
        </div>

        {message.text && (
          <p className={`message ${message.type}`}>{message.text}</p>
        )}

        {!editing ? (
          <div className="profile-view">
            <Field label="Full Name" value={user.name} />
            <Field label="Email" value={user.email} />
            <Field label="Phone" value={user.phone || '—'} />
            <Field label="Location" value={user.location || '—'} />
            <Field label="Bio" value={user.bio || 'No bio yet.'} full />
          </div>
        ) : (
          <form className="profile-form" onSubmit={handleSave} noValidate>
            <div className="form-group">
              <label>Full Name</label>
              <input
                value={draft.name}
                onChange={handleChange('name')}
                disabled={saving}
              />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={draft.email}
                onChange={handleChange('email')}
                disabled={saving}
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Phone</label>
                <input
                  value={draft.phone}
                  onChange={handleChange('phone')}
                  disabled={saving}
                />
              </div>
              <div className="form-group">
                <label>Location</label>
                <input
                  value={draft.location}
                  onChange={handleChange('location')}
                  disabled={saving}
                />
              </div>
            </div>
            <div className="form-group">
              <label>Bio</label>
              <textarea
                rows={4}
                value={draft.bio}
                onChange={handleChange('bio')}
                disabled={saving}
              />
            </div>
            <div className="form-actions">
              <button
                type="button"
                className="btn-small btn-ghost"
                onClick={cancelEdit}
                disabled={saving}
              >
                Cancel
              </button>
              <button type="submit" className="btn-small" disabled={saving}>
                {saving ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </form>
        )}
      </div>
    </AppLayout>
  );
}

function Field({ label, value, full = false }) {
  return (
    <div className={`view-field ${full ? 'full' : ''}`}>
      <span className="view-label">{label}</span>
      <span className="view-value">{value || '—'}</span>
    </div>
  );
}

export default Profile;