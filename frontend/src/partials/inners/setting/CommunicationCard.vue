<template>
  <div
    class="relative h-full flex flex-col bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-b-lg"
  >
    <div class="absolute top-0 left-0 right-0 h-0.5 bg-sky-500" aria-hidden="true"></div>
    <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700/60">
      <header class="flex items-center">
        <div class="w-6 h-6 rounded-full shrink-0 bg-sky-500 mr-3">
          <svg class="w-6 h-6 shrink-0 fill-current text-white" viewBox="0 0 24 24">
            <path d="M12 20c.83 0 1.5.67 1.5 1.5S12.83 23 12 23s-1.5-.67-1.5-1.5S11.17 20 12 20Zm-5.5-4.5a1 1 0 0 0 1.41 0 5.99 5.99 0 0 1 8.18 0 1 1 0 1 0 1.41-1.41 7.99 7.99 0 0 0-11 0 1 1 0 0 0 0 1.41Zm-3.54-3.54a1 1 0 0 0 1.41 0 10.93 10.93 0 0 1 15.44 0 1 1 0 0 0 1.42-1.42 12.93 12.93 0 0 0-18.28 0 1 1 0 0 0 0 1.42Z" />
          </svg>
        </div>
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">
          {{ t("config.plansPanel.communication.title") }}
        </h3>
      </header>
    </div>
    <div class="px-4 py-4 space-y-4 flex-1">
      <!-- ── TCP/IP 서브섹션 ── -->
      <div class="space-y-3">
        <div class="text-xs text-gray-800 dark:text-gray-100 font-semibold uppercase mb-1">TCP/IP</div>
      <!-- DHCP Toggle -->
      <div class="flex items-center justify-between">
        <label class="block text-sm font-medium">DHCP</label>
        <div
          class="relative inline-flex items-center cursor-pointer"
          @click="inputDict.tcpip.dhcp = inputDict.tcpip.dhcp === 1 ? 0 : 1"
        >
          <div
            class="w-11 h-6 rounded-full transition-colors duration-200"
            :class="inputDict.tcpip.dhcp === 1 ? 'bg-sky-500' : 'bg-gray-300 dark:bg-gray-600'"
          ></div>
          <div
            class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
            :class="inputDict.tcpip.dhcp === 1 ? 'translate-x-5' : 'translate-x-0'"
          ></div>
        </div>
      </div>
      <!-- DHCP 활성화 시 안내 메시지 -->
      <div
        v-if="inputDict.tcpip.dhcp === 1"
        class="flex items-center px-3 py-2 bg-sky-50 dark:bg-sky-900/20 border border-sky-200 dark:border-sky-700/50 rounded-md"
      >
        <svg class="w-4 h-4 text-sky-500 mr-2 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="text-xs text-sky-700 dark:text-sky-300">
          {{ t("config.plansPanel.dhcp") }}
        </span>
      </div>
      <!-- Static IP -->
      <template v-if="inputDict.tcpip.dhcp !== 1">
        <div class="flex gap-2">
          <div class="flex-1 min-w-0">
            <label class="block text-sm font-medium mb-2">
              {{ t("config.plansPanel.communication.ip") }}
            </label>
            <input v-model="inputDict.tcpip.ip_address" class="form-input w-full" type="text" maxlength="20" />
          </div>
          <div class="flex-1 min-w-0">
            <label class="block text-sm font-medium mb-2">
              {{ t("config.plansPanel.communication.sm") }}
            </label>
            <input v-model="inputDict.tcpip.subnet_mask" class="form-input w-full" type="text" maxlength="20" />
          </div>
        </div>
        <div class="flex gap-2">
          <div class="flex-1 min-w-0">
            <label class="block text-sm font-medium mb-2">
              {{ t("config.plansPanel.communication.gw") }}
            </label>
            <input v-model="inputDict.tcpip.gateway" class="form-input w-full" type="text" maxlength="20" />
          </div>
          <div class="flex-1 min-w-0">
            <label class="block text-sm font-medium mb-2">
              {{ t("config.plansPanel.communication.dns") }}
            </label>
            <input v-model="inputDict.tcpip.dnsserver" class="form-input w-full" type="text" maxlength="20" />
          </div>
        </div>
      </template>
      </div>

      <!-- 구분선 -->
      <hr class="border-gray-200 dark:border-gray-700/60" />

      <!-- ── Modbus TCP 서브섹션 ── -->
      <div class="space-y-3">
        <div class="text-xs text-gray-800 dark:text-gray-100 font-semibold uppercase mb-1">Modbus TCP</div>
        <div class="flex items-center gap-4">
          <!-- Log enable -->
          <div class="flex items-center gap-2 shrink-0">
            <label class="block text-sm font-medium">{{ t("config.plansPanel.communication.logEnable") }}</label>
            <div
              class="relative inline-flex items-center cursor-pointer"
              @click="inputDict.modbus.tcp_log = inputDict.modbus.tcp_log === 1 ? 0 : 1"
            >
              <div
                class="w-11 h-6 rounded-full transition-colors duration-200"
                :class="inputDict.modbus.tcp_log === 1 ? 'bg-sky-500' : 'bg-gray-300 dark:bg-gray-600'"
              ></div>
              <div
                class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
                :class="inputDict.modbus.tcp_log === 1 ? 'translate-x-5' : 'translate-x-0'"
              ></div>
            </div>
          </div>
          <!-- Port -->
          <div class="flex items-center gap-2 flex-1 min-w-0">
            <label class="block text-sm font-medium shrink-0">
              {{ t("config.plansPanel.modbus.tcp") }}
            </label>
            <input
              v-model.number="inputDict.modbus.tcp_port"
              class="form-input flex-1 min-w-0"
              type="number"
              maxlength="20"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { inject } from "vue";
import { useI18n } from "vue-i18n";

export default {
  name: "CommunicationCard",
  setup() {
    const { t } = useI18n();
    const inputDict = inject("inputDict");
    return { t, inputDict };
  },
};
</script>
