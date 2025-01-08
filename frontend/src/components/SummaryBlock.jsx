export default function SummaryBlock({ summary }) {
    return (
      <div className="bg-white shadow-lg rounded-lg p-6 mb-4">
        <h2 className="text-xl font-semibold mb-4">Summary:</h2>
        <p>{summary}</p>
      </div>
    );
  }
  