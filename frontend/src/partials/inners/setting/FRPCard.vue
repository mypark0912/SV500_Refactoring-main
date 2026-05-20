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
      <div class="flex items-center gap-2">
        <label class="block text-sm font-medium shrink-0 w-24">externalPort</label>
        <input
          v-model="inputDict.FRP.externalport"
          class="form-input flex-1 min-w-0"
          type="number"
          placeholder="port"
        />
      </div>
      <div class="flex items-center gap-2">
        <label class="block text-sm font-medium shrink-0 w-24">externalUrl</label>
        <input
          v-model="inputDict.FRP.url"
          class="form-input flex-1 min-w-0"
          type="text"
          placeholder="url"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, computed } from "vue";

const inputDict = inject("inputDict");

const visible = computed(() => inputDict.value.FRP?.Use === 1);
</script>
