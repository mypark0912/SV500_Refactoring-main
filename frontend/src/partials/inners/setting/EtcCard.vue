<template>
  <div
    class="relative h-full flex flex-col bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
  >
    <div class="absolute top-0 left-0 right-0 h-0.5 bg-amber-500" aria-hidden="true"></div>
    <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700/60">
      <header class="flex items-center">
        <div class="w-6 h-6 rounded-full shrink-0 bg-amber-500 mr-3">
          <svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24">
            <path d="M12 4a8 8 0 100 16 8 8 0 000-16zm0 12a1 1 0 110-2 1 1 0 010 2zm1-4h-2V8h2v4z" />
          </svg>
        </div>
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">{{ t("config.plansPanel.etc.title") }}</h3>
      </header>
    </div>
    <div class="px-4 py-4 space-y-3">
      <div>
        <label class="block text-sm font-medium mb-1.5">PF Sign</label>
        <select
          v-model.number="inputDict.pf_sign"
          class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
        >
          <option :value="0">IEC</option>
          <option :value="1">IEEE</option>
        </select>
      </div>
      <div class="flex gap-2">
        <div class="flex-1 min-w-0">
          <label class="block text-sm font-medium mb-1.5">VA type</label>
          <select
            v-model.number="inputDict.va_type"
            class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option :value="0">RMS</option>
            <option :value="1">vector</option>
          </select>
        </div>
        <div class="flex-1 min-w-0">
          <label class="block text-sm font-medium mb-1.5">Unbalance</label>
          <select
            v-model.number="inputDict.unbalance"
            class="form-select w-full bg-white border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            <option :value="0">Nema</option>
            <option :value="1">Sequence Components</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { inject } from "vue";
import { useI18n } from "vue-i18n";

export default {
  name: "EtcCard",
  setup() {
    const { t } = useI18n();
    const inputDict = inject("inputDict");
    return { t, inputDict };
  },
};
</script>
