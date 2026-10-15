/**
 * Всероссийская Федерация Литрбола (ВФЛ) — Frontend Application
 */

const STATE = {
  name: "Атлетов Иван",
  gender: "m",
  weight: 80,
  experience: "amateur",
  drinks: [
    { name: "Светлое пиво", volume_ml: 500, abv: 5.0, count: 2, icon: "🍺" }
  ],
  hours: 3.0,
  snack: "medium",
  penalties: {
    vomited: false,
    fell_asleep: false,
    called_ex: false,
    lost_items: false
  },
  currentResult: null,
  quizQuestions: [],
  quizCurrentIdx: 0,
  quizTotalScore: 0,
  selectedAvatar: "barman",
  customPhoto: null,
  detectorVerified: false,
  detectorScore: 0
};

// Пресеты напитков
const DRINK_PRESETS = [
  { name: "Светлое пиво", volume_ml: 500, abv: 4.8, icon: "🍺" },
  { name: "Крафтовое IPA", volume_ml: 500, abv: 6.8, icon: "🍻" },
  { name: "Стопка водки", volume_ml: 50, abv: 40.0, icon: "🥃" },
  { name: "Бокал вина", volume_ml: 150, abv: 12.5, icon: "🍷" },
  { name: "Виски / Коньяк", volume_ml: 100, abv: 40.0, icon: "🥃" },
  { name: "Коктейль «Ёрш»", volume_ml: 500, abv: 12.0, icon: "🍹" },
  { name: "Шот текилы", volume_ml: 50, abv: 38.0, icon: "🍋" },
  { name: "Настойка деда", volume_ml: 50, abv: 45.0, icon: "🧪" }
];

// Инициализация при загрузке страницы
document.addEventListener("DOMContentLoaded", () => {
  initTelegramWebApp();
  initTabs();
  initCalculator();
  initQuiz();
  initDetector();
  renderDrinksList();
  fetchRanksTable();
  drawDefaultCertificate();
  initBacTracker();
  initDuels();
  initLeaderboard();
  initSosAndToasts();
});

// Telegram WebApp адаптация
function initTelegramWebApp() {
  const urlParams = new URLSearchParams(window.location.search);
  STATE.chatId = urlParams.get('chat_id') || null;
  const urlRoomId = urlParams.get('room_id') || null;

  if (window.Telegram && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    try {
      tg.setHeaderColor('#10131d');
      tg.setBackgroundColor('#0c0e14');
    } catch(e) {}

    if (tg.initDataUnsafe) {
      if (tg.initDataUnsafe.start_param) {
        const param = tg.initDataUnsafe.start_param;
        if (param.startsWith('chat_')) {
          STATE.chatId = param.replace('chat_', '');
        } else if (param.startsWith('room_')) {
          STATE.targetRoomId = param.replace('room_', '').toUpperCase().trim();
        } else if (!isNaN(param)) {
          STATE.chatId = param;
        } else if (param.length === 6) {
          STATE.targetRoomId = param.toUpperCase().trim();
        }
      }
      if (tg.initDataUnsafe.user) {
        const u = tg.initDataUnsafe.user;
        STATE.tgUser = u;
        STATE.tgUserId = u.id;
        STATE.name = `${u.first_name || ''} ${u.last_name || ''}`.trim() || 'Атлет Telegram';
        const nameInput = document.getElementById("athleteName");
        if (nameInput) nameInput.value = STATE.name;

        const badge = document.getElementById("tgUserBadge");
        if (badge) {
          badge.innerHTML = `<span>●</span> ${escapeHtml(u.first_name || 'Атлет')}`;
        }
      }
    }
  }

  if (urlRoomId) {
    STATE.targetRoomId = urlRoomId.toUpperCase().trim();
  }

  // Если был передан room_id или в хэше #tab-duel, переключаем на дуэль
  if (STATE.targetRoomId || window.location.hash.includes('tab-duel')) {
    setTimeout(() => {
      switchTab('tab-duel');
      if (STATE.targetRoomId) {
        joinPartyRoom(STATE.targetRoomId);
      }
    }, 250);
  }
}

// Навигация по вкладкам
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;
      switchTab(target);
    });
  });
}

const SUB_TABS = ["tab-detector", "tab-duel", "tab-sos", "tab-quiz", "tab-rules"];

function switchTab(tabId) {
  const activeNavTarget = SUB_TABS.includes(tabId) ? "tab-more" : tabId;

  document.querySelectorAll(".tab-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.tab === activeNavTarget);
  });
  document.querySelectorAll(".tab-pane").forEach(p => {
    p.classList.toggle("active", p.id === tabId);
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (tabId === "tab-cert") {
    renderCertificateCanvas();
  }
  if (tabId === "tab-top") {
    fetchLeaderboard();
  }
}
window.switchTab = switchTab;

// Калькулятор
function initCalculator() {
  // Быстрые кнопки добавления напитков
  const quickGrid = document.getElementById("quickDrinksGrid");
  if (quickGrid) {
    quickGrid.innerHTML = "";
    DRINK_PRESETS.forEach(preset => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "quick-drink-btn";
      btn.innerHTML = `
        <span class="icon">${preset.icon}</span>
        <span class="title">${preset.name}</span>
        <span class="sub">${preset.volume_ml} мл • ${preset.abv}%</span>
      `;
      btn.addEventListener("click", () => addDrink(preset));
      quickGrid.appendChild(btn);
    });
  }

  // Ползунок времени
  const hoursSlider = document.getElementById("hoursSlider");
  const hoursVal = document.getElementById("hoursVal");
  if (hoursSlider && hoursVal) {
    hoursSlider.addEventListener("input", (e) => {
      STATE.hours = parseFloat(e.target.value);
      hoursVal.textContent = `${STATE.hours} ч.`;
    });
  }

  // Слушатели радиокнопок опыта и закуски
  document.querySelectorAll('input[name="snack"]').forEach(r => {
    r.addEventListener("change", (e) => {
      STATE.snack = e.target.value;
      updateOptionCardStyles('snack');
    });
  });

  document.querySelectorAll('input[name="experience"]').forEach(r => {
    r.addEventListener("change", (e) => {
      STATE.experience = e.target.value;
      updateOptionCardStyles('experience');
    });
  });

  // Кнопка добавления кастомного напитка
  const customBtn = document.getElementById("addCustomDrinkBtn");
  if (customBtn) {
    customBtn.addEventListener("click", () => {
      const name = document.getElementById("customDrinkName").value.trim() || "Специальный снаряд";
      const vol = parseFloat(document.getElementById("customDrinkVol").value) || 250;
      const abv = parseFloat(document.getElementById("customDrinkAbv").value) || 10;
      addDrink({ name, volume_ml: vol, abv, icon: "🍸" });
      document.getElementById("customDrinkName").value = "";
    });
  }

  // Кнопка расчета норматива
  const calcBtn = document.getElementById("calculateBtn");
  if (calcBtn) {
    calcBtn.addEventListener("click", performCalculation);
  }

  // Загрузка своего фото для удостоверения
  const photoInput = document.getElementById("customPhotoInput");
  if (photoInput) {
    photoInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const img = new Image();
          img.onload = () => {
            STATE.customPhoto = img;
            renderCertificateCanvas();
          };
          img.src = event.target.result;
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Выбор аватара
  const avatarSelect = document.getElementById("avatarSelect");
  if (avatarSelect) {
    avatarSelect.addEventListener("change", (e) => {
      STATE.selectedAvatar = e.target.value;
      STATE.customPhoto = null;
      renderCertificateCanvas();
    });
  }

  // Скачивание удостоверения
  const downloadBtn = document.getElementById("downloadCertBtn");
  if (downloadBtn) {
    downloadBtn.addEventListener("click", downloadCertificate);
  }

  // Поделиться удостоверением
  const shareBtn = document.getElementById("shareCertBtn");
  if (shareBtn) {
    shareBtn.addEventListener("click", shareCertificate);
  }
}

function updateOptionCardStyles(groupName) {
  document.querySelectorAll(`input[name="${groupName}"]`).forEach(input => {
    const card = input.closest(".option-card");
    if (card) {
      card.classList.toggle("selected", input.checked);
    }
  });
}

function addDrink(preset) {
  const existing = STATE.drinks.find(d => d.name === preset.name && d.abv === preset.abv && d.volume_ml === preset.volume_ml);
  if (existing) {
    existing.count += 1;
  } else {
    STATE.drinks.push({
      name: preset.name,
      volume_ml: preset.volume_ml,
      abv: preset.abv,
      icon: preset.icon || "🍺",
      count: 1
    });
  }
  renderDrinksList();
}

function renderDrinksList() {
  const listEl = document.getElementById("drinksList");
  if (!listEl) return;

  if (STATE.drinks.length === 0) {
    listEl.innerHTML = `
      <div style="text-align:center; padding:15px; color:var(--text-muted); font-size:0.85rem;">
        Пока снаряды не выбраны. Нажмите на напитки выше, чтобы добавить подходы.
      </div>
    `;
    return;
  }

  listEl.innerHTML = "";
  STATE.drinks.forEach((drink, index) => {
    const item = document.createElement("div");
    item.className = "drink-item";
    item.innerHTML = `
      <div class="drink-item-info">
        <span class="drink-item-name">${drink.icon || "🍺"} ${drink.name}</span>
        <span class="drink-item-sub">${drink.volume_ml} мл • ${drink.abv}% об. (${drink.volume_ml * drink.count} мл всего)</span>
      </div>
      <div class="drink-item-actions">
        <button type="button" class="counter-btn" onclick="modifyDrinkCount(${index}, -1)">-</button>
        <span style="font-weight:700; min-width:20px; text-align:center;">${drink.count}</span>
        <button type="button" class="counter-btn" onclick="modifyDrinkCount(${index}, 1)">+</button>
        <button type="button" class="remove-btn" title="Удалить" onclick="removeDrink(${index})">✕</button>
      </div>
    `;
    listEl.appendChild(item);
  });
}

window.modifyDrinkCount = function(index, delta) {
  if (STATE.drinks[index]) {
    STATE.drinks[index].count += delta;
    if (STATE.drinks[index].count <= 0) {
      STATE.drinks.splice(index, 1);
    }
    renderDrinksList();
  }
};

window.removeDrink = function(index) {
  if (STATE.drinks[index]) {
    STATE.drinks.splice(index, 1);
    renderDrinksList();
  }
};

// Выполнение расчета
async function performCalculation() {
  const nameInput = document.getElementById("athleteName");
  if (nameInput && nameInput.value.trim()) {
    STATE.name = nameInput.value.trim();
  }

  const weightInput = document.getElementById("athleteWeight");
  if (weightInput) {
    STATE.weight = parseFloat(weightInput.value) || 75;
  }

  const genderSelect = document.getElementById("athleteGender");
  if (genderSelect) {
    STATE.gender = genderSelect.value;
  }

  // Штрафы
  STATE.penalties.vomited = document.getElementById("penVomit")?.checked || false;
  STATE.penalties.fell_asleep = document.getElementById("penSleep")?.checked || false;
  STATE.penalties.called_ex = document.getElementById("penEx")?.checked || false;
  STATE.penalties.lost_items = document.getElementById("penLost")?.checked || false;

  const payload = {
    name: STATE.name,
    weight: STATE.weight,
    gender: STATE.gender,
    experience: STATE.experience,
    drinks: STATE.drinks,
    hours: STATE.hours,
    snack: STATE.snack,
    penalties: STATE.penalties
  };

  try {
    const res = await fetch("/api/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    STATE.currentResult = data;
    renderCalculationResult(data);
  } catch (err) {
    console.error("Ошибка API расчета, используем клиентский расчет:", err);
    // Клиентский фоллбэк
    const fallback = clientCalculate(payload);
    STATE.currentResult = fallback;
    renderCalculationResult(fallback);
  }
}

function clientCalculate(p) {
  let pure_g = 0;
  p.drinks.forEach(d => {
    pure_g += (d.volume_ml * d.count) * (d.abv / 100) * 0.789;
  });
  const r = p.gender === 'm' ? 0.68 : 0.55;
  const raw_bac = pure_g / (p.weight * r);
  const est_bac = Math.max(0, raw_bac - Math.max(0, (p.hours - 0.5) * 0.15));
  const sober_hours = Math.round((raw_bac / 0.15) * 10) / 10;
  
  let score = pure_g * (75 / Math.max(40, p.weight));
  if (p.penalties.vomited) score = 15;

  let rank = {
    title: "1-й Взрослый разряд",
    badge: "🥈",
    icon: "🥃",
    description: "Честная пол-литра. Автопилот настроен идеально.",
    morning_verdict: "Похмелье классическое. Рекомендуется минералка."
  };
  if (score > 180) {
    rank = {
      title: "Мастер Спорта по Литрболу (МС)",
      badge: "⭐",
      icon: "🎖️",
      description: "Гроссмейстер хмельных баталий.",
      morning_verdict: "Просыпается и готовит яичницу."
    };
  } else if (score > 130) {
    rank = {
      title: "КМС по Литрболу",
      badge: "🥇",
      icon: "🏆",
      description: "Элита застолья. Ни одного звонка бывшим.",
      morning_verdict: "Огуречный рассол и аспирин."
    };
  }

  return {
    score: Math.round(score),
    pure_ethanol_g: Math.round(pure_g * 10) / 10,
    est_bac_promille: Math.round(est_bac * 100) / 100,
    sober_hours: sober_hours,
    rank: rank,
    order_num: `№ 77-A/ФЛР-2026`,
    disciplines: "Академическое застольное многоборье",
    penalty_notes: []
  };
}

function renderCalculationResult(res) {
  const box = document.getElementById("calcResultContainer") || document.getElementById("calcResultBox");
  if (!box) return;

  box.style.display = "block";
  box.scrollIntoView({ behavior: 'smooth' });

  const badgeEl = document.getElementById("resBadge");
  const rankEl = document.getElementById("resRankTitle") || document.getElementById("resTitle");
  const discEl = document.getElementById("resDiscipline");
  const descEl = document.getElementById("resDescription") || document.getElementById("resVerdict");
  const scoreEl = document.getElementById("resScore");
  const ethEl = document.getElementById("resEthanol");
  const bacEl = document.getElementById("resBac");
  const soberEl = document.getElementById("resSober");
  const morningEl = document.getElementById("resMorning");

  if (badgeEl) badgeEl.textContent = res.rank.badge || "🏅";
  if (rankEl) rankEl.textContent = res.rank.title || "Атлет";
  if (discEl) discEl.textContent = res.disciplines || "Застольное многоборье";
  if (descEl) descEl.textContent = res.rank.description || "";
  if (scoreEl) scoreEl.textContent = res.score;
  if (ethEl) ethEl.textContent = `${res.pure_ethanol_g} г`;
  if (bacEl) bacEl.textContent = `~${res.est_bac_promille} ‰`;
  if (soberEl) soberEl.textContent = `${res.sober_hours} ч.`;
  if (morningEl) morningEl.textContent = res.rank.morning_verdict || "Готов к новым свершениям";

  // Штрафы
  const penContainer = document.getElementById("resPenaltiesContainer");
  const penList = document.getElementById("resPenaltiesList");
  if (penContainer && penList) {
    if (res.penalty_notes && res.penalty_notes.length > 0) {
      penList.innerHTML = res.penalty_notes.map(n => `<li>${escapeHtml(n)}</li>`).join('');
      penContainer.style.display = "block";
    } else {
      penContainer.style.display = "none";
    }
  }

  // Кнопка перехода к корочке
  const toCertBtn = document.getElementById("goToCertBtn");
  if (toCertBtn) {
    toCertBtn.onclick = () => {
      if (!STATE.detectorVerified) {
        if (confirm("🚨 ВНИМАНИЕ: Вы претендуете на спортивный разряд!\nЖелаете пройти «Детектор Пиздежа», чтобы подтвердить подлинность и получить защитный штамп ВАК?")) {
          startDetectorFromCalc();
          return;
        }
      }
      switchTab("tab-cert");
    };
  }

  const toDetectorBtn = document.getElementById("goToDetectorBtn");
  if (toDetectorBtn) {
    toDetectorBtn.onclick = () => {
      startDetectorFromCalc();
    };
  }
}

// ==========================================
// ЭКЗАМЕН ВАК (ТЕОРИЯ)
// ==========================================

async function initQuiz() {
  try {
    const res = await fetch("/api/questions");
    STATE.quizQuestions = await res.json();
  } catch (e) {
    console.warn("Using inline questions fallback");
    STATE.quizQuestions = [
      {
        question: "Вам предлагают запить крепкий напиток сладкой газировкой. Ваши действия?",
        options: [
          { text: "С радостью соглашусь, так слаще", score: 2 },
          { text: "Откажусь и запью чистой водой", score: 10 },
          { text: "Запивать? Только закусывать огурцом!", score: 15 },
          { text: "Запью нефильтрованным пивом («Ёрш»)", score: 12 }
        ]
      }
    ];
  }
  renderQuizQuestion();
}

function renderQuizQuestion() {
  const container = document.getElementById("quizContainer");
  if (!container || !STATE.quizQuestions.length) return;

  const q = STATE.quizQuestions[STATE.quizCurrentIdx];
  const total = STATE.quizQuestions.length;
  const progressPct = ((STATE.quizCurrentIdx + 1) / total) * 100;

  const fillEl = document.getElementById("quizProgressFill");
  if (fillEl) fillEl.style.width = `${progressPct}%`;

  const letters = ["А", "Б", "В", "Г"];

  container.innerHTML = `
    <div class="quiz-question-box">
      <div class="quiz-q-num">Вопрос ${STATE.quizCurrentIdx + 1} из ${total}</div>
      <div class="quiz-q-text">${q.question}</div>
      <div class="quiz-options">
        ${q.options.map((opt, i) => `
          <button type="button" class="quiz-opt-btn" onclick="handleQuizAnswer(${opt.score}, '${escapeHtml(opt.comment || '')}')">
            <span class="quiz-opt-letter">${letters[i]}</span>
            <span>${opt.text}</span>
          </button>
        `).join("")}
      </div>
    </div>
  `;
}

window.handleQuizAnswer = function(score, comment) {
  STATE.quizTotalScore += score;
  STATE.quizCurrentIdx++;

  if (STATE.quizCurrentIdx < STATE.quizQuestions.length) {
    renderQuizQuestion();
  } else {
    finishQuiz();
  }
};

function finishQuiz() {
  const container = document.getElementById("quizContainer");
  if (!container) return;

  const score = STATE.quizTotalScore;
  let rankTitle = "3-й Взрослый разряд по Литрболу";
  let badge = "🥈";
  let desc = "Теоретическая база крепкая. Знает технику безопасности и правила застольного этикета.";

  if (score >= 130) {
    rankTitle = "Мастер Спорта (Теоретик-Гроссмейстер)";
    badge = "⭐";
    desc = "Абсолютное знание регламента, традиций и фармакологии! Рекомендован на должность председателя ВАК.";
  } else if (score >= 95) {
    rankTitle = "КМС по теоретическому литрболу";
    badge = "🥇";
    desc = "Отличное понимание психологии застолья и первой помощи собутыльникам.";
  } else if (score < 50) {
    rankTitle = "Юношеский разряд (Кефирный теоретик)";
    badge = "🍼";
    desc = "Много тактических ошибок. Рекомендуется повторить правила перед следующим выходом на дистанцию.";
  }

  // Обновляем состояние атлета
  STATE.currentResult = {
    score: score,
    pure_ethanol_g: 0,
    est_bac_promille: 0,
    sober_hours: 0,
    rank: {
      title: rankTitle,
      badge: badge,
      description: desc,
      morning_verdict: "Теоретически подкован, похмелья нет."
    },
    order_num: `№ ТЕОРИЯ-${score}/ВАК`,
    disciplines: "Теоретическая классификация и этикет"
  };

  container.innerHTML = `
    <div class="result-card">
      <div class="result-badge">${badge}</div>
      <div class="result-title">${rankTitle}</div>
      <div class="result-order">ИТОГОВЫЙ БАЛЛ ЭКЗАМЕНА: ${score} ОЧКОВ</div>
      <div class="result-verdict">${desc}</div>
      <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin-top:20px;">
        <button type="button" class="btn-primary" style="width:auto; padding:12px 24px;" onclick="switchTab('tab-cert')">
          🎖️ Получить официальную корочку
        </button>
        <button type="button" class="btn-secondary" onclick="restartQuiz()">
          🔄 Сдать экзамен заново
        </button>
      </div>
    </div>
  `;
}

window.restartQuiz = function() {
  STATE.quizCurrentIdx = 0;
  STATE.quizTotalScore = 0;
  renderQuizQuestion();
};

function escapeHtml(str) {
  return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ==========================================
// ГЕНЕРАТОР УДОСТОВЕРЕНИЯ (CANVAS 1200 x 800)
// ==========================================

function drawDefaultCertificate() {
  // Инициализируем канвас заглушкой
  setTimeout(() => {
    renderCertificateCanvas();
  }, 100);
}

function renderCertificateCanvas() {
  const canvas = document.getElementById("certCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = 1200;
  const H = 800;

  canvas.width = W;
  canvas.height = H;

  const result = STATE.currentResult || {
    rank: { title: "Мастер Спорта по Литрболу (МС)" },
    order_num: "№ 40-ОПОХМЕЛ/ФЛР-2026",
    disciplines: "Академическое застольное многоборье"
  };

  // 1. Внешний фон (корочка цвета бордовый сафьян / темно-синяя кожа)
  const isRedCover = true;
  const gradBg = ctx.createLinearGradient(0, 0, W, H);
  if (isRedCover) {
    gradBg.addColorStop(0, "#4a0e17");
    gradBg.addColorStop(0.5, "#6b1422");
    gradBg.addColorStop(1, "#360810");
  } else {
    gradBg.addColorStop(0, "#0f172a");
    gradBg.addColorStop(0.5, "#1e293b");
    gradBg.addColorStop(1, "#0a0f1d");
  }
  ctx.fillStyle = gradBg;
  roundRect(ctx, 0, 0, W, H, 24);
  ctx.fill();

  // Золотая прострочка по периметру
  ctx.strokeStyle = "#e5a93b";
  ctx.lineWidth = 4;
  roundRect(ctx, 16, 16, W - 32, H - 32, 18);
  ctx.stroke();

  // Линия сгиба удостоверения по центру
  const foldX = W / 2;
  const foldGrad = ctx.createLinearGradient(foldX - 15, 0, foldX + 15, 0);
  foldGrad.addColorStop(0, "rgba(0,0,0,0.4)");
  foldGrad.addColorStop(0.5, "rgba(0,0,0,0.85)");
  foldGrad.addColorStop(1, "rgba(0,0,0,0.4)");
  ctx.fillStyle = foldGrad;
  ctx.fillRect(foldX - 10, 16, 20, H - 32);

  // Внутренние бежево-гербовые страницы (разворот)
  drawInnerPage(ctx, 30, 30, foldX - 45, H - 60, true);
  drawInnerPage(ctx, foldX + 15, 30, foldX - 45, H - 60, false);

  // ------------------------------------------
  // ЛЕВАЯ СТРАНИЦА: Обложка и герб
  // ------------------------------------------
  const leftCenterX = 30 + (foldX - 45) / 2;

  // Золотой герб ФЛР
  drawCoatOfArms(ctx, leftCenterX, 220);

  ctx.textAlign = "center";
  ctx.fillStyle = "#1e1e24";
  ctx.font = "bold 22px 'Times New Roman', serif";
  ctx.fillText("ВСЕРОССИЙСКАЯ ФЕДЕРАЦИЯ ЛИТРБОЛА", leftCenterX, 380);

  ctx.fillStyle = "#8b1e2d";
  ctx.font = "bold 15px sans-serif";
  ctx.letterSpacing = "2px";
  ctx.fillText("ВЫСШАЯ АТТЕСТАЦИОННАЯ КОМИССИЯ", leftCenterX, 410);

  ctx.fillStyle = "#b45309";
  ctx.font = "bold 32px 'Times New Roman', serif";
  ctx.fillText("УДОСТОВЕРЕНИЕ", leftCenterX, 490);

  ctx.font = "bold 20px 'Times New Roman', serif";
  ctx.fillStyle = "#1e1e24";
  ctx.fillText("СПОРТИВНОГО РАЗРЯДА", leftCenterX, 525);

  ctx.font = "italic 16px 'Times New Roman', serif";
  ctx.fillStyle = "#4b5563";
  ctx.fillText(result.order_num || "Приказ № 05-ОПОХМЕЛ/2026", leftCenterX, 580);
  ctx.fillText(`Действительно при наличии чувства юмора и закуски`, leftCenterX, 610);

  // Защитная гильоширная полоска
  drawGuillocheLine(ctx, 60, 660, foldX - 75, 660);

  // Штамп Детектора Пиздежа
  if (STATE.detectorVerified) {
    drawDetectorStamp(ctx, leftCenterX, 650);
  }

  // ------------------------------------------
  // ПРАВАЯ СТРАНИЦА: Данные спортсмена, разряд, печать
  // ------------------------------------------
  const rightLeftX = foldX + 45;
  const rightWidth = foldX - 75;

  ctx.textAlign = "center";
  ctx.fillStyle = "#1e1e24";
  ctx.font = "bold 16px 'Times New Roman', serif";
  ctx.fillText("ЕДИНАЯ ЗАСТОЛЬНАЯ СПОРТИВНАЯ КЛАССИФИКАЦИЯ (ЕЗСК)", rightLeftX + rightWidth / 2, 70);

  // Фото / Аватарка (слева на правой странице)
  const photoX = rightLeftX + 15;
  const photoY = 100;
  const photoW = 150;
  const photoH = 190;
  drawAthletePhoto(ctx, photoX, photoY, photoW, photoH);

  // Текстовые поля спортсмена (справа от фото)
  ctx.textAlign = "left";
  const infoX = photoX + photoW + 25;

  ctx.fillStyle = "#6b7280";
  ctx.font = "12px sans-serif";
  ctx.fillText("ФАМИЛИЯ, ИМЯ:", infoX, 120);
  ctx.fillStyle = "#111827";
  ctx.font = "bold 24px 'Times New Roman', serif";
  ctx.fillText(STATE.name || "Атлетов Иван", infoX, 150);

  ctx.fillStyle = "#6b7280";
  ctx.font = "12px sans-serif";
  ctx.fillText("ВЕСОВАЯ КАТЕГОРИЯ:", infoX, 190);
  ctx.fillStyle = "#111827";
  ctx.font = "bold 18px sans-serif";
  ctx.fillText(`${STATE.weight} кг (${getWeightCategory(STATE.weight)})`, infoX, 215);

  ctx.fillStyle = "#6b7280";
  ctx.font = "12px sans-serif";
  ctx.fillText("КОРОННАЯ ДИСЦИПЛИНА:", infoX, 255);
  ctx.fillStyle = "#8b1e2d";
  ctx.font = "bold 16px sans-serif";
  ctx.fillText(result.disciplines || "Академическое многоборье", infoX, 280);

  // Золотая плашка присвоенного разряда
  const rankY = 320;
  const rankBoxW = rightWidth - 20;
  const rankGrad = ctx.createLinearGradient(rightLeftX + 10, rankY, rightLeftX + 10 + rankBoxW, rankY + 60);
  rankGrad.addColorStop(0, "#fef3c7");
  rankGrad.addColorStop(0.5, "#fde68a");
  rankGrad.addColorStop(1, "#fef3c7");
  ctx.fillStyle = rankGrad;
  ctx.strokeStyle = "#d97706";
  ctx.lineWidth = 2;
  roundRect(ctx, rightLeftX + 10, rankY, rankBoxW, 64, 10);
  ctx.fill();
  ctx.stroke();

  ctx.textAlign = "center";
  ctx.fillStyle = "#78350f";
  ctx.font = "bold 13px sans-serif";
  ctx.fillText("ПРИСВОЕНО СПОРТИВНОЕ ЗВАНИЕ / РАЗРЯД:", rightLeftX + 10 + rankBoxW / 2, rankY + 22);

  ctx.fillStyle = "#991b1b";
  ctx.font = "bold 24px 'Times New Roman', serif";
  ctx.fillText(result.rank.title, rightLeftX + 10 + rankBoxW / 2, rankY + 50);

  // Метрики выступления
  if (result.pure_ethanol_g > 0) {
    ctx.textAlign = "left";
    ctx.font = "13px sans-serif";
    ctx.fillStyle = "#4b5563";
    ctx.fillText(`Чистый спирт (C₂H₅OH): ${result.pure_ethanol_g} г  •  Промилле: ~${result.est_bac_promille} ‰`, rightLeftX + 15, 415);
  }

  // Подписи и печать внизу
  const sigY = 560;
  ctx.font = "14px 'Times New Roman', serif";
  ctx.fillStyle = "#111827";
  ctx.fillText("Председатель ВАК:", rightLeftX + 20, sigY);
  ctx.font = "italic 18px 'Brush Script MT', cursive, serif";
  ctx.fillStyle = "#1e3a8a";
  ctx.fillText("С. Г. Наливашкин", rightLeftX + 170, sigY - 2);

  ctx.strokeStyle = "#4b5563";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(rightLeftX + 160, sigY + 5);
  ctx.lineTo(rightLeftX + 310, sigY + 5);
  ctx.stroke();

  ctx.font = "14px 'Times New Roman', serif";
  ctx.fillStyle = "#111827";
  ctx.fillText("Секретарь комиссии:", rightLeftX + 20, sigY + 45);
  ctx.font = "italic 16px 'Brush Script MT', cursive, serif";
  ctx.fillStyle = "#1e3a8a";
  ctx.fillText("О. П. Опохмелова", rightLeftX + 170, sigY + 43);

  ctx.beginPath();
  ctx.moveTo(rightLeftX + 160, sigY + 50);
  ctx.lineTo(rightLeftX + 310, sigY + 50);
  ctx.stroke();

  // Синяя гербовая печать
  drawOfficialStamp(ctx, rightLeftX + 330, sigY + 10);

  // Защитный стилизованный QR-код
  drawFakeQrCode(ctx, rightLeftX + rightWidth - 85, sigY - 20, 75);
}

// Вспомогательные функции отрисовки
function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function drawInnerPage(ctx, x, y, w, h, isLeft) {
  // Кремово-защитная бумага с водяной сеткой
  ctx.fillStyle = "#fcfaf2";
  roundRect(ctx, x, y, w, h, 8);
  ctx.fill();

  // Тонкая рамка страницы
  ctx.strokeStyle = "#d4af37";
  ctx.lineWidth = 1.5;
  roundRect(ctx, x + 8, y + 8, w - 16, h - 16, 6);
  ctx.stroke();

  ctx.strokeStyle = "#e8dfc8";
  ctx.lineWidth = 0.5;
  roundRect(ctx, x + 12, y + 12, w - 24, h - 24, 4);
  ctx.stroke();
}

function drawCoatOfArms(ctx, cx, cy) {
  ctx.save();
  ctx.translate(cx, cy);

  // Золотой лавровый венок
  ctx.strokeStyle = "#d97706";
  ctx.fillStyle = "#fef3c7";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(0, 0, 70, 0, Math.PI * 2);
  ctx.stroke();
  ctx.fill();

  // Скрещенные штопоры / вилки
  ctx.strokeStyle = "#b45309";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(-40, -40);
  ctx.lineTo(40, 40);
  ctx.moveTo(40, -40);
  ctx.lineTo(-40, 40);
  ctx.stroke();

  // Граненый стакан по центру
  ctx.fillStyle = "#2563eb";
  ctx.strokeStyle = "#1d4ed8";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(-22, -25);
  ctx.lineTo(22, -25);
  ctx.lineTo(16, 35);
  ctx.lineTo(-16, 35);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // Долька лимона или огурец
  ctx.fillStyle = "#84cc16";
  ctx.beginPath();
  ctx.arc(0, -28, 12, 0, Math.PI, true);
  ctx.closePath();
  ctx.fill();

  // Пятиконечная золотая звезда сверху
  drawStar(ctx, 0, -52, 5, 12, 6, "#d97706");

  ctx.restore();
}

function drawStar(ctx, cx, cy, spikes, outerRadius, innerRadius, color) {
  let rot = Math.PI / 2 * 3;
  let x = cx;
  let y = cy;
  let step = Math.PI / spikes;

  ctx.beginPath();
  ctx.moveTo(cx, cy - outerRadius);
  for (let i = 0; i < spikes; i++) {
    x = cx + Math.cos(rot) * outerRadius;
    y = cy + Math.sin(rot) * outerRadius;
    ctx.lineTo(x, y);
    rot += step;

    x = cx + Math.cos(rot) * innerRadius;
    y = cy + Math.sin(rot) * innerRadius;
    ctx.lineTo(x, y);
    rot += step;
  }
  ctx.lineTo(cx, cy - outerRadius);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
}

function drawAthletePhoto(ctx, x, y, w, h) {
  ctx.save();
  ctx.fillStyle = "#e5e7eb";
  ctx.strokeStyle = "#9ca3af";
  ctx.lineWidth = 2;
  roundRect(ctx, x, y, w, h, 6);
  ctx.fill();
  ctx.stroke();

  if (STATE.customPhoto) {
    ctx.clip();
    ctx.drawImage(STATE.customPhoto, x, y, w, h);
  } else {
    // Векторный аватар
    ctx.clip();
    ctx.fillStyle = "#cbd5e1";
    ctx.fillRect(x, y, w, h);

    // Голова и силуэт
    const cx = x + w / 2;
    const cy = y + h / 2 - 10;
    
    // Плечи
    ctx.fillStyle = "#475569";
    ctx.beginPath();
    ctx.arc(cx, cy + 90, 60, Math.PI, 0, false);
    ctx.fill();

    // Голова
    ctx.fillStyle = "#fbcfe8";
    ctx.beginPath();
    ctx.arc(cx, cy, 38, 0, Math.PI * 2);
    ctx.fill();

    // Шапка или прическа в зависимости от аватара
    ctx.fillStyle = "#1e293b";
    ctx.beginPath();
    ctx.arc(cx, cy - 12, 40, Math.PI, 0, false);
    ctx.fill();

    // Темные очки / усы
    ctx.fillStyle = "#0f172a";
    ctx.fillRect(cx - 24, cy - 5, 20, 10);
    ctx.fillRect(cx + 4, cy - 5, 20, 10);
    ctx.fillRect(cx - 6, cy - 3, 12, 3);
  }

  ctx.restore();

  // Печать уголка фото
  ctx.save();
  ctx.strokeStyle = "rgba(30, 58, 138, 0.4)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(x + w, y + h, 35, Math.PI, Math.PI * 1.5);
  ctx.stroke();
  ctx.restore();
}

function drawOfficialStamp(ctx, cx, cy) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(-0.15); // легкий естественный наклон штампа

  ctx.strokeStyle = "rgba(30, 58, 138, 0.75)";
  ctx.fillStyle = "rgba(30, 58, 138, 0.75)";
  ctx.lineWidth = 3;

  // Внешний круг
  ctx.beginPath();
  ctx.arc(0, 0, 55, 0, Math.PI * 2);
  ctx.stroke();

  // Внутренний круг
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(0, 0, 48, 0, Math.PI * 2);
  ctx.stroke();

  // Текст по кругу
  ctx.font = "bold 9px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("★ ФЕДЕРАЦИЯ ЛИТРБОЛА РОССИИ ★", 0, -32);
  ctx.fillText("АТТЕСТОВАНО ВАК", 0, 36);

  // Центр печати
  ctx.font = "bold 11px sans-serif";
  ctx.fillText("ДЛЯ", 0, -8);
  ctx.fillText("ДОКУМЕНТОВ", 0, 6);
  ctx.font = "8px sans-serif";
  ctx.fillText("№ 1984-ФЛР", 0, 18);

  ctx.restore();
}

function drawFakeQrCode(ctx, x, y, size) {
  ctx.save();
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(x, y, size, size);
  ctx.strokeStyle = "#1f2937";
  ctx.lineWidth = 1;
  ctx.strokeRect(x, y, size, size);

  // Стилизованная QR матрица
  ctx.fillStyle = "#111827";
  const step = size / 7;
  // Угловые маркеры
  ctx.fillRect(x + step * 0.5, y + step * 0.5, step * 2, step * 2);
  ctx.fillRect(x + size - step * 2.5, y + step * 0.5, step * 2, step * 2);
  ctx.fillRect(x + step * 0.5, y + size - step * 2.5, step * 2, step * 2);

  // Псевдо-пиксели
  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 5; c++) {
      if ((r + c * 3) % 2 === 0) {
        ctx.fillRect(x + (c + 1) * step, y + (r + 1) * step, step * 0.8, step * 0.8);
      }
    }
  }

  ctx.font = "8px sans-serif";
  ctx.fillStyle = "#4b5563";
  ctx.textAlign = "center";
  ctx.fillText("ПРОВЕРЕНО", x + size / 2, y + size + 10);
  ctx.restore();
}

function drawGuillocheLine(ctx, x1, y1, x2, y2) {
  ctx.strokeStyle = "#e5e7eb";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}

function getWeightCategory(w) {
  if (w < 65) return "Полулегкий вес";
  if (w < 80) return "Средний вес";
  if (w < 100) return "Полутяжелый вес";
  return "Супертяжелый вес (Танк)";
}

function downloadCertificate() {
  const canvas = document.getElementById("certCanvas");
  if (!canvas) return;

  const link = document.createElement("a");
  link.download = `Удостоверение_Литрбол_${(STATE.name || "Атлет").replace(/\s+/g, '_')}.png`;
  link.href = canvas.toDataURL("image/png");
  link.click();
}

function shareCertificate() {
  const canvas = document.getElementById("certCanvas");
  const rank = STATE.currentResult?.rank?.title || "Мастер Спорта по Литрболу";
  const text = `🍺 Мой официальный разряд по литрболу: ${rank}! Приказ ВАК выдан. Проверь свой разряд!`;

  if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.openTelegramLink) {
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(window.location.href)}&text=${encodeURIComponent(text)}`;
    window.Telegram.WebApp.openTelegramLink(shareUrl);
  } else if (navigator.share) {
    canvas.toBlob(blob => {
      const file = new File([blob], "litrball_cert.png", { type: "image/png" });
      navigator.share({
        title: "Федерация Литрбола России",
        text: text,
        files: [file]
      }).catch(() => {});
    });
  } else {
    navigator.clipboard.writeText(text);
    alert("Текст скопирован в буфер обмена! Отправьте его друзьям в чат.");
  }
}

// Загрузка справочника разрядов
async function fetchRanksTable() {
  const tbody = document.getElementById("ranksTableBody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/ranks");
    const ranks = await res.json();
    tbody.innerHTML = ranks.map(r => `
      <tr>
        <td><div class="rank-badge-cell"><span>${r.icon || '🏅'}</span> <strong>${r.title}</strong></div></td>
        <td style="color:var(--gold-glow); font-weight:700;">${r.min_score}+ очков</td>
        <td style="font-size:0.85rem; color:var(--text-muted);">${r.description}</td>
        <td style="font-size:0.85rem; color:#a7f3d0;">${r.morning_verdict}</td>
      </tr>
    `).join("");
  } catch (e) {
    console.warn("Could not load ranks table", e);
  }
}

function drawDetectorStamp(ctx, cx, cy) {
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(-0.04);
  ctx.strokeStyle = "rgba(185, 28, 28, 0.9)";
  ctx.lineWidth = 2.5;
  roundRect(ctx, -145, -16, 290, 32, 6);
  ctx.stroke();

  ctx.fillStyle = "rgba(185, 28, 28, 0.9)";
  ctx.font = "bold 11px sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("★ ПРОВЕРЕНО ВАК: ПИЗДЕЖА НЕТ ★", 0, 4);
  ctx.restore();
}

// ==========================================
// ДЕТЕКТОР ПИЗДЕЖА (ПОЛИГРАФ ВАК)
// ==========================================

const DETECTOR_STATE = {
  mathTimerInterval: null,
  mathTimeLeft: 10.0,
  correctChange: 160,
  motorTimerInterval: null,
  motorTimeLeft: 8.0,
  motorHits: 0,
  requiredHits: 4,
  pickleMoveInterval: null,
  mathPassed: false,
  motorPassed: false
};

function initDetector() {
  setupDetectorProof();
  const detTabBtn = document.querySelector('button[data-tab="tab-detector"]');
  if (detTabBtn) {
    detTabBtn.addEventListener("click", () => {
      resetAndStartDetector();
    });
  }
}

function startDetectorFromCalc() {
  switchTab("tab-detector");
  resetAndStartDetector();
}

function resetAndStartDetector() {
  const stepMath = document.getElementById("detStepMath");
  const stepMotor = document.getElementById("detStepMotor");
  const stepProof = document.getElementById("detStepProof");
  const resultBox = document.getElementById("detResultBox");

  if (stepMath) stepMath.style.display = "block";
  if (stepMotor) stepMotor.style.display = "none";
  if (stepProof) stepProof.style.display = "none";
  if (resultBox) resultBox.style.display = "none";

  startMathStep();
}

function startMathStep() {
  const beerPrice = [120, 130, 140, 150][Math.floor(Math.random() * 4)];
  const snackPrice = [60, 70, 80, 90][Math.floor(Math.random() * 4)];
  const total = beerPrice * 2 + snackPrice;
  const bill = 500;
  DETECTOR_STATE.correctChange = bill - total;

  const qEl = document.getElementById("detMathQuestion");
  if (qEl) {
    qEl.textContent = `Вы берете 2 бутылки пива по ${beerPrice}₽ и пачку сухариков за ${snackPrice}₽. Дали кассирше ${bill}₽. Сколько сдачи вам обязаны вернуть?`;
  }

  const optionsContainer = document.getElementById("detMathOptions");
  if (!optionsContainer) return;
  optionsContainer.innerHTML = "";

  const options = [
    { text: `${DETECTOR_STATE.correctChange} ₽`, correct: true },
    { text: `${DETECTOR_STATE.correctChange - 30} ₽`, correct: false },
    { text: `${DETECTOR_STATE.correctChange + 40} ₽`, correct: false },
    { text: "«Сдачи не надо, я миллионер!» 💸", correct: true, boss: true }
  ].sort(() => Math.random() - 0.5);

  options.forEach(opt => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-secondary";
    btn.style.width = "100%";
    btn.style.padding = "12px";
    btn.textContent = opt.text;
    btn.onclick = () => handleMathAnswer(opt);
    optionsContainer.appendChild(btn);
  });

  // Запуск таймера
  clearInterval(DETECTOR_STATE.mathTimerInterval);
  DETECTOR_STATE.mathTimeLeft = 10.0;
  const timerEl = document.getElementById("detMathTimer");
  if (timerEl) {
    timerEl.textContent = "10.0 сек";
    timerEl.style.color = "var(--accent-red)";
  }

  DETECTOR_STATE.mathTimerInterval = setInterval(() => {
    DETECTOR_STATE.mathTimeLeft -= 0.1;
    if (DETECTOR_STATE.mathTimeLeft <= 0) {
      clearInterval(DETECTOR_STATE.mathTimerInterval);
      if (timerEl) timerEl.textContent = "0.0 сек (Время вышло!)";
      handleMathAnswer({ correct: false, timeout: true });
    } else {
      if (timerEl) timerEl.textContent = `${DETECTOR_STATE.mathTimeLeft.toFixed(1)} сек`;
    }
  }, 100);
}

function handleMathAnswer(opt) {
  clearInterval(DETECTOR_STATE.mathTimerInterval);
  DETECTOR_STATE.mathPassed = opt.correct;

  setTimeout(() => {
    const stepMath = document.getElementById("detStepMath");
    const stepMotor = document.getElementById("detStepMotor");
    if (stepMath) stepMath.style.display = "none";
    if (stepMotor) stepMotor.style.display = "block";
    startMotorStep();
  }, 400);
}

function startMotorStep() {
  DETECTOR_STATE.motorHits = 0;
  DETECTOR_STATE.motorTimeLeft = 8.0;

  const hitCountEl = document.getElementById("detHitCount");
  if (hitCountEl) hitCountEl.textContent = `0 / ${DETECTOR_STATE.requiredHits}`;

  const timerEl = document.getElementById("detMotorTimer");
  if (timerEl) timerEl.textContent = "8.0 сек";

  const area = document.getElementById("pickleGameArea");
  const target = document.getElementById("pickleTarget");

  function movePickle() {
    if (!area || !target) return;
    const maxX = Math.max(10, area.clientWidth - 50);
    const maxY = Math.max(10, area.clientHeight - 50);
    const randX = Math.floor(Math.random() * maxX);
    const randY = Math.floor(Math.random() * maxY);
    target.style.left = `${randX}px`;
    target.style.top = `${randY}px`;
  }

  movePickle();
  clearInterval(DETECTOR_STATE.pickleMoveInterval);
  DETECTOR_STATE.pickleMoveInterval = setInterval(movePickle, 700);

  if (target) {
    target.onclick = () => {
      DETECTOR_STATE.motorHits++;
      if (hitCountEl) hitCountEl.textContent = `${DETECTOR_STATE.motorHits} / ${DETECTOR_STATE.requiredHits}`;
      movePickle();
      if (DETECTOR_STATE.motorHits >= DETECTOR_STATE.requiredHits) {
        finishMotorStep(true);
      }
    };
  }

  clearInterval(DETECTOR_STATE.motorTimerInterval);
  DETECTOR_STATE.motorTimerInterval = setInterval(() => {
    DETECTOR_STATE.motorTimeLeft -= 0.1;
    if (DETECTOR_STATE.motorTimeLeft <= 0) {
      finishMotorStep(DETECTOR_STATE.motorHits >= DETECTOR_STATE.requiredHits);
    } else {
      if (timerEl) timerEl.textContent = `${DETECTOR_STATE.motorTimeLeft.toFixed(1)} сек`;
    }
  }, 100);
}

function finishMotorStep(passed) {
  clearInterval(DETECTOR_STATE.motorTimerInterval);
  clearInterval(DETECTOR_STATE.pickleMoveInterval);
  DETECTOR_STATE.motorPassed = passed;

  const stepMotor = document.getElementById("detStepMotor");
  const stepProof = document.getElementById("detStepProof");
  if (stepMotor) stepMotor.style.display = "none";
  if (stepProof) stepProof.style.display = "block";
}

function setupDetectorProof() {
  const oathBtn = document.getElementById("detOathBtn");
  if (oathBtn) {
    oathBtn.onclick = () => finishDetector(true);
  }

  const photoInput = document.getElementById("detPhotoProof");
  if (photoInput) {
    photoInput.onchange = () => {
      alert("🔬 Сканирование снимка нейросетью ВАК...\nОбнаружено: тара стеклянная, следы этикета и солений!\nПодлинность подтверждена.");
      finishDetector(true);
    };
  }

  const finishBtn = document.getElementById("detFinishBtn");
  if (finishBtn) {
    finishBtn.onclick = () => {
      switchTab("tab-cert");
    };
  }
}

function finishDetector(proofAccepted) {
  const stepProof = document.getElementById("detStepProof");
  const resBox = document.getElementById("detResultBox");
  if (stepProof) stepProof.style.display = "none";
  if (resBox) resBox.style.display = "block";

  STATE.detectorVerified = true;

  let title = "ПИЗДЁЖ НЕ ВЫЯВЛЕН! АТТЕСТОВАНО ВАК";
  let badge = "🛡️";
  let desc = "Полевые испытания завершены успешно. Алкогольная математика и реакция на огурец соответствуют соревновательным нормам. В официальное удостоверение спортсмена внесена защитная гербовая отметка ВАК!";

  if (!DETECTOR_STATE.mathPassed && !DETECTOR_STATE.motorPassed) {
    title = "ВЫСОКИЙ УРОВЕНЬ ТРЕМОРА!";
    badge = "⚠️";
    desc = "Касса посчитана неверно, огурец убежал. Однако это доказывает, что спортсмен действительно употребил! Разряд подтвержден с занесением замечания за потерю координации.";
  }

  const titleEl = document.getElementById("detVerdictTitle");
  const badgeEl = document.getElementById("detVerdictBadge");
  const descEl = document.getElementById("detVerdictDesc");

  if (titleEl) titleEl.textContent = title;
  if (badgeEl) badgeEl.textContent = badge;
  if (descEl) descEl.innerHTML = desc;

  renderCertificateCanvas();
}

// =============================================================
// УЛЬТИМАТИВНЫЙ ФАРШ: ТРЕЗВОМЕР (BAC / ВИДМАРК)
// =============================================================
function initBacTracker() {
  const slider = document.getElementById("bacElapsedSlider");
  const sliderVal = document.getElementById("bacElapsedVal");

  if (slider) {
    slider.addEventListener("input", () => {
      if (sliderVal) sliderVal.textContent = `${slider.value} ч.`;
      updateBacDisplay(parseFloat(slider.value));
    });
  }

  // Обновляем при изменении параметров
  const calcBtn = document.getElementById("calculateBtn");
  if (calcBtn) {
    calcBtn.addEventListener("click", () => {
      setTimeout(() => updateBacDisplay(slider ? parseFloat(slider.value) : 0), 200);
    });
  }
}

function updateBacDisplay(hoursPassed = 0) {
  let totalEthanolG = 0;
  STATE.drinks.forEach(d => {
    const vol = (d.volume_ml || 0) * (d.count || 1);
    const abv = d.abv || 0;
    totalEthanolG += vol * (abv / 100.0) * 0.789;
  });

  const weight = STATE.weight || 80;
  const gender = STATE.gender || 'm';
  const r = gender === 'm' ? 0.68 : 0.55;
  const peakBac = totalEthanolG / (weight * r);
  const currentBac = Math.max(0, peakBac - (hoursPassed * 0.15));

  const driveHours = currentBac > 0.35 ? Math.round(((currentBac - 0.35) / 0.15) * 10) / 10 : 0.0;
  const fullHours = Math.round((currentBac / 0.15) * 10) / 10;

  const bacNumEl = document.getElementById("bacNumber");
  const stageEl = document.getElementById("bacStageBadge");
  const descEl = document.getElementById("bacStageDesc");
  const driveEl = document.getElementById("bacDriveHours");
  const fullEl = document.getElementById("bacFullHours");
  const gauge = document.getElementById("gaugeCircle");

  if (bacNumEl) bacNumEl.textContent = currentBac.toFixed(2);
  if (driveEl) driveEl.textContent = `${driveHours} ч.`;
  if (fullEl) fullEl.textContent = `${fullHours} ч.`;

  // Определение стадии
  let stage = "Абсолютная трезвость";
  let desc = "Реакция 100%, готов к вождению и защите диссертации.";
  let color = "#10b981";

  if (currentBac > 0 && currentBac < 0.5) {
    stage = "Легкая эйфория";
    desc = "Подъем настроения, расслабленность, легкая тяга к душевным беседам.";
    color = "#3b82f6";
  } else if (currentBac >= 0.5 && currentBac < 1.0) {
    stage = "Среднее опьянение";
    desc = "Снижение концентрации, эмоциональные тосты, желание спеть хором.";
    color = "#f59e0b";
  } else if (currentBac >= 1.0 && currentBac < 1.5) {
    stage = "Заметное опьянение";
    desc = "Шаткая походка, автопилот включен, ключи лучше убрать в дальний карман.";
    color = "#f97316";
  } else if (currentBac >= 1.5 && currentBac < 2.5) {
    stage = "Тяжелое опьянение";
    desc = "Глубокая ночная философия, споры о геополитике, срочно нужен чай и подушка.";
    color = "#ef4444";
  } else if (currentBac >= 2.5) {
    stage = "Космическая перегрузка";
    desc = "Критическая зона! Срочно сорбенты, вода и горизонтальный покой.";
    color = "#7f1d1d";
  }

  if (stageEl) {
    stageEl.textContent = stage;
    stageEl.style.color = color;
    stageEl.style.background = `rgba(${color === '#10b981' ? '16, 185, 129' : '239, 68, 68'}, 0.2)`;
  }
  if (descEl) descEl.textContent = desc;

  // Поворот спидометра (от -45deg до 135deg)
  if (gauge) {
    const deg = Math.min(135, -45 + (currentBac / 3.0) * 180);
    gauge.style.transform = `rotate(${deg}deg)`;
    gauge.style.borderTopColor = color;
  }
}

// =============================================================
// УЛЬТИМАТИВНЫЙ ФАРШ: КОМНАТА ЗАСТОЛЬНОЙ ЗАРУБЫ (PARTY BATTLE ROOM)
// =============================================================
let activePartyRoom = null;
let roomPollInterval = null;
let roomCountdownTimer = null;
let selectedRoomDuration = 15;

function initDuels() {
  // Выбор длительности зарубы
  document.querySelectorAll(".room-duration-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".room-duration-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      selectedRoomDuration = parseInt(btn.dataset.mins, 10);
    });
  });

  // Кнопка "Создать комнату"
  const btnCreate = document.getElementById("btnCreateRoom");
  if (btnCreate) {
    btnCreate.addEventListener("click", createPartyRoom);
  }

  // Кнопка "Войти по коду"
  const btnJoin = document.getElementById("btnJoinRoomByCode");
  if (btnJoin) {
    btnJoin.addEventListener("click", () => {
      const codeInput = document.getElementById("inputRoomCode");
      const code = codeInput ? codeInput.value.trim().toUpperCase() : "";
      if (!code) {
        alert("Пожалуйста, введите код комнаты!");
        return;
      }
      joinPartyRoom(code);
    });
  }

  // Кнопка "Готов"
  const btnReady = document.getElementById("btnToggleReady");
  if (btnReady) {
    btnReady.addEventListener("click", togglePartyReady);
  }

  // Кнопка "Старт" (Хост)
  const btnStart = document.getElementById("btnStartRoom");
  if (btnStart) {
    btnStart.addEventListener("click", startPartyRoom);
  }

  // Селфи лица
  const photoInput = document.getElementById("roomPhotoInput");
  if (photoInput) {
    photoInput.addEventListener("change", handleRoomPhotoUpload);
  }

  // Подтвердить "Я в строю!"
  const btnAlive = document.getElementById("btnConfirmAlive");
  if (btnAlive) {
    btnAlive.addEventListener("click", confirmPartyAlive);
  }

  // Завершить перекличку и подвести итоги
  const btnFinalize = document.getElementById("btnFinalizeResults");
  if (btnFinalize) {
    btnFinalize.addEventListener("click", finalizePartyRoom);
  }

  // Досрочное завершение
  const btnFinishEarly = document.getElementById("btnFinishBattleEarly");
  if (btnFinishEarly) {
    btnFinishEarly.addEventListener("click", () => {
      if (confirm("Вы уверены, что хотите завершить зарубу досрочно и перейти к перекличке?")) {
        finalizePartyRoom();
      }
    });
  }

  // Проверяем, есть ли уже сохраненная комната или параметр в URL
  if (STATE.targetRoomId) {
    joinPartyRoom(STATE.targetRoomId);
  }
}

async function createPartyRoom() {
  const titleInput = document.getElementById("inputRoomTitle");
  const title = (titleInput && titleInput.value.trim()) || "Застольная Заруба";
  const userId = STATE.tgUserId || (1000 + Math.floor(Math.random() * 9000));
  const userName = STATE.name || "Атлет";

  try {
    const resp = await fetch("/api/room/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        creator_id: userId,
        creator_name: userName,
        duration_min: selectedRoomDuration,
        chat_id: STATE.chatId
      })
    });
    const room = await resp.json();
    if (room && room.room_id) {
      activePartyRoom = room;
      renderPartyRoomState(room);
      startRoomPolling(room.room_id);
    }
  } catch (e) {
    console.error("Failed to create room:", e);
    alert("Ошибка создания комнаты. Проверьте соединение.");
  }
}

async function joinPartyRoom(roomId) {
  const userId = STATE.tgUserId || (1000 + Math.floor(Math.random() * 9000));
  const userName = STATE.name || "Атлет";
  const username = STATE.tgUser ? STATE.tgUser.username : null;

  try {
    const resp = await fetch("/api/room/join", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_id: roomId,
        tg_user_id: userId,
        user_name: userName,
        username: username
      })
    });
    const room = await resp.json();
    if (room && !room.error) {
      activePartyRoom = room;
      renderPartyRoomState(room);
      startRoomPolling(room.room_id);
    } else {
      alert(room.error || "Комната не найдена");
    }
  } catch (e) {
    console.error("Failed to join room:", e);
  }
}

async function togglePartyReady() {
  if (!activePartyRoom) return;
  const userId = STATE.tgUserId || 1000;
  try {
    const resp = await fetch("/api/room/ready", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_id: activePartyRoom.room_id,
        tg_user_id: userId
      })
    });
    const room = await resp.json();
    if (room && !room.error) {
      activePartyRoom = room;
      renderPartyRoomState(room);
    }
  } catch (e) {
    console.error("Failed to toggle ready:", e);
  }
}

async function startPartyRoom() {
  if (!activePartyRoom) return;
  try {
    const resp = await fetch("/api/room/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_id: activePartyRoom.room_id
      })
    });
    const room = await resp.json();
    if (room && !room.error) {
      activePartyRoom = room;
      renderPartyRoomState(room);
    }
  } catch (e) {
    console.error("Failed to start room:", e);
  }
}

window.addRoomDrinkQuick = async function(drinkName, vol, abv) {
  if (!activePartyRoom) return;
  const userId = STATE.tgUserId || 1000;
  try {
    const resp = await fetch("/api/room/drink", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_id: activePartyRoom.room_id,
        tg_user_id: userId,
        drink_name: drinkName,
        volume_ml: vol,
        abv: abv
      })
    });
    const room = await resp.json();
    if (room && !room.error) {
      activePartyRoom = room;
      renderPartyRoomState(room);
      if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred("success");
      }
    }
  } catch (e) {
    console.error("Failed to add room drink:", e);
  }
};

async function handleRoomPhotoUpload(event) {
  const file = event.target.files && event.target.files[0];
  if (!file || !activePartyRoom) return;

  const reader = new FileReader();
  reader.onload = async (e) => {
    const base64Data = e.target.result;
    const userId = STATE.tgUserId || 1000;
    try {
      const resp = await fetch("/api/room/photo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          room_id: activePartyRoom.room_id,
          tg_user_id: userId,
          photo_data: base64Data,
          stage: activePartyRoom.status || "active"
        })
      });
      const room = await resp.json();
      if (room && !room.error) {
        activePartyRoom = room;
        renderPartyRoomState(room);

        // Показываем превью
        const previewBox = document.getElementById("roomPhotoPreviewBox");
        const previewImg = document.getElementById("roomPhotoPreviewImg");
        const captionEl = document.getElementById("roomPhotoCaption");
        if (previewBox && previewImg) {
          previewImg.src = base64Data;
          const userPhoto = room.photos && room.photos.slice().reverse().find(p => p.tg_user_id == userId);
          if (captionEl && userPhoto) {
            captionEl.textContent = `Судейский вердикт: «${userPhoto.funny_caption}»`;
          }
          previewBox.style.display = "block";
        }
      }
    } catch (err) {
      console.error("Photo upload error:", err);
    }
  };
  reader.readAsDataURL(file);
}

async function confirmPartyAlive() {
  if (!activePartyRoom) return;
  const userId = STATE.tgUserId || 1000;
  try {
    const resp = await fetch("/api/room/confirm_alive", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_id: activePartyRoom.room_id,
        tg_user_id: userId
      })
    });
    const room = await resp.json();
    if (room && !room.error) {
      activePartyRoom = room;
      renderPartyRoomState(room);
      const notice = document.getElementById("aliveConfirmedNotice");
      if (notice) notice.style.display = "block";
      const btn = document.getElementById("btnConfirmAlive");
      if (btn) btn.style.display = "none";
      if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.notificationOccurred("success");
      }
    }
  } catch (e) {
    console.error("Failed to confirm alive:", e);
  }
}

async function finalizePartyRoom() {
  if (!activePartyRoom) return;
  try {
    const resp = await fetch("/api/room/finish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_id: activePartyRoom.room_id
      })
    });
    const room = await resp.json();
    if (room && !room.error) {
      activePartyRoom = room;
      renderPartyRoomState(room);
    }
  } catch (e) {
    console.error("Failed to finish room:", e);
  }
}

window.refreshPartyRoomState = async function() {
  if (!activePartyRoom) return;
  try {
    const resp = await fetch(`/api/room/state?room_id=${activePartyRoom.room_id}`);
    const room = await resp.json();
    if (room && !room.error) {
      activePartyRoom = room;
      renderPartyRoomState(room);
    }
  } catch (e) {
    console.error("Failed to refresh room state:", e);
  }
};

function startRoomPolling(roomId) {
  if (roomPollInterval) clearInterval(roomPollInterval);
  roomPollInterval = setInterval(async () => {
    const duelTab = document.getElementById("tab-duel");
    if (!duelTab || !duelTab.classList.contains("active")) return;
    if (!activePartyRoom || activePartyRoom.status === 'finished') {
      clearInterval(roomPollInterval);
      return;
    }
    try {
      const resp = await fetch(`/api/room/state?room_id=${roomId}`);
      const room = await resp.json();
      if (room && !room.error) {
        activePartyRoom = room;
        renderPartyRoomState(room);
      }
    } catch (e) {}
  }, 3500);
}

function renderPartyRoomState(room) {
  if (!room) return;

  const views = {
    entry: document.getElementById("roomEntryView"),
    lobby: document.getElementById("roomLobbyView"),
    active: document.getElementById("roomActiveView"),
    finishing: document.getElementById("roomFinishingView"),
    finished: document.getElementById("roomFinishedView")
  };

  const badge = document.getElementById("partyRoomBadge");
  const userId = STATE.tgUserId || 1000;

  // Скрываем все виды
  Object.values(views).forEach(v => { if (v) v.style.display = "none"; });

  if (room.status === "waiting") {
    if (views.lobby) views.lobby.style.display = "block";
    if (badge) { badge.textContent = "ЛОББИ"; badge.style.background = "#3b82f6"; }

    const codeEl = document.getElementById("lobbyRoomCode");
    if (codeEl) codeEl.textContent = `#${room.room_id} 📋`;
    const durEl = document.getElementById("lobbyDuration");
    if (durEl) durEl.textContent = `${room.duration_min} мин`;
    const titleEl = document.getElementById("lobbyRoomTitle");
    if (titleEl) titleEl.textContent = room.title;
    const hostEl = document.getElementById("lobbyRoomHost");
    if (hostEl) hostEl.textContent = `Организатор: ${room.creator_name}`;

    const countEl = document.getElementById("lobbyParticipantsCount");
    if (countEl) countEl.textContent = `${room.participants_count} чел (Готовы: ${room.ready_count})`;

    const listEl = document.getElementById("lobbyParticipantsList");
    if (listEl && room.participants) {
      listEl.innerHTML = room.participants.map(p => `
        <div class="room-participant-card ${p.is_ready ? 'ready' : ''}">
          <div style="font-size: 1.8rem;">${p.is_ready ? '🥊' : '⏳'}</div>
          <div style="font-weight: bold; font-size: 0.85rem; color: #fff; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${escapeHtml(p.user_name)}
          </div>
          <div style="font-size: 0.72rem; color: ${p.is_ready ? '#10b981' : '#9ca3af'}; margin-top: 2px;">
            ${p.is_ready ? '✅ Готов к бою' : '⏳ Ждет старта'}
          </div>
        </div>
      `).join('');
    }

    const currentP = room.participants && room.participants.find(p => p.tg_user_id == userId);
    const readyBtn = document.getElementById("btnToggleReady");
    if (readyBtn) {
      readyBtn.textContent = (currentP && currentP.is_ready) ? "❌ Снять готовность" : "✋ Я готов к бою!";
    }

  } else if (room.status === "active") {
    if (views.active) views.active.style.display = "block";
    if (badge) { badge.textContent = "ИДЕТ БОЙ"; badge.style.background = "#ef4444"; }

    updateCountdownDisplay(room.seconds_left, (room.duration_min || 30) * 60);

    // Лидерборд активной комнаты
    const lbEl = document.getElementById("activeLeaderboardList");
    if (lbEl && room.participants) {
      lbEl.innerHTML = room.participants.map((p, idx) => `
        <div class="table-row" style="padding: 10px 12px; margin-bottom: 6px; background: var(--bg-card); border-radius: 10px; display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <div style="font-weight: 900; font-size: 1.1rem; color: ${idx === 0 ? 'var(--gold-glow)' : 'var(--text-muted)'}; min-width: 24px;">
              #${idx + 1}
            </div>
            <div>
              <div style="font-weight: bold; font-size: 0.9rem; color: #fff;">${escapeHtml(p.user_name)}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">🥃 ${p.drinks_count} подходов | 📸 ${p.photos_count || 0} фото</div>
            </div>
          </div>
          <div style="text-align: right;">
            <div style="font-weight: 900; color: var(--gold-primary); font-size: 1rem;">${p.score} очков</div>
            <div style="font-size: 0.72rem; color: #60a5fa;">${p.pure_ethanol_g}г чистого спирта</div>
          </div>
        </div>
      `).join('');
    }

    // Лента последних напитков
    const feedEl = document.getElementById("activeDrinksFeed");
    if (feedEl && room.drinks) {
      if (room.drinks.length === 0) {
        feedEl.innerHTML = `<div style="font-size: 0.8rem; color: var(--text-muted); padding: 8px 0;">Пока никто не наливал. Будьте первыми!</div>`;
      } else {
        feedEl.innerHTML = room.drinks.slice(0, 8).map(d => `
          <div style="font-size: 0.82rem; padding: 4px 0; border-bottom: 1px dashed rgba(255,255,255,0.08); display: flex; justify-content: space-between;">
            <span>🍻 <strong>${escapeHtml(d.user_name)}</strong> принял: <em>${escapeHtml(d.drink_name)}</em> (${d.volume_ml} мл)</span>
            <span style="color: var(--text-muted); font-size: 0.75rem;">+${d.pure_ethanol_g}г</span>
          </div>
        `).join('');
      }
    }

  } else if (room.status === "finishing") {
    if (views.finishing) views.finishing.style.display = "block";
    if (badge) { badge.textContent = "ПЕРЕКЛИЧКА"; badge.style.background = "#f59e0b"; }

    const currentP = room.participants && room.participants.find(p => p.tg_user_id == userId);
    const notice = document.getElementById("aliveConfirmedNotice");
    const btnAlive = document.getElementById("btnConfirmAlive");

    if (currentP && currentP.confirmed_alive) {
      if (notice) notice.style.display = "block";
      if (btnAlive) btnAlive.style.display = "none";
    } else {
      if (notice) notice.style.display = "none";
      if (btnAlive) btnAlive.style.display = "block";
    }

    const rollcallEl = document.getElementById("rollcallConfirmedList");
    if (rollcallEl && room.participants) {
      rollcallEl.innerHTML = room.participants.map(p => `
        <span class="badge" style="background: ${p.confirmed_alive ? '#10b981' : '#4b5563'}; font-size: 0.78rem; padding: 4px 8px;">
          ${p.confirmed_alive ? '✅' : '⏳'} ${escapeHtml(p.user_name)}
        </span>
      `).join('');
    }

  } else if (room.status === "finished") {
    if (views.finished) views.finished.style.display = "block";
    if (badge) { badge.textContent = "ИТОГИ"; badge.style.background = "#10b981"; }

    const wName = document.getElementById("finishedWinnerName");
    const wScore = document.getElementById("finishedWinnerScore");
    if (wName) wName.textContent = room.winner_name || "Никто не выжил 💀";
    if (wScore) wScore.textContent = `${room.winner_score || 0} очков`;

    // Список отрубившихся (💀 ОТРУБИЛСЯ)
    const knockedSection = document.getElementById("knockedOutSection");
    const knockedList = document.getElementById("knockedOutList");
    const knockedOuts = (room.participants || []).filter(p => p.status === 'knocked_out' || !p.confirmed_alive);

    if (knockedSection && knockedList) {
      if (knockedOuts.length > 0) {
        knockedSection.style.display = "block";
        knockedList.innerHTML = knockedOuts.map(p => `
          <div style="margin-top: 4px;">
            💀 <strong>${escapeHtml(p.user_name)}</strong> — уснул в салате / не подтвердил явку (${p.drinks_count} подходов)
          </div>
        `).join('');
      } else {
        knockedSection.style.display = "none";
      }
    }

    // Выжившие
    const survList = document.getElementById("finishedSurvivingList");
    const survivors = (room.participants || []).filter(p => p.confirmed_alive == 1);
    if (survList) {
      if (survivors.length === 0) {
        survList.innerHTML = `<div style="font-size: 0.85rem; color: var(--text-muted);">Все участники отрубились на дистанции!</div>`;
      } else {
        survList.innerHTML = survivors.map((p, idx) => `
          <div class="table-row" style="padding: 10px 12px; margin-bottom: 6px; background: var(--bg-card); border-radius: 10px; display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <div style="font-weight: 900; font-size: 1.1rem; color: ${idx === 0 ? 'var(--gold-glow)' : 'var(--text-muted)'};">
                ${idx === 0 ? '👑' : (idx === 1 ? '🥈' : (idx === 2 ? '🥉' : `#${idx + 1}`))}
              </div>
              <div>
                <div style="font-weight: bold; font-size: 0.9rem; color: #fff;">${escapeHtml(p.user_name)}</div>
                <div style="font-size: 0.72rem; color: #10b981;">Выжил и подтвердил явку в строй</div>
              </div>
            </div>
            <div style="text-align: right;">
              <div style="font-weight: 900; color: var(--gold-primary); font-size: 1rem;">${p.score} очков</div>
              <div style="font-size: 0.72rem; color: var(--text-muted);">${p.drinks_count} подходов</div>
            </div>
          </div>
        `).join('');
      }
    }

    // Галерея фото
    const photoCountEl = document.getElementById("finishedPhotosCount");
    const galleryEl = document.getElementById("finishedGalleryGrid");
    if (photoCountEl) photoCountEl.textContent = `${(room.photos || []).length} фото`;

    if (galleryEl && room.photos) {
      if (room.photos.length === 0) {
        galleryEl.innerHTML = `<div style="grid-column: 1 / -1; font-size: 0.85rem; color: var(--text-muted); text-align: center; padding: 20px 0;">Селфи не делались. Фотопротокол пуст.</div>`;
      } else {
        galleryEl.innerHTML = room.photos.map(ph => `
          <div class="gallery-photo-card">
            <img src="${ph.photo_url || ''}" alt="Селфи участника" onerror="this.src='https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150'">
            <div class="gp-caption">«${escapeHtml(ph.funny_caption || 'Без слов')}»</div>
            <div class="gp-author">📸 ${escapeHtml(ph.user_name)}</div>
          </div>
        `).join('');
      }
    }
  } else {
    if (views.entry) views.entry.style.display = "block";
    if (badge) { badge.textContent = "АРЕНА"; badge.style.background = "#ef4444"; }
  }
}

function updateCountdownDisplay(secondsLeft, totalDurationSec) {
  const cdEl = document.getElementById("activeCountdown");
  const barEl = document.getElementById("activeProgressBar");
  if (!cdEl) return;

  const m = Math.floor(Math.max(0, secondsLeft) / 60);
  const s = Math.max(0, secondsLeft) % 60;
  const mm = String(m).padStart(2, '0');
  const ss = String(s).padStart(2, '0');
  cdEl.textContent = `00:${mm}:${ss}`;

  if (barEl && totalDurationSec > 0) {
    const pct = Math.min(100, Math.max(0, (secondsLeft / totalDurationSec) * 100));
    barEl.style.width = `${pct}%`;
  }
}

window.copyRoomCode = function() {
  if (!activePartyRoom) return;
  const code = activePartyRoom.room_id;
  navigator.clipboard.writeText(code).then(() => {
    alert(`Код комнаты #${code} скопирован в буфер!`);
  }).catch(() => {
    prompt("Скопируйте код комнаты:", code);
  });
};

window.shareRoomInvite = function() {
  if (!activePartyRoom) return;
  const code = activePartyRoom.room_id;
  const text = `🍻 Залетай в Застольную Зарубу #${code}! Чеканим бокалы и делаем селфи!`;
  if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.openTelegramLink) {
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(window.location.origin + '?room_id=' + code)}&text=${encodeURIComponent(text)}`;
    window.Telegram.WebApp.openTelegramLink(shareUrl);
  } else {
    navigator.clipboard.writeText(window.location.origin + '?room_id=' + code).then(() => {
      alert("Ссылка на комнату скопирована в буфер обмена!");
    });
  }
};

window.shareRoomResults = function() {
  if (!activePartyRoom) return;
  const w = activePartyRoom.winner_name || "Никто";
  const text = `🏆 ИТОГИ ЗАРУБЫ #${activePartyRoom.room_id}!\n👑 Царь Застолья: ${w} (${activePartyRoom.winner_score} очков).\nОтрубившихся: ${activePartyRoom.knocked_out_count || 0}. Проверь свой разряд в Литрбол Федерации!`;
  if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.openTelegramLink) {
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(window.location.origin)}&text=${encodeURIComponent(text)}`;
    window.Telegram.WebApp.openTelegramLink(shareUrl);
  } else {
    navigator.clipboard.writeText(text).then(() => {
      alert("Результаты зарубы скопированы в буфер!");
    });
  }
};

window.resetToRoomEntry = function() {
  activePartyRoom = null;
  if (roomPollInterval) clearInterval(roomPollInterval);
  renderPartyRoomState({ status: 'none' });
};

// =============================================================
// УЛЬТИМАТИВНЫЙ ФАРШ: ЗАЛ СЛАВЫ И ТОП ЧАТА (РЕЙТИНГ)
// =============================================================
let currentTopMode = 'auto'; // 'chat' or 'global'

window.switchTopMode = function(mode) {
  currentTopMode = mode;
  const btnChat = document.getElementById("btnTopChat");
  const btnGlobal = document.getElementById("btnTopGlobal");
  if (btnChat) btnChat.classList.toggle("active", mode === 'chat');
  if (btnGlobal) btnGlobal.classList.toggle("active", mode === 'global');
  fetchLeaderboard();
};

async function initLeaderboard() {
  const refreshBtn = document.getElementById("refreshLeaderboardBtn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => fetchLeaderboard());
  }

  // Если приложение запущено из группы, по умолчанию открываем топ чата
  if (STATE.chatId) {
    currentTopMode = 'chat';
    const btnChat = document.getElementById("btnTopChat");
    const btnGlobal = document.getElementById("btnTopGlobal");
    if (btnChat) btnChat.classList.add("active");
    if (btnGlobal) btnGlobal.classList.remove("active");
  } else {
    currentTopMode = 'global';
    const btnChat = document.getElementById("btnTopChat");
    const btnGlobal = document.getElementById("btnTopGlobal");
    if (btnChat) btnChat.classList.remove("active");
    if (btnGlobal) btnGlobal.classList.add("active");
  }

  await fetchLeaderboard();
}

async function fetchLeaderboard() {
  const cardsContainer = document.getElementById("leaderboardCards");
  const tbody = document.getElementById("leaderboardBody");
  const banner = document.getElementById("chatInfoBanner");
  const titleEl = document.getElementById("topSectionTitle");
  const descEl = document.getElementById("topSectionDesc");
  const badgeEl = document.getElementById("topBadge");

  const isChat = (currentTopMode === 'chat') || (currentTopMode === 'auto' && Boolean(STATE.chatId));

  let url = "/api/leaderboard?limit=25";
  if (isChat && STATE.chatId) {
    url += `&chat_id=${encodeURIComponent(STATE.chatId)}`;
    if (titleEl) titleEl.textContent = "👥 Рейтинг участников чата";
    if (descEl) descEl.textContent = "Официальный протокол застолья этого чата. Статистика растет от команд в группе.";
    if (badgeEl) badgeEl.textContent = "ЧАТ";

    try {
      const chatResp = await fetch(`/api/chat/stats?chat_id=${encodeURIComponent(STATE.chatId)}`);
      if (chatResp.ok) {
        const chatData = await chatResp.json();
        if (banner) {
          banner.style.display = "block";
          const bTitle = document.getElementById("chatBannerTitle");
          const bMembers = document.getElementById("chatBannerMembers");
          const bStats = document.getElementById("chatBannerStats");
          if (bTitle) bTitle.textContent = `🏛️ ${chatData.title || 'Застольный чат'}`;
          if (bMembers) bMembers.textContent = `👥 ${chatData.member_count || 0} участников`;
          const bottles = Math.round(((chatData.total_ethanol_g || 0) / (500 * 0.40 * 0.789)) * 10) / 10;
          if (bStats) {
            bStats.innerHTML = `🍻 Подходов: <strong>${chatData.drinks_count || 0}</strong> • Чистого спирта: <strong>${chatData.total_ethanol_g || 0} г</strong> (~${bottles} бут. водки)`;
          }
        }
      }
    } catch (e) {
      console.warn("Chat stats error:", e);
    }
  } else {
    if (banner) banner.style.display = "none";
    if (titleEl) titleEl.textContent = "🌍 Официальный Зал Славы ВФЛ";
    if (descEl) descEl.textContent = "Единый всероссийский реестр реальных атлетов. Только верифицированные рекорды!";
    if (badgeEl) badgeEl.textContent = "ТОП РФ";
  }

  try {
    const resp = await fetch(url);
    const data = await resp.json();

    if (tbody) tbody.innerHTML = "";
    if (cardsContainer) cardsContainer.innerHTML = "";

    if (!Array.isArray(data) || data.length === 0) {
      const emptyMsg = isChat
        ? "В этом чате пока никто не зафиксировал подход! Напишите в группе <code>/drink пиво 500</code> или сдайте норматив!"
        : "В Зале Славы пока нет атлетов. Сдайте норматив в Калькуляторе и станьте первым чемпионом!";
      
      if (cardsContainer) {
        cardsContainer.innerHTML = `
          <div class="empty-leaderboard-card">
            <div style="font-size: 2.5rem; margin-bottom: 8px;">🍺</div>
            <div style="font-weight: 700; color: #fff; margin-bottom: 4px;">Список пуст</div>
            <div style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.4;">${emptyMsg}</div>
          </div>
        `;
      }
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">${emptyMsg}</td></tr>`;
      }
      return;
    }

    const medals = ["🥇", "🥈", "🥉"];

    data.forEach((a, idx) => {
      const pos = idx + 1;
      const medal = idx < 3 ? medals[idx] : `${pos}`;
      const name = a.user_name || a.name || 'Атлет';
      const rankTitle = a.rank_title || 'Любитель';
      const score = Math.round((a.score || 0) * 10) / 10;
      const subInfo = (isChat && a.pure_ethanol_g !== undefined)
        ? `Спирт: ${a.pure_ethanol_g || 0}г • ${a.drinks_count || 0} подходов`
        : (a.discipline || 'Застольное многоборье');
      const verified = a.verified ? ` <span title="Проверен Детектором" style="color: #10b981;">🛡️</span>` : '';

      // Карточка для мобильных телефонов
      if (cardsContainer) {
        const card = document.createElement("div");
        card.className = "athlete-card";
        card.innerHTML = `
          <div class="athlete-card-rank">${medal}</div>
          <div class="athlete-card-info">
            <div class="athlete-card-name">
              <span>${escapeHtml(name)}</span>${verified}
            </div>
            <div class="athlete-card-sub">
              <span style="color: #f59e0b; font-weight: 600;">${rankTitle}</span> • ${escapeHtml(subInfo)}
            </div>
          </div>
          <div class="athlete-card-score">
            <div class="athlete-card-pts">${score}</div>
            <div class="athlete-card-pts-label">очков</div>
          </div>
        `;
        cardsContainer.appendChild(card);
      }

      // Строка для десктопной таблицы
      if (tbody) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${medal}</strong></td>
          <td><strong>${escapeHtml(name)}</strong>${verified}</td>
          <td>${rankTitle}</td>
          <td style="color: var(--gold-glow); font-weight: bold;">${score}</td>
          <td style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(subInfo)}</td>
        `;
        tbody.appendChild(tr);
      }
    });

  } catch (e) {
    console.error("Leaderboard error:", e);
    if (cardsContainer) {
      cardsContainer.innerHTML = `<div class="empty-leaderboard-card" style="color: #f87171;">Ошибка загрузки рейтинга: ${e}</div>`;
    }
  }
}

// =============================================================
// УЛЬТИМАТИВНЫЙ ФАРШ: SOS, ТОСТЫ И ФЕЙКОВЫЙ ЗВОНОК
// =============================================================
let TOASTS_LIST = [];
let currentToastIdx = 0;
let ringtoneAudioContext = null;
let ringtoneInterval = null;
let callTimerInterval = null;

async function initSosAndToasts() {
  // Загрузка протокола похмелья
  try {
    const resp = await fetch("/api/hangover");
    const data = await resp.json();
    renderHangoverStages(data.stages);
  } catch (e) {
    console.error("Hangover protocol error:", e);
  }

  // Загрузка тостов
  try {
    const resp = await fetch("/api/toasts");
    TOASTS_LIST = await resp.json();
    if (TOASTS_LIST.length > 0) renderToast(TOASTS_LIST[0]);
  } catch (e) {
    console.error("Toasts error:", e);
  }

  const nextToastBtn = document.getElementById("nextToastBtn");
  if (nextToastBtn) {
    nextToastBtn.addEventListener("click", () => {
      currentToastIdx = (currentToastIdx + 1) % TOASTS_LIST.length;
      renderToast(TOASTS_LIST[currentToastIdx]);
    });
  }

  const copyToastBtn = document.getElementById("copyToastBtn");
  if (copyToastBtn) {
    copyToastBtn.addEventListener("click", () => {
      const toastText = document.getElementById("toastText");
      if (toastText) {
        navigator.clipboard.writeText(toastText.textContent);
        alert("Тост скопирован в буфер обмена!");
      }
    });
  }

  // Фейковый звонок
  const callBtn = document.getElementById("triggerFakeCallBtn");
  const callModal = document.getElementById("fakeCallModal");
  const acceptBtn = document.getElementById("acceptCallBtn");
  const rejectBtn = document.getElementById("rejectCallBtn");
  const dialogText = document.getElementById("callDialogText");
  const callTimer = document.getElementById("callTimer");

  if (callBtn && callModal) {
    callBtn.addEventListener("click", () => {
      callModal.style.display = "flex";
      if (dialogText) dialogText.style.display = "none";
      if (callTimer) callTimer.style.display = "none";
      startTelephoneRingtone();
    });
  }

  if (acceptBtn) {
    acceptBtn.addEventListener("click", () => {
      stopTelephoneRingtone();
      if (dialogText) dialogText.style.display = "block";
      if (callTimer) {
        callTimer.style.display = "block";
        let seconds = 0;
        clearInterval(callTimerInterval);
        callTimerInterval = setInterval(() => {
          seconds++;
          const m = String(Math.floor(seconds / 60)).padStart(2, '0');
          const s = String(seconds % 60).padStart(2, '0');
          callTimer.textContent = `${m}:${s}`;
        }, 1000);
      }
    });
  }

  if (rejectBtn && callModal) {
    rejectBtn.addEventListener("click", () => {
      stopTelephoneRingtone();
      clearInterval(callTimerInterval);
      callModal.style.display = "none";
    });
  }

  // Отправка в Telegram
  const sendToTgBtn = document.getElementById("sendToTgBtn");
  if (sendToTgBtn) {
    sendToTgBtn.addEventListener("click", () => {
      if (!STATE.currentResult) {
        alert("Сначала рассчитайте норматив во вкладке «Нормативы»!");
        return;
      }

      if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.sendData) {
        const payload = {
          action: "save_result",
          result: STATE.currentResult,
          weight: STATE.weight,
          gender: STATE.gender,
          verified: STATE.detectorVerified
        };
        window.Telegram.WebApp.sendData(JSON.stringify(payload));
      } else {
        alert("Корочка сохранена! Откройте приложение внутри официального Telegram-бота @gamumuFILMS_bot, чтобы получить удостоверение прямо в чат.");
      }
    });
  }
}

function renderHangoverStages(stages) {
  const container = document.getElementById("hangoverStagesContainer");
  if (!container || !stages) return;

  container.innerHTML = "";
  stages.forEach(s => {
    const div = document.createElement("div");
    div.style.cssText = "background: var(--bg-card-hover); padding: 12px; border-radius: 8px; border-left: 3px solid #10b981;";
    div.innerHTML = `
      <div style="font-weight: bold; color: #34d399; font-size: 0.9rem; margin-bottom: 2px;">
        ⏰ ${s.time} — ${s.title}
      </div>
      <div style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.5;">${s.action}</div>
    `;
    container.appendChild(div);
  });
}

function renderToast(toast) {
  const titleEl = document.getElementById("toastTitle");
  const textEl = document.getElementById("toastText");
  const iconEl = document.getElementById("toastIcon");

  if (titleEl) titleEl.textContent = toast.title;
  if (textEl) textEl.textContent = `«${toast.text}»`;
  if (iconEl) iconEl.textContent = toast.icon || "🥂";
}

// Генератор телефонного рингтона через Web Audio API
function startTelephoneRingtone() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    ringtoneAudioContext = new AudioCtx();

    function playBip() {
      if (!ringtoneAudioContext) return;
      const osc1 = ringtoneAudioContext.createOscillator();
      const osc2 = ringtoneAudioContext.createOscillator();
      const gain = ringtoneAudioContext.createGain();

      osc1.frequency.value = 425;
      osc2.frequency.value = 425;
      osc1.type = 'sine';
      osc2.type = 'sine';

      gain.gain.setValueAtTime(0.2, ringtoneAudioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ringtoneAudioContext.currentTime + 0.9);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ringtoneAudioContext.destination);

      osc1.start();
      osc2.start();
      osc1.stop(ringtoneAudioContext.currentTime + 0.9);
      osc2.stop(ringtoneAudioContext.currentTime + 0.9);
    }

    playBip();
    ringtoneInterval = setInterval(playBip, 2500);
  } catch (e) {
    console.warn("AudioContext not supported:", e);
  }
}

function stopTelephoneRingtone() {
  if (ringtoneInterval) clearInterval(ringtoneInterval);
  if (ringtoneAudioContext) {
    try { ringtoneAudioContext.close(); } catch(e) {}
    ringtoneAudioContext = null;
  }
}

