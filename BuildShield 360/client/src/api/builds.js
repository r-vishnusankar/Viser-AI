const API = '/api';

export async function triggerBuild(options = {}) {
  const res = await fetch(`${API}/builds/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(options),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getBuilds(limit = 20, skip = 0) {
  const res = await fetch(`${API}/builds?limit=${limit}&skip=${skip}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getBuildTrend(limit = 10) {
  const res = await fetch(`${API}/builds/trend?limit=${limit}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
