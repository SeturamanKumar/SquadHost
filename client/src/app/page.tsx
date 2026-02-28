
'use client'
import { useState, useEffect, use } from "react";

export default function Home() {

  const [serverName, setServerName] = useState<string>('');
  const [serverPassword, setServerPassword] = useState<string>('');
  const [mcVersion, setMcVersion] = useState<string>('LATEST');
  const [difficulty, setDifficulty] = useState<string>('normal');
  const [maxPlayers, setMaxPlayers] = useState<number>(10);
  const [allowTlauncher, setAllowTlauncher] = useState<boolean>(false);
  const [seed, setSeed] = useState<string>('');

  const [status, setStatus] = useState<string>('');
  const [assignedAddress, setAssignedAddressed] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);
  const [availableVersions, setAvailableVersions] = useState<string[]>([]);

  useEffect(() => {

    const fetchVersions = async () => {

      try {
        const response = await fetch('https://api.papermc.io/v2/projects/paper');
        const data = await response.json();

        const reversedVersions = data.versions.reverse();
        setAvailableVersions(reversedVersions);

        if(reversedVersions.length > 0) {
          setMcVersion(reversedVersions[0]);
        }

      } catch (error) {
        console.error("Failed to fetch PaperMC versions", error);
        setAvailableVersions(['LATEST', '1.21', '1.20.6', '1.20', '1.19.6', '1.19', '1.18.2', '1.18']);
      }
    };

    fetchVersions();
  }, []);

  const handleCreateServer = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault;
    setStatus('Booting server... Please wait...');
    setAssignedAddressed('');
    setCopied(false);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/servers/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          server_name: serverName,
          server_password: serverPassword,
          mc_version: mcVersion,
          difficulty: difficulty,
          max_players: maxPlayers,
          allow_tlauncher: allowTlauncher,
          seed: seed,
        }),
      });

      const data = await response.json();

      if(response.ok) {
        setStatus(`Success! Server is running on port`);
        setAssignedAddressed(`127.0.0.1:${data.server.port_number}`);
      } else {
        setStatus(`Error ${data.error || 'Failed to start'}`);
      }
    } catch (error) {
      setStatus(`Network Error: Could not reach Django backend...`);
    }
  };

  const copyToClipboard = () => {
    if(assignedAddress) {
      navigator.clipboard.writeText(assignedAddress);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
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

      <section className="card" style={{ margin: '2rem 0', padding: '2rem' }}>
        <h2>Deploy New Server</h2>

        <form onSubmit={handleCreateServer} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem'}}>
            <input 
              type="text" 
              placeholder="Server Name (e.g., Hermitcraft)"
              value={serverName}
              onChange={(e) => setServerName(e.target.value)}
              required
              style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#333', color: 'white' }}
            />
            <input 
              type="password" 
              placeholder="Password123"
              value={serverPassword}
              onChange={(e) => setServerPassword(e.target.value)}
              required
              style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#333', color: 'white' }}
            />
          </div>

          <div style={{ display: 'gird', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem'}}>
            <select 
              value={mcVersion}
              onChange={(e) => setMcVersion(e.target.value)}
              style={{ padding: '0.75rem', borderRadius: '4px', marginRight: '5px',  border: '1px solid #444', backgroundColor: '#333', color: 'white' }}>
                <option value="LATEST">Latest Version</option>
                {
                  availableVersions.map((version) => (
                    <option key={version} value={version}>
                      {version}
                    </option>
                  ))
                }
            </select>

            <select 
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              style={{ padding: '0.75rem', borderRadius: '4px', marginRight: '5px', border: '1px solid #444', backgroundColor: '#333', color: 'white' }}>
                <option value="peaceful">Peaceful</option>
                <option value="easy">Easy</option>
                <option value="normal">Normal</option>
                <option value="hard">Hard</option>
              </select>

              <input 
                type="number"
                placeholder="Max Players"
                value={maxPlayers}
                onChange={(e) => setMaxPlayers(parseInt(e.target.value) || 10)}
                min="2"
                max="20"
                required
                style={{ padding: '0.75rem', borderRadius: '4px', marginRight: '5px', border: '1px solid #444', backgroundColor: '#333', color: 'white' }}
              />

          </div>

            <input 
              type="text"
              placeholder="Custom Seed"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              style={{ padding: '0.75rem', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#333', color: 'white' }}
            />

            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'white', cursor: 'pointer' }}>
              <input 
                type="checkbox"
                checked={allowTlauncher}
                onChange={(e) => setAllowTlauncher(e.target.checked)}
                style={{ width: '1.2rem', height: '1.2rem', cursor: 'pointer' }}/>
                Enable Tlauncher support
            </label>
          
          <button type="submit" className="btn-primary" style={{ marginTop: '1rem' }}>
            Launch Server
          </button>

        </form>

        {
          status && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#2a2a2a', borderRadius: '8px', borderLeft: '4px solid var(--primary)' }}>
              
              <p style={{ margin: '0 0 0.5rem 0', fontWeight: 'bold', color: 'white' }}>
                {status}
              </p>

              {
                assignedAddress && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <code style={{ backgroundColor: '#111', padding: '0.5rem 1rem', borderRadius: '4px', color: 'var(--primary)', fontSize: '1.1rem' }}>
                      {assignedAddress}
                    </code>
                    <button 
                      onClick={copyToClipboard}
                      style={{padding: '0.5rem 1rem', backgroundColor: '#444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>
                        {copied ? 'Copied!': 'Copy Address'}
                      </button>
                  </div>
                )
              }
            </div>
          )
        }

      </section>
    </main>
  );

}