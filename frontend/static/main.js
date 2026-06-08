document.addEventListener("DOMContentLoaded", () => {
    // State management
    let state = {
        tenders: [],
        currentTab: "active", // "active" (New/In Work/Favs) vs "archive"
        searchQuery: "",
        selectedType: "",
        selectedPlatform: ""
    };

    // DOM Elements
    const tbody = document.getElementById("tenders-tbody");
    const btnScrape = document.getElementById("btn-scrape");
    const searchInput = document.getElementById("search-input");
    const filterType = document.getElementById("filter-type");
    const filterPlatform = document.getElementById("filter-platform");
    const tabActiveBtn = document.getElementById("tab-active");
    const tabArchiveBtn = document.getElementById("tab-archive");

    // KPI count placeholders
    const statTotal = document.getElementById("stat-total");
    const statNew = document.getElementById("stat-new");
    const statProgress = document.getElementById("stat-progress");
    const statArchive = document.getElementById("stat-archive");

    // KPI Click handlers for fast filtering
    document.getElementById("kpi-new").addEventListener("click", () => {
        setTab("active");
        filterType.value = "";
        filterPlatform.value = "";
        searchInput.value = "";
        state.selectedType = "";
        state.selectedPlatform = "";
        state.searchQuery = "";
        renderTenders("Новый");
    });

    document.getElementById("kpi-progress").addEventListener("click", () => {
        setTab("active");
        filterType.value = "";
        filterPlatform.value = "";
        searchInput.value = "";
        state.selectedType = "";
        state.selectedPlatform = "";
        state.searchQuery = "";
        renderTenders("В работе");
    });

    document.getElementById("kpi-archive").addEventListener("click", () => {
        setTab("archive");
        filterType.value = "";
        filterPlatform.value = "";
        searchInput.value = "";
        state.selectedType = "";
        state.selectedPlatform = "";
        state.searchQuery = "";
        renderTenders("Архив");
    });

    // Toast Notifications
    function showToast(message) {
        const toast = document.getElementById("toast");
        const toastMsg = document.getElementById("toast-message");
        toastMsg.textContent = message;
        toast.classList.remove("hidden");
        
        setTimeout(() => {
            toast.classList.add("hidden");
        }, 4000);
    }

    // API fetches
    async function fetchTenders() {
        try {
            const res = await fetch("/api/tenders");
            if (!res.ok) throw new Error("Failed to load tenders");
            state.tenders = await res.json();
            
            updateKPIs();
            renderTenders();
        } catch (error) {
            console.error(error);
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-8 text-center text-red-400">
                        <i class="fa-solid fa-triangle-exclamation text-xl mb-1"></i>
                        <p>Ошибка при загрузке данных с сервера</p>
                    </td>
                </tr>
            `;
        }
    }

    // Update KPIs from state
    function updateKPIs() {
        const total = state.tenders.length;
        const newCount = state.tenders.filter(t => t.status === "Новый").length;
        const progressCount = state.tenders.filter(t => t.status === "В работе").length;
        const archiveCount = state.tenders.filter(t => t.status === "Архив").length;

        statTotal.textContent = total;
        statNew.textContent = newCount;
        statProgress.textContent = progressCount;
        statArchive.textContent = archiveCount;
    }

    // Render logic
    function renderTenders(forceStatusFilter = null) {
        tbody.innerHTML = "";
        
        let filtered = state.tenders.filter(t => {
            // Tab filtering
            if (forceStatusFilter) {
                if (t.status !== forceStatusFilter) return false;
            } else {
                if (state.currentTab === "active" && t.status === "Архив") return false;
                if (state.currentTab === "archive" && t.status !== "Архив") return false;
            }

            // Search filter
            if (state.searchQuery) {
                const query = state.searchQuery.toLowerCase();
                const titleMatch = t.title.toLowerCase().includes(query);
                const descMatch = (t.description || "").toLowerCase().includes(query);
                if (!titleMatch && !descMatch) return false;
            }

            // Machinery Type filter
            if (state.selectedType && t.machinery_type !== state.selectedType) return false;

            // Platform filter
            if (state.selectedPlatform && t.source_platform !== state.selectedPlatform) return false;

            return true;
        });

        if (filtered.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-12 text-center text-slate-500">
                        <i class="fa-solid fa-folder-open text-2xl mb-2"></i>
                        <p>Нет тендеров, соответствующих фильтрам</p>
                    </td>
                </tr>
            `;
            return;
        }

        filtered.forEach(tender => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-slate-900/40 transition-colors";
            
            // Score Badge styling
            let scoreBadgeClass = "bg-slate-800 text-slate-400";
            if (tender.scout_score >= 20) {
                scoreBadgeClass = "bg-emerald-950/80 text-emerald-400 border border-emerald-500/20 shadow-lg shadow-emerald-500/10";
            } else if (tender.scout_score > 0) {
                scoreBadgeClass = "bg-amber-950/80 text-amber-400 border border-amber-500/20";
            }

            // Actions mapping
            let actionButtons = "";
            if (tender.status === "Новый") {
                actionButtons = `
                    <button data-id="${tender.id}" data-action="work" class="text-xs bg-indigo-950 hover:bg-indigo-900 text-indigo-400 px-3 py-1.5 rounded border border-indigo-500/20 transition-all font-semibold mr-2">
                        В работу
                    </button>
                    <button data-id="${tender.id}" data-action="archive" class="text-xs bg-slate-900 hover:bg-slate-850 text-slate-400 px-3 py-1.5 rounded border border-slate-700/30 transition-all font-semibold">
                        Архив
                    </button>
                `;
            } else if (tender.status === "В работе") {
                actionButtons = `
                    <span class="text-xs text-amber-400 font-medium bg-amber-950/30 border border-amber-500/20 px-2.5 py-1 rounded mr-2">В работе</span>
                    <button data-id="${tender.id}" data-action="archive" class="text-xs bg-slate-900 hover:bg-slate-850 text-slate-400 px-3 py-1.5 rounded border border-slate-700/30 transition-all font-semibold">
                        В архив
                    </button>
                `;
            } else if (tender.status === "Архив") {
                actionButtons = `
                    <button data-id="${tender.id}" data-action="new" class="text-xs bg-slate-800 hover:bg-slate-750 text-slate-300 px-3 py-1.5 rounded border border-slate-700/50 transition-all font-semibold">
                        Восстановить
                    </button>
                `;
            }

            tr.innerHTML = `
                <td class="px-6 py-4 max-w-sm">
                    <div class="font-semibold text-white hover:text-indigo-400 transition-colors">
                        <a href="${tender.url}" target="_blank" class="flex items-center gap-1.5">
                            <span>${tender.title}</span>
                            <i class="fa-solid fa-external-link text-xs text-slate-500"></i>
                        </a>
                    </div>
                    <div class="text-xs text-slate-400 mt-1 line-clamp-2 hover:line-clamp-none transition-all duration-300 cursor-pointer" title="Нажмите, чтобы развернуть">
                        ${tender.description || "Без описания"}
                    </div>
                </td>
                <td class="px-6 py-4">
                    <span class="px-2 py-0.5 text-xs font-semibold rounded ${tender.machinery_type ? 'bg-indigo-950 text-indigo-300 border border-indigo-500/20' : 'bg-slate-800 text-slate-400'}">
                        ${tender.machinery_type || "Не определен"}
                    </span>
                </td>
                <td class="px-6 py-4 text-center">
                    <span class="px-3 py-1 rounded-full text-xs font-bold ${scoreBadgeClass}">
                        ${tender.scout_score > 0 ? `+${tender.scout_score}%` : `0%`}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <div class="font-bold text-white text-sm">
                        ${tender.price_current ? tender.price_current.toLocaleString("ru-RU") : "—"} ₽
                    </div>
                    <div class="text-xs text-slate-500 line-through">
                        ${tender.price_start ? tender.price_start.toLocaleString("ru-RU") + " ₽" : ""}
                    </div>
                </td>
                <td class="px-6 py-4">
                    <div class="text-xs text-indigo-400 font-semibold">${tender.source_platform}</div>
                    <div class="text-xs text-slate-500 mt-0.5">${tender.region || "Не указан"}</div>
                </td>
                <td class="px-6 py-4 text-right whitespace-nowrap">
                    <div class="flex justify-end items-center">
                        ${actionButtons}
                    </div>
                </td>
            `;

            tbody.appendChild(tr);
        });

        // Add event listeners to newly rendered action buttons
        tbody.querySelectorAll("[data-action]").forEach(btn => {
            btn.addEventListener("click", handleStatusChange);
        });
    }

    // Handle Quick Status Changes
    async function handleStatusChange(e) {
        const id = e.currentTarget.getAttribute("data-id");
        const action = e.currentTarget.getAttribute("data-action");
        
        let newStatus = "Новый";
        if (action === "work") newStatus = "В работе";
        if (action === "archive") newStatus = "Архив";
        if (action === "new") newStatus = "Новый";

        try {
            const res = await fetch(`/api/tenders/${id}/status`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: newStatus })
            });

            if (!res.ok) throw new Error("Failed to update status");

            const updated = await res.json();
            
            // Update local state
            const index = state.tenders.findIndex(t => t.id === updated.id);
            if (index !== -1) {
                state.tenders[index] = updated;
            }

            showToast(`Лот перенесен в статус: "${newStatus}"`);
            updateKPIs();
            renderTenders();

        } catch (err) {
            console.error(err);
            showToast("Не удалось обновить статус лота");
        }
    }

    // Set active tab
    function setTab(tabName) {
        state.currentTab = tabName;
        if (tabName === "active") {
            tabActiveBtn.className = "px-3 py-1.5 text-xs font-semibold rounded-md bg-indigo-600 text-white transition-all";
            tabArchiveBtn.className = "px-3 py-1.5 text-xs font-semibold rounded-md text-slate-400 hover:text-white transition-all";
        } else {
            tabActiveBtn.className = "px-3 py-1.5 text-xs font-semibold rounded-md text-slate-400 hover:text-white transition-all";
            tabArchiveBtn.className = "px-3 py-1.5 text-xs font-semibold rounded-md bg-indigo-600 text-white transition-all";
        }
    }

    // Event Listeners for tabs & filters
    tabActiveBtn.addEventListener("click", () => {
        setTab("active");
        renderTenders();
    });

    tabArchiveBtn.addEventListener("click", () => {
        setTab("archive");
        renderTenders();
    });

    searchInput.addEventListener("input", (e) => {
        state.searchQuery = e.target.value;
        renderTenders();
    });

    filterType.addEventListener("change", (e) => {
        state.selectedType = e.target.value;
        renderTenders();
    });

    filterPlatform.addEventListener("change", (e) => {
        state.selectedPlatform = e.target.value;
        renderTenders();
    });

    // Scrape button handler
    btnScrape.addEventListener("click", async () => {
        const icon = btnScrape.querySelector("i");
        icon.classList.add("fa-spin");
        btnScrape.disabled = true;
        btnScrape.classList.add("opacity-60");

        showToast("Запуск парсинга... Пожалуйста, подождите.");

        try {
            const res = await fetch("/api/tenders/trigger-scrape", { method: "POST" });
            if (!res.ok) throw new Error("Scraper execution failed");

            const data = await res.json();
            const added = data.new_items_added;
            
            showToast(`Парсинг успешно завершен! Добавлено новых лотов: ${added}`);
            
            // Reload all tenders
            await fetchTenders();

        } catch (err) {
            console.error(err);
            showToast("Ошибка при запуске парсера");
        } finally {
            icon.classList.remove("fa-spin");
            btnScrape.disabled = false;
            btnScrape.classList.remove("opacity-60");
        }
    });

    // Initial load
    fetchTenders();
});
