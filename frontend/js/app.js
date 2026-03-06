document.getElementById('submit-form').addEventListener('submit', async function(e){
  e.preventDefault();
  const fileInput = document.getElementById('file');
  const username = document.getElementById('username').value || 'anonymous';
  if (!fileInput.files.length) return alert('Select a file');
  const form = new FormData();
  form.append('file', fileInput.files[0]);
  form.append('username', username);

  const res = await fetch('/api/submit', { method: 'POST', body: form });
  const data = await res.json();
  document.getElementById('submit-result').textContent = JSON.stringify(data);
});

async function loadLeaderboard(){
  const res = await fetch('/api/leaderboard');
  const data = await res.json();
  const list = document.getElementById('leaderboard-list');
  list.innerHTML = '';
  data.forEach(item => {
    const li = document.createElement('li');
    li.textContent = `${item.username} — ${item.score}`;
    list.appendChild(li);
  });
}

loadLeaderboard();
