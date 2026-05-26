<template>
  <div class="stage-wrapper" :class="{ 'stage-wrapper--wide': wide }">
    <div class="stage-title" :class="{ 'stage-title--selected': selected, 'stage-title--wide': wide }">
      {{ stage.label }}
    </div>
    <button
      class="stage-button"
      :class="{ 'stage-button--selected': selected, 'stage-button--wide': wide }"
      @click="$emit('select')"
    >
      <!-- 알림 뱃지 -->
      <div class="stage-badge stage-badge--danger" v-if="alertCount > 0">{{ alertCount }}</div>
      <div class="stage-badge stage-badge--warn" v-else-if="warnCount > 0">{{ warnCount }}</div>

      <!-- 아이콘 -->
      <div class="stage-icon" :style="{ color: iconColor }">
        <!-- source: AC 전원 -->
        <svg v-if="stageKey === 'source'" width="28" height="28" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="6" y="14" width="36" height="20" rx="3" />
          <line x1="4" y1="20" x2="6" y2="20" /><line x1="4" y1="28" x2="6" y2="28" />
          <line x1="42" y1="20" x2="44" y2="20" /><line x1="42" y1="28" x2="44" y2="28" />
          <text x="24" y="27" text-anchor="middle" font-size="10" fill="currentColor" stroke="none" font-weight="bold">AC</text>
        </svg>
        <!-- inverter -->
        <svg v-else-if="stageKey === 'inverter'" width="28" height="28" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="8" y="10" width="32" height="28" rx="3" />
          <path d="M16 28 L22 18 L22 28 L28 18" />
          <circle cx="34" cy="16" r="2" fill="currentColor" stroke="none" />
        </svg>
        <!-- motor-elec -->
        <svg v-else-if="stageKey === 'motor-elec'" width="28" height="28" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="24" cy="24" r="14" /><circle cx="24" cy="24" r="6" />
          <line x1="24" y1="10" x2="24" y2="14" /><line x1="24" y1="34" x2="24" y2="38" />
          <line x1="10" y1="24" x2="14" y2="24" /><line x1="34" y1="24" x2="38" y2="24" />
          <path d="M15 15 L18 18" /><path d="M30 30 L33 33" />
        </svg>
        <!-- motor-mech -->
        <svg v-else width="28" height="28" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="20" cy="24" r="12" /><circle cx="20" cy="24" r="4" />
          <line x1="32" y1="24" x2="44" y2="24" />
          <circle cx="20" cy="24" r="1.5" fill="currentColor" stroke="none" />
          <path d="M34 20 L34 28" /><path d="M38 18 L38 30" />
        </svg>
      </div>

      <!-- 상태 도트 -->
      <div class="stage-dots">
        <div
          v-for="(item, i) in stage.items"
          :key="i"
          class="stage-dot"
          :style="{ backgroundColor: statusColor(item.status), opacity: item.status === 0 ? 0.3 : 1 }"
        />
      </div>
    </button>
  </div>
</template>

<script>
const COLORS = { 0: '#c4c4c4', 1: '#16a34a', 2: '#ca8a04', 3: '#ea580c', 4: '#dc2626' }

export default {
  name: 'StageButton',
  props: {
    stageKey: { type: String, required: true },
    stage: { type: Object, required: true },
    selected: { type: Boolean, default: false },
    wide: { type: Boolean, default: false },
  },
  emits: ['select'],
  computed: {
    alertCount() {
      return this.stage.items.filter(i => i.status >= 3).length
    },
    warnCount() {
      return this.stage.items.filter(i => i.status === 2).length
    },
    iconColor() {
      if (this.selected) return '#3b82f6'
      const worst = Math.max(0, ...this.stage.items.map(i => i.status))
      return worst >= 2 ? COLORS[worst] : '#64748b'
    },
  },
  methods: {
    statusColor(status) {
      return COLORS[status] || COLORS[0]
    }
  }
}
</script>

<style scoped>
.stage-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.stage-wrapper--wide {
  align-items: stretch;
}
.stage-title {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  text-align: center;
}
.stage-title--wide {
  text-align: left;
  padding-left: 2px;
}
.stage-title--selected {
  color: #1e40af;
}
.stage-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px 20px;
  min-width: 100px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background-color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  outline: none;
}
.stage-button--wide {
  flex-direction: row;
  justify-content: flex-start;
  gap: 12px;
  padding: 12px 20px;
  min-width: 200px;
}
.stage-button--selected {
  border: 2px solid #3b82f6;
  background-color: #f0f7ff;
  box-shadow: 0 2px 12px rgba(59,130,246,0.15);
}
.stage-button:hover:not(.stage-button--selected) {
  border-color: #cbd5e1;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}
.stage-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stage-badge--danger {
  background-color: #dc2626;
  box-shadow: 0 2px 6px rgba(220,38,38,0.35);
}
.stage-badge--warn {
  background-color: #ca8a04;
  box-shadow: 0 2px 6px rgba(202,138,4,0.3);
}
.stage-icon {
  flex-shrink: 0;
  transition: color 0.2s;
}
.stage-dots {
  display: flex;
  gap: 3px;
}
.stage-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
</style>
