import React from "react";

export default function FederationGraphTable({ repos }) {
  return (
    <div className="mt-6">
      <h2 className="text-xl font-bold mb-4">Federated Repositories</h2>
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr>
            <th className="border p-2">Repo ID</th>
            <th className="border p-2">Owner</th>
            <th className="border p-2">Repo</th>
            <th className="border p-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {repos.map((repo) => (
            <tr key={repo.repo_id}>
              <td className="border p-2">{repo.repo_id}</td>
              <td className="border p-2">{repo.owner}</td>
              <td className="border p-2">{repo.repo}</td>
              <td className="border p-2">{repo.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
