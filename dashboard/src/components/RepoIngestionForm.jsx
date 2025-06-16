import React, { useState } from "react";

export default function RepoIngestionForm({ onSubmit }) {
  const [owner, setOwner] = useState("");
  const [repo, setRepo] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (owner && repo) {
      onSubmit({ owner, repo });
      setOwner("");
      setRepo("");
    }
  };

  return (
    <form className="p-4 space-y-4 bg-white rounded-lg shadow-md" onSubmit={handleSubmit}>
      <h2 className="text-xl font-bold">Ingest New Repository</h2>
      <input
        type="text"
        placeholder="GitHub Owner"
        value={owner}
        onChange={(e) => setOwner(e.target.value)}
        className="w-full p-2 border rounded"
      />
      <input
        type="text"
        placeholder="GitHub Repository"
        value={repo}
        onChange={(e) => setRepo(e.target.value)}
        className="w-full p-2 border rounded"
      />
      <button type="submit" className="px-4 py-2 bg-blue-500 text-white rounded">
        Ingest Repository
      </button>
    </form>
  );
}
