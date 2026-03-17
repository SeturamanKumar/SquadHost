'use client'
import { useState, useEffect, useRef } from "react";

interface ServerInstance {
  id: string;
  server_name: string;
  mc_version: string;
  difficulty: string;
  max_players: number;
  is_running: Boolean;
  server_ip?: string;
  status: string;
  created_at: string;
}

const STAGES = [
  { key: 'PROVISIONING', label: 'Provisioning EC2',        detail: 'Launching your cloud instance' },
  { key: 'INSTALLING',   label: 'Installing Dependencies', detail: 'Setting up Docker & AWS CLI' },
  { key: 'STARTING',     label: 'Starting Container',      detail: 'Downloading world & launching Minecraft' },
  { key: 'BOOTING',      label: 'Booting Minecraft',       detail: 'Server is loading chunks & world data' },
  { key: 'ONLINE',       label: 'Online',                  detail: 'Server is ready to play!' },
];

function ServerProgress({ status, elapsedSeconds }: { status: string, elapsedSeconds: number}) {

  const currentIndex = STAGES.findIndex(s => s.key === status);
  const progress = Math.min((((currentIndex) + 1) / STAGES.length) * 100, 100);
  const mins = Math.floor(elapsedSeconds / 60);
  const secs = elapsedSeconds % 60;

  return(
    <div style={{ marginTop: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--primary)', fontWeight: 'bold' }}>
          {STAGES[currentIndex]?.label ?? 'Pending'}
        </span>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          {mins}:{secs.toString().padStart(2, '0')} elapsed
        </span>
      </div>

      <div style={{ height: '6px', backgroundColor: '#444', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{
          height: '100%',
          width: `${progress}%`,
          backgroundColor: 'var(--primary)',
          borderRadius: '3px',
          transition: 'width 0.5s ease'
        }} />
      </div>

      <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
        {STAGES.map((stage, i) => {
          const done = i < currentIndex;
          const active = i === currentIndex;
          return (
            <span 
              key={stage.key}
              title={stage.detail}
              style={{
                fontSize: '0.75rem',
                padding: '0.2rem 0.5rem',
                borderRadius: '12px',
                backgroundColor: done ? '#1a3a1a' : active ? '#2a3a1a' : '#333',
                color: done ? 'var(--primary)' : active ? '#aed581' : 'var(--text-muted)',
                border: `1px solid ${done ? 'var(--primary)' : active ? '#aed581' : '#555'}`,
                cursor: 'default',
              }}>
                {done ? '✓ ' : active ? '⟳ ' : ''}{stage.label}
              </span>
          );
        })}
      </div>
    </div>
  );

}

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
  const [servers, setServers] = useState<ServerInstance[]>([]);

  const notifiedServers = useRef<Set<string>>(new Set());

  const playNotifications = () => {
    
    const ctx = new AudioContext();

    const playNote = (frequency: number, startTime: number, duration: number) => {
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      oscillator.connect(ctx.destination);
      oscillator.frequency.value = frequency;
      oscillator.type = 'sine';
      gainNode.gain.setValueAtTime(0, startTime);
      gainNode.gain.linearRampToValueAtTime(0.3, startTime + 0.01);
      gainNode.gain.linearRampToValueAtTime(0, startTime + duration);
      oscillator.start(startTime);
      oscillator.stop(startTime + duration);
    };

    const now = ctx.currentTime;
    playNote(523, now, 0.15);
    playNote(659, now + 0.15, 0.15);
    playNote(784, now + 0.30, 0.3);

  }

  useEffect(() => {
    servers.forEach(server => {
      if(server.status === 'ONLINE' && !notifiedServers.current.has(server.id)) {
        notifiedServers.current.add(server.id);
        playNotifications();
      }
    })
  }, [servers])

  const fetchServers = async () => {

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
      const response = await fetch(`${apiUrl}/api/servers/list/`);
      if(response.ok) {
        const data = await response.json();
        setServers(data);
      }
    } catch (error) {
      console.error("Failed to fetch the server list:", error);
    }

  }

  useEffect(() => {

    const fetchVersions = async () => {

      try {
        const response = await fetch('/api/route/versions');
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
    fetchServers();

    const interval = setInterval(() => {
      fetchServers();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const newlyCreated = servers.find(s => s.server_name === serverName);
    if(newlyCreated && newlyCreated.server_ip){
      setAssignedAddressed(newlyCreated.server_ip);
      setStatus('Success! Server is booting. It may take upto 5-6 minutes!')
    }
  }, [servers, serverName])

  const handleCreateServer = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if(!/^[a-zA-Z0-9_-]+$/.test(serverName)) {
      setStatus('Error: Server name can only container letters, numbers, hyphens and underscores. No spaces');
      return;
    }

    setStatus('Booting server... Please wait...');
    setAssignedAddressed('');
    setCopied(false);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
      const response = await fetch(`${apiUrl}/api/servers/create/`, {
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
        setStatus(`Success! Server is Starting`);
        setAssignedAddressed(`Pending AWS IP Assignment...`);
        fetchServers();
      } else {
        setStatus(`Error ${data.error || 'Failed to start'}`);
      }
    } catch (error) {
      setStatus(`Network Error: Could not reach Django backend...`);
    }
  };

  const handleDelete = async (targetServiceName: string) => {
    const password = window.prompt(`Enter the admin password for ${targetServiceName} to permanently delete it:`);
    if (!password) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
      const response = await fetch(`${apiUrl}/api/servers/delete/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          server_name: targetServiceName,
          server_password: password,
        }),
      });

      if(response.ok){
        fetchServers();
      } else {
        const data = await response.json();
        alert(`Failed to Delete Server: ${data.error}`);
      }
    } catch (error) {
      alert("Network Error: Could not reach backend.");
    }
  }

  const handleRestart = async (targetServiceName: string) => {
    const password = window.prompt(`Enter the admin password for ${targetServiceName} to restart it`);
    if(!password) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'
      const response = await fetch(`${apiUrl}/api/servers/restart/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          server_name: targetServiceName,
          server_password: password,
        }),
      });

      const data = await response.json();
      
      if(response.ok){
        const restartedServer = servers.find(s => s.server_name === targetServiceName)
        if(restartedServer) {
          notifiedServers.current.delete(restartedServer.id);
        }
        alert(`Success! Server is starting, it may take 5-6 minutes`);
        fetchServers();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert(`Network Error: Could not reach backend.`);
    }
  }

  const copyToClipboard = () => {
    if(assignedAddress && assignedAddress === 'Pending AWS IP Assignment...') return;

    if(navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(assignedAddress);
    } else {
      const el = document.createElement('textarea');
      el.value = assignedAddress;
      el.style.position = 'fixed';
      el.style.opacity = '0';
      document.body.appendChild(el);
      el.focus();
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return(
    <main className="container">

      <header>
        <h1>SquadHost Dashboard</h1>
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem'}}>
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
                      disabled={assignedAddress === 'Pending AWS IP Assignment...'}
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

      <section className="card" style={{ margin: '2rem 0', padding: '2rem'}}>
        <h2>Active Servers</h2>
        {
          servers.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', marginTop: '1rem' }}>No servers</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
              {
                servers.map((server) => (
                  <div key={server.id} style={{ padding: '1.5rem', backgroundColor: '#2a2a2a', borderRadius: '8px', border: '1px solid #444' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <h3 style={{ margin: '0 0 0.5rem 0', color: 'white' }}>{server.server_name}</h3>
                        <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                          <span>Version: {server.mc_version}</span>
                          <span>Players: {server.max_players}</span>
                          <span>Difficulty: {server.difficulty}</span>
                        </div>
                        <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: server.is_running ? '#4caf50' : '#f44336' }}></div>
                          <code style={{ color: 'var(--primary)' }}>{server.server_ip ? `${server.server_ip}` : 'Pending AWS IP...'}</code>
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button 
                          onClick={() => handleRestart(server.server_name)}
                          style={{ padding: '0.5rem 1rem', backgroundColor: '#2196F3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                          >
                          Restart
                        </button>
                        <button 
                          onClick={() => handleDelete(server.server_name)}
                          style={{ padding: '0.5rem 1rem', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
                          >
                          Delete
                        </button>
                      </div>
                    </div>
                    {server.status !== 'ONLINE' && server.status !== 'OFFLINE' && (
                      <ServerProgress
                        status={server.status}
                        elapsedSeconds={Math.floor((Date.now() - new Date(server.created_at).getTime()) / 1000)}
                      />
                    )}
                  </div>
                ))
              }
            </div>
          )
        }
      </section>
    </main>
  );

}
