<template>
  <div class="harmonics-tab">
    <!-- 컨트롤 바: 신호종류 콤보 + 뷰 토글 + Draw -->
    <div class="flex flex-wrap items-center gap-4 mb-3">
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-600 dark:text-gray-300">신호종류</label>
        <select v-model="measurement"
          class="form-select text-sm rounded border-gray-300 dark:bg-gray-700 dark:border-gray-600">
          <option v-for="s in signalTypes" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
      </div>

      <div class="flex rounded-md overflow-hidden border border-gray-300 dark:border-gray-600">
        <button v-for="v in views" :key="v.value"
          @click="viewMode = v.value"
          class="px-3 py-1.5 text-sm"
          :class="viewMode === v.value
            ? 'bg-violet-600 text-white'
            : 'bg-white text-gray-600 dark:bg-gray-700 dark:text-gray-300'">
          {{ v.label }}
        </button>
      </div>

      <button @click="drawChart" :disabled="loading || !hasData"
        class="px-4 py-1.5 text-sm rounded bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-40">
        Draw
      </button>
    </div>

    <!-- 뷰별 서브 컨트롤 -->
    <div v-show="!loading && !errorMsg && hasData" class="mb-3">
      <!-- 차수 선택 (최대 4) -->
      <div v-show="viewMode === 'lines'" class="flex items-start gap-2">
        <span class="text-sm text-gray-600 dark:text-gray-300 mt-1 whitespace-nowrap">
          차수 ({{ selectedOrders.length }}/4)
        </span>
        <div class="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
          <button v-for="o in matrix.orders" :key="o"
            @click="toggleOrder(o)"
            class="px-2 py-0.5 text-xs rounded border"
            :class="selectedOrders.includes(o)
              ? 'bg-violet-600 text-white border-violet-600'
              : 'bg-white text-gray-600 border-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600'">
            {{ o }}
          </button>
        </div>
      </div>

      <!-- 시점 슬라이더 -->
      <div v-show="viewMode === 'spectrum'" class="flex items-center gap-3">
        <span class="text-sm text-gray-600 dark:text-gray-300 whitespace-nowrap">시점</span>
        <input type="range" min="0" :max="Math.max(0, matrix.times.length - 1)" v-model.number="timeIdx"
          class="flex-1 max-w-md" />
        <span class="text-sm text-gray-700 dark:text-gray-200 whitespace-nowrap w-32">
          {{ matrix.times[timeIdx] ? fmtTime(matrix.times[timeIdx]) : "-" }}
        </span>
      </div>
    </div>

    <!-- 상태 -->
    <div v-if="loading" class="text-sm text-gray-500 py-8 text-center">불러오는 중...</div>
    <div v-else-if="errorMsg" class="text-sm text-red-500 py-8 text-center">{{ errorMsg }}</div>
    <div v-else-if="!hasData" class="text-sm text-gray-500 py-8 text-center">데이터 없음</div>

    <!-- 3상 차트 3개 (두 뷰 공용, Draw 시 렌더) -->
    <div v-show="!loading && !errorMsg && hasData">
      <div v-for="(ph, i) in phases" :key="ph"
        :ref="el => (chartEls[i] = el)" class="phase-chart"></div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from "vue";
import axios from "axios";
import * as echarts from "echarts";

const PALETTE = ["#7c3aed", "#0ea5e9", "#f59e0b", "#ef4444"];

export default {
  name: "HarmonicsTab",
  props: {
    channel: { type: String, default: "Main" },
    startdate: { type: [String, Number, Date], default: null },
    enddate: { type: [String, Number, Date], default: null },
    asset: { type: String, default: "" },
  },
  setup(props) {
    const signalTypes = [
      { value: "harmonics_u", label: "상전압" },
      { value: "harmonics_upp", label: "선간전압" },
      { value: "harmonics_i", label: "상전류" },
    ];
    const views = [
      { value: "lines", label: "차수 선택" },     // 선택차수 트렌드
      { value: "spectrum", label: "시점 선택" },  // 특정시점 스펙트럼
    ];
    const phases = ["l1", "l2", "l3"];

    const measurement = ref("harmonics_i");
    const viewMode = ref("lines");
    const loading = ref(false);
    const errorMsg = ref("");

    const selectedOrders = ref([]);   // 최대 4
    const timeIdx = ref(0);           // 슬라이더 위치

    const matrix = reactive({ times: [], orders: [], phases: [], data: {} });
    const hasData = computed(() => matrix.times.length > 0 && matrix.orders.length > 0);

    // ── 차트 인스턴스 (3상) ──────────────────────────────────
    const chartEls = [];
    const charts = [null, null, null];
    const ensureChart = (i) => {
      if (!charts[i] && chartEls[i]) charts[i] = echarts.init(chartEls[i]);
      return charts[i];
    };

    const fmtTime = (iso) => {
      const d = new Date(iso);
      const MM = String(d.getMonth() + 1).padStart(2, "0");
      const dd = String(d.getDate()).padStart(2, "0");
      const HH = String(d.getHours()).padStart(2, "0");
      const mm = String(d.getMinutes()).padStart(2, "0");
      return `${MM}-${dd} ${HH}:${mm}`;
    };

    // ── 선택차수 트렌드 (x=시간, 선택 차수 라인) ──────────────
    const renderLines = () => {
      const timeLabels = matrix.times.map(fmtTime);
      phases.forEach((ph, i) => {
        const chart = ensureChart(i);
        if (!chart) return;
        const grid2d = matrix.data[ph] || [];
        const series = selectedOrders.value.map((ord, k) => {
          const oi = matrix.orders.indexOf(ord);
          const data = matrix.times.map((_, ti) => (grid2d[ti] ? grid2d[ti][oi] : null));
          return { name: `${ord}차`, type: "line", showSymbol: false, data, lineStyle: { color: PALETTE[k] }, itemStyle: { color: PALETTE[k] } };
        });
        chart.setOption({
          title: { text: `L${i + 1}`, left: "left", textStyle: { fontSize: 13 } },
          tooltip: { trigger: "axis" },
          legend: { top: 0, right: 0 },
          grid: { left: 55, right: 20, top: 30, bottom: 45 },
          xAxis: { type: "category", data: timeLabels, axisLabel: { rotate: 45, fontSize: 9 } },
          yAxis: { type: "value" },
          series,
        }, true);
        chart.resize();
      });
    };

    // ── 특정시점 스펙트럼 (x=차수, 막대) ──────────────────────
    const renderSpectrum = () => {
      const ti = timeIdx.value;
      const orderLabels = matrix.orders.map(String);
      const timeLabel = matrix.times[ti] ? fmtTime(matrix.times[ti]) : "";
      phases.forEach((ph, i) => {
        const chart = ensureChart(i);
        if (!chart) return;
        const row = (matrix.data[ph] || [])[ti] || [];
        const data = matrix.orders.map((_, oi) => row[oi]);
        chart.setOption({
          title: { text: `L${i + 1}  (${timeLabel})`, left: "left", textStyle: { fontSize: 13 } },
          tooltip: { trigger: "axis" },
          grid: { left: 55, right: 20, top: 30, bottom: 40 },
          xAxis: { type: "category", data: orderLabels, name: "차수", axisLabel: { fontSize: 9 } },
          yAxis: { type: "value" },
          series: [{ type: "bar", data, itemStyle: { color: "#7c3aed" } }],
        }, true);
        chart.resize();
      });
    };

    // Draw 버튼 — 현재 뷰/선택 기준으로 렌더
    const drawChart = () => {
      if (!hasData.value) return;
      if (viewMode.value === "lines") renderLines();
      else renderSpectrum();
    };

    // ── 상호작용 ─────────────────────────────────────────────
    const toggleOrder = (o) => {
      const idx = selectedOrders.value.indexOf(o);
      if (idx >= 0) selectedOrders.value.splice(idx, 1);
      else if (selectedOrders.value.length < 4) selectedOrders.value.push(o);
    };

    // ── 데이터 조회 (렌더는 Draw 에서) ───────────────────────
    const fetchData = async () => {
      if (!props.channel) return;
      loading.value = true;
      errorMsg.value = "";
      try {
        const res = await axios.post(`/api/getHarmonicsTrend/${props.channel}`, {
          startDate: props.startdate,
          endDate: props.enddate,
          measurement: measurement.value,
        });
        if (res.data && res.data.result) {
          matrix.times = res.data.times || [];
          matrix.orders = res.data.orders || [];
          matrix.phases = res.data.phases || [];
          matrix.data = res.data.matrix || {};
          timeIdx.value = Math.max(0, matrix.times.length - 1);
          if (selectedOrders.value.length === 0) {
            selectedOrders.value = [5, 7].filter((o) => matrix.orders.includes(o)).slice(0, 4);
          }
        } else {
          errorMsg.value = "조회 실패";
        }
      } catch (e) {
        console.error("Harmonics fetch failed:", e);
        errorMsg.value = "조회 실패";
      } finally {
        loading.value = false;
      }
    };

    const onResize = () => charts.forEach((c) => c && c.resize());

    // 신호종류·구간·채널 변경 → 매트릭스만 재조회 (그리기는 Draw)
    watch(() => [measurement.value, props.startdate, props.enddate, props.channel], fetchData);

    onMounted(() => {
      window.addEventListener("resize", onResize);
      fetchData();
    });
    onBeforeUnmount(() => {
      window.removeEventListener("resize", onResize);
      charts.forEach((c, i) => { if (c) { c.dispose(); charts[i] = null; } });
    });

    return {
      signalTypes, views, phases, measurement, viewMode, loading, errorMsg,
      matrix, hasData, selectedOrders, timeIdx, chartEls, fmtTime,
      toggleOrder, drawChart,
    };
  },
};
</script>

<style scoped>
.phase-chart {
  width: 100%;
  height: 240px;
  margin-bottom: 8px;
}
</style>
