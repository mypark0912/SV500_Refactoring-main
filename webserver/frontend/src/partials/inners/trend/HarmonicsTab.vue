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

      <button @click="onDraw"
        :disabled="loading || (viewMode === 'lines' && selectedOrders.length === 0)"
        class="px-4 py-1.5 text-sm rounded bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-40">
        Draw
      </button>
    </div>

    <!-- 뷰별 서브 컨트롤 (조회 조건이므로 Draw 전에도 표시) -->
    <div v-show="!loading" class="mb-3">
      <!-- 차수 선택 (최대 4) — 선택한 차수만 조회 -->
      <div v-show="viewMode === 'lines'" class="flex items-start gap-2">
        <span class="text-sm text-gray-600 dark:text-gray-300 mt-1 whitespace-nowrap">
          차수 ({{ selectedOrders.length }}/4)
        </span>
        <div class="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
          <button v-for="o in availableOrders" :key="o"
            @click="toggleOrder(o)"
            class="px-2 py-0.5 text-xs rounded border"
            :class="selectedOrders.includes(o)
              ? 'bg-violet-600 text-white border-violet-600'
              : 'bg-white text-gray-600 border-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600'">
            {{ o }}
          </button>
        </div>
      </div>

      <!-- 시점 (최신 기본 + 직접 입력) — 1개 시점만 조회 -->
      <div v-show="viewMode === 'spectrum'" class="flex items-center gap-3">
        <span class="text-sm text-gray-600 dark:text-gray-300 whitespace-nowrap">시점</span>
        <input type="datetime-local" v-model="spectrumTime"
          class="form-input text-sm rounded border-gray-300 dark:bg-gray-700 dark:border-gray-600" />
        <button @click="spectrumTime = ''"
          class="px-2 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 dark:text-gray-300">
          최신
        </button>
        <span class="text-sm text-gray-500 whitespace-nowrap">{{ spectrumTime ? "" : "(범위 내 최신 시점)" }}</span>
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
import { ref, reactive, computed, onMounted, onBeforeUnmount } from "vue";
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

    const availableOrders = Array.from({ length: 62 }, (_, i) => i + 2); // 선택 가능한 차수 2~63 (정적)
    const selectedOrders = ref([5, 7]);  // 최대 4 (기본 5·7차)
    const spectrumTime = ref("");     // "" = 범위 내 최신, 값 있으면 해당 시점
    const timeIdx = ref(0);           // spectrum 응답은 1시점 → 항상 0

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

    // ── 데이터 조회 — 뷰가 필요한 만큼만 (64차 전체 조회 방지) ──
    //   lines    : 선택차수(≤4)만 기간 트렌드
    //   spectrum : 1개 시점(최신/지정)의 전차수
    const fetchData = async () => {
      if (!props.channel) return;
      loading.value = true;
      errorMsg.value = "";
      try {
        const payload = {
          startDate: props.startdate,
          endDate: props.enddate,
          measurement: measurement.value,
          mode: viewMode.value,
        };
        if (viewMode.value === "lines") {
          payload.orders = selectedOrders.value;
        } else {
          // datetime-local(로컬) → ISO(UTC). 비우면 최신.
          payload.time = spectrumTime.value ? new Date(spectrumTime.value).toISOString() : null;
        }
        const res = await axios.post(`/api/getHarmonicsTrend/${props.channel}`, payload);
        if (res.data && res.data.result) {
          matrix.times = res.data.times || [];
          matrix.orders = res.data.orders || [];
          matrix.phases = res.data.phases || [];
          matrix.data = res.data.matrix || {};
          timeIdx.value = Math.max(0, matrix.times.length - 1);
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

    // Draw 클릭 → 조회 후 렌더 (자동 조회 없음)
    const onDraw = async () => {
      await fetchData();
      if (!errorMsg.value && hasData.value) drawChart();
    };

    const onResize = () => charts.forEach((c) => c && c.resize());

    onMounted(() => {
      window.addEventListener("resize", onResize);
    });
    onBeforeUnmount(() => {
      window.removeEventListener("resize", onResize);
      charts.forEach((c, i) => { if (c) { c.dispose(); charts[i] = null; } });
    });

    return {
      signalTypes, views, phases, measurement, viewMode, loading, errorMsg,
      matrix, hasData, availableOrders, selectedOrders, spectrumTime, timeIdx,
      chartEls, fmtTime, toggleOrder, onDraw,
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
