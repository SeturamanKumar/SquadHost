
'use client'
import { useState } from "react";

export default function Home() {

  const [serverName, setServerName] = useState<string>('');
  const [serverPassword, setServerPassword] = useState<string>('');
  const [status, setStatus] = useState<string>('');

  const handleCreateServer = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault;
    setStatus('Booting server... Please wait...');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/servers/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          server_name: serverName,
          server_password: serverPassword,
          mc_version: '1.20.4',
          difficulty: 'hard',
          max_players: 5,
          allow_tlauncher: true,
        }),
      });

      const data = await response.json();

      if(response.ok) {
        setStatus(`Success! Server is running on port ${data.port}`);
      } else {
        setStatus(`Error ${data.error || 'Failed to start'}`);
      }
    } catch (error) {
      setStatus(`Network Error: Could not reach Django backend...`);
    }
  };

  return(
    <main className="container">
      <header>
        <h1>SqaudHost Dashboard</h1>
        <p style={{ color: 'var(--text-muted)' }}>
          Manage your AWS-hosted Minecraft servers.
        </p>
      </header>
      <section className="card" style={{ margin: '2rem' }}>
        <h2>Deploy New Server</h2>
        <form onSubmit={handleCreateServer} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
          <input 
            type="text" 
            placeholder="Server Name (e.g., Hermitcraft"
            value={serverName}
            onChange={(e) => setServerName(e.target.value)}
            required
            style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#333', color: 'white' }}
          />
          <input 
            type="password" 
            placeholder="Password123"
            value={serverPassword}
            onChange={(e) => setServerPassword(e.target.value)}
            required
            style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#333', color: 'white' }}
          />
          <button type="submit" className="btn-primary">
            Launch Server
          </button>
        </form>
        {
          status && (
            <p style={{ margin: '1rem', fontWeight: 'bold', color: 'var(--primary)'}}>
              {status}
            </p>
          )
        }
      </section>
    </main>
  );

}