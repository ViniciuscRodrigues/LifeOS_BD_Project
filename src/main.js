const fmt = (val) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    val,
  );

window.switchTab = (tabId, btn) => {
  document
    .querySelectorAll(".tab-content")
    .forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach((el) => {
    el.className =
      "nav-btn w-full text-left px-4 py-3 rounded-lg text-slate-400 hover:bg-slate-800 font-medium transition-colors";
  });
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
  const btnSearch = document.getElementById("btn-search");
  btnSearch.style.display =
    cat === "fii" || cat === "renda_fixa" ? "block" : "none";
  btnSearch.title = cat === "fii" ? "Buscar Cotação e DY" : "Puxar Taxa CDI";
  document.getElementById("inv-invested").readOnly = cat === "fii";
  if (cat === "fii")
    document.getElementById("inv-invested").classList.add("opacity-50");
  else document.getElementById("inv-invested").classList.remove("opacity-50");
};

window.calcTotalFII = () => {
  const price = parseFloat(document.getElementById("inv-price").value) || 0;
  const quotas = parseFloat(document.getElementById("inv-quotas").value) || 0;
  document.getElementById("inv-invested").value = (price * quotas).toFixed(2);
};

window.searchTicker = async () => {
  const cat = document.getElementById("inv-cat").value;
  const btn = document.getElementById("btn-search");
  btn.innerText = "⏳";
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
        calcTotalFII();
      }
    } else if (cat === "renda_fixa") {
      const percCdi =
        parseFloat(document.getElementById("inv-cdi-percent").value) || 100;
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
    alert("Erro interno na comunicação.");
  } finally {
    btn.innerText = "🔍";
  }
};

window.addEventListener("pywebviewready", async function () {
  const data = await window.pywebview.api.GetDashboardData();
  renderAll(data);
});

window.askAI = async () => {
  const btn = document.getElementById("btn-ai");
  const responseP = document.getElementById("ai-response");
  btn.innerText = "Pensando...";
  btn.classList.add("animate-pulse", "bg-indigo-400");
  btn.disabled = true;
  responseP.innerText =
    "Consultando o PostgreSQL em todas as tabelas e enviando para o Gemini...";

  try {
    const data = await window.pywebview.api.GetAIInsights();
    if (data.error)
      responseP.innerHTML = `<span class="text-rose-400">Erro: ${data.error}</span>`;
    else
      responseP.innerHTML = `<span class="text-emerald-300 font-medium">Análise:</span> ${data.response.replace(/\*\*/g, "").replace(/\n/g, "<br>")}`;
  } catch (e) {
    responseP.innerText = "Erro ao contactar Python.";
  } finally {
    btn.innerText = "Analisar Minha Rotina";
    btn.classList.remove("animate-pulse", "bg-indigo-400");
    btn.disabled = false;
  }
};

// --- MÉTODOS DE AÇÃO (CRUD) ---
window.addTx = async () => {
  const type = document.getElementById("tx-type").value,
    cat = document.getElementById("tx-cat").value,
    val = parseFloat(document.getElementById("tx-val").value);
  if (!cat || isNaN(val)) return;
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
  const inv = parseFloat(document.getElementById("inv-invested").value) || 0,
    rate = parseFloat(document.getElementById("inv-rate").value) || 0;
  const price = parseFloat(document.getElementById("inv-price").value) || 0,
    quotas = parseFloat(document.getElementById("inv-quotas").value) || 0;
  if (!name) return;
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

window.addEstudo = async () => {
  const id = document.getElementById("sel-disciplina").value,
    topico = document.getElementById("estudo-topico").value,
    dur = document.getElementById("estudo-duracao").value;
  if (!id || !dur) return;
  renderAll(await window.pywebview.api.AddEstudo(id, dur, topico));
};
window.deleteEstudo = async (id) => {
  if (confirm("Apagar registo?"))
    renderAll(await window.pywebview.api.DeleteEstudo(id));
};

window.addTreino = async () => {
  const id = document.getElementById("sel-exercicio").value,
    reps = document.getElementById("treino-reps").value,
    carga = document.getElementById("treino-carga").value;
  if (!id || !reps || !carga) return;
  renderAll(await window.pywebview.api.AddTreino(id, reps, carga));
};
window.deleteTreino = async (id) => {
  if (confirm("Apagar série?"))
    renderAll(await window.pywebview.api.DeleteTreino(id));
};

window.addDieta = async () => {
  const id = document.getElementById("sel-alimento").value,
    porcoes = document.getElementById("dieta-porcoes").value;
  if (!id || !porcoes) return;
  renderAll(await window.pywebview.api.AddDieta(id, porcoes));
};
window.deleteDieta = async (id) => {
  if (confirm("Apagar consumo?"))
    renderAll(await window.pywebview.api.DeleteDieta(id));
};

window.addHabito = async () => {
  const id = document.getElementById("sel-habito").value,
    st = document.getElementById("habito-status").value;
  if (!id) return;
  renderAll(await window.pywebview.api.AddHabito(id, st));
};
window.deleteHabito = async (id) => {
  if (confirm("Apagar registo?"))
    renderAll(await window.pywebview.api.DeleteHabito(id));
};

// --- FUNÇÃO DE RENDERIZAÇÃO GERAL ---
function renderAll(data) {
  if (data.error) {
    console.error(data.error);
    return;
  }

  // Atualiza Painel Financeiro
  document.getElementById("ui-balance").innerText = fmt(data.balance);
  document.getElementById("ui-incomes").innerText = fmt(data.incomes);
  document.getElementById("ui-expenses").innerText = fmt(data.expenses);

  // Preencher Caixas de Seleção (Dropdowns)
  document.getElementById("sel-disciplina").innerHTML =
    data.catalogs.disciplinas
      .map(
        (c) =>
          `<option class="bg-slate-900" value="${c.id}">${c.nome}</option>`,
      )
      .join("");
  document.getElementById("sel-exercicio").innerHTML = data.catalogs.exercicios
    .map(
      (c) => `<option class="bg-slate-900" value="${c.id}">${c.nome}</option>`,
    )
    .join("");
  document.getElementById("sel-alimento").innerHTML = data.catalogs.alimentos
    .map(
      (c) => `<option class="bg-slate-900" value="${c.id}">${c.nome}</option>`,
    )
    .join("");
  document.getElementById("sel-habito").innerHTML = data.catalogs.habitos
    .map(
      (c) => `<option class="bg-slate-900" value="${c.id}">${c.nome}</option>`,
    )
    .join("");

  // Renderizar Listas do Histórico
  document.getElementById("tx-list").innerHTML = data.transactions
    .map(
      (tx) => `
        <li class="p-4 flex justify-between items-center hover:bg-slate-800/50 transition group">
            <span class="font-medium text-slate-200">${tx.categoria}</span>
            <div class="flex items-center gap-4">
                <span class="font-bold ${tx.tipo === "Entrada" ? "text-emerald-400" : "text-rose-400"}">${tx.tipo === "Entrada" ? "+" : "-"} ${fmt(tx.valor)}</span>
                <button onclick="deleteTx(${tx.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity">🗑️</button>
            </div>
        </li>`,
    )
    .join("");

  document.getElementById("inv-list").innerHTML = data.investments
    .map(
      (inv) => `
        <div class="bg-slate-950 p-5 rounded-xl border border-slate-800 flex flex-col gap-2 group">
            <div class="flex justify-between items-center border-b border-slate-800 pb-2">
                <span class="text-xs font-bold text-indigo-400 uppercase">${inv.categoria}</span>
                <div class="flex items-center gap-3"><span class="font-bold text-slate-200">${inv.ticker_nome}</span><button onclick="deleteInv(${inv.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity">🗑️</button></div>
            </div>
            <div class="flex justify-between text-sm mt-2"><span class="text-slate-400">Investido:</span><span class="font-bold text-white">${fmt(inv.valor_investido)}</span></div>
        </div>`,
    )
    .join("");

  document.getElementById("estudos-list").innerHTML = data.history.estudos
    .map(
      (e) => `
        <li class="p-4 flex justify-between items-center hover:bg-slate-800/50 group">
            <div><p class="font-medium text-slate-200">${e.disciplina}</p><p class="text-xs text-slate-500">${e.topico_estudado}</p></div>
            <div class="flex items-center gap-4"><span class="text-indigo-400 font-bold">${e.duracao_minutos} min</span><button onclick="deleteEstudo(${e.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity">🗑️</button></div>
        </li>`,
    )
    .join("");

  document.getElementById("treinos-list").innerHTML = data.history.treinos
    .map(
      (t) => `
        <li class="p-4 flex justify-between items-center hover:bg-slate-800/50 group">
            <span class="font-medium text-slate-200">${t.exercicio}</span>
            <div class="flex items-center gap-4"><span class="text-indigo-400 font-bold">${t.repeticoes}x — ${t.carga_kg} Kg</span><button onclick="deleteTreino(${t.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity">🗑️</button></div>
        </li>`,
    )
    .join("");

  document.getElementById("dieta-list").innerHTML = data.history.dieta
    .map(
      (d) => `
        <li class="p-4 flex justify-between items-center hover:bg-slate-800/50 group">
            <div><p class="font-medium text-slate-200">${d.alimento}</p><p class="text-xs text-slate-500">${d.quantidade_porcoes} porções consumidas</p></div>
            <div class="flex items-center gap-4"><div class="text-right"><p class="text-emerald-400 font-bold text-sm">${d.calorias_totais} kcal</p><p class="text-blue-400 text-xs">${d.prot_totais}g Prot</p></div><button onclick="deleteDieta(${d.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity">🗑️</button></div>
        </li>`,
    )
    .join("");

  document.getElementById("habitos-list").innerHTML = data.history.habitos
    .map(
      (h) => `
        <li class="p-4 flex justify-between items-center hover:bg-slate-800/50 group">
            <div><p class="font-medium text-slate-200">${h.habito}</p><p class="text-xs text-slate-500">Tipo: ${h.tipo}</p></div>
            <div class="flex items-center gap-4"><span class="px-2 py-1 text-xs rounded-md font-bold ${h.status === "Concluido" ? "bg-emerald-900/50 text-emerald-400" : h.status === "Falhou" ? "bg-rose-900/50 text-rose-400" : "bg-amber-900/50 text-amber-400"}">${h.status}</span><button onclick="deleteHabito(${h.id})" class="text-slate-500 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity">🗑️</button></div>
        </li>`,
    )
    .join("");
}
