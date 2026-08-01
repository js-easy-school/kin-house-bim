const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const roomData = {
  ground: {
    total: 126,
    label: "План первого этажа",
    shell: "0,0 1480,0 1480,1080 0,1080",
    rooms: [
      ["G01", "Гостиная", "Гостиная", 28.6, .30, .30, 7.15, 4.00],
      ["G02", "Кухня-столовая", "Кухня-столовая", 23.4, 7.35, .30, 5.85, 4.00],
      ["G03", "Кладовая кухни", "Кладовая", 3.2, 13.40, .30, .80, 4.00],
      ["G04", "Двухсветный холл", "Двухсветный холл", 13.8, .30, 4.45, 4.3125, 3.20],
      ["G05", "Кабинет / гостевая", "Кабинет / гостевая", 12.6, 4.8125, 4.45, 3.9375, 3.20],
      ["G06", "Гибкая комната", "Гибкая комната", 10.4, 8.95, 4.45, 3.25, 3.20],
      ["G07", "Гостевой душ", "Душ", 4.1, 12.40, 4.45, 1.28125, 3.20],
      ["G08", "Лестница и коридор", "Лестница", 9.6, .30, 7.80, 4.363636, 2.20],
      ["G09", "Постирочная", "Постирочная", 6.4, 4.813636, 7.80, 2.909091, 2.20],
      ["G10", "Гардероб входа", "Гардероб", 2.8, 7.872727, 7.80, 1.272727, 2.20],
      ["G11", "Техническая", "Техническая", 5.2, 9.295455, 7.80, 2.363636, 2.20],
      ["G12", "Хранение", "Хранение", 5.9, 11.809091, 7.80, 2.681818, 2.20]
    ]
  },
  upper: {
    total: 89,
    label: "План второго этажа",
    shell: "0,0 1005,0 1005,400 1480,400 1480,1080 0,1080",
    rooms: [
      ["U01", "Главная спальня", "Главная спальня", 17.2, .30, .30, 3.822222, 4.50],
      ["U02", "Спальня 2", "Спальня 2", 13.6, 4.272222, .30, 3.022222, 4.50],
      ["U03", "Спальня 3", "Спальня 3", 13.1, 7.444444, .30, 2.911111, 4.50],
      ["U04", "Гардероб главной спальни", "Гардероб", 5.4, .30, 5.00, 2.454545, 2.20],
      ["U05", "Ванная главной спальни", "Ванная", 6.0, 2.904545, 5.00, 2.727273, 2.20],
      ["U06", "Общая ванная", "Общая ванная", 6.7, 10.00, 5.00, 3.045455, 2.20],
      ["U07", "Бельевой шкаф", "Бельё", 2.1, 13.195455, 5.00, .954545, 2.20],
      ["U08", "Галерея / лестница", "Галерея", 12.4, 5.50, 7.40, 4.133333, 3.00],
      ["U09", "Семейная гостиная", "Семейная гостиная", 12.5, 9.983333, 7.40, 4.166667, 3.00]
    ]
  }
};

const planColors = ["#d9ff52", "#c8ded8", "#eadfb9", "#c9d0e0", "#d8c8b8", "#bcd4c3", "#d7c7d5", "#cad7dc", "#d5d1be", "#c0cbc6", "#d7c2aa", "#c8c8c1"];

function svgEl(tag, attrs = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
  return node;
}

function drawPlan(level = "ground") {
  const data = roomData[level];
  const svg = $("#planSvg");
  const list = $("#roomList");
  svg.replaceChildren();
  list.replaceChildren();
  svg.setAttribute("aria-label", data.label);

  const shell = svgEl("polygon", { points: data.shell, class: "shell" });
  svg.append(shell);

  data.rooms.forEach((room, index) => {
    const [code, fullName, shortName, area, x, y, w, d] = room;
    const px = x * 100;
    const py = 1080 - (y + d) * 100;
    const pw = w * 100;
    const ph = d * 100;
    const group = svgEl("g");
    const rect = svgEl("rect", { x: px, y: py, width: pw, height: ph, fill: planColors[index % planColors.length], class: "room" });
    const codeText = svgEl("text", { x: px + 15, y: py + 24, class: "code" });
    codeText.textContent = code;
    const nameText = svgEl("text", { x: px + pw / 2, y: py + ph / 2 - 6, class: "room-name", "text-anchor": "middle" });
    nameText.textContent = pw < 145 ? code : shortName;
    const areaText = svgEl("text", { x: px + pw / 2, y: py + ph / 2 + 24, class: "room-area", "text-anchor": "middle" });
    areaText.textContent = `${area.toFixed(1).replace(".", ",")} м²`;
    group.append(rect, codeText, nameText, areaText);
    svg.append(group);

    const row = document.createElement("div");
    row.className = "room-row";
    row.innerHTML = `<span><b>${code}</b>${fullName}</span><em>${area.toFixed(1).replace(".", ",")} м²</em>`;
    list.append(row);
  });
  $("#levelTotal").textContent = `${data.total.toFixed(1).replace(".", ",")} м²`;
}

$$('.section-tabs button').forEach(button => {
  button.addEventListener('click', () => {
    $$('.section-tabs button').forEach(item => item.classList.toggle('active', item === button));
    $$('.tab-panel').forEach(panel => panel.classList.toggle('active', panel.id === `tab-${button.dataset.tab}`));
    document.querySelector('.section-tabs').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

$$('.level-switch button').forEach(button => {
  button.addEventListener('click', () => {
    $$('.level-switch button').forEach(item => item.classList.toggle('active', item === button));
    drawPlan(button.dataset.level);
  });
});

const model = $('#houseModel');
const spinButton = $('#toggleSpin');
model.addEventListener('load', () => {
  const loader = $('.model-loader', model);
  if (loader) loader.style.display = 'none';
});
model.addEventListener('error', () => showToast('3D-модель не загрузилась — проверьте подключение. Виды и файлы остаются доступны.'));

$('#resetView').addEventListener('click', () => {
  model.cameraOrbit = '32deg 69deg auto';
  model.cameraTarget = 'auto auto auto';
  model.fieldOfView = 'auto';
  model.jumpCameraToGoal?.();
});

spinButton.addEventListener('click', () => {
  const enabled = spinButton.getAttribute('aria-pressed') === 'true';
  spinButton.setAttribute('aria-pressed', String(!enabled));
  model.toggleAttribute('auto-rotate', !enabled);
});

$('#fullScreen').addEventListener('click', async () => {
  try {
    if (!document.fullscreenElement) await $('.viewer-stage').requestFullscreen();
    else await document.exitFullscreen();
  } catch { showToast('Полноэкранный режим недоступен в этом окне.'); }
});

$('#openBonsai').addEventListener('click', async event => {
  const button = event.currentTarget;
  button.disabled = true;
  button.textContent = 'Подготавливаю…';
  try {
    const isLocalViewer = ['127.0.0.1', 'localhost'].includes(window.location.hostname);
    if (!isLocalViewer) {
      const link = document.createElement('a');
      link.href = 'project/kin-house-bonsai.blend';
      link.download = 'kin-house-bonsai.blend';
      document.body.append(link);
      link.click();
      link.remove();
      showToast('Файл Bonsai загружается. Откройте его в Blender с установленным дополнением Bonsai.');
      return;
    }
    const response = await fetch('/actions/open-bonsai', { method: 'POST' });
    if (!response.ok) throw new Error('launch failed');
    showToast('Bonsai запускается с BIM-проектом. Первое открытие может занять несколько секунд.');
  } catch {
    showToast('Не удалось запустить Bonsai автоматически. Скачайте файл BIM в разделе «Файлы».');
  } finally {
    setTimeout(() => { button.disabled = false; button.textContent = 'Открыть в Bonsai'; }, 1600);
  }
});

const imageDialog = $('#imageDialog');
$$('.view-card').forEach(card => {
  card.addEventListener('click', () => {
    $('img', imageDialog).src = card.dataset.image;
    imageDialog.showModal();
  });
});
$('button', imageDialog).addEventListener('click', () => imageDialog.close());
imageDialog.addEventListener('click', event => { if (event.target === imageDialog) imageDialog.close(); });

let toastTimer;
function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 4500);
}

drawPlan('ground');
