const gameTypeSelect = document.querySelector('#game-type');
const periodSelect = document.querySelector('#ranking-period');
const archiveNotice = document.querySelector('#archive-notice');
const status = document.querySelector('#status');
const body = document.querySelector('#leaderboard');
let entries = [];
let publicationHistory = { lastUpdatedAt: null, snapshots: [] };
let sortField = 'aps';
let descending = true;

function selectedSnapshot() {
  return publicationHistory.snapshots.find(snapshot => snapshot.month === periodSelect.value);
}

function dataPrefix() {
  const snapshot = selectedSnapshot();
  return snapshot ? snapshot.path : 'data';
}

function renderEntries() {
  body.replaceChildren();
  [...entries].sort((first, second) => descending ? second[sortField] - first[sortField] : first[sortField] - second[sortField]).forEach((entry, index) => {
    const row = document.createElement('tr');
    row.innerHTML = `<td>${index + 1}</td><td><a href="${dataPrefix()}/bots/${encodeURIComponent(entry.name)}-${encodeURIComponent(entry.version)}.json">${entry.bot}</a></td><td>${entry.aps.toFixed(2)}</td><td>${entry.battles}</td><td>${entry.pairings}</td>`;
    body.append(row);
  });
}

async function loadLeaderboard() {
  const gameType = gameTypeSelect.value;
  const snapshot = selectedSnapshot();
  status.textContent = 'Loading leaderboard…';
  archiveNotice.hidden = !snapshot;
  try {
    const response = await fetch(`${dataPrefix()}/leaderboard/${gameType}.json`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    entries = data.entries;
    renderEntries();
    const updatedAt = snapshot ? snapshot.updatedAt : publicationHistory.lastUpdatedAt;
    const updatedText = updatedAt ? ` · ranking data last updated ${new Date(updatedAt).toLocaleString()}` : '';
    status.textContent = `${data.entries.length} active bots · behavior version ${data.behaviorVersion}${updatedText}`;
  } catch (error) {
    status.textContent = `The leaderboard is unavailable: ${error.message}`;
  }
}

async function loadHistory() {
  try {
    const response = await fetch('data/history.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    publicationHistory = await response.json();
    [...publicationHistory.snapshots].reverse().forEach(snapshot => {
      const option = document.createElement('option');
      option.value = snapshot.month;
      option.textContent = snapshot.month;
      periodSelect.append(option);
    });
  } catch (error) {
    status.textContent = `Ranking history is unavailable: ${error.message}`;
  }
}

gameTypeSelect.addEventListener('change', loadLeaderboard);
periodSelect.addEventListener('change', loadLeaderboard);
document.querySelectorAll('[data-sort]').forEach(button => button.addEventListener('click', () => {
  if (sortField === button.dataset.sort) descending = !descending;
  else { sortField = button.dataset.sort; descending = true; }
  renderEntries();
}));
loadHistory().then(loadLeaderboard);
