<template>
    <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
    <td class="px-4 py-1 align-top">
        <div class="flex items-start text-sm" :class="{'font-bold': isParent}">
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
        {{ itemTitle }}
        </div>
    </td>
    <td class="px-4 py-1 text-sm align-top"> {{ item.Value }} </td>
    <td class="px-4 py-1 align-top">

        <div class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center" :class="mode === 'Fault' ? getStatusColor2(getStatusText(item.Status)) : statusTextClass">
          {{ getStatusCText(getStatusText(item.Status)) }}
        </div>

    </td>
    <td v-if="mode !='Event'" class="px-4 py-1 text-sm align-top"> {{ descStr }} </td>
    </tr>
    <template v-if="item.children && expanded">
        <TreeRow
        v-for="child in item.children"
        :key="child.id"
        :item="child"
        :level="level + 1"
        :expanded="false"
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

  const statusTextClass = computed(() => {
    switch (props.item.Status) {
      case 1: return 'bg-green-500/20 text-green-700 font-semibold dark:bg-green-600/40 dark:text-green-300'
      case 2: return 'bg-yellow-500/20 text-yellow-700 font-semibold dark:bg-yellow-600/40 dark:text-yellow-300'
      case 3: return 'bg-orange-500/20 text-orange-700 font-semibold dark:bg-orange-600/40 dark:text-orange-300'
      case 4: return 'bg-red-500/20 text-red-700 font-semibold dark:bg-red-600/40 dark:text-red-300'
      default: return 'bg-gray-500/20 text-gray-500 font-semibold dark:bg-gray-600/40 dark:text-gray-400'
    }
  })

  const expanded = ref(false);
  const mode = ref('');
  const { t } = useI18n();
  const { locale } = useI18n();
  const descStr = ref('')
  const itemTitle = ref('')
  onMounted(()=>{
    expanded.value = false;
    mode.value = props.mode;
  });

  watch([locale, () => props.item], ([newLocale, newItem]) => {
  if (newItem?.Descriptions?.[newLocale]) {
    descStr.value = newItem.Descriptions[newLocale];
  } else {
    descStr.value = "-";
  }
  if (newItem?.Titles?.[newLocale]) {
    itemTitle.value = newItem.Titles[newLocale];
  } else {
    itemTitle.value = newItem?.Title ?? '';
  }
}, { immediate: true, deep: true });

  const getStatusColor2 = (status) => {
        switch (status) {
          case 'OK': return 'bg-green-500/20 text-green-700 font-semibold dark:bg-green-600/40 dark:text-green-300';
          case 'Low': return 'bg-yellow-500/20 text-yellow-700 font-semibold dark:bg-yellow-600/40 dark:text-yellow-300';
          case 'Medium': return 'bg-yellow-500/20 text-yellow-700 font-semibold dark:bg-yellow-600/40 dark:text-yellow-300';
          case 'High': return 'bg-yellow-500/20 text-yellow-700 font-semibold dark:bg-yellow-600/40 dark:text-yellow-300';
          default: return 'bg-gray-500/20 text-gray-700 font-semibold dark:bg-gray-600/40 dark:text-gray-300';
        }
      }; 

      const getStatusCText = (status) => {
        switch (status) {
          case 'OK': return t('diagnosis.tabContext.pqfe1');
          case 'Low': return t('diagnosis.tabContext.pqfe2');
          case 'Medium': return t('diagnosis.tabContext.pqfe3');
          case 'High': return t('diagnosis.tabContext.pqfe4');
          default: return t('diagnosis.tabContext.pqfe0');
        }
      };

      const getStatusText = (status) => {
        switch (status) {
          case 1: return 'OK';
          case 2: return 'Low';
          case 3: return 'Medium';
          case 4: return 'High';
          default: return 'No Data';
        }
      }
  
  </script>