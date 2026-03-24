<template>
  <div class="card-wrap">
    <div class="card-header">
      <h3 class="card-title">알람 / 이벤트 로그</h3>
      <span class="card-channel">
        {{ channel === 'Main' ? t('dashboard.meter.subtitle_main') : t('dashboard.meter.subtitle_sub') }}
      </span>
    </div>
    <div class="card-body">
      <div class="log-table-wrap">
        <table class="log-table">
          <thead>
            <tr>
              <th>시간</th>
              <th>유형</th>
              <th>내용</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in logItems" :key="idx">
              <td class="col-time">{{ item.time }}</td>
              <td>
                <span class="badge" :class="'badge-' + item.level">{{ item.type }}</span>
              </td>
              <td class="col-msg">{{ item.message }}</td>
              <td>
                <span class="status-tag" :class="'tag-' + item.status">{{ item.statusText }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

export default {
  name: 'MeasCard_EventLog',
  props: {
    channel: { type: String, default: 'Main' },
  },
  setup() {
    const { t } = useI18n()
    const logItems = ref([
      { time: '14:32:10', type: '경고', level: 'warn', message: '전압 불평형률 2.8% 초과', status: 'active', statusText: '발생' },
      { time: '14:28:45', type: '알람', level: 'danger', message: 'THD-I 8.2% 기준 초과', status: 'active', statusText: '발생' },
      { time: '14:15:22', type: '정보', level: 'info', message: '역률 95% 이상 회복', status: 'resolved', statusText: '복구' },
      { time: '13:58:03', type: '경고', level: 'warn', message: '전류 불평형률 2.1% 초과', status: 'resolved', statusText: '복구' },
      { time: '13:42:17', type: '알람', level: 'danger', message: '순간 전압 강하 감지', status: 'resolved', statusText: '복구' },
      { time: '13:30:00', type: '정보', level: 'info', message: '시스템 정상 가동 확인', status: 'resolved', statusText: '확인' },
    ])

    return { t, logItems }
  },
}
</script>

<style scoped>
.card-wrap {
  @apply col-span-full sm:col-span-6 xl:col-span-5;
  @apply bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900;
  @apply shadow-lg rounded-xl border border-gray-200/50 dark:border-gray-700/50;
  @apply overflow-hidden;
}
.card-header {
  @apply flex justify-between items-center px-4 py-2.5;
}
.card-title {
  @apply text-base font-bold text-gray-800 dark:text-white flex items-center gap-2;
}
.card-title::before {
  content: '';
  @apply w-1 h-4 rounded-full bg-teal-500 inline-block flex-shrink-0;
}
.card-channel {
  @apply text-gray-500 dark:text-gray-500;
  font-size: 10px;
}
.card-body {
  @apply px-4 py-3;
}

/* Table */
.log-table-wrap {
  @apply overflow-y-auto;
  max-height: 220px;
}
.log-table {
  @apply w-full text-left;
  border-collapse: collapse;
}
.log-table thead th {
  @apply text-sm font-semibold text-gray-500 dark:text-gray-400 pb-2;
  @apply border-b border-gray-200 dark:border-gray-700;
  @apply sticky top-0 bg-white dark:bg-gray-800;
}
.log-table tbody tr {
  @apply border-b border-gray-100 dark:border-gray-700/50;
}
.log-table tbody td {
  @apply py-2 text-sm text-gray-600 dark:text-gray-300;
}
.col-time {
  @apply tabular-nums text-gray-600 dark:text-gray-400 whitespace-nowrap pr-2 text-sm;
}
.col-msg {
  @apply truncate max-w-[160px];
}

/* Badge */
.badge {
  @apply text-sm font-semibold px-1.5 py-0.5 rounded;
}
.badge-danger {
  @apply bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400;
}
.badge-warn {
  @apply bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400;
}
.badge-info {
  @apply bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400;
}

/* Status tag */
.status-tag {
  @apply text-sm font-medium;
}
.tag-active {
  @apply text-red-500 dark:text-red-400;
}
.tag-resolved {
  @apply text-green-500 dark:text-green-400;
}
</style>
