document.addEventListener("DOMContentLoaded", () => {
    // State management
    let state = {
        tenders: [],
        currentTab: "active", // "active", "archive", "favorite"
        searchQuery: "",
        selectedType: "",
        selectedPlatform: "",
        selectedRegion: "",
        priceMin: "",
        priceMax: "",
        sortBy: "created_desc",
        selectedTenderIds: new Set(),
        keywords: [],
        platforms: [],
        regions: []
    };

    // DOM Elements
    const tbody = document.getElementById("tenders-tbody");
    const btnScrape = document.getElementById("btn-scrape");
    const searchInput = document.getElementById("search-input");
    const filterType = document.getElementById("filter-type");
    const filterPlatform = document.getElementById("filter-platform");
    const filterRegion = document.getElementById("filter-region");
    const filterPriceMin = document.getElementById("filter-price-min");
    const filterPriceMax = document.getElementById("filter-price-max");
    const sortOrder = document.getElementById("sort-order");
    const tabActiveBtn = document.getElementById("tab-active");
    const tabArchiveBtn = document.getElementById("tab-archive");
    const checkAll = document.getElementById("check-all");

    // Batch Actions DOM Elements
    const batchActionsBar = document.getElementById("batch-actions-bar");
    const batchSelectCount = document.getElementById("batch-select-count");
    const btnBatchWork = document.getElementById("btn-batch-work");
    const btnBatchArchive = document.getElementById("btn-batch-archive");
    const btnBatchDelete = document.getElementById("btn-batch-delete");
    
    // Settings DOM Elements
    const btnSettings = document.getElementById("btn-settings");
    const settingsModal = document.getElementById("settings-modal");
    const btnCloseSettings = document.getElementById("btn-close-settings");
    const btnCancelSettings = document.getElementById("btn-cancel-settings");
    const settingsForm = document.getElementById("settings-form");
    
    const settingsKeywords = document.getElementById("settings-keywords");
    const settingsMinusWords = document.getElementById("settings-minus-words");
    const customCategoryInput = document.getElementById("custom-category-input");
    const btnAddCustomCat = document.getElementById("btn-add-custom-cat");
    const customCategoriesContainer = document.getElementById("custom-categories-container");

    const customEisCategoryInput = document.getElementById("custom-eis-category-input");
    const btnAddCustomEisCat = document.getElementById("btn-add-custom-eis-cat");
    const customEisCategoriesContainer = document.getElementById("custom-eis-categories-container");
    
    const eisStrictKeywords = document.getElementById("eis-strict-keywords");
    const eisExclude223fz = document.getElementById("eis-exclude-223fz");
    const settingsRetentionDays = document.getElementById("settings-retention-days");
    const settingsMaxLimit = document.getElementById("settings-max-limit");
    
    const btnClearArchive = document.getElementById("btn-clear-archive");
    const btnClearAll = document.getElementById("btn-clear-all");

    // KPI count placeholders
    const statTotal = document.getElementById("stat-total");
    const statNew = document.getElementById("stat-new");
    const statProgress = document.getElementById("stat-progress");
    const statFavorite = document.getElementById("stat-favorite");
    const statArchive = document.getElementById("stat-archive");

    // KPI Click handlers for fast filtering
    document.getElementById("kpi-total").addEventListener("click", () => {
        setTab("active");
        resetFilters();
        fetchTenders();
    });

    document.getElementById("kpi-new").addEventListener("click", () => {
        setTab("active");
        resetFilters();
        state.selectedType = ""; // Render only "Новый" via local filter if desired, or fetch status
        state.tenders = [];
        renderTenders("Новый");
        tbody.querySelectorAll("tr").forEach(tr => {
            const statusLabel = tr.querySelector("[data-status]");
            if (statusLabel && statusLabel.getAttribute("data-status") !== "Новый") {
                tr.remove();
            }
        });
    });

    document.getElementById("kpi-progress").addEventListener("click", () => {
        setTab("active");
        resetFilters();
        renderTenders("В работе");
        tbody.querySelectorAll("tr").forEach(tr => {
            const statusLabel = tr.querySelector("[data-status]");
            if (statusLabel && statusLabel.getAttribute("data-status") !== "В работе") {
                tr.remove();
            }
        });
    });

    document.getElementById("kpi-favorite").addEventListener("click", () => {
        setTab("favorite");
        resetFilters();
        fetchTenders();
    });

    document.getElementById("kpi-archive").addEventListener("click", () => {
        setTab("archive");
        resetFilters();
        fetchTenders();
    });

    function resetFilters() {
        filterType.value = "";
        filterPlatform.value = "";
        filterRegion.value = "";
        filterPriceMin.value = "";
        filterPriceMax.value = "";
        sortOrder.value = "created_desc";
        searchInput.value = "";
        
        state.selectedType = "";
        state.selectedPlatform = "";
        state.selectedRegion = "";
        state.priceMin = "";
        state.priceMax = "";
        state.sortBy = "created_desc";
        state.searchQuery = "";
        state.selectedTenderIds.clear();
        updateBatchBar();
    }

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
            let url = `/api/tenders?order_by=${state.sortBy}&limit=150`;
            if (state.searchQuery) url += `&search=${encodeURIComponent(state.searchQuery)}`;
            if (state.selectedType) url += `&machinery_type=${encodeURIComponent(state.selectedType)}`;
            if (state.selectedPlatform) url += `&source_platform=${encodeURIComponent(state.selectedPlatform)}`;
            if (state.selectedRegion) url += `&region=${encodeURIComponent(state.selectedRegion)}`;
            if (state.priceMin) url += `&price_min=${state.priceMin}`;
            if (state.priceMax) url += `&price_max=${state.priceMax}`;
            
            if (state.currentTab === "archive") {
                url += "&status=Архив";
            } else if (state.currentTab === "favorite") {
                url += "&is_favorite=true";
            }
            
            const res = await fetch(url);
            if (!res.ok) throw new Error("Failed to load tenders");
            state.tenders = await res.json();
            
            populateFilterPlatform();
            populateFilterRegion();
            updateKPIs();
            renderTenders();
        } catch (error) {
            console.error(error);
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="px-6 py-8 text-center text-red-400">
                        <i class="fa-solid fa-triangle-exclamation text-xl mb-1"></i>
                        <p>Ошибка при загрузке данных с сервера</p>
                    </td>
                </tr>
            `;
        }
    }

    async function fetchPlatforms() {
        try {
            const res = await fetch("/api/tenders/platforms");
            if (!res.ok) throw new Error("Failed to load platforms");
            state.platforms = await res.json();
            populateFilterPlatform();
        } catch (error) {
            console.error(error);
        }
    }

    async function fetchRegions() {
        try {
            const res = await fetch("/api/tenders/regions");
            if (!res.ok) throw new Error("Failed to load regions");
            state.regions = await res.json();
            populateFilterRegion();
        } catch (error) {
            console.error(error);
        }
    }

    // Update KPIs from state
    function updateKPIs() {
        const total = state.tenders.length;
        const newCount = state.tenders.filter(t => t.status === "Новый").length;
        const progressCount = state.tenders.filter(t => t.status === "В работе").length;
        const favoriteCount = state.tenders.filter(t => t.is_favorite).length;
        const archiveCount = state.tenders.filter(t => t.status === "Архив").length;

        statTotal.textContent = total;
        statNew.textContent = newCount;
        statProgress.textContent = progressCount;
        statFavorite.textContent = favoriteCount;
        statArchive.textContent = archiveCount;
    }

    // Render logic
    function renderTenders(forceLocalStatus = null) {
        tbody.innerHTML = "";
        checkAll.checked = false;
        
        let filtered = state.tenders.filter(t => {
            // Local fallback filter if forcing tab view
            if (forceLocalStatus) {
                if (t.status !== forceLocalStatus) return false;
            } else {
                if (state.currentTab === "active" && t.status === "Архив") return false;
                if (state.currentTab === "archive" && t.status !== "Архив") return false;
                if (state.currentTab === "favorite" && !t.is_favorite) return false;
            }
            return true;
        });

        if (filtered.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="px-6 py-12 text-center text-slate-500">
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

            // Star Class
            const starClass = tender.is_favorite ? "fa-solid fa-star text-yellow-400" : "fa-regular fa-star text-slate-500 hover:text-yellow-400";

            // Actions mapping
            let actionButtons = "";
            if (tender.status === "Новый") {
                actionButtons = `
                    <button data-id="${tender.id}" data-action="work" class="text-xs bg-indigo-950 hover:bg-indigo-900 text-indigo-400 px-3 py-1.5 rounded border border-indigo-500/20 transition-all font-semibold mr-1.5">
                        В работу
                    </button>
                    <button data-id="${tender.id}" data-action="archive" class="text-xs bg-slate-900 hover:bg-slate-850 text-slate-400 px-3 py-1.5 rounded border border-slate-700/30 transition-all font-semibold mr-1.5">
                        Архив
                    </button>
                `;
            } else if (tender.status === "В работе") {
                actionButtons = `
                    <span class="text-xs text-amber-400 font-medium bg-amber-950/30 border border-amber-500/20 px-2.5 py-1 rounded mr-2" data-status="В работе">В работе</span>
                    <button data-id="${tender.id}" data-action="archive" class="text-xs bg-slate-900 hover:bg-slate-850 text-slate-400 px-3 py-1.5 rounded border border-slate-700/30 transition-all font-semibold mr-1.5">
                        В архив
                    </button>
                `;
            } else if (tender.status === "Архив") {
                actionButtons = `
                    <button data-id="${tender.id}" data-action="new" class="text-xs bg-slate-800 hover:bg-slate-750 text-slate-300 px-3 py-1.5 rounded border border-slate-700/50 transition-all font-semibold mr-1.5">
                        Восстановить
                    </button>
                `;
            }

            // Always add Delete permanently action
            actionButtons += `
                <button data-id="${tender.id}" data-action="delete" class="text-xs bg-red-950/30 hover:bg-red-950/80 text-red-400 px-3 py-1.5 rounded border border-red-500/20 transition-all font-semibold" title="Удалить навсегда">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            `;

            const isChecked = state.selectedTenderIds.has(tender.id);

            tr.innerHTML = `
                <td class="px-6 py-4 w-10">
                    <input type="checkbox" data-id="${tender.id}" class="row-checkbox w-4 h-4 rounded border-slate-850 text-indigo-650 focus:ring-indigo-500 bg-slate-950" ${isChecked ? 'checked' : ''}>
                </td>
                <td class="px-6 py-4 max-w-sm">
                    <div class="font-semibold text-white hover:text-indigo-400 transition-colors flex items-center gap-2">
                        <button data-id="${tender.id}" data-action="toggle-star" class="focus:outline-none text-sm">
                            <i class="${starClass}"></i>
                        </button>
                        <a href="${tender.url}" target="_blank" class="flex items-center gap-1.5 truncate">
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
                    <div class="mt-2 flex items-center gap-1.5">
                        <input type="text" data-id="${tender.id}" class="tender-notes-input w-full px-2 py-1 text-2xs bg-slate-950 border border-slate-850 rounded focus:outline-none focus:border-indigo-500 text-slate-300 placeholder-slate-700" placeholder="Добавить заметку..." value="${tender.notes || ''}">
                    </div>
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
            btn.addEventListener("click", handleTenderAction);
        });

        // Add event listeners to checkboxes
        tbody.querySelectorAll(".row-checkbox").forEach(cb => {
            cb.addEventListener("change", handleRowCheckChange);
        });

        // Add event listeners to inline notes inputs
        tbody.querySelectorAll(".tender-notes-input").forEach(input => {
            input.addEventListener("blur", handleSaveNotes);
            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    e.target.blur();
                }
            });
        });
    }

    // Handle inline Notes Save
    async function handleSaveNotes(e) {
        const id = e.target.getAttribute("data-id");
        const notes = e.target.value.trim();
        
        try {
            const res = await fetch(`/api/tenders/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ notes })
            });

            if (!res.ok) throw new Error("Failed to save notes");
            const updated = await res.json();
            
            // Sync local state
            const index = state.tenders.findIndex(t => t.id === updated.id);
            if (index !== -1) {
                state.tenders[index].notes = updated.notes;
            }
            showToast("Заметка сохранена");
        } catch (err) {
            console.error(err);
            showToast("Ошибка при сохранении заметки");
        }
    }

    // Handle row check change
    function handleRowCheckChange(e) {
        const id = parseInt(e.target.getAttribute("data-id"));
        if (e.target.checked) {
            state.selectedTenderIds.add(id);
        } else {
            state.selectedTenderIds.delete(id);
        }
        updateBatchBar();
    }

    // Update batch action bar state
    function updateBatchBar() {
        const count = state.selectedTenderIds.size;
        batchSelectCount.textContent = count;
        if (count > 0) {
            batchActionsBar.classList.remove("hidden");
        } else {
            batchActionsBar.classList.add("hidden");
        }
    }

    // Check All toggle
    checkAll.addEventListener("change", (e) => {
        const checked = e.target.checked;
        tbody.querySelectorAll(".row-checkbox").forEach(cb => {
            const id = parseInt(cb.getAttribute("data-id"));
            cb.checked = checked;
            if (checked) {
                state.selectedTenderIds.add(id);
            } else {
                state.selectedTenderIds.delete(id);
            }
        });
        updateBatchBar();
    });

    // Handle Tender Actions (Star toggle, delete, status changes)
    async function handleTenderAction(e) {
        const id = e.currentTarget.getAttribute("data-id");
        const action = e.currentTarget.getAttribute("data-action");
        
        if (action === "toggle-star") {
            const tender = state.tenders.find(t => t.id == id);
            if (!tender) return;
            const newFavoriteState = !tender.is_favorite;
            try {
                const res = await fetch(`/api/tenders/${id}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ is_favorite: newFavoriteState })
                });
                if (!res.ok) throw new Error("Failed to toggle favorite status");
                const updated = await res.json();
                
                // Sync state
                const index = state.tenders.findIndex(t => t.id === updated.id);
                if (index !== -1) state.tenders[index] = updated;

                updateKPIs();
                renderTenders();
            } catch (err) {
                console.error(err);
                showToast("Ошибка при изменении избранного");
            }
            return;
        }

        if (action === "delete") {
            if (!confirm("Вы действительно хотите удалить этот тендер навсегда из базы?")) return;
            try {
                const res = await fetch(`/api/tenders/${id}`, { method: "DELETE" });
                if (!res.ok) throw new Error("Failed to delete tender");
                
                state.tenders = state.tenders.filter(t => t.id != id);
                state.selectedTenderIds.delete(parseInt(id));
                updateBatchBar();
                updateKPIs();
                renderTenders();
                showToast("Тендер успешно удален из базы данных");
            } catch (err) {
                console.error(err);
                showToast("Ошибка при удалении тендера");
            }
            return;
        }

        // Standard status actions
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

    // Batch Action Handlers
    async function executeBatchAction(actionName) {
        if (state.selectedTenderIds.size === 0) return;
        
        if (actionName === "delete") {
            if (!confirm(`Вы действительно хотите безвозвратно удалить ${state.selectedTenderIds.size} лотов из базы?`)) return;
        }

        const ids = [...state.selectedTenderIds];
        
        try {
            const res = await fetch("/api/tenders/batch-action", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tender_ids: ids, action: actionName })
            });

            if (!res.ok) throw new Error("Batch action execution failed");
            
            showToast("Групповая операция успешно выполнена!");
            state.selectedTenderIds.clear();
            updateBatchBar();
            await fetchTenders();
        } catch (err) {
            console.error(err);
            showToast("Не удалось выполнить групповую операцию");
        }
    }

    btnBatchWork.addEventListener("click", () => executeBatchAction("work"));
    btnBatchArchive.addEventListener("click", () => executeBatchAction("archive"));
    btnBatchDelete.addEventListener("click", () => executeBatchAction("delete"));

    // Set active tab
    function setTab(tabName) {
        state.currentTab = tabName;
        
        tabActiveBtn.className = "px-3 py-1.5 text-xs font-semibold rounded-md text-slate-400 hover:text-white transition-all";
        tabArchiveBtn.className = "px-3 py-1.5 text-xs font-semibold rounded-md text-slate-400 hover:text-white transition-all";

        if (tabName === "active") {
            tabActiveBtn.className = "px-3 py-1.5 text-xs font-semibold rounded-md bg-indigo-600 text-white transition-all";
        } else if (tabName === "archive") {
            tabArchiveBtn.className = "px-3 py-1.5 text-xs font-semibold rounded-md bg-indigo-600 text-white transition-all";
        }
    }

    // Event Listeners for tabs & filters
    tabActiveBtn.addEventListener("click", () => {
        setTab("active");
        fetchTenders();
    });

    tabArchiveBtn.addEventListener("click", () => {
        setTab("archive");
        fetchTenders();
    });

    searchInput.addEventListener("input", (e) => {
        state.searchQuery = e.target.value;
        fetchTenders();
    });

    filterType.addEventListener("change", (e) => {
        state.selectedType = e.target.value;
        fetchTenders();
    });

    filterPlatform.addEventListener("change", (e) => {
        state.selectedPlatform = e.target.value;
        fetchTenders();
    });

    filterRegion.addEventListener("change", (e) => {
        state.selectedRegion = e.target.value;
        fetchTenders();
    });

    filterPriceMin.addEventListener("input", (e) => {
        state.priceMin = e.target.value;
        fetchTenders();
    });

    filterPriceMax.addEventListener("input", (e) => {
        state.priceMax = e.target.value;
        fetchTenders();
    });

    sortOrder.addEventListener("change", (e) => {
        state.sortBy = e.target.value;
        fetchTenders();
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
            
            // Reload metadata lists & tenders list
            await fetchPlatforms();
            await fetchRegions();
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

    // Populate Platforms list dynamically
    function populateFilterPlatform() {
        const platforms = state.platforms || [];
        filterPlatform.innerHTML = '<option value="">Все площадки</option>';
        platforms.forEach(plat => {
            const opt = document.createElement("option");
            opt.value = plat;
            opt.textContent = plat;
            filterPlatform.appendChild(opt);
        });
        if (state.selectedPlatform && platforms.includes(state.selectedPlatform)) {
            filterPlatform.value = state.selectedPlatform;
        } else {
            state.selectedPlatform = "";
        }
    }

    // Populate Regions list dynamically
    function populateFilterRegion() {
        const regions = state.regions || [];
        filterRegion.innerHTML = '<option value="">Все регионы</option>';
        regions.forEach(reg => {
            const opt = document.createElement("option");
            opt.value = reg;
            opt.textContent = reg;
            filterRegion.appendChild(opt);
        });
        if (state.selectedRegion && regions.includes(state.selectedRegion)) {
            filterRegion.value = state.selectedRegion;
        } else {
            state.selectedRegion = "";
        }
    }

    // Populate Settings / Keywords
    async function fetchSettings() {
        try {
            const res = await fetch("/api/settings");
            if (!res.ok) throw new Error("Failed to load settings");
            const data = await res.json();
            state.keywords = data.keywords;
            populateFilterType(state.keywords);
            return data;
        } catch (error) {
            console.error("Error loading settings:", error);
        }
    }

    function populateFilterType(keywords) {
        const currentSelected = filterType.value;
        filterType.innerHTML = '<option value="">Все типы спецтехники</option>';
        keywords.forEach(kw => {
            const opt = document.createElement("option");
            opt.value = kw.trim();
            opt.textContent = kw.trim();
            filterType.appendChild(opt);
        });
        if (keywords.includes(currentSelected)) {
            filterType.value = currentSelected;
        } else {
            state.selectedType = "";
        }
    }

    // Custom categories arrays
    let customCategories = [];
    let customEisCategories = [];

    function renderCustomCategories() {
        customCategoriesContainer.innerHTML = "";
        customCategories.forEach(code => {
            const pill = document.createElement("div");
            pill.className = "flex items-center gap-1.5 bg-slate-800 text-slate-300 text-xs px-2.5 py-1 rounded-full border border-slate-700/50";
            
            const span = document.createElement("span");
            span.textContent = code;
            
            const removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.className = "text-slate-500 hover:text-red-400 transition-colors ml-1";
            removeBtn.innerHTML = '<i class="fa-solid fa-xmark text-2xs"></i>';
            removeBtn.addEventListener("click", () => {
                customCategories = customCategories.filter(c => c !== code);
                renderCustomCategories();
            });
            
            pill.appendChild(span);
            pill.appendChild(removeBtn);
            customCategoriesContainer.appendChild(pill);
        });
    }

    function renderCustomEisCategories() {
        customEisCategoriesContainer.innerHTML = "";
        customEisCategories.forEach(code => {
            const pill = document.createElement("div");
            pill.className = "flex items-center gap-1.5 bg-slate-800 text-slate-300 text-xs px-2.5 py-1 rounded-full border border-slate-700/50";
            
            const span = document.createElement("span");
            span.textContent = code;
            
            const removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.className = "text-slate-500 hover:text-red-400 transition-colors ml-1";
            removeBtn.innerHTML = '<i class="fa-solid fa-xmark text-2xs"></i>';
            removeBtn.addEventListener("click", () => {
                customEisCategories = customEisCategories.filter(c => c !== code);
                renderCustomEisCategories();
            });
            
            pill.appendChild(span);
            pill.appendChild(removeBtn);
            customEisCategoriesContainer.appendChild(pill);
        });
    }

    // Settings Modal Event Listeners
    btnSettings.addEventListener("click", async () => {
        const data = await fetchSettings();
        if (data) {
            // 1. Reset checkboxes
            const checkboxes = document.querySelectorAll("input[name='category-checkbox']");
            checkboxes.forEach(cb => cb.checked = false);

            const eisCheckboxes = document.querySelectorAll("input[name='eis-category-checkbox']");
            eisCheckboxes.forEach(cb => cb.checked = false);

            customCategories = [];
            customEisCategories = [];

            // 2. Populate checkboxes & custom category pills
            (data.categories || []).forEach(code => {
                const cb = [...checkboxes].find(c => c.value === code);
                if (cb) {
                    cb.checked = true;
                } else {
                    customCategories.push(code);
                }
            });

            (data.eis_okpd2_codes || []).forEach(code => {
                const cb = [...eisCheckboxes].find(c => c.value === code);
                if (cb) {
                    cb.checked = true;
                } else {
                    customEisCategories.push(code);
                }
            });

            renderCustomCategories();
            renderCustomEisCategories();

            // 3. Populate values
            settingsKeywords.value = (data.keywords || []).join(", ");
            settingsMinusWords.value = (data.minus_words || []).join(", ");
            
            if (eisStrictKeywords) eisStrictKeywords.checked = !!data.eis_strict_keywords;
            if (eisExclude223fz) eisExclude223fz.checked = !!data.eis_exclude_223fz;
            
            settingsRetentionDays.value = data.retention_days ?? 30;
            settingsMaxLimit.value = data.max_tenders_limit ?? 500;
            
            settingsModal.classList.remove("hidden");
        } else {
            showToast("Не удалось загрузить настройки");
        }
    });

    // Handle adding custom category code
    btnAddCustomCat.addEventListener("click", () => {
        const code = customCategoryInput.value.trim();
        if (code) {
            const checkboxes = document.querySelectorAll("input[name='category-checkbox']");
            const cb = [...checkboxes].find(c => c.value === code);
            if (cb) {
                cb.checked = true;
            } else if (!customCategories.includes(code)) {
                customCategories.push(code);
                renderCustomCategories();
            }
            customCategoryInput.value = "";
        }
    });

    // Handle adding custom EIS OKPD2 category code
    btnAddCustomEisCat.addEventListener("click", () => {
        const code = customEisCategoryInput.value.trim();
        if (code) {
            const checkboxes = document.querySelectorAll("input[name='eis-category-checkbox']");
            const cb = [...checkboxes].find(c => c.value === code);
            if (cb) {
                cb.checked = true;
            } else if (!customEisCategories.includes(code)) {
                customEisCategories.push(code);
                renderCustomEisCategories();
            }
            customEisCategoryInput.value = "";
        }
    });

    // Manual Clearing Action Handlers
    btnClearArchive.addEventListener("click", async () => {
        if (!confirm("Вы действительно хотите навсегда стереть все лоты в Архиве из базы данных?")) return;
        try {
            const res = await fetch("/api/settings/clear-archive", { method: "POST" });
            if (!res.ok) throw new Error("Clear archive failed");
            const resData = await res.json();
            showToast(`Успешно удалено архивных лотов: ${resData.deleted_count}`);
            await fetchTenders();
        } catch (err) {
            console.error(err);
            showToast("Ошибка при очистке архива");
        }
    });

    btnClearAll.addEventListener("click", async () => {
        if (!confirm("Внимание! Вы собираетесь БЕЗВОЗВРАТНО СТЕРЕТЬ ВСЕ ЛОТЫ из базы данных. Продолжить?")) return;
        try {
            const res = await fetch("/api/settings/clear-all", { method: "POST" });
            if (!res.ok) throw new Error("Clear database failed");
            showToast("База данных успешно полностью очищена!");
            await fetchTenders();
        } catch (err) {
            console.error(err);
            showToast("Ошибка при полной очистке базы данных");
        }
    });

    const hideSettings = () => settingsModal.classList.add("hidden");
    btnCloseSettings.addEventListener("click", hideSettings);
    btnCancelSettings.addEventListener("click", hideSettings);

    settingsForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        // Gather standard checked categories
        const checkboxes = document.querySelectorAll("input[name='category-checkbox']:checked");
        const standardCats = [...checkboxes].map(cb => cb.value);
        const categories = [...standardCats, ...customCategories];

        // Gather EIS checked categories
        const eisCheckboxes = document.querySelectorAll("input[name='eis-category-checkbox']:checked");
        const standardEisCats = [...eisCheckboxes].map(cb => cb.value);
        const eis_okpd2_codes = [...standardEisCats, ...customEisCategories];

        const eis_strict_keywords = eisStrictKeywords.checked;
        const eis_exclude_223fz = eisExclude223fz.checked;
        const retention_days = parseInt(settingsRetentionDays.value) || 0;
        const max_tenders_limit = parseInt(settingsMaxLimit.value) || 0;

        const keywords = settingsKeywords.value.split(",").map(x => x.trim()).filter(Boolean);
        const minus_words = settingsMinusWords.value.split(",").map(x => x.trim()).filter(Boolean);

        const btnSave = document.getElementById("btn-save-settings");
        btnSave.disabled = true;
        btnSave.classList.add("opacity-60");

        try {
            const res = await fetch("/api/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    categories, 
                    keywords, 
                    minus_words,
                    eis_okpd2_codes,
                    eis_strict_keywords,
                    eis_exclude_223fz,
                    retention_days,
                    max_tenders_limit
                })
            });

            if (!res.ok) throw new Error("Failed to save settings");

            showToast("Настройки успешно сохранены!");
            hideSettings();
            await fetchSettings();
            await fetchTenders();
            
        } catch (err) {
            console.error(err);
            showToast("Ошибка при сохранении настроек");
        } finally {
            btnSave.disabled = false;
            btnSave.classList.remove("opacity-60");
        }
    });

    // Initial load
    fetchSettings();
    fetchPlatforms();
    fetchRegions();
    fetchTenders();
});
