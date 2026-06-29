<template>
  <!-- FRP (Tunneling) -->
  <div
    v-if="visible"
    class="relative col-span-full xl:col-span-3 flex flex-col bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
  >
    <div
      class="absolute top-0 left-0 right-0 h-0.5 bg-emerald-500"
      aria-hidden="true"
    ></div>
    <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700/60">
      <header class="flex items-center">
        <div class="w-6 h-6 rounded-full shrink-0 bg-emerald-500 mr-3 flex items-center justify-center">
          <!-- 양방향 화살표 (터널) 아이콘 -->
          <svg
            class="w-4 h-4 fill-current text-white"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M3 8a1 1 0 0 1 1-1h13.586l-2.293-2.293a1 1 0 1 1 1.414-1.414l4 4a1 1 0 0 1 0 1.414l-4 4a1 1 0 0 1-1.414-1.414L17.586 9H4a1 1 0 0 1-1-1zm18 8a1 1 0 0 1-1 1H6.414l2.293 2.293a1 1 0 0 1-1.414 1.414l-4-4a1 1 0 0 1 0-1.414l4-4a1 1 0 1 1 1.414 1.414L6.414 15H20a1 1 0 0 1 1 1z" />
          </svg>
        </div>
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">Tunneling</h3>
      </header>
    </div>
    <div class="px-4 py-3 space-y-3">
      <!-- 터널링 모드(Public/External) + 외부 서버 설정 버튼 -->
      <div class="flex items-center gap-2">
        <label class="block text-sm font-medium shrink-0 w-16">Mode</label>
        <select
          v-model="inputDict.FRP.type"
          class="form-select flex-1 min-w-0"
        >
          <option value="Public">Public</option>
          <option value="External">External</option>
        </select>
        <button
          type="button"
          class="shrink-0 px-3 py-2 text-sm rounded-md bg-emerald-500 text-white disabled:opacity-40 disabled:cursor-not-allowed"
          :disabled="inputDict.FRP.type !== 'External'"
          @click="showServer = true"
        >
          {{ t("config.plansPanel.tunneling.serverSettings") }}
        </button>
      </div>
      <!-- externalPort | externalUrl — 한 줄(수평) -->
      <div class="flex gap-2">
        <div class="flex-1 min-w-0">
          <label class="block text-sm font-medium mb-1.5">externalPort</label>
          <input
            v-model="inputDict.FRP.externalport"
            class="form-input w-full min-w-0"
            type="number"
            placeholder="port"
          />
        </div>
        <div class="flex-1 min-w-0">
          <label class="block text-sm font-medium mb-1.5">externalUrl</label>
          <input
            v-model="inputDict.FRP.url"
            class="form-input w-full min-w-0"
            type="text"
            placeholder="url"
          />
        </div>
      </div>
    </div>

    <!-- 외부 터널링 서버 설정 모달 (External 일 때 host/token 입력) -->
    <div
      v-if="showServer"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click.self="showServer = false"
    >
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-80 max-w-[90vw] p-5 space-y-3">
        <h4 class="text-base font-semibold text-gray-800 dark:text-gray-100">{{ t("config.plansPanel.tunneling.serverModalTitle") }}</h4>
        <div>
          <label class="block text-sm font-medium mb-1.5">host</label>
          <input
            v-model="inputDict.FRP.host"
            class="form-input w-full"
            type="text"
            placeholder="host"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1.5">token</label>
          <input
            v-model="inputDict.FRP.token"
            class="form-input w-full"
            type="password"
            placeholder="token"
          />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1.5">{{ t("config.plansPanel.tunneling.allowIP") }}</label>
          <input
            v-model="inputDict.FRP.allowIP"
            class="form-input w-full"
            type="text"
            placeholder="0.0.0.0/0"
          />
          <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ t("config.plansPanel.tunneling.allowIPHint") }}</p>
        </div>
        <div class="flex justify-end pt-2">
          <button
            type="button"
            class="px-3 py-2 text-sm rounded-md bg-emerald-500 text-white"
            @click="showServer = false"
          >
            {{ t("config.plansPanel.tunneling.confirm") }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, computed, ref } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const inputDict = inject("inputDict");

const visible = computed(() => inputDict.value.FRP?.Use === 1);
const showServer = ref(false);
</script>
