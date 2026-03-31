<template>
  <div class="detail-card">
    <!-- 헤더 - 컴팩트 인라인 -->
    <div class="card-header">
      <span class="card-title">
        {{ mode === 'pq' ? t('dashboard.diagnosis.pq') : t('dashboard.diagnosis.diagnostic') }}
      </span>
    </div>

    <!-- 상태 인디케이터 - 1줄 가로 배치 -->
    <div class="status-section">
      <div class="status-indicators">
        <template v-for="(item, idx) in displayedStatuses" :key="idx">
          <div
            class="status-item"
            :class="{ 'status-active': stData.devStatus === idx + 1 }"
          >
            <div class="status-icon-wrapper">
              <div
                class="status-icon"
                :class="[
                  item.fill,
                  stData.devStatus === idx + 1 ? 'status-icon-active' : 'status-icon-inactive'
                ]"
              >
                <div
                  v-if="(stData.devStatus === idx + 1) && stData.devStatus > 1"
                  class="status-pulse"
                  :class="item.fill"
                ></div>
              </div>
            </div>
            <span
              class="status-text"
              :class="stData.devStatus === idx + 1 ? 'status-text-active' : 'status-text-inactive'"
            >
              {{ item.text }}
            </span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  data: Object,
  channel: String,
  mode: String,
})

const { t } = useI18n()
const stData = computed(() => props.data)

const displayedStatuses = computed(() => {
  const fills = [
    'bg-emerald-500',
    'bg-amber-400',
    'bg-orange-500',
    'bg-red-500',
  ]

  const texts = props.mode === 'diagnosis'
    ? [
        t('dashboard.diagnosis.st1'),
        t('dashboard.diagnosis.st2'),
        t('dashboard.diagnosis.st3'),
        t('dashboard.diagnosis.st4'),
      ]
    : [
        t('dashboard.diagnosis.pqfe1'),
        t('dashboard.diagnosis.pqfe2'),
        t('dashboard.diagnosis.pqfe3'),
        t('dashboard.diagnosis.pqfe4'),
      ]

  return texts.map((text, i) => ({
    text,
    fill: fills[i],
  }))
})
</script>

<style scoped>
.detail-card {
  @apply col-span-full sm:col-span-6 xl:col-span-6;
  @apply bg-gray-50 dark:bg-gray-700/50 rounded-lg overflow-hidden;
}

.card-header {
  @apply px-3 py-1.5;
  @apply bg-gray-100 dark:bg-gray-600 border-b border-gray-200 dark:border-gray-500;
}

.card-title {
  @apply text-sm font-bold text-gray-700 dark:text-white;
}

.status-section {
  @apply px-2 py-2;
}

.status-indicators {
  @apply grid grid-cols-4 gap-1;
}

.status-item {
  @apply flex flex-col items-center justify-center gap-1.5;
  @apply py-2 px-1 rounded-md transition-all duration-300;
}

.status-active {
  @apply transform scale-105;
}

.status-icon-wrapper {
  @apply relative;
}

.status-icon {
  @apply w-5 h-5 rounded-full transition-all duration-300;
  @apply flex items-center justify-center;
  @apply shadow-sm;
}

.status-icon-active {
  @apply shadow-md transform scale-110;
}

.status-icon-inactive {
  @apply bg-gray-300 dark:bg-gray-600;
  @apply opacity-50;
}

.status-pulse {
  @apply absolute inset-0 rounded-full;
  @apply animate-ping opacity-75;
}

.status-text {
  @apply text-xs font-medium text-center leading-tight;
}

.status-text-active {
  @apply text-gray-900 dark:text-white font-semibold;
}

.status-text-inactive {
  @apply text-gray-500 dark:text-gray-400;
}

@media (max-width: 640px) {
  .detail-card {
    @apply col-span-full;
  }
  .status-indicators {
    @apply grid-cols-4 gap-1;
  }
}
</style>
