// Minimal login script: posts to /api/v1/login/ and stores tokens.
// Adjust paths if your API root differs.

const form = document.getElementById('login-form');
const msg = document.getElementById('msg');

function showMsg(text, err = true) {
  msg.textContent = text;
  msg.style.color = err ? '#dc2626' : '#16a34a';
}

function saveTokens(access, refresh) {
  // For demo: localStorage. In production consider secure http-only cookies.
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

// Example helper to call protected endpoint
async function fetchProfile() {
  const access = localStorage.getItem('access_token');
  if (!access) return null;
  const r = await fetch('/api/v1/get-me/', {
    headers: { 'Authorization': `Bearer ${access}` },
    credentials: 'same-origin'
  });
  if (!r.ok) return null;
  return await r.json();
}

form.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  showMsg('Signing in...', false);
  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value;

  try {
    const res = await fetch('/api/v1/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      // Try to parse JSON error
      let errText = `Login failed (${res.status})`;
      try {
        const e = await res.json();
        // Common SimpleJWT errors: { "detail": "No active account found with the given credentials" }
        errText = e.detail || JSON.stringify(e);
      } catch (e) { /* ignore */ }
      showMsg(errText, true);
      return;
    }

    const data = await res.json();
    // expected: { access: '...', refresh: '...' }
    if (!data.access) {
      showMsg('Login succeeded but no access token returned', true);
      return;
    }

    saveTokens(data.access, data.refresh || '');
    showMsg('Login successful — fetching profile...', false);

    const profile = await fetchProfile();
    if (profile) {
      // redirect or show username
      showMsg(`Welcome, ${profile.email || profile.username || profile.id}`, false);
      // e.g. redirect to dashboard:
      // window.location.href = '/dashboard/';
    } else {
      showMsg('Logged in, but failed to fetch profile', true);
    }

  } catch (err) {
    console.error(err);
    showMsg('Network error — check console', true);
  }
});
