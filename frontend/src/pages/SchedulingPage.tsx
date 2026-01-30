export default function SchedulingPage() {
  return (
    <div>
      <div className="page-header">
        <h2>Scheduling</h2>
        <p>Generate and manage school schedules</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Schedule Generation</h3>
        </div>
        <div className="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
          </svg>
          <p>Schedule generation coming soon!</p>
          <p style={{ fontSize: "0.875rem", marginTop: "0.5rem" }}>
            This feature will use constraint optimization to generate optimal timetables.
          </p>
        </div>
      </div>
    </div>
  );
}
