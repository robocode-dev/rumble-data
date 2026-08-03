const select = document.querySelector('#game-type');
const status = document.querySelector('#status');
const body = document.querySelector('#leaderboard');
let entries = [];
let sortField = 'aps';
let descending = true;

function renderEntries() {
  body.replaceChildren();
  [...entries].sort((first, second) => descending ? second[sortField] - first[sortField] : first[sortField] - second[sortField]).forEach((entry, index) => {
    const row = document.createElement('tr');
    row.innerHTML = `<td>${index + 1}</td><td><a href="data/bots/${encodeURIComponent(entry.name)}-${encodeURIComponent(entry.version)}.json">${entry.bot}</a></td><td>${entry.aps.toFixed(2)}</td><td>${entry.battles}</td><td>${entry.pairings}</td>`;
    body.append(row);
  });
}

async function loadLeaderboard() {
  const gameType = select.value;
  status.textContent = 'Loading leaderboard…';
  try {
    const response = await fetch(`data/leaderboard/${gameType}.json`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    entries = data.entries;
    renderEntries();
    status.textContent = `${data.entries.length} active bots · behavior version ${data.behaviorVersion}`;
  } catch (error) {
    status.textContent = `The leaderboard is unavailable: ${error.message}`;
  }
}

select.addEventListener('change', loadLeaderboard);
document.querySelectorAll('[data-sort]').forEach(button => button.addEventListener('click', () => {
  if (sortField === button.dataset.sort) descending = !descending;
  else { sortField = button.dataset.sort; descending = true; }
  renderEntries();
}));
loadLeaderboard();
