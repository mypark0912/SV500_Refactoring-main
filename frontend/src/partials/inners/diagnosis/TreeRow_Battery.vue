<template>
    <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
    <td class="px-4 py-1">
        <div :style="{ paddingLeft: level * 20 + 'px' }" class="flex items-center text-sm" :class="{'font-bold': isParent}">
        <button
            v-if="item.children"
            @click="expanded = !expanded"
            class="mr-1 text-gray-500 hover:text-gray-800"
        >
            <component
            :is="expanded ? ChevronDownIcon : ChevronRightIcon"
            class="w-4 h-4"
            />
        </button>
        <span v-else class="w-5"></span>
        {{ itemTitle }}
        </div>
    </td>
    <td class="px-4 py-1 text-sm">{{ item.AssemblyID }}</td>
    <td class="px-4 py-1 text-sm">{{ formatValue(item.Value) }}</td>
    <!-- 상태: 텍스트 + 배터리 -->
    <td class="px-4 py-1">
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold whitespace-nowrap" :class="statusTextClass">
          {{ statusLabel }}
        </span>
        <div class="battery-body">
          <div class="battery-segments">
            <div
              v-for="seg in 4"
              :key="seg"
              class="battery-seg"
              :class="[
                `seg-${seg}`,
                seg <= item.Status && item.Status > 0 ? 'active' : 'inactive'
              ]"
            ></div>
          </div>
        </div>
      </div>
    </td>
    <td class="px-4 py-1 text-sm"> {{ item.children ? descStr : '-' }}</td>
    </tr>
    <template v-if="item.children && expanded">
        <TreeRow_Battery
        v-for="child in item.children"
        :key="child.id"
        :item="child"
        :level="level + 1"
        :expanded="false"
        :mode="mode"
        />
  </template>
</template>

  <script setup>
  import { ref, computed, onMounted, watch } from 'vue'
  import { ChevronRightIcon, ChevronDownIcon } from '@heroicons/vue/20/solid'
  import { useI18n } from 'vue-i18n'

  const props = defineProps({
    item: { type: Object, required: true },
    level: { type: Number, default: 0 },
    expanded : { type: Boolean, default: false},
    mode : { type: String, default:''},
  })

  const isParent = computed(() => props.item.children || props.item.isParent)

  const expanded = ref(false);
  const mode = ref('');
  const { t } = useI18n();
  const descStr = ref('')
  const itemTitle = ref('')
  const { locale } = useI18n();

  onMounted(()=>{
    expanded.value = false;
    mode.value = props.mode;
  });

  watch(() => locale.value, (newLocale) => {
    if (props.item?.Descriptions?.[newLocale]) {
      if(props.item.Status > 1)
        descStr.value = props.item.Descriptions[newLocale];
      else
        descStr.value = "-";
    } else {
      descStr.value = "-";
    }
    if(props.item?.Titles?.[newLocale]){
      itemTitle.value = props.item.Titles[newLocale];
    }else{
      itemTitle.value = props.item.Title;
    }
  }, { immediate: true });

  const formatValue = (value) => {
    return (value == null || value == NaN || value == 'NaN') ? '-' : parseFloat(value).toFixed(2);
  }

  /* 상태 텍스트 */
  const statusLabel = computed(() => {
    if (props.mode === 'PowerQuality') {
      switch (props.item.Status) {
        case 1: return t('diagnosis.tabContext.pqfe1')
        case 2: return t('diagnosis.tabContext.pqfe2')
        case 3: return t('diagnosis.tabContext.pqfe3')
        case 4: return t('diagnosis.tabContext.pqfe4')
        default: return t('diagnosis.tabContext.pqfe0')
      }
    }
    switch (props.item.Status) {
      case 1: return t('diagnosis.tabContext.st1')
      case 2: return t('diagnosis.tabContext.st2')
      case 3: return t('diagnosis.tabContext.st3')
      case 4: return t('diagnosis.tabContext.st4')
      default: return t('diagnosis.tabContext.st0')
    }
  })

  /* 상태 텍스트 색상 */
  const statusTextClass = computed(() => {
    switch (props.item.Status) {
      case 1: return 'text-green-700 dark:text-green-300'
      case 2: return 'text-yellow-700 dark:text-yellow-300'
      case 3: return 'text-orange-700 dark:text-orange-300'
      case 4: return 'text-red-700 dark:text-red-300'
      default: return 'text-gray-500 dark:text-gray-400'
    }
  })
  </script>

  <style scoped>
  .battery-body {
    width: 60px;
    height: 22px;
    border-radius: 4px;
    border: 2px solid #d1d5db;
    padding: 2px;
    display: flex;
    align-items: center;
  }
  :is(.dark) .battery-body {
    border-color: #4b5563;
  }
  .battery-segments {
    display: flex;
    gap: 2px;
    width: 100%;
    height: 100%;
  }
  .battery-seg {
    flex: 1;
    border-radius: 2px;
    transition: all 0.3s ease;
  }
  .battery-seg.seg-1 { background-color: #22c55e; }
  .battery-seg.seg-2 { background-color: #eab308; }
  .battery-seg.seg-3 { background-color: #f97316; }
  .battery-seg.seg-4 { background-color: #ef4444; }
  .battery-seg.inactive {
    background-color: #9ca3af;
    opacity: 0.3;
    filter: grayscale(80%);
  }
  :is(.dark) .battery-seg.inactive {
    background-color: #6b7280;
  }
  </style>
