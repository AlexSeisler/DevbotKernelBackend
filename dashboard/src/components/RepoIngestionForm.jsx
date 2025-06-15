import React, { useState } from 'react';
import axios from 'axios';

export default function RepoIngestionForm() {
  const [owner, setOwner] = useState('');
  const [repo, setRepo] = useState('');

  const handleSubmit = async () => {
    try {
      await axios.post('/federation/import-repo', {
        owner,
        repo,
        default_branch: 'main'
      });
      alert('Repo Ingestion Triggered');
    } catch (err) {
      console.error(err);
      alert('Error during ingestion');
    }
  };

  return (
    <div className="mb-4">
      <h2 className="mb-2">Ingest New Repository</h2>
      <input className="border p-1 mr-2" value={owner} onChange={e => setOwner(e.target.value)} placeholder="Owner" />
      <input className="border p-1 mr-2" value={repo} onChange={e => setRepo(e.target.value)} placeholder="Repo Name" />
      <button onClick={handleSubmit} className="bg-blue-500 text-white px-3 py-1">Ingest</button>
    </div>
  );
}