import React from 'react';
import FederationGraphTable from '../components/FederationGraphTable';
import RepoIngestionForm from '../components/RepoIngestionForm';

export default function App() {
  return (
    <div className="p-6">
      <h1 className="text-2xl mb-4">Federation Kernel Dashboard</h1>
      <RepoIngestionForm />
      <FederationGraphTable />
    </div>
  );
}