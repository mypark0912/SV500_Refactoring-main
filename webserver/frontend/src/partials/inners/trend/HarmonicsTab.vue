<template>
  <div class="harmonics-tab">
    <!-- 컨트롤 바: 신호종류 콤보 + 뷰 토글 + Draw -->
    <div class="flex flex-wrap items-center gap-4 mb-3">
      <div class="flex items-center gap-2">
        <label class="text-sm text-gray-600 dark:text-gray-300">{{ t("trend.harmonicsTab.signalType") }}</label>
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
        {{ t("trend.harmonicsTab.draw") }}
      </button>
    </div>

    <!-- 뷰별 서브 컨트롤 (조회 조건이므로 Draw 전에도 표시) -->
    <div v-show="!loading" class="mb-3">
      <!-- 차수 선택 (최대 4) — 선택한 차수만 조회 -->
      <div v-show="viewMode === 'lines'" class="flex items-start gap-2">
        <span class="text-sm text-gray-600 dark:text-gray-300 mt-1 whitespace-nowrap">
          {{ t("trend.harmonicsTab.order") }} ({{ selectedOrders.length }}/4)
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

      <!-- 시점 슬라이더 — 슬라이더로 고르고 Draw 누르면 그 1시점 렌더 (시간축은 자동 로드) -->
      <div v-show="viewMode === 'spectrum'" class="flex items-center gap-3">
        <span class="text-sm text-gray-600 dark:text-gray-300 whitespace-nowrap">{{ t("trend.harmonicsTab.time") }}</span>
        <input type="range" min="0" :max="Math.max(0, spectrumTimes.length - 1)"
          v-model.number="specIdx"
          :disabled="spectrumTimes.length === 0" class="flex-1 max-w-md" />
        <span class="text-sm text-gray-700 dark:text-gray-200 whitespace-nowrap w-36">
          {{ spectrumTimes.length ? fmtTime(spectrumTimes[specIdx]) : (timesLoading ? t("trend.harmonicsTab.loadingTimes") : t("trend.harmonicsTab.noTimes")) }}
        </span>
      </div>
    </div>

    <!-- 상태 -->
    <div v-if="loading" class="text-sm text-gray-500 py-8 text-center">{{ t("trend.harmonicsTab.loading") }}</div>
    <div v-else-if="errorMsg" class="text-sm text-red-500 py-8 text-center">{{ errorMsg }}</div>
    <div v-else-if="!hasData" class="text-sm text-gray-500 py-8 text-center">{{ t("trend.harmonicsTab.noData") }}</div>

    <!-- 3상 차트 3개 (두 뷰 공용, Draw 시 렌더). loading 중에도 표시해 둬야
         nextTick 렌더 시점에 컨테이너가 보이는 상태라 차트 크기가 고정됨. -->
    <div v-show="!errorMsg && hasData">
      <div v-for="(ph, i) in phases" :key="ph"
        :ref="el => (chartEls[i] = el)" class="phase-chart"></div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, nextTick, onMounted, onBeforeUnmount } from "vue";
import { useI18n } from "vue-i18n";
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
    const { t } = useI18n();
    const signalTypes = computed(() => [
      { value: "harmonics_u", label: t("trend.harmonicsTab.phaseVoltage") },
      { value: "harmonics_upp", label: t("trend.harmonicsTab.lineVoltage") },
      { value: "harmonics_i", label: t("trend.harmonicsTab.phaseCurrent") },
    ]);
    const views = computed(() => [
      { value: "lines", label: t("trend.harmonicsTab.viewLines") },     // 선택차수 트렌드
      { value: "spectrum", label: t("trend.harmonicsTab.viewSpectrum") },  // 특정시점 스펙트럼
    ]);
    const phases = ["l1", "l2", "l3"];

    const measurement = ref("harmonics_i");
    const viewMode = ref("lines");
    const loading = ref(false);
    const errorMsg = ref("");

    const availableOrders = Array.from({ length: 62 }, (_, i) => i + 2); // 선택 가능한 차수 2~63 (정적)
    const selectedOrders = ref([5, 7]);  // 최대 4 (기본 5·7차)
    const spectrumTimes = ref([]);    // spectrum 슬라이더용 시간축 (뷰 진입 시 가볍게 자동 로드)
    const timesLoading = ref(false);  // 시간축 로딩 표시
    const specIdx = ref(0);           // 슬라이더 위치
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
      // 점이 1개면 선이 안 그려지므로 마커를 표시 (적은 포인트일 때도 보이게)
      const fewPoints = matrix.times.length <= 2;
      phases.forEach((ph, i) => {
        const chart = ensureChart(i);
        if (!chart) return;
        const grid2d = matrix.data[ph] || [];
        const series = selectedOrders.value.map((ord, k) => {
          const oi = matrix.orders.indexOf(ord);
          const data = matrix.times.map((_, ti) => (grid2d[ti] ? grid2d[ti][oi] : null));
          return { name: `${ord}${t("trend.harmonicsTab.orderUnit")}`, type: "line", showSymbol: fewPoints, symbolSize: 8, data, lineStyle: { color: PALETTE[k] }, itemStyle: { color: PALETTE[k] } };
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
          xAxis: { type: "category", data: orderLabels, name: t("trend.harmonicsTab.order"), axisLabel: { fontSize: 9 } },
          yAxis: { type: "value" },
          series: [{ type: "bar", data, itemStyle: { color: "#7c3aed" } }],
        }, true);
        chart.resize();
      });
    };

    // ── 상호작용 ─────────────────────────────────────────────
    const toggleOrder = (o) => {
      const idx = selectedOrders.value.indexOf(o);
      if (idx >= 0) selectedOrders.value.splice(idx, 1);
      else if (selectedOrders.value.length < 4) selectedOrders.value.push(o);
    };

    // ── 데이터 조회 — 뷰가 필요한 만큼만 (64차 전체 조회 방지) ──
    const post = (payload) =>
      axios.post(`/api/getHarmonicsTrend/${props.channel}`, {
        startDate: props.startdate, endDate: props.enddate,
        measurement: measurement.value, ...payload,
      });

    const applyMatrix = (d) => {
      matrix.times = d.times || [];
      matrix.orders = d.orders || [];
      matrix.phases = d.phases || [];
      matrix.data = d.matrix || {};
    };

    // lines: 선택차수(≤4)만 기간 트렌드
    const fetchLines = async () => {
      const res = await post({ mode: "lines", orders: selectedOrders.value });
      if (res.data && res.data.result) { applyMatrix(res.data); timeIdx.value = 0; }
      else errorMsg.value = t("trend.harmonicsTab.fetchFail");
    };

    // spectrum 시간축만 가볍게 조회 (1차수·1필드)
    const fetchTimes = async () => {
      const res = await post({ mode: "times" });
      spectrumTimes.value = (res.data && res.data.result) ? (res.data.times || []) : [];
    };

    // spectrum: 슬라이더가 가리키는 1시점의 전차수만
    const fetchSpectrum = async () => {
      const t = spectrumTimes.value[specIdx.value] || null;
      const res = await post({ mode: "spectrum", time: t });
      if (res.data && res.data.result) { applyMatrix(res.data); timeIdx.value = 0; }
      else errorMsg.value = t("trend.harmonicsTab.fetchFail");
    };

    // Draw 클릭 → 조회 후 렌더 (자동 조회 없음)
    const onDraw = async () => {
      if (!props.channel) return;
      loading.value = true; errorMsg.value = "";
      try {
        if (viewMode.value === "lines") {
          await fetchLines();
          if (!errorMsg.value && hasData.value) { await nextTick(); renderLines(); }
        } else {
          if (spectrumTimes.value.length === 0) {
            await fetchTimes();
            specIdx.value = Math.max(0, spectrumTimes.value.length - 1); // 최신 시점 기본
          }
          await fetchSpectrum();
          if (!errorMsg.value && hasData.value) { await nextTick(); renderSpectrum(); }
        }
      } catch (e) {
        console.error("Harmonics fetch failed:", e);
        errorMsg.value = t("trend.harmonicsTab.fetchFail");
      } finally {
        loading.value = false;
      }
    };

    const onResize = () => charts.forEach((c) => c && c.resize());

    // spectrum 뷰 진입 시 시간축만 가볍게 미리 로드 → 슬라이더 바로 활성화 (스펙트럼 데이터는 Draw에서)
    const loadSpectrumTimes = async () => {
      if (viewMode.value !== "spectrum" || !props.channel) return;
      timesLoading.value = true;
      try {
        await fetchTimes();
        specIdx.value = Math.max(0, spectrumTimes.value.length - 1); // 기본 최신 시점
      } catch (e) {
        console.error("Harmonics times fetch failed:", e);
        spectrumTimes.value = [];
      } finally {
        timesLoading.value = false;
      }
    };

    // 신호종류·구간·채널·뷰 변경 → 시간축 무효화 후, spectrum 뷰면 가벼운 시간축만 다시 로드
    watch(() => [measurement.value, props.startdate, props.enddate, props.channel, viewMode.value], () => {
      spectrumTimes.value = [];
      loadSpectrumTimes();
    });

    onMounted(() => {
      window.addEventListener("resize", onResize);
    });
    onBeforeUnmount(() => {
      window.removeEventListener("resize", onResize);
      charts.forEach((c, i) => { if (c) { c.dispose(); charts[i] = null; } });
    });

    return {
      t,
      signalTypes, views, phases, measurement, viewMode, loading, errorMsg,
      matrix, hasData, availableOrders, selectedOrders, spectrumTimes, timesLoading, specIdx,
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
