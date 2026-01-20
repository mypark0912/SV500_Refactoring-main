<template>
  <div class="premium-dashboard-card">
    <!-- 헤더 섹션 -->
    <div class="card-header">
      <header class="header-content">
        <h2 class="card-title">{{ t("dashboard.diagnosis.title2") }}</h2>
      </header>
    </div>

    <!-- 변압기 정보 섹션 -->
    <div class="equipment-section">
      <div class="flex items-center justify-between">
        <!-- 장비 정보 - 왼쪽 -->
        <div class="flex items-center gap-3">
          <div class="equipment-avatar">
            <img
              class="avatar-image"
              :src="motorImageSrc"
              :alt="stData.devType"
            />
          </div>
          <div class="equipment-info">
            <h3 class="equipment-name">{{ stData.devNickname }}</h3>
            <span class="equipment-type">{{ stData.devType }}</span>
          </div>
        </div>

        <!-- 가동중 배지 - 오른쪽 -->
        <div class="equipment-status">
          <span
            class="status-badge"
            :class="isRunning ? 'status-running' : 'status-stopped'"
          >
            <span class="status-indicator"></span>
            <span class="status-text">
              {{
                isRunning
                  ? t("dashboard.singleinfo.running")
                  : t("dashboard.singleinfo.stopped")
              }}
            </span>
          </span>
        </div>
      </div>
    </div>

    <!-- 온도 / 부하율 / 누설전류 섹션 (Transformer 타입일 때만) -->
    <div
      class="metrics-grid-section"
      v-if="stData.devType?.includes('Transformer')"
    >
      <!-- 1행: 부하율 + 누설전류 -->
      <div class="metrics-row-2">
        <!-- 부하율 -->
        <div class="metric-card">
          <div class="metric-icon">⚡</div>
          <div class="metric-content">
            <div class="metric-label">
              {{ t("dashboard.transDiag.LoadFactor") }}
            </div>
            <div class="metric-main">
              <span class="metric-value">{{ LoadRate }}</span>
              <span class="metric-unit">%</span>
            </div>
          </div>
        </div>

        <!-- 누설전류 -->
        <div class="metric-card">
          <div class="metric-icon">💧</div>
          <div class="metric-content">
            <div class="metric-label">{{ t("dashboard.transDiag.Ig") }}</div>
            <div class="metric-main">
              <span class="metric-value">{{
                transData.Ig?.toFixed(2) ?? "-"
              }}</span>
              <span class="metric-unit">mA</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 2행: Primary 온도 (Main 채널에서 가져옴, 데이터 있을 때만) -->
      <div class="metrics-row-3" v-if="hasPrimaryTempData">
        <div
          v-for="(label, index) in ['R', 'S', 'T']"
          :key="'primary-temp-' + index"
          class="metric-card"
        >
          <div class="metric-icon">🌡️</div>
          <div class="metric-content">
            <div class="metric-label">Primary Temp {{ label }}</div>
            <div class="metric-main">
              <span class="metric-value">{{
                primaryTempData?.[index]?.toFixed(2) ?? "-"
              }}</span>
              <span class="metric-unit">℃</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 3행: Secondary 온도 (Sub 채널에서 가져옴, 데이터 있을 때만) -->
      <div class="metrics-row-3" v-if="hasSecondaryTempData">
        <div
          v-for="(label, index) in ['R', 'S', 'T']"
          :key="'secondary-temp-' + index"
          class="metric-card"
        >
          <div class="metric-icon">🌡️</div>
          <div class="metric-content">
            <div class="metric-label">Secondary Temp {{ label }}</div>
            <div class="metric-main">
              <span class="metric-value">{{
                transData.Temp?.[index]?.toFixed(2) ?? "-"
              }}</span>
              <span class="metric-unit">℃</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 진단 정보 섹션 -->
    <div class="status-item-section" v-if="DiagEnable">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <!-- 왼쪽 컬럼: 설비진단 + 전력품질진단 -->
        <div class="flex flex-col gap-4">
          <StatusItem :channel="channel" :data="stData" :mode="'diagnosis'" />
          <StatusItem :channel="channel" :data="pqData" :mode="'pq'" />
        </div>

        <!-- 오른쪽 컬럼: 이벤트진단 -->
        <div class="h-full">
          <div class="detail-card h-full flex flex-col">
            <div class="detail-header flex-shrink-0">
              <h3 class="detail-title">{{ t("dashboard.diagnosis.event") }}</h3>
            </div>
            <div class="status-section flex-grow flex flex-col justify-between">
              <div class="space-y-2">
                <div
                  v-for="(item, index) in eventData"
                  :key="item.Name"
                  class="data-row"
                >
                  <span class="data-label">{{ item.Title }}</span>
                  <div
                    class="status-badge-event"
                    :class="getStatusColor2(getStatusText(item.Status))"
                  >
                    {{ getStatusCText(getStatusText(item.Status)) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { watch, ref, computed, onMounted, onUnmounted } from "vue";
import { useI18n } from "vue-i18n";
import DashboardCard_THD from "./DashboardCard_THD.vue";
import StatusItem from "./StatusItem_Trans.vue";
import { useSetupStore } from "@/store/setup";
import { useRealtimeStore } from "@/store/realtime";

// 이미지 import
import motorImg from "@/images/motor_m.png";
import fanImg from "@/images/fan_m.png";
import pumpImg from "@/images/pump_m.png";
import compImg from "@/images/comp_m.png";
import powerImg from "@/images/power_m.png";
import defaultImg from "@/images/cleaned_logo.png";
import transImg from "@/images/trans.png";

export default {
  name: "PremiumDashboardCard_Integrated",
  props: {
    channel: String,
    data: Object,
    diagData: Object,
  },
  components: {
    DashboardCard_THD,
    StatusItem,
  },
  setup(props) {
    const { t } = useI18n();

    const channel = ref(props.channel);
    const store = useRealtimeStore();
    const setupStore = useSetupStore();

    // 실시간 데이터
    const data2 = computed(() => {
      if (!props.channel) return {};
      const channelName =
        props.channel?.toLowerCase() === "main" ? "Main" : "Sub";
      return store.getChannelData(channelName) || {};
    });

    const channelStatus = computed(() => setupStore.getChannelSetting);
    const asset = computed(() => setupStore.getAssetConfig);

    // Main과 Sub 데이터 모두 가져오기
    const meterDictMain = computed(() => store.getChannelData("Main") || {});
    const meterDictSub = computed(() => store.getChannelData("Sub") || {});

    const computedChannel = computed(() => {
      return channel.value == "Main" || channel.value == "main"
        ? "Main"
        : "Sub";
    });

    // 가동 상태
    const isRunning = ref(true);

    // 진단 데이터
    const stData = computed(() => {
      if (props.diagData?.data?.Diagnostic) {
        const chType =
          channel.value == "main"
            ? asset.value.assetType_main
            : asset.value.assetType_sub;
        const chNick =
          channel.value == "main"
            ? asset.value.assetNickname_main
            : asset.value.assetNickname_sub;

        return {
          devName: channel.value == "main" ? "Main" : "Sub",
          devType: chType,
          devStatus: props.diagData.data.Diagnostic.status,
          devNickname: chNick,
          runhour: props.diagData.runhours || 0,
          Ig: 0,
        };
      }
      return {
        devName: "",
        devType: "",
        devStatus: -2,
        devNickname: "",
        runhour: 0,
        Ig: 0,
      };
    });

    const pqData = computed(() => {
      if (props.diagData?.data?.PQ) {
        return {
          devName: props.diagData.data.PQ.item || "",
          devStatus: props.diagData.data.PQ.status || -2,
        };
      }
      return { devName: "", devStatus: -2 };
    });

    const eventData = computed(() => props.diagData?.eventTree || []);

    // 변압기 관련 데이터 (Sub 채널에서 가져옴 - Secondary 온도, 누설전류, 피상전력)
    const transData = computed(() => {
      return {
        Temp: meterDictSub.value.Temp,
        Ig: meterDictSub.value.Ig,
        Stotal: meterDictSub.value.S4,
      };
    });

    // Primary 온도 데이터 (Main 채널에서 가져옴)
    const primaryTempData = computed(() => {
      return meterDictMain.value.Temp;
    });

    // Primary 온도 데이터 유무 (Main 채널)
    const hasPrimaryTempData = computed(() => {
      return primaryTempData.value?.length > 0;
    });

    // Secondary 온도 데이터 유무 (Sub 채널)
    const hasSecondaryTempData = computed(() => {
      return transData.value?.Temp?.length > 0;
    });

    // 부하율 계산
    const LoadRate = ref(0);
    const LoadFactor = computed(() => {
      let kva = -1;
      if (stData.value.devType?.includes("Transformer")) {
        // Sub 채널 기준으로 kva 가져오기
        kva = setupStore.getSkva;
      }
      return kva;
    });

    watch(
      () => [LoadFactor.value, transData.value?.Stotal],
      ([newLoadFactor, newStotal]) => {
        if (newLoadFactor > 0 && newStotal) {
          LoadRate.value = ((newStotal / 1000 / newLoadFactor) * 100).toFixed(
            2,
          );
        }
      },
      { immediate: true },
    );

    // 장비 이미지
    const motorImageSrc = computed(() => {
      switch (stData.value.devType) {
        case "Motor":
        case "MotorFeed":
          return motorImg;
        case "Pump":
          return pumpImg;
        case "Fan":
          return fanImg;
        case "Compressor":
          return compImg;
        case "PSupply":
        case "PowerSupply":
          return powerImg;
        case "PrimaryTransformer":
        case "Transformer":
          return transImg;
        default:
          return defaultImg;
      }
    });

    const DiagEnable = ref(false);

    // 상태 관련 함수들
    const getStatusColor2 = (status) => {
      switch (status) {
        case "OK":
          return "bg-green-500/20 text-green-700 font-semibold dark:bg-green-600/40 dark:text-green-300";
        case "Low":
          return "bg-yellow-500/20 text-yellow-700 font-semibold dark:bg-yellow-600/40 dark:text-yellow-300";
        case "Medium":
          return "bg-orange-500/20 text-orange-700 font-semibold dark:bg-orange-600/40 dark:text-orange-300";
        case "High":
          return "bg-red-500/20 text-red-700 font-semibold dark:bg-red-600/40 dark:text-red-300";
        default:
          return "bg-gray-500/20 text-gray-700 font-semibold dark:bg-gray-600/40 dark:text-gray-300";
      }
    };

    const getStatusCText = (status) => {
      switch (status) {
        case "OK":
          return t("diagnosis.tabContext.pqfe1");
        case "Low":
          return t("diagnosis.tabContext.pqfe2");
        case "Medium":
          return t("diagnosis.tabContext.pqfe3");
        case "High":
          return t("diagnosis.tabContext.pqfe4");
        default:
          return t("diagnosis.tabContext.pqfe0");
      }
    };

    const getStatusText = (status) => {
      switch (status) {
        case 1:
          return "OK";
        case 2:
          return "Low";
        case 3:
          return "Medium";
        case 4:
          return "High";
        default:
          return "No Data";
      }
    };

    // DiagEnable 감시
    watch(
      () => channelStatus.value,
      () => {
        if (channel.value == "main")
          DiagEnable.value = channelStatus.value.MainDiagnosis;
        else DiagEnable.value = channelStatus.value.SubDiagnosis;
      },
      { immediate: true },
    );

    onMounted(async () => {
      await setupStore.checkSetting();
    });

    return {
      channel,
      data2,
      stData,
      pqData,
      transData,
      primaryTempData,
      DiagEnable,
      t,
      eventData,
      getStatusText,
      getStatusColor2,
      getStatusCText,
      motorImageSrc,
      isRunning,
      hasPrimaryTempData,
      hasSecondaryTempData,
      LoadRate,
      computedChannel,
    };
  },
};
</script>

<style scoped>
.premium-dashboard-card {
  @apply col-span-full sm:col-span-6 xl:col-span-6;
  @apply bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900;
  @apply shadow-lg rounded-xl border border-gray-200/50 dark:border-gray-700/50;
  @apply backdrop-blur-sm;
  @apply transition-all duration-300 hover:shadow-xl;
}

/* 헤더 섹션 */
.card-header {
  @apply p-3;
  @apply bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-blue-900/20 dark:to-purple-900/20;
  @apply rounded-t-xl;
}

.header-content {
  @apply flex justify-between items-center;
}

.card-title {
  @apply text-lg font-bold text-gray-900 dark:text-white;
  @apply bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent;
}

.channel-info {
  @apply flex items-center;
}

.channel-text {
  @apply text-xs font-semibold text-gray-400 dark:text-gray-300 uppercase;
}

/* ========== 변압기 정보 섹션 ========== */
.equipment-section {
  @apply px-5 py-4;
}

.equipment-avatar {
  @apply relative flex-shrink-0;
}

.avatar-image {
  @apply w-12 h-12 rounded-lg object-cover;
  @apply shadow-sm border border-gray-200 dark:border-gray-600;
}

.equipment-info {
  @apply flex flex-col justify-center;
}

.equipment-name {
  @apply text-base font-bold text-gray-800 dark:text-gray-100;
  @apply leading-tight;
}

.equipment-type {
  @apply text-xs text-gray-500 dark:text-gray-400;
  @apply px-2 py-0.5 mt-1 rounded-full;
  @apply bg-gray-100 dark:bg-gray-700;
  @apply inline-block w-fit;
}

/* 상태 배지 */
.equipment-status {
  @apply flex items-center flex-shrink-0;
}

.status-badge {
  @apply flex items-center gap-1.5 px-3 py-1.5;
  @apply rounded-full font-semibold text-xs;
  @apply border-2 transition-all duration-300;
  @apply shadow-sm whitespace-nowrap;
}

.status-indicator {
  @apply w-2 h-2 rounded-full animate-pulse;
}

.status-running {
  @apply bg-green-50 dark:bg-green-900/30;
  @apply border-green-500 dark:border-green-600;
  @apply text-green-700 dark:text-green-300;
}

.status-running .status-indicator {
  @apply bg-green-500;
}

.status-stopped {
  @apply bg-gray-50 dark:bg-gray-700/30;
  @apply border-gray-400 dark:border-gray-500;
  @apply text-gray-700 dark:text-gray-300;
}

.status-stopped .status-indicator {
  @apply bg-gray-400 animate-none;
}

/* ========== 온도/부하율/누설전류 그리드 섹션 ========== */
.metrics-grid-section {
  @apply px-5 py-4 space-y-3;
}

.metrics-row-2 {
  @apply grid grid-cols-2 gap-3;
}

.metrics-row-3 {
  @apply grid grid-cols-3 gap-3;
}

.metric-card {
  @apply flex items-center gap-3 p-3 rounded-xl;
  @apply border border-gray-200 dark:border-gray-700;
  @apply bg-white dark:bg-gray-800;
  @apply transition-all duration-200;
  @apply hover:shadow-md hover:scale-[1.02];
}

.metric-icon {
  @apply text-2xl flex-shrink-0;
}

.metric-content {
  @apply flex flex-col;
}

.metric-label {
  @apply text-xs font-medium text-gray-500 dark:text-gray-400;
  @apply mb-1;
}

.metric-main {
  @apply flex items-baseline gap-1;
}

.metric-value {
  @apply text-xl font-bold text-gray-900 dark:text-white;
}

.metric-unit {
  @apply text-sm font-medium text-gray-500 dark:text-gray-400;
}

/* ========== 진단 정보 섹션 ========== */
.status-item-section {
  @apply px-5 py-4;
}

/* 상세 카드 */
.detail-card {
  @apply bg-white dark:bg-gray-800 rounded-lg;
  @apply border border-gray-200 dark:border-gray-700;
  @apply shadow-sm hover:shadow-md transition-all duration-200;
  @apply overflow-hidden;
}

.detail-header {
  @apply p-3 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-600;
}

.detail-title {
  @apply text-sm font-semibold text-gray-900 dark:text-gray-100;
}

/* 상태 섹션 */
.status-section {
  @apply px-4 py-4;
}

/* 데이터 행 */
.data-row {
  @apply flex items-center justify-between;
  @apply px-3 py-2.5;
  @apply rounded-lg transition-all duration-200;
  @apply hover:bg-gray-50 dark:hover:bg-gray-700/30;
}

.data-label {
  @apply text-sm font-medium text-gray-700 dark:text-gray-300;
}

/* 이벤트 상태 뱃지 */
.status-badge-event {
  @apply text-sm rounded-full px-3 py-1;
  @apply min-w-[80px] text-center;
  @apply font-medium shadow-sm;
}

/* ========== 반응형 ========== */
@media (max-width: 768px) {
  .metrics-row-2 {
    @apply grid-cols-2;
  }

  .metrics-row-3 {
    @apply grid-cols-3;
  }

  .metric-card {
    @apply p-2;
  }

  .metric-icon {
    @apply text-xl;
  }

  .metric-value {
    @apply text-lg;
  }

  .status-item-section .grid {
    @apply grid-cols-1;
  }
}

@media (max-width: 480px) {
  .metrics-row-2 {
    @apply grid-cols-1;
  }

  .metrics-row-3 {
    @apply grid-cols-1;
  }
}
</style>