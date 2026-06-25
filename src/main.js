const fmt = (val) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    val,
  );
let investChartInstance = null;

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("treino-peso").value =
    localStorage.getItem("user_peso") || "75";
  document.getElementById("treino-altura").value =
    localStorage.getItem("user_altura") || "175";
});

window.saveMetrics = () => {
  localStorage.setItem(
    "user_peso",
    document.getElementById("treino-peso").value,
  );
  localStorage.setItem(
    "user_altura",
    document.getElementById("treino-altura").value,
  );
};

window.switchTab = (tabId, btn) => {
  document
    .querySelectorAll(".tab-content")
    .forEach((el) => el.classList.remove("active"));
  document
    .querySelectorAll(".nav-btn")
    .forEach(
      (el) =>
        (el.className =
          "nav-btn w-full text-left px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800 font-medium transition-colors"),
    );
  document.getElementById(tabId).classList.add("active");
  btn.className =
    "nav-btn w-full text-left px-4 py-3 rounded-lg bg-indigo-600 text-white font-medium transition-colors";
};

window.toggleInvFields = () => {
  const cat = document.getElementById("inv-cat").value;
  document.getElementById("fii-fields").style.display =
    cat === "fii" ? "grid" : "none";
  document.getElementById("rf-fields").style.display =
    cat === "renda_fixa" ? "grid" : "none";
  document.getElementById("btn-search").style.display =
    cat === "fii" || cat === "renda_fixa" ? "block" : "none";
  document.getElementById("inv-invested").readOnly = cat === "fii";
};

window.calcTotalFII = () => {
  const price = Math.abs(
    parseFloat(document.getElementById("inv-price").value) || 0,
  );
  const quotas = Math.abs(
    parseFloat(document.getElementById("inv-quotas").value) || 0,
  );
  document.getElementById("inv-invested").value = (price * quotas).toFixed(2);
};

window.searchTicker = async () => {
  const cat = document.getElementById("inv-cat").value;
  const btn = document.getElementById("btn-search");
  btn.innerHTML = '<i class="fa-solid fa-hourglass-half animate-spin"></i>';
  try {
    if (cat === "fii") {
      const ticker = document
        .getElementById("inv-name")
        .value.trim()
        .toUpperCase();
      if (!ticker) {
        alert("Digite o código do FII!");
        return;
      }
      const data = await window.pywebview.api.FetchTicker(ticker);
      if (data.error) alert(data.error);
      else {
        document.getElementById("inv-price").value = data.price.toFixed(2);
        document.getElementById("inv-rate").value = data.yield.toFixed(2);
        window.calcTotalFII();
      }
    } else if (cat === "renda_fixa") {
      const percCdi = Math.abs(
        parseFloat(document.getElementById("inv-cdi-percent").value) || 100,
      );
      const data = await window.pywebview.api.FetchCDI();
      if (data.error) alert(data.error);
      else {
        document.getElementById("inv-rate").value = (
          data.rate *
          (percCdi / 100)
        ).toFixed(2);
      }
    }
  } catch (e) {
    alert("Erro na comunicação com o servidor.");
  } finally {
    btn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i>';
  }
};

window.addEventListener("pywebviewready", async function () {
  const data = await window.pywebview.api.GetDashboardData();
  renderAll(data);
});

window.askAI = async () => {
  const btn = document.getElementById("btn-ai"),
    responseP = document.getElementById("ai-response");
  btn.innerHTML =
    '<i class="fa-solid fa-spinner animate-spin mr-2"></i>Gerando Insight...';
  btn.disabled = true;
  btn.classList.add("animate-pulse");
  responseP.innerHTML =
    "Analisando seus dados para gerar uma sugestão prática de melhoria...";
  try {
    const data = await window.pywebview.api.GetAIInsights();
    if (data.error) {
      responseP.innerHTML = `<span class="text-rose-400">Erro: ${data.error}</span>`;
    } else {
      const textoLimpo = data.response
        .replace(/\*\*/g, "")
        .replace(/\n/g, "<br><br>");
      responseP.innerHTML = `<span class="text-indigo-300 font-bold text-base block mb-2"><i class="fa-solid fa-lightbulb text-yellow-400 mr-2"></i> Sugestão / Insight:</span> <span class="text-slate-200">${textoLimpo}</span>`;
    }
  } catch (e) {
    console.error(e);
    responseP.innerText = "Erro ao contactar Python. Verifique seu console.";
  } finally {
    btn.innerText = "Gerar Insight da Rotina";
    btn.disabled = false;
    btn.classList.remove("animate-pulse");
  }
};

window.addTx = async () => {
  const type = document.getElementById("tx-type").value;
  const cat = document.getElementById("tx-cat").value;
  const val = parseFloat(document.getElementById("tx-val").value);
  if (!cat || isNaN(val)) return;
  if (val <= 0) {
    alert("Atenção: O valor da transação deve ser positivo e maior que zero.");
    return;
  }
  renderAll(await window.pywebview.api.AddTransaction(type, cat, val));
  document.getElementById("tx-cat").value = "";
  document.getElementById("tx-val").value = "";
};

window.deleteTx = async (id) => {
  if (confirm("Apagar transação?"))
    renderAll(await window.pywebview.api.DeleteTransaction(id));
};

window.addInv = async () => {
  const cat = document.getElementById("inv-cat").value,
    name = document.getElementById("inv-name").value;
  const inv = parseFloat(document.getElementById("inv-invested").value) || 0;
  const rate = parseFloat(document.getElementById("inv-rate").value) || 0;
  const price = parseFloat(document.getElementById("inv-price").value) || 0;
  const quotas = parseFloat(document.getElementById("inv-quotas").value) || 0;
  if (!name) return;
  if (inv < 0 || rate < 0 || price < 0 || quotas < 0) {
    alert(
      "Atenção: Nenhum campo de investimento pode conter valores negativos.",
    );
    return;
  }
  renderAll(
    await window.pywebview.api.AddInvestment(
      cat,
      name,
      inv,
      rate,
      price,
      quotas,
    ),
  );
};

window.deleteInv = async (id) => {
  if (confirm("Apagar investimento?"))
    renderAll(await window.pywebview.api.DeleteInvestment(id));
};

window.addDietaIA = async () => {
  const alimento = document.getElementById("dieta-alimento").value;
  const gramas = parseFloat(document.getElementById("dieta-gramas").value);
  if (!alimento || isNaN(gramas)) return;
  if (gramas <= 0) {
    alert("Atenção: A quantidade em gramas deve ser um valor positivo.");
    return;
  }
  const btn = document.getElementById("btn-add-dieta");
  btn.innerHTML =
    '<i class="fa-solid fa-hourglass-half animate-spin mr-2"></i>Gerando Macros...';
  btn.classList.add("animate-pulse", "bg-indigo-400");
  btn.disabled = true;
  try {
    const data = await window.pywebview.api.AddDietaIA(alimento, gramas);
    if (data.error) alert("Erro: " + data.error);
    else {
      renderAll(data);
      document.getElementById("dieta-alimento").value = "";
      document.getElementById("dieta-gramas").value = "";
    }
  } catch (e) {
    alert("Erro ao conectar com o backend Python.");
  } finally {
    btn.innerText = "Adicionar Alimento";
    btn.classList.remove("animate-pulse", "bg-indigo-400");
    btn.disabled = false;
  }
};

window.deleteDieta = async (id) => {
  if (confirm("Apagar consumo?"))
    renderAll(await window.pywebview.api.DeleteDieta(id));
};

window.addEstudoLivre = async () => {
  const materia = document.getElementById("estudo-materia").value.trim();
  const topico = document.getElementById("estudo-topico").value.trim();
  const desc = document.getElementById("estudo-descricao").value.trim();
  const dur = parseInt(document.getElementById("estudo-duracao").value);
  if (!materia || !topico || isNaN(dur)) {
    alert("Preencha Matéria, Tópico e Duração!");
    return;
  }
  if (dur <= 0) {
    alert("Atenção: O tempo estudado deve ser um número positivo.");
    return;
  }
  renderAll(
    await window.pywebview.api.AddEstudoLivre(materia, topico, desc, dur),
  );
  document.getElementById("estudo-topico").value = "";
  document.getElementById("estudo-descricao").value = "";
  document.getElementById("estudo-duracao").value = "";
};

window.deleteEstudo = async (id) => {
  if (confirm("Apagar registo de estudo?"))
    renderAll(await window.pywebview.api.DeleteEstudo(id));
};

window.addTreinoIA = async () => {
  const peso = parseFloat(document.getElementById("treino-peso").value);
  const altura = parseFloat(document.getElementById("treino-altura").value);
  const ex = document.getElementById("treino-exercicio").value.trim();
  const reps = parseInt(document.getElementById("treino-reps").value);
  const carga = parseFloat(document.getElementById("treino-carga").value);
  if (!ex || isNaN(reps) || isNaN(carga) || isNaN(peso) || isNaN(altura)) {
    alert("Preencha todos os campos do treino!");
    return;
  }
  if (peso <= 0 || altura <= 0 || reps <= 0 || carga < 0) {
    alert(
      "Atenção: Os valores de peso, altura, repetições e carga devem ser positivos.",
    );
    return;
  }
  const btn = document.getElementById("btn-add-treino");
  btn.innerHTML =
    '<i class="fa-solid fa-hourglass-half animate-spin mr-2"></i>Calculando...';
  btn.classList.add("animate-pulse");
  btn.disabled = true;
  try {
    const data = await window.pywebview.api.AddTreinoIA(
      peso,
      altura,
      ex,
      reps,
      carga,
    );
    if (data.error) alert("Erro: " + data.error);
    else {
      renderAll(data);
      document.getElementById("treino-exercicio").value = "";
      document.getElementById("treino-reps").value = "";
      document.getElementById("treino-carga").value = "";
    }
  } catch (e) {
    alert("Erro ao contactar Python.");
  } finally {
    btn.innerText = "Adicionar Exercício";
    btn.classList.remove("animate-pulse");
    btn.disabled = false;
  }
};

window.deleteTreino = async (id) => {
  if (confirm("Apagar série do treino?"))
    renderAll(await window.pywebview.api.DeleteTreino(id));
};

window.createHabito = async () => {
  const nome = document.getElementById("habito-nome").value.trim();
  if (!nome) return;
  renderAll(await window.pywebview.api.CreateHabito(nome));
  document.getElementById("habito-nome").value = "";
};

window.toggleHabito = async (id, isChecked) => {
  renderAll(await window.pywebview.api.ToggleHabito(id, isChecked));
};

window.deleteHabito = async (id) => {
  if (confirm("Apagar hábito permanentemente?"))
    renderAll(await window.pywebview.api.DeleteHabito(id));
};

function renderAll(data) {
  if (data.error) {
    console.error(data.error);
    return;
  }

  document.getElementById("sum-patrimonio").innerText = fmt(
    data.summary.patrimonio_total,
  );
  document.getElementById("sum-estudo").innerText =
    `${data.summary.horas_estudo} h`;
  document.getElementById("sum-treino").innerText =
    data.summary.treinos_realizados;
  document.getElementById("sum-habito").innerText = data.summary.taxa_habitos;

  const ctx = document.getElementById("investChart").getContext("2d");
  if (investChartInstance) investChartInstance.destroy();
  investChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.summary.grafico_investimentos.map((d) => d.data),
      datasets: [
        {
          label: "Acumulado",
          data: data.summary.grafico_investimentos.map(
            (d) => d.total_acumulado,
          ),
          borderColor: "#818cf8",
          backgroundColor: "rgba(129, 140, 248, 0.2)",
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          grid: { color: "rgba(51, 65, 85, 0.5)" },
          ticks: { color: "#94a3b8" },
        },
        x: {
          grid: { color: "rgba(51, 65, 85, 0.5)" },
          ticks: { color: "#94a3b8" },
        },
      },
      plugins: { legend: { labels: { color: "#cbd5e1" } } },
    },
  });

  document.getElementById("ui-balance").innerText = fmt(data.balance);
  document.getElementById("ui-incomes").innerText = fmt(data.incomes);
  document.getElementById("ui-expenses").innerText = fmt(data.expenses);

  document.getElementById("tx-list").innerHTML = data.transactions
    .map(
      (tx) =>
        `<li class="p-4 flex justify-between items-center hover:bg-slate-800/50 transition group"><span class="font-medium text-slate-200">${tx.categoria}</span><div class="flex items-center gap-4"><span class="font-bold ${tx.tipo === "Entrada" ? "text-emerald-400" : "text-rose-400"}">${tx.tipo === "Entrada" ? "+" : "-"} ${fmt(tx.valor)}</span><button onclick="deleteTx(${tx.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity"><i class="fa-solid fa-trash"></i></button></div></li>`,
    )
    .join("");

  document.getElementById("inv-list").innerHTML = data.investments
    .map(
      (inv) =>
        `<div class="bg-slate-950 p-5 rounded-xl border border-slate-800 flex flex-col gap-2 group"><div class="flex justify-between items-center border-b border-slate-800 pb-2"><span class="text-xs font-bold text-indigo-400 uppercase">${inv.categoria}</span><div class="flex items-center gap-3"><span class="font-bold text-slate-200">${inv.ticker_nome}</span><button onclick="deleteInv(${inv.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity"><i class="fa-solid fa-trash"></i></button></div></div><div class="flex justify-between text-sm mt-2"><span class="text-slate-400">Investido:</span><span class="font-bold text-white">${fmt(inv.valor_investido)}</span></div></div>`,
    )
    .join("");

  document.getElementById("dieta-list").innerHTML = data.history.dieta
    .map(
      (d) =>
        `<li class="p-4 flex justify-between items-center hover:bg-slate-800/50 group"><div><p class="font-medium text-slate-200">${d.alimento}</p><p class="text-xs text-slate-500">${d.quantidade_porcoes * 100}g consumidos</p></div><div class="flex items-center gap-4"><div class="text-right"><p class="text-emerald-400 font-bold text-sm">${d.calorias_totais.toFixed(0)} kcal</p><p class="text-blue-400 text-xs">${d.prot_totais.toFixed(1)}g Prot</p></div><button onclick="deleteDieta(${d.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity"><i class="fa-solid fa-trash"></i></button></div></li>`,
    )
    .join("");

  document.getElementById("estudos-list").innerHTML = data.history.estudos
    .map(
      (e) =>
        `<li class="p-4 flex justify-between items-center hover:bg-slate-800/50 group"><div><p class="font-bold text-indigo-400">${e.disciplina}</p><p class="text-slate-200">${e.topico_estudado}</p><p class="text-xs text-slate-500 mt-1">${e.descricao_topico || ""}</p></div><div class="flex items-center gap-4"><span class="text-slate-400 font-bold bg-slate-900 px-3 py-1 rounded">${e.duracao_minutos} min</span><button onclick="deleteEstudo(${e.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity"><i class="fa-solid fa-trash"></i></button></div></li>`,
    )
    .join("");

  document.getElementById("treinos-list").innerHTML = data.history.treinos
    .map(
      (t) =>
        `<li class="p-4 flex justify-between items-center hover:bg-slate-800/50 group"><div><span class="font-medium text-slate-200 text-lg">${t.exercicio}</span><p class="text-xs text-orange-400 font-semibold mt-1"><i class="fa-solid fa-fire mr-1"></i> Estimativa: ${t.calorias_gastas.toFixed(1)} kcal gastas</p></div><div class="flex items-center gap-4"><span class="text-slate-400 font-bold bg-slate-900 px-3 py-1 rounded">${t.repeticoes}x — ${t.carga_kg} Kg</span><button onclick="deleteTreino(${t.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity"><i class="fa-solid fa-trash"></i></button></div></li>`,
    )
    .join("");

  document.getElementById("habitos-list").innerHTML =
    data.history.habitos_diarios
      .map(
        (h) =>
          `<li class="p-4 flex justify-between items-center hover:bg-slate-800/50 group border-b border-slate-800/50 last:border-0"><div class="flex items-center gap-4"><input type="checkbox" ${h.concluido_hoje ? "checked" : ""} onchange="toggleHabito(${h.id}, this.checked)" class="w-6 h-6 accent-indigo-500 rounded bg-slate-900 border-slate-700 cursor-pointer" /><span class="font-medium text-lg ${h.concluido_hoje ? "text-slate-600 line-through" : "text-slate-200"} transition-all duration-300">${h.nome}</span></div><button onclick="deleteHabito(${h.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity"><i class="fa-solid fa-trash"></i></button></li>`,
      )
      .join("");
}
