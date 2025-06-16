import React, { useState } from "react";
import RepoIngestionForm from "../components/RepoIngestionForm";
import FederationGraphTable from "../components/FederationGraphTable";
import FederationPatchQueue from "../components/FederationPatchQueue";

export default function FederationDashboard() {
  const [repos, setRepos] = useState([]);
  const [patches, setPatches] = useState([]);

  const handleIngest = (repo) => {
    const newRepo = {
      repo_id: Math.floor(Math.random() * 100000),
      owner: repo.owner,
      repo: repo.repo,
      status: "Ingested"
    };
    setRepos([...repos, newRepo]);
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Federation Control Dashboard</h1>
      <RepoIngestionForm onSubmit={handleIngest} />
      <FederationGraphTable repos={repos} />
      <FederationPatchQueue patches={patches} />
    </div>
  );
}
