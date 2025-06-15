import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function FederationGraphTable() {
  const [graph, setGraph] = useState([]);

  useEffect(() => {
    axios.get('/federation/graph/query')
      .then(res => setGraph(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div>
      <h2 className="mb-2">Federation Graph</h2>
      <table className="border w-full">
        <thead>
          <tr>
            <th>Repo</th>
            <th>File</th>
            <th>Node</th>
            <th>Linked</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {graph.map((row, idx) => (
            <tr key={idx} className="border">
              <td className="p-1">{row.repo_id}</td>
              <td className="p-1">{row.file_path}</td>
              <td className="p-1">{row.name}</td>
              <td className="p-1">{row.cross_linked_to}</td>
              <td className="p-1">{row.notes}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}