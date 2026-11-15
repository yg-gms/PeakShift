'use strict';
const $ = id => document.getElementById(id);
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clock = minute => `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`;
const table = (headings, rows) => `<div class="table-wrap"><table><thead><tr>${headings.map(h => `<th>${escapeHTML(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(v => `<td>${escapeHTML(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
let data, python, tasks = [], savedRaw = null, dayLoad = [], earliestLoad = [], comparisonComplete = false;
function message(text = '', error = false) {
  $('message').textContent = text;
  $('message').className = error ? 'error' : '';
}
function swissNow() {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA', {timeZone:'Europe/Zurich', year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', hourCycle:'h23'}).formatToParts(new Date()).map(p => [p.type, p.value]));
  return {date:`${parts.year}-${parts.month}-${parts.day}`, minute:Number(parts.hour) * 60 + Number(parts.minute)};
}
function profile() {
  const weekday = (new Date($('date').value + 'T12:00:00Z').getUTCDay() + 6) % 7;
  if (!data.profiles[weekday]) throw new Error('Choose a valid planning date.');
  return data.profiles[weekday];
}
// Send task data as JSON to the same Python scheduler used by the local app.
function compute(list, mode) {
  const now = swissNow();
  python.globals.set('request_json', JSON.stringify({profile:profile(), tasks:list, mode, not_before:$('date').value === now.date ? now.minute + 1 : 0}));
  return JSON.parse(python.runPython(`
request = json.loads(request_json)
planned, curve = plan_day(request['profile'], request['tasks'], request['not_before'])
# Rebuild the displayed curve from saved starts without moving tasks.
if request['mode'] == 'view':
    planned = request['tasks']
    curve = [float(value) for value in request['profile'] for _ in range(60)]
    for task in planned:
        if task['start'] is not None:
            add_task_load(curve, task, task['start'])
earliest, earliest_curve = plan_day(request['profile'], request['tasks'], request['not_before'], earliest_start=True)
complete = all(task['start'] is not None for task in planned + earliest)
json.dumps({'tasks': planned, 'load': curve, 'earliest_load': earliest_curve, 'comparison_complete': complete}, allow_nan=False)
`));
}
function persist(list, replan = false) {
  const result = compute(list, replan ? 'plan' : 'view');
  const key = 'peakshift.day.' + $('date').value;
  // Refuse to overwrite a plan that another tab has changed since we loaded it.
  if (localStorage.getItem(key) !== savedRaw) throw new Error('This day changed in another tab. Select the date again to reload it.');
  const raw = JSON.stringify(result.tasks);
  localStorage.setItem(key, raw);
  savedRaw = raw; tasks = result.tasks; dayLoad = result.load; earliestLoad = result.earliest_load; comparisonComplete = result.comparison_complete;
  render(); message();
}
function loadDay() {
  try {
    savedRaw = localStorage.getItem('peakshift.day.' + $('date').value);
    const saved = savedRaw === null ? [] : JSON.parse(savedRaw);
    if (!Array.isArray(saved)) throw new Error('Saved plan could not be read.');
    const result = compute(saved, 'view');
    tasks = result.tasks; dayLoad = result.load; earliestLoad = result.earliest_load; comparisonComplete = result.comparison_complete;
    render(); $('add').disabled = false; $('replan').disabled = false; message();
  } catch (error) {
    $('add').disabled = true; $('replan').disabled = true;
    message(`Could not open this day's plan. ${error.message}`, true);
  }
}
function render() {
  const weekday = new Date($('date').value + 'T12:00:00Z').toLocaleDateString('en-GB', {weekday:'long',timeZone:'UTC'});
  $('plan-title').textContent = `Your ${weekday} plan`;
  const finished = tasks.filter(t => t.status === 'Done').length;
  $('totals').innerHTML = tasks.length ? `<div><strong>${finished} / ${tasks.length}</strong><span>Completed</span></div><div><strong>${tasks.reduce((s,t) => s + t.kwh, 0).toFixed(2)} kWh</strong><span>Estimated task energy</span></div>` : '';
  $('tasks').innerHTML = tasks.length ? [...tasks].sort((a,b) => (a.start ?? 1441) - (b.start ?? 1441)).map(task => {
    const id = escapeHTML(task.id);
    const parent = tasks.find(t => t.id === task.after);
    const ready = !parent || parent.status === 'Done';
    const dependents = tasks.filter(t => t.after === task.id);
    let actions = '';
    if (task.start !== null) {
      if (task.status === 'Planned') actions += `<button data-action="start" data-id="${id}" ${ready ? '' : 'disabled title="Complete the earlier task first"'}>Start</button>`;
      if (task.status !== 'Done') actions += `<button data-action="done" data-id="${id}" ${ready ? '' : 'disabled title="Complete the earlier task first"'}>Mark done</button>`;
      else actions += `<button data-action="undo" data-id="${id}" ${dependents.some(t => t.status !== 'Planned') ? 'disabled' : ''}>Undo done</button>`;
    }
    return `<article class="task"><div class="task-top"><h3>${escapeHTML(task.appliance)}</h3><span class="status ${task.status === 'Done' ? 'done' : ''}">${escapeHTML(task.status)}</span></div><p class="task-time">${task.start === null ? 'Needs a time' : clock(task.start) + '–' + clock(task.start + task.minutes)}</p>${task.start === null ? `<p class="notice">${escapeHTML(task.reason)}</p>` : ''}<p class="muted small">${task.minutes} min · ~${task.kwh} kWh${parent ? ' · After ' + escapeHTML(parent.appliance) : ''}</p><div class="actions">${actions}<button data-action="remove" data-id="${id}" ${dependents.length ? 'disabled title="Remove dependent tasks first"' : ''}>Remove</button></div></article>`;
  }).join('') : '<div class="empty">Add the appliances you want to use. Your start and finish times will appear here.</div>';
  const selected = $('after').value;
  $('after').innerHTML = '<option value="">Any time in my window</option>' + tasks.map((t,i) => `<option value="${escapeHTML(t.id)}">${i + 1}. ${escapeHTML(t.appliance)}</option>`).join('');
  if (tasks.some(t => t.id === selected)) $('after').value = selected;
  $('download').hidden = $('day-chart').hidden = !tasks.length;
  drawPlan();
}
function chart(id, lines) {
  const canvas = $(id), width = canvas.clientWidth;
  if (!width) return;
  const height = 260, ratio = window.devicePixelRatio || 1;
  canvas.width = width * ratio; canvas.height = height * ratio;
  const ctx = canvas.getContext('2d'); ctx.scale(ratio, ratio);
  const left = 46, right = width - 20, top = 22, bottom = height - 36;
  const max = Math.max(1, ...lines.flatMap(line => line.values)) * 1.12;
  ctx.font = '12px sans-serif'; ctx.fillStyle = '#65746a';
  for (let tick = 0; tick <= 4; tick++) {
    const y = bottom - (bottom - top) * tick / 4;
    ctx.strokeStyle = '#e6ece5'; ctx.beginPath(); ctx.moveTo(left,y); ctx.lineTo(right,y); ctx.stroke();
    ctx.fillText((max * tick / 4).toFixed(1), 8, y + 4);
  }
  ctx.fillText('kW', 8, 13);
  [0,6,12,18,24].forEach(hour => ctx.fillText(`${String(hour).padStart(2,'0')}:00`, left + (right-left)*hour/24 - 12, height - 12));
  lines.forEach(line => {
    ctx.strokeStyle = line.color; ctx.lineWidth = 2; ctx.setLineDash(line.dash || []); ctx.beginPath();
    line.values.forEach((value,i) => {
      const x = left + (right-left) * i / line.values.length;
      const y = bottom - (bottom-top) * value / max;
      i ? ctx.lineTo(x,y) : ctx.moveTo(x,y);
    }); ctx.stroke();
  });
}
function drawPlan() {
  if (!data || !dayLoad.length) return;
  const earliestPeak = Math.max(...earliestLoad), planPeak = Math.max(...dayLoad);
  const difference = earliestPeak - planPeak;
  $('comparison').innerHTML = comparisonComplete
    ? `<div class="totals"><div><strong>${earliestPeak.toFixed(2)} kW</strong><span>Earliest-start peak</span></div><div><strong>${planPeak.toFixed(2)} kW</strong><span>Your plan peak</span></div></div><p>${Math.abs(difference) < 0.005 ? 'Same estimated peak in both schedules.' : `Your plan has a ${Math.abs(difference).toFixed(2)} kW ${difference > 0 ? 'lower' : 'higher'} estimated peak.`} Same appliance energy; only timing changes.</p>`
    : '<p class="notice">Peak comparison unavailable: at least one run has no time in one of the schedules. Resolve the time windows to compare the same complete set of runs.</p>';
  $('earliest-legend').hidden = !comparisonComplete;
  const lines = [{values:profile().flatMap(v => Array(60).fill(v)), color:'#9aa99d', dash:[2,4]}];
  if (comparisonComplete) lines.push({values:earliestLoad, color:'#a96628', dash:[7,4]});
  lines.push({values:dayLoad, color:'#276955'});
  chart('plan-canvas', lines);
}
function showReadings() {
  const values = data.readings[$('recorded-date').value];
  $('recorded-totals').innerHTML = `<div><strong>${values.reduce((a,b) => a+b,0).toFixed(2)} kWh</strong><span>Recorded daily energy</span></div><div><strong>${Math.max(...values).toFixed(2)} kW</strong><span>Highest hourly average</span></div>`;
  $('readings-table').innerHTML = table(['Hour','Recorded demand (kW)'], values.map((v,i) => [clock(i * 60), v.toFixed(3)]));
  chart('recorded-canvas', [{values:values.flatMap(v => Array(60).fill(v)), color:'#276955'}]);
}
function preset() {
  const value = data.appliances[$('appliance').value];
  $('duration').value = value.minutes; $('energy').value = value.kwh;
  $('preset').textContent = `Example run · ${value.minutes} min · about ${value.kwh} kWh`;
}
function showEvidence() {
  $('scores').innerHTML = ['test','validation'].map(key => {
    const score = data.evaluation[key];
    return `<article class="panel"><h3>${key === 'test' ? 'Final test' : 'Validation'} · ${score.days} complete days</h3>${table(['Metric','Yesterday baseline','Decision tree'], [
      ['Hourly error (kW)',score.baseline_hourly_mae_kw.toFixed(3),score.model_hourly_mae_kw.toFixed(3)],
      ['Daily peak error (kW)',score.baseline_peak_mae_kw.toFixed(3),score.model_peak_mae_kw.toFixed(3)],
      ['Average peak after scheduling (kW)',score.average_simulated_peak_kw.Baseline.toFixed(3),score.average_simulated_peak_kw.Model.toFixed(3)]
    ])}<p class="muted small">Against baseline scheduling · ${score.model_vs_baseline.better} better · ${score.model_vs_baseline.equal} equal · ${score.model_vs_baseline.worse} worse. ${score.skipped_days} incomplete or clock-change days skipped.</p></article>`;
  }).join('');
}
async function initialize() {
  try {
    const [response, sourceResponse] = await Promise.all([fetch('data.json'), fetch('daily_planner.py')]);
    if (!response.ok || !sourceResponse.ok) throw new Error('The sample data could not be loaded.');
    data = await response.json();
    $('appliance').innerHTML = Object.keys(data.appliances).map(name => `<option>${escapeHTML(name)}</option>`).join('');
    ['earliest','deadline'].forEach(id => {
      $(id).innerHTML = Array.from({length:97}, (_,i) => `<option value="${i * 15}">${clock(i * 15)}</option>`).join('');
    });
    $('earliest').value = 480; $('deadline').value = 1320; $('date').value = swissNow().date;
    $('recorded-date').innerHTML = Object.keys(data.readings).reverse().map(day => `<option>${day}</option>`).join('');
    $('appliance-source').href = data.appliance_source;
    $('presets-table').innerHTML = table(['Appliance','Example minutes','Estimated kWh'], Object.entries(data.appliances).map(([name,p]) => [name,p.minutes,p.kwh]));
    preset(); showReadings(); showEvidence();
    // Pyodide runs the shared Python planner directly in the browser.
    python = await loadPyodide();
    python.FS.writeFile('daily_planner.py', await sourceResponse.text());
    python.runPython('import json\nfrom daily_planner import plan_day, add_task_load');
    loadDay();
  } catch (error) { message(`The planner could not start. ${error.message} Refresh to try again.`,true); }
}
$('appliance').addEventListener('change', preset);
$('date').addEventListener('change', () => { if (python) loadDay(); });
$('recorded-date').addEventListener('change', showReadings);
$('add-form').addEventListener('submit', event => {
  event.preventDefault();
  try {
    const task = {id:crypto.randomUUID(), appliance:$('appliance').value, minutes:Number($('duration').value), kwh:Number($('energy').value), earliest:Number($('earliest').value), deadline:Number($('deadline').value), after:$('after').value || null, status:'Planned', start:null};
    if (task.minutes > task.deadline - task.earliest) throw new Error('The run needs a wider window to finish.');
    persist([...tasks,task],true);
  } catch (error) { message(error.message,true); }
});
$('replan').addEventListener('click', () => {try {persist(tasks,true);} catch (error) {message(error.message,true);}});
$('tasks').addEventListener('click', event => {
  const button = event.target.closest('button[data-action]');
  if (!button || button.disabled) return;
  try {
    const list = structuredClone(tasks), task = list.find(t => t.id === button.dataset.id);
    if (button.dataset.action === 'remove') persist(list.filter(t => t.id !== task.id),true);
    else {task.status = {start:'Running',done:'Done',undo:'Planned'}[button.dataset.action]; persist(list);}
  } catch (error) {message(error.message,true);}
});
$('download').addEventListener('click', () => {
  const rows = [['Appliance','Start','Finish','Status','Estimated energy (kWh)'],...tasks.map(t => [t.appliance,t.start === null ? 'Unscheduled' : clock(t.start),t.start === null ? '' : clock(t.start+t.minutes),t.status,t.kwh])];
  const blob = new Blob([rows.map(row => row.map(v => '"'+String(v).replaceAll('"','""')+'"').join(',')).join('\n')],{type:'text/csv'});
  const url = URL.createObjectURL(blob), link = document.createElement('a');link.href = url;link.download = `peakshift-${$('date').value}.csv`;link.click();setTimeout(() => URL.revokeObjectURL(url),1000);
});
document.querySelectorAll('nav button').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('nav button').forEach(other => other.removeAttribute('aria-current'));
  button.setAttribute('aria-current','page');
  ['planner','household','evidence'].forEach(id => $(id).hidden = id !== button.dataset.tab);
  if (data) {showReadings();drawPlan();}
}));
$('day-chart').addEventListener('toggle', drawPlan);
window.addEventListener('resize', () => {if(data){drawPlan();showReadings();}});
window.addEventListener('storage', event => {if (event.key === 'peakshift.day.' + $('date').value) loadDay();});
initialize();
