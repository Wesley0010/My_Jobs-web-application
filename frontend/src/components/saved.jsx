import AppLayout from './AppLayout';

function Saved() {
  return (
    <AppLayout>
      <div className="dashboard-panel">
        <h2>Saved Jobs</h2>
        <p style={{ color: '#718096', marginTop: 8 }}>
          Your saved jobs will appear here.
        </p>
      </div>
    </AppLayout>
  );
}

export default Saved;