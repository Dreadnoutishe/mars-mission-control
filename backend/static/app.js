'use strict';
let missions = [];
let filter = 'all';
const list = document.querySelector('#missions');

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed.');
  return data;
}

function toast(message) {
  const element = document.querySelector('#toast');
  element.textContent = message;
  element.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { element.hidden = true; }, 4500);
}

function render() {
  list.replaceChildren();
  const visible = missions.filter(m => filter === 'all' || m.status === filter);
  if (!visible.length) {
    const p = document.createElement('p');
    p.className = 'empty';
    p.textContent = filter === 'completed' ? 'Your first achievement is waiting. Complete a mission!' : 'No missions here yet. Launch your next adventure.';
    list.append(p);
  }
  for (const mission of visible) {
    const card = document.createElement('article');
    card.className = `mission ${mission.status}`;
    const heading = document.createElement('div');
    heading.className = 'mission-top';
    const category = document.createElement('span');
    category.className = `badge ${mission.category.toLowerCase()}`;
    category.textContent = mission.category;
    const credits = document.createElement('span');
    credits.className = 'reward';
    credits.textContent = `+${mission.reward} CR`;
    heading.append(category, credits);
    const title = document.createElement('h3');
    // Render all user content as text, never HTML.
    title.textContent = mission.title;
    const destination = document.createElement('p');
    destination.className = 'destination';
    destination.textContent = `↗ ${mission.sector} · Mission #${mission.id}`;
    const actions = document.createElement('div');
    actions.className = 'actions';
    if (mission.status === 'available') {
      const complete = document.createElement('button');
      complete.className = 'complete';
      complete.textContent = '✓ Complete mission';
      complete.addEventListener('click', () => mutate(complete, `/api/missions/${mission.id}/complete`, 'PATCH', `${mission.reward} credits earned. Mission complete!`));
      const cancel = document.createElement('button');
      cancel.className = 'quiet';
      cancel.textContent = 'Cancel';
      cancel.addEventListener('click', () => {
        if (confirm(`Cancel “${mission.title}”?`)) mutate(cancel, `/api/missions/${mission.id}`, 'DELETE', 'Mission cancelled.');
      });
      actions.append(complete, cancel);
    } else {
      const done = document.createElement('span');
      done.className = 'done';
      done.textContent = `✓ Completed · ${new Date(mission.completed_at).toLocaleDateString()}`;
      actions.append(done);
    }
    card.append(heading, title, destination, actions);
    list.append(card);
  }
}

async function load() {
  const connection = document.querySelector('#connection');
  try {
    const [records, stats] = await Promise.all([api('/api/missions'), api('/api/stats')]);
    missions = records;
    for (const key of ['available', 'completed', 'credits', 'rank']) document.getElementById(key).textContent = stats[key];
    document.querySelector('#rank-progress').style.width = `${Math.min(stats.credits / 1000 * 100, 100)}%`;
    document.querySelector('#rank-hint').textContent = stats.credits < 400 ? `${400 - stats.credits} CR to Explorer` : stats.credits < 1000 ? `${1000 - stats.credits} CR to Pioneer` : 'Pioneer status achieved';
    connection.textContent = '● Colony online';
    connection.classList.remove('offline');
    render();
    return true;
  } catch (error) {
    connection.textContent = '● Colony offline';
    connection.classList.add('offline');
    list.replaceChildren();
    const p = document.createElement('p');
    p.className = 'empty';
    p.textContent = 'Cannot load colony records. Check the connection and press Refresh.';
    list.append(p);
    for (const key of ['available', 'completed', 'credits', 'rank']) document.getElementById(key).textContent = '—';
    document.querySelector('#rank-progress').style.width = '0%';
    document.querySelector('#rank-hint').textContent = 'Progress temporarily unavailable';
    toast(error.message);
    return false;
  }
}

async function mutate(button, path, method, success) {
  button.disabled = true;
  try {
    await api(path, {method});
    if (await load()) toast(success);
  } catch (error) { toast(error.message); }
  finally { button.disabled = false; }
}

document.querySelector('#mission-form').addEventListener('submit', async event => {
  event.preventDefault();
  const button = document.querySelector('#launch');
  const message = document.querySelector('#form-message');
  button.disabled = true;
  message.textContent = '';
  try {
    await api('/api/missions', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        title: document.querySelector('#title').value,
        sector: document.querySelector('#sector').value,
        category: document.querySelector('#category').value,
        reward: Number(document.querySelector('#reward').value)
      })
    });
    event.target.reset();
    if (await load()) toast('New mission added to the colony board.');
  } catch (error) { message.textContent = error.message; }
  finally { button.disabled = false; }
});
for (const tab of document.querySelectorAll('[data-filter]')) tab.addEventListener('click', () => {
  filter = tab.dataset.filter;
  for (const other of document.querySelectorAll('[data-filter]')) {
    other.classList.toggle('active', other === tab);
    other.setAttribute('aria-pressed', other === tab ? 'true' : 'false');
  }
  render();
});
document.querySelector('#refresh').addEventListener('click', load);
load();
