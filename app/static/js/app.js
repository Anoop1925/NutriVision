/* ═══════════════════════════════════════════════════════════
   app.js — NutriVision multi-page front-end
   ═══════════════════════════════════════════════════════════ */
(() => {
  "use strict";

  /* ── Helpers ────────────────────────────────────────────── */
  const $ = (s, p = document) => p.querySelector(s);
  const $$ = (s, p = document) => [...p.querySelectorAll(s)];

  function toast(msg, type = "info") {
    const c = $("#toast-container");
    if (!c) return;
    const t = document.createElement("div");
    t.className = `toast ${type}`;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; t.style.transform = "translateY(-8px)"; setTimeout(() => t.remove(), 300); }, 4000);
  }

  function setLoading(btn, spinnerId, loading) {
    const spinner = $(`#${spinnerId}`);
    if (!spinner || !btn) return;
    if (loading) {
      btn.disabled = true;
      const label = btn.querySelector("span:first-of-type");
      if (label) label.classList.add("hidden");
      spinner.classList.remove("hidden");
    } else {
      btn.disabled = false;
      const label = btn.querySelector("span:first-of-type");
      if (label) label.classList.remove("hidden");
      spinner.classList.add("hidden");
    }
  }

  const NUTRITION_KEYS = [
    "Calories", "FatContent", "SaturatedFatContent", "CholesterolContent",
    "SodiumContent", "CarbohydrateContent", "FiberContent", "SugarContent", "ProteinContent"
  ];
  const NUTRITION_LABELS = [
    "Calories (kcal)", "Fat (g)", "Saturated Fat (g)", "Cholesterol (mg)",
    "Sodium (mg)", "Carbs (g)", "Fiber (g)", "Sugar (g)", "Protein (g)"
  ];
  const NUTRITION_MAX = [2000, 100, 13, 300, 2300, 325, 40, 40, 200];
  const NUTRITION_DEFAULTS = [500, 50, 0, 0, 400, 100, 10, 10, 10];

  /* ═══════════════════════════════════════════════════════════
     GLOBAL — Navbar & auth
     ═══════════════════════════════════════════════════════════ */
  (() => {
    // Mobile menu toggle
    const toggle = $("#mobile-toggle");
    const menu = $("#mobile-menu");
    if (toggle && menu) {
      toggle.addEventListener("click", () => menu.classList.toggle("hidden"));
      $$("a", menu).forEach(a => a.addEventListener("click", () => menu.classList.add("hidden")));
    }

    // Logout
    const logoutBtn = $("#logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        await fetch("/auth/logout", { method: "POST" });
        window.location.href = "/login";
      });
    }

    // Navbar scroll effect
    const nav = $("nav");
    if (nav) {
      window.addEventListener("scroll", () => {
        nav.classList.toggle("nav-scrolled", window.scrollY > 40);
      });
    }
  })();

  /* ═══════════════════════════════════════════════════════════
     PAGE: DIET PLAN
     ═══════════════════════════════════════════════════════════ */
  (() => {
    const form = $("#diet-form");
    if (!form) return;

    let recs = [];
    let selectedMeals = {};

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      setLoading(btn, "diet-spinner", true);
      $("#diet-results").classList.add("hidden");

      const d = Object.fromEntries(new FormData(form));

      try {
        // Step 1 — fast BMI + calorie plans
        const calcRes = await fetch("/api/diet/calculate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(d),
        });
        if (!calcRes.ok) throw new Error("Calculation failed");
        const { bmi, plans } = await calcRes.json();

        renderBMI(bmi);
        renderPlans(plans);
        $("#diet-results").classList.remove("hidden");
        setLoading(btn, "diet-spinner", false);

        // Step 2 — slow ML recommendations
        const gen = $("#diet-generating");
        const mealRecs = $("#meal-recommendations");
        const mealCharts = $("#meal-charts");
        if (gen) gen.classList.remove("hidden");
        if (mealRecs) mealRecs.classList.add("hidden");
        if (mealCharts) mealCharts.classList.add("hidden");

        const recRes = await fetch("/api/diet/recommend", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(d),
        });
        if (!recRes.ok) throw new Error("Recommendation failed");
        const { recommendations } = await recRes.json();

        recs = recommendations || [];
        renderMealRecommendations(recs);
        selectedMeals = {};
        recs.forEach((_, i) => { selectedMeals[i] = 0; });
        renderMealSelectors(recs);

        if (gen) gen.classList.add("hidden");
        if (mealRecs) mealRecs.classList.remove("hidden");
        if (mealCharts) mealCharts.classList.remove("hidden");

        // Render charts AFTER containers are visible so ECharts gets real dimensions
        requestAnimationFrame(() => {
          renderDietCharts();
          toast("Diet plan generated!", "success");
        });
      } catch (err) {
        toast(err.message || "Something went wrong", "error");
        setLoading(btn, "diet-spinner", false);
        const gen = $("#diet-generating");
        if (gen) gen.classList.add("hidden");
      }
    });

    function renderBMI(bmi) {
      const bmiEl = $("#bmi-value");
      const badge = $("#bmi-badge");
      if (!bmiEl || !badge) return;
      bmiEl.textContent = bmi.value;
      const colorMap = { green: "bg-green-100 text-green-700", yellow: "bg-amber-100 text-amber-700", red: "bg-red-100 text-red-700" };
      badge.textContent = bmi.category;
      badge.className = `inline-block mt-3 px-3 py-1 rounded-full text-sm font-semibold ${colorMap[bmi.color] || ""}`;
    }

    function renderPlans(plans) {
      const c = $("#calorie-cards");
      if (!c) return;
      c.innerHTML = plans.map(p => `
        <div class="calorie-card">
          <p class="cal-label">${p.name}</p>
          <p class="cal-value">${p.calories.toLocaleString()}</p>
          <p class="cal-unit">kcal/day</p>
          <p class="text-xs text-surface-700/40 mt-1">${p.delta}</p>
        </div>`).join("");
    }

    function renderMealRecommendations(meals) {
      const c = $("#meal-recommendations");
      if (!c) return;
      c.innerHTML = meals.map((group, gi) => {
        const title = group.meal.charAt(0).toUpperCase() + group.meal.slice(1);
        const cards = (group.recipes || []).map((r, ri) => recipeCard(r, `diet-${gi}-${ri}`)).join("");
        return `
          <div data-aos="fade-up">
            <h3 class="text-xl font-bold mb-1 capitalize flex items-center gap-2">
              <span class="w-8 h-8 rounded-lg bg-brand-100 text-brand-600 flex items-center justify-center text-sm font-bold">${gi + 1}</span>
              ${title}
            </h3>
            <p class="text-sm text-surface-700/40 mb-5">~${Math.round((group.recipes[0]?.Calories || 0))} kcal target</p>
            <div class="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">${cards}</div>
          </div>`;
      }).join("");
      // Re-init AOS for new elements
      if (window.AOS) AOS.refresh();
    }

    function renderMealSelectors(meals) {
      const c = $("#meal-selectors");
      if (!c) return;
      c.innerHTML = "";
      meals.forEach((group, gi) => {
        (group.recipes || []).forEach((r, ri) => {
          const pill = document.createElement("button");
          pill.type = "button";
          pill.className = `meal-selector ${ri === 0 ? "active" : ""}`;
          pill.dataset.gi = gi;
          pill.dataset.ri = ri;
          pill.textContent = `${group.meal}: ${truncate(r.Name, 18)}`;
          pill.addEventListener("click", () => {
            selectedMeals[gi] = ri;
            $$(".meal-selector").forEach(p => p.classList.remove("active"));
            Object.entries(selectedMeals).forEach(([g, r2]) => {
              const sel = $(`.meal-selector[data-gi="${g}"][data-ri="${r2}"]`);
              if (sel) sel.classList.add("active");
            });
            renderDietCharts();
          });
          c.appendChild(pill);
        });
      });
    }

    /* ── DUAL-AXIS LINE CHART + SUNBURST DIAGRAM ─────────── */
    let calChartInstance = null;
    let nutriChartInstance = null;

    function renderDietCharts() {
      const selected = Object.entries(selectedMeals).map(([gi, ri]) => {
        const group = recs[gi];
        const recipe = group?.recipes?.[ri];
        return recipe ? { label: `${group.meal}: ${truncate(recipe.Name, 20)}`, recipe } : null;
      }).filter(Boolean);

      if (!selected.length) return;

      /* ── Chart 1: Dual-axis line chart (Calories + Protein) ── */
      const calEl = document.getElementById("chart-calories");
      if (calEl) {
        // Dispose and recreate to get fresh dimensions
        if (calChartInstance) { calChartInstance.dispose(); calChartInstance = null; }
        calChartInstance = echarts.init(calEl, null, { renderer: 'canvas' });
        const labels = selected.map(s => s.label);
        const calories = selected.map(s => Math.round(s.recipe.Calories || 0));
        const protein = selected.map(s => Math.round(s.recipe.ProteinContent || 0));

        calChartInstance.setOption({
          tooltip: {
            trigger: "axis",
            axisPointer: { type: "cross" },
            backgroundColor: "rgba(255,255,255,0.95)",
            borderColor: "#e4e4e7",
            textStyle: { color: "#18181b", fontSize: 12 },
          },
          legend: {
            data: ["Calories", "Protein"],
            bottom: 4,
            textStyle: { fontSize: 12, color: "#71717a" },
          },
          grid: { left: 60, right: 60, bottom: 50, top: 40, containLabel: false },
          xAxis: {
            type: "category",
            data: labels,
            axisLabel: { rotate: 15, fontSize: 10, color: "#71717a", overflow: "truncate", width: 80 },
            axisLine: { lineStyle: { color: "#e4e4e7" } },
            axisTick: { alignWithLabel: true },
          },
          yAxis: [
            {
              type: "value",
              name: "kcal",
              nameTextStyle: { color: "#22c55e", fontSize: 12, padding: [0, 0, 0, 0] },
              nameLocation: "end",
              axisLabel: { color: "#22c55e", fontSize: 11, formatter: (v) => v >= 1000 ? (v/1000).toFixed(1)+'k' : v },
              axisLine: { show: true, lineStyle: { color: "#22c55e" } },
              splitLine: { lineStyle: { color: "#f4f4f5" } },
            },
            {
              type: "value",
              name: "g protein",
              nameTextStyle: { color: "#8b5cf6", fontSize: 12, padding: [0, 0, 0, 0] },
              nameLocation: "end",
              axisLabel: { color: "#8b5cf6", fontSize: 11 },
              axisLine: { show: true, lineStyle: { color: "#8b5cf6" } },
              splitLine: { show: false },
            }
          ],
          series: [
            {
              name: "Calories",
              type: "line",
              yAxisIndex: 0,
              data: calories,
              smooth: true,
              symbol: "circle",
              symbolSize: 8,
              lineStyle: { width: 3, color: "#22c55e" },
              itemStyle: { color: "#22c55e", borderWidth: 2, borderColor: "#fff" },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: "rgba(34,197,94,0.25)" },
                  { offset: 1, color: "rgba(34,197,94,0.02)" },
                ]),
              },
            },
            {
              name: "Protein",
              type: "line",
              yAxisIndex: 1,
              data: protein,
              smooth: true,
              symbol: "diamond",
              symbolSize: 8,
              lineStyle: { width: 3, color: "#8b5cf6" },
              itemStyle: { color: "#8b5cf6", borderWidth: 2, borderColor: "#fff" },
              areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: "rgba(139,92,246,0.2)" },
                  { offset: 1, color: "rgba(139,92,246,0.02)" },
                ]),
              },
            },
          ],
        }, true);
      }

      /* ── Chart 2: Sunburst diagram (hierarchical nutrition) ── */
      const nutriEl = document.getElementById("chart-nutrition");
      if (nutriEl) {
        // Dispose and recreate to get fresh dimensions
        if (nutriChartInstance) { nutriChartInstance.dispose(); nutriChartInstance = null; }
        nutriChartInstance = echarts.init(nutriEl, null, { renderer: 'canvas' });

        // Build sunburst data: root → meals → nutrients
        const SUNBURST_COLORS = {
          Fat: "#f59e0b",
          "Sat. Fat": "#f97316",
          Cholesterol: "#ef4444",
          Sodium: "#ec4899",
          Carbs: "#3b82f6",
          Fiber: "#8b5cf6",
          Sugar: "#e879f9",
          Protein: "#22c55e",
        };

        const sunburstData = selected.map((s, idx) => {
          const r = s.recipe;
          const children = [
            { name: "Fat", value: Math.round(r.FatContent || 0) },
            { name: "Sat. Fat", value: Math.round(r.SaturatedFatContent || 0) },
            { name: "Cholesterol", value: Math.round(r.CholesterolContent || 0) },
            { name: "Sodium", value: Math.round(r.SodiumContent || 0) },
            { name: "Carbs", value: Math.round(r.CarbohydrateContent || 0) },
            { name: "Fiber", value: Math.round(r.FiberContent || 0) },
            { name: "Sugar", value: Math.round(r.SugarContent || 0) },
            { name: "Protein", value: Math.round(r.ProteinContent || 0) },
          ].filter(c => c.value > 0).map(c => ({
            ...c,
            itemStyle: { color: SUNBURST_COLORS[c.name] || "#94a3b8" },
          }));

          const mealColors = ["#22c55e", "#3b82f6", "#f59e0b", "#8b5cf6", "#ef4444"];
          return {
            name: truncate(s.label, 22),
            children,
            itemStyle: { color: mealColors[idx % mealColors.length] },
          };
        });

        nutriChartInstance.setOption({
          tooltip: {
            trigger: "item",
            formatter: (p) => {
              if (p.treePathInfo && p.treePathInfo.length > 1) {
                const path = p.treePathInfo.map(n => n.name).filter(Boolean).join(" › ");
                return `<b>${path}</b><br/>${p.value}`;
              }
              return `<b>${p.name}</b>`;
            },
            backgroundColor: "rgba(255,255,255,0.95)",
            borderColor: "#e4e4e7",
            textStyle: { color: "#18181b", fontSize: 12 },
          },
          series: [{
            type: "sunburst",
            data: sunburstData,
            radius: ["10%", "80%"],
            center: ["50%", "50%"],
            sort: null,
            emphasis: { focus: "ancestor" },
            levels: [
              {},
              {
                r0: "10%", r: "45%",
                itemStyle: { borderWidth: 2, borderColor: "#fff" },
                label: { fontSize: 11, fontWeight: 600, color: "#fff", rotate: "radial" },
              },
              {
                r0: "45%", r: "80%",
                itemStyle: { borderWidth: 1, borderColor: "#fff" },
                label: { fontSize: 10, color: "#fff", align: "center", rotate: "radial" },
              },
            ],
          }],
        }, true);
      }

      // Resize handler
      window.addEventListener("resize", () => {
        if (calChartInstance) calChartInstance.resize();
        if (nutriChartInstance) nutriChartInstance.resize();
      });
    }
  })();

  /* ═══════════════════════════════════════════════════════════
     PAGE: RECIPE FINDER
     ═══════════════════════════════════════════════════════════ */
  (() => {
    const form = $("#custom-form");
    if (!form) return;

    // Build sliders
    const sliderBox = $("#nutrition-sliders");
    if (sliderBox) {
      NUTRITION_LABELS.forEach((label, i) => {
        const id = `slider-${i}`;
        const max = NUTRITION_MAX[i];
        const val = NUTRITION_DEFAULTS[i];
        sliderBox.innerHTML += `
          <div class="slider-row">
            <div class="slider-head"><span>${label}</span><span id="${id}-val">${val}</span></div>
            <input type="range" id="${id}" min="0" max="${max}" value="${val}" step="1" />
          </div>`;
      });
      NUTRITION_LABELS.forEach((_, i) => {
        const slider = $(`#slider-${i}`);
        const valSpan = $(`#slider-${i}-val`);
        if (slider && valSpan) {
          slider.addEventListener("input", () => { valSpan.textContent = slider.value; });
        }
      });
    }

    let customRecipes = [];

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      setLoading(btn, "custom-spinner", true);
      $("#custom-results")?.classList.add("hidden");

      const nutrition = NUTRITION_LABELS.map((_, i) => parseFloat($(`#slider-${i}`)?.value || 0));
      const count = parseInt($("#c-count")?.value || "10", 10);
      const ingredients = ($("#c-ingredients")?.value || "").trim();

      try {
        const res = await fetch("/api/custom/recommend", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nutrition, count, ingredients }),
        });
        if (!res.ok) throw new Error("Recommendation failed");
        const { recipes } = await res.json();
        customRecipes = recipes || [];

        if (!customRecipes.length) {
          toast("No matching recipes found. Try adjusting your filters.", "error");
          setLoading(btn, "custom-spinner", false);
          return;
        }

        renderCustomGrid(customRecipes);
        renderCustomOverview(customRecipes);
        $("#custom-results")?.classList.remove("hidden");
        toast(`Found ${customRecipes.length} recipes`, "success");
      } catch (err) {
        toast(err.message || "Something went wrong", "error");
      } finally {
        setLoading(btn, "custom-spinner", false);
      }
    });

    function renderCustomGrid(recipes) {
      const c = $("#custom-grid");
      if (c) c.innerHTML = recipes.map((r, i) => recipeCard(r, `custom-${i}`)).join("");
    }

    let pieChart = null;
    function renderCustomOverview(recipes) {
      const sel = $("#custom-recipe-select");
      if (!sel) return;
      sel.innerHTML = recipes.map((r, i) => `<option value="${i}">${truncate(r.Name, 40)}</option>`).join("");
      sel.onchange = () => drawCustomSunburst(recipes[sel.value]);
      // Make container visible FIRST, then draw chart after a frame
      $("#custom-overview")?.classList.remove("hidden");
      requestAnimationFrame(() => drawCustomSunburst(recipes[0]));
    }

    function drawCustomSunburst(recipe) {
      const el = document.getElementById("chart-custom-pie");
      if (!el) return;
      // Dispose and recreate to get fresh dimensions
      if (pieChart) { pieChart.dispose(); pieChart = null; }
      pieChart = echarts.init(el, null, { renderer: 'canvas' });

      // Build hierarchical data: Category → individual nutrients
      const sunburstData = [
        {
          name: "Fats",
          itemStyle: { color: "#f59e0b" },
          children: [
            { name: "Fat", value: Math.round(recipe.FatContent || 0), itemStyle: { color: "#fbbf24" } },
            { name: "Sat. Fat", value: Math.round(recipe.SaturatedFatContent || 0), itemStyle: { color: "#f97316" } },
          ].filter(c => c.value > 0),
        },
        {
          name: "Carbohydrates",
          itemStyle: { color: "#3b82f6" },
          children: [
            { name: "Carbs", value: Math.round(recipe.CarbohydrateContent || 0), itemStyle: { color: "#60a5fa" } },
            { name: "Fiber", value: Math.round(recipe.FiberContent || 0), itemStyle: { color: "#8b5cf6" } },
            { name: "Sugar", value: Math.round(recipe.SugarContent || 0), itemStyle: { color: "#e879f9" } },
          ].filter(c => c.value > 0),
        },
        {
          name: "Protein",
          itemStyle: { color: "#22c55e" },
          children: [
            { name: "Protein", value: Math.round(recipe.ProteinContent || 0), itemStyle: { color: "#4ade80" } },
          ].filter(c => c.value > 0),
        },
        {
          name: "Other",
          itemStyle: { color: "#ec4899" },
          children: [
            { name: "Cholesterol", value: Math.round(recipe.CholesterolContent || 0), itemStyle: { color: "#f472b6" } },
            { name: "Sodium", value: Math.round(recipe.SodiumContent || 0), itemStyle: { color: "#fb7185" } },
          ].filter(c => c.value > 0),
        },
      ].filter(g => g.children.length > 0);

      pieChart.setOption({
        tooltip: {
          trigger: "item",
          formatter: (p) => {
            const path = (p.treePathInfo || []).map(n => n.name).filter(Boolean).join(" › ");
            return p.value != null ? `<b>${path}</b><br/>${p.value}` : `<b>${p.name}</b>`;
          },
          backgroundColor: "rgba(255,255,255,0.96)",
          borderColor: "#e4e4e7",
          textStyle: { color: "#18181b", fontSize: 12 },
        },
        series: [{
          type: "sunburst",
          data: sunburstData,
          radius: ["10%", "78%"],
          center: ["50%", "50%"],
          sort: null,
          emphasis: { focus: "ancestor" },
          levels: [
            {},
            {
              r0: "10%", r: "42%",
              itemStyle: { borderWidth: 3, borderColor: "#fff" },
              label: { fontSize: 12, fontWeight: 700, color: "#fff", rotate: "radial" },
            },
            {
              r0: "42%", r: "78%",
              itemStyle: { borderWidth: 2, borderColor: "#fff" },
              label: { fontSize: 11, fontWeight: 500, color: "#fff", align: "center", rotate: "radial" },
            },
          ],
        }],
      }, true);

      window.removeEventListener("resize", resizeCustomChart);
      window.addEventListener("resize", resizeCustomChart);
    }
    function resizeCustomChart() { if (pieChart) pieChart.resize(); }
  })();

  /* ═══════════════════════════════════════════════════════════
     PAGE: FOOD ANALYZER
     ═══════════════════════════════════════════════════════════ */
  (() => {
    const form = $("#analyzer-form");
    if (!form) return;

    const fileInput = $("#food-image");
    const dropZone = $("#drop-zone");
    const placeholder = $("#drop-placeholder");
    const previewImg = $("#preview-img");

    if (fileInput) {
      fileInput.addEventListener("change", () => {
        if (fileInput.files.length) showPreview(fileInput.files[0]);
      });
    }
    if (dropZone) {
      dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drop-active"); });
      dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drop-active"));
      dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("drop-active");
        if (e.dataTransfer.files.length && fileInput) {
          fileInput.files = e.dataTransfer.files;
          showPreview(e.dataTransfer.files[0]);
        }
      });
    }

    function showPreview(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (previewImg) {
          previewImg.src = e.target.result;
          previewImg.classList.remove("hidden");
        }
        if (placeholder) placeholder.classList.add("hidden");
      };
      reader.readAsDataURL(file);
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!fileInput?.files.length) { toast("Please upload an image first", "error"); return; }

      const btn = form.querySelector('button[type="submit"]');
      setLoading(btn, "analyzer-spinner", true);
      $("#analyzer-results")?.classList.add("hidden");

      const fd = new FormData();
      fd.append("image", fileInput.files[0]);

      try {
        const res = await fetch("/api/analyzer/analyze", { method: "POST", body: fd });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || "Analysis failed");
        }
        const data = await res.json();
        renderAnalyzerResults(data);
        $("#analyzer-results")?.classList.remove("hidden");
        toast("Analysis complete!", "success");
      } catch (err) {
        toast(err.message || "Something went wrong", "error");
      } finally {
        setLoading(btn, "analyzer-spinner", false);
      }
    });

    let analyzerChart = null;

    function renderAnalyzerResults(data) {
      // Items
      const itemsEl = $("#analyzer-items");
      if (itemsEl) {
        itemsEl.innerHTML = (data.items || []).map(item => {
          const bgMap = { green: "bg-green-50 text-green-700", yellow: "bg-amber-50 text-amber-700", red: "bg-red-50 text-red-700" };
          const rows = NUTRITION_KEYS.map((k, i) => `
            <tr>
              <td class="font-medium">${NUTRITION_LABELS[i]}</td>
              <td class="text-right">${item.nutrition_per_unit[k] ?? "-"}</td>
              <td class="text-right font-semibold">${item.total_nutrition[k] ?? "-"}</td>
            </tr>`).join("");

          return `
            <div class="analyzer-item" data-aos="fade-up">
              <div class="flex items-center gap-3 mb-4">
                <h4 class="text-lg font-bold">${item.item_name}</h4>
                <span class="status-badge ${bgMap[item.health_color] || ""}">${item.health_status}</span>
              </div>
              <p class="text-sm text-surface-700/50 mb-1">Qty: <strong>${item.quantity}</strong> &middot; Serving: ${item.serving_size}</p>
              <p class="text-sm text-surface-700/50 mb-4">${item.weight_impact}</p>
              <table>
                <thead><tr><th>Nutrient</th><th class="text-right">Per unit</th><th class="text-right">Total</th></tr></thead>
                <tbody>${rows}</tbody>
              </table>
            </div>`;
        }).join("");
      }

      // Grand total
      const gt = data.grand_total || {};
      const bgMap = { green: "bg-green-50 text-green-700 border-green-200", yellow: "bg-amber-50 text-amber-700 border-amber-200", red: "bg-red-50 text-red-700 border-red-200" };
      const totalRows = NUTRITION_KEYS.map((k, i) => `
        <tr><td class="font-medium">${NUTRITION_LABELS[i]}</td><td class="text-right font-semibold">${gt[k] ?? "-"}</td></tr>`).join("");

      const totalEl = $("#analyzer-total");
      if (totalEl) {
        totalEl.innerHTML = `
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-bold">Grand Total</h3>
            <span class="status-badge border ${bgMap[data.overall_color] || ""}">${data.overall_status} &middot; ${data.overall_impact}</span>
          </div>
          <table class="w-full text-sm">
            <thead><tr><th class="text-left text-xs font-semibold text-surface-700/40 uppercase tracking-wide pb-2 border-b border-surface-100">Nutrient</th><th class="text-right text-xs font-semibold text-surface-700/40 uppercase tracking-wide pb-2 border-b border-surface-100">Total</th></tr></thead>
            <tbody>${totalRows}</tbody>
          </table>`;
      }

      // Analyzer donut chart
      const chartWrap = $("#analyzer-chart-wrap");
      const chartEl = document.getElementById("chart-analyzer");
      if (chartWrap && chartEl && gt.Calories) {
        chartWrap.classList.remove("hidden");
        // Dispose and recreate to get fresh dimensions
        if (analyzerChart) { analyzerChart.dispose(); analyzerChart = null; }
        requestAnimationFrame(() => {
          analyzerChart = echarts.init(chartEl, null, { renderer: 'canvas' });
          const keys = ["FatContent", "CarbohydrateContent", "ProteinContent", "FiberContent", "SugarContent"];
          const labels = ["Fat", "Carbs", "Protein", "Fiber", "Sugar"];
          const colors = ["#f59e0b", "#3b82f6", "#22c55e", "#8b5cf6", "#ef4444"];
          analyzerChart.setOption({
            tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
            legend: { bottom: 0, textStyle: { fontSize: 11, color: "#71717a" } },
            series: [{
              type: "pie", radius: ["40%", "65%"], center: ["50%", "45%"],
              itemStyle: { borderRadius: 8, borderColor: "#fff", borderWidth: 2 },
              label: { show: false },
              data: keys.map((k, i) => ({
                name: labels[i],
                value: parseFloat(gt[k]) || 0,
                itemStyle: { color: colors[i] },
              })),
            }],
          }, true);
          window.addEventListener("resize", () => { if (analyzerChart) analyzerChart.resize(); });
        });
      }

      // Re-init AOS for dynamic elements
      if (window.AOS) AOS.refresh();
    }
  })();

  /* ═══════════════════════════════════════════════════════════
     SHARED — Recipe card builder
     ═══════════════════════════════════════════════════════════ */
  function recipeCard(r, uid) {
    const img = r.image_link || "";
    const imgHtml = img
      ? `<img src="${img}" alt="${esc(r.Name)}" class="recipe-img" loading="lazy" onerror="this.style.display='none'" />`
      : `<div class="recipe-img flex items-center justify-center text-surface-700/20"><svg class="w-10 h-10" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path d="M12 6v6l4 2"/><circle cx="12" cy="12" r="10"/></svg></div>`;

    const pills = [
      r.Calories ? `${Math.round(r.Calories)} kcal` : null,
      r.ProteinContent ? `${Math.round(r.ProteinContent)}g protein` : null,
      r.FatContent ? `${Math.round(r.FatContent)}g fat` : null,
      r.CarbohydrateContent ? `${Math.round(r.CarbohydrateContent)}g carbs` : null,
    ].filter(Boolean);

    const ingredients = (r.RecipeIngredientParts || []).slice(0, 6);
    const instructions = (r.RecipeInstructions || []);

    return `
      <div class="recipe-card" id="rc-${uid}">
        ${imgHtml}
        <div class="recipe-body">
          <p class="recipe-title">${esc(r.Name || "Untitled")}</p>
          <div class="recipe-meta">${pills.map(p => `<span class="pill">${p}</span>`).join("")}</div>
          ${ingredients.length ? `
          <details class="mt-3">
            <summary class="text-xs font-semibold text-brand-600 cursor-pointer hover:underline">Ingredients (${r.RecipeIngredientParts?.length || 0})</summary>
            <ul class="mt-2 text-xs text-surface-700/60 space-y-0.5 list-disc pl-4">${ingredients.map(i => `<li>${esc(i)}</li>`).join("")}</ul>
          </details>` : ""}
          ${instructions.length ? `
          <details class="mt-2">
            <summary class="text-xs font-semibold text-brand-600 cursor-pointer hover:underline">Instructions</summary>
            <ol class="mt-2 text-xs text-surface-700/60 space-y-1 list-decimal pl-4">${instructions.map(s => `<li>${esc(s)}</li>`).join("")}</ol>
          </details>` : ""}
          ${r.CookTime || r.PrepTime ? `<p class="text-[11px] text-surface-700/30 mt-3">Prep ${r.PrepTime || "–"} · Cook ${r.CookTime || "–"}</p>` : ""}
        </div>
      </div>`;
  }

  function truncate(s, n) { return (s && s.length > n) ? s.slice(0, n) + "…" : (s || ""); }
  function esc(s) { const d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; }

  /* ── Lucide icons init ──────────────────────────────────── */
  if (window.lucide) lucide.createIcons();

})();
