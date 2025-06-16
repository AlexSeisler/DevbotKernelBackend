import React from "react";

export default function FederationPatchQueue({ patches }) {
  return (
    <div className="mt-6">
      <h2 className="text-xl font-bold mb-4">Pending Patch Proposals</h2>
      <table className="w-full border-collapse border border-gray-300">
        <thead>
          <tr>
            <th className="border p-2">Patch ID</th>
            <th className="border p-2">File Path</th>
            <th className="border p-2">Owner/Repo</th>
            <th className="border p-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {patches.map((patch) => (
            <tr key={patch.patch_id}>
              <td className="border p-2">{patch.patch_id}</td>
              <td className="border p-2">{patch.file_path}</td>
              <td className="border p-2">{patch.owner}/{patch.repo}</td>
              <td className="border p-2">{patch.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
