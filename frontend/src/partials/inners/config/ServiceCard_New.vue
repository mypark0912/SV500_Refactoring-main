<template>
  <div class="col-span-full xl:col-span-6 2xl:col-span-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-lg">
    <div class="flex flex-col h-full p-5">
      <div class="grow">
        <!-- Header -->
        <header class="flex items-center justify-between mb-4">
          <div class="flex items-center">
            <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold mr-4">{{ itemDict[item] }}</h3>
            
            <!-- 상태 뱃지 -->
            <span v-if="health" class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-green-500/20 text-green-700 font-semibold">
              Running
            </span>
            <span v-else class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-red-500/20 text-red-700 font-semibold">
              Stopped
            </span>
          </div>
          
          <div class="flex items-center gap-2">
            <!-- 버전 정보 -->
            <span v-if="versionInfo && !['Redis', 'InfluxDB'].includes(item)" class="text-sm text-gray-500 dark:text-gray-400 font-mono">
              v{{ versionInfo }}
            </span>
            
            <!-- 로그 버튼 -->
            <button
              v-if="hasLog && isNtek"
              class="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
              @click="openLog"
              title="View Logs"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="20" height="20" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10,9 9,9 8,9"/>
              </svg>
            </button>
          </div>
        </header>
        
        <!-- 버튼 영역 -->
        <div class="flex justify-center space-x-4">
          <button
            class="btn h-9 px-5 bg-green-900 text-green-100 hover:bg-green-800 dark:bg-green-100 dark:text-green-800 dark:hover:bg-white"
            @click="start"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="24" height="24" stroke-width="1.25">
              <path d="M7 4v16l13 -8z"></path>
            </svg>
            &nbsp;Start
          </button>
          
          <button
            class="btn h-9 px-5 bg-yellow-900 text-yellow-100 hover:bg-yellow-800 dark:bg-yellow-100 dark:text-yellow-800 dark:hover:bg-white"
            @click="restart"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="24" height="24" stroke-width="1.25">
              <path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4"></path>
              <path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4"></path>
            </svg>
            &nbsp;Restart
          </button>
          
          <button
            :disabled="item === 'WebServer'"
            class="btn h-9 px-5 bg-red-900 text-red-100 hover:bg-red-800 dark:bg-red-100 dark:text-red-800 dark:hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
            @click="stop"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="24" height="24" stroke-width="1.25">
              <path d="M5 5m0 2a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v10a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2z"></path>
            </svg>
            &nbsp;Stop
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, computed, inject } from 'vue'
import axios from 'axios';
import { useAuthStore } from "@/store/auth"; // ✅ Pinia Store 사용

export default {
  name: 'ServiceCard',
  props: ['item', 'version'],
  emits: ['service-done', 'open-log'],
  
  setup(props, { emit }) {
    const authStore = useAuthStore();
    const item = ref(props.item);
    const versionInfo = ref(props.version);
    const health = ref(false);
    const message = ref('');

    const Status = inject('sysStatus');
    const isNtek = computed(() => {
      const userName = authStore.getUser;
      const role = authStore.getUserRole;
      if (userName == "ntek" && role == "3") return true;
      else return false;
    });
    const itemDict = ref({
      "Redis": "Redis",
      "InfluxDB": "InfluxDB",
      "SmartSystems": "SmartSystem",
      "SmartAPI": "Smart RestAPI",
      "Core": "Core",
      "WebServer": "WebServer",
      "A35": "A35",
      "MQTTClient": "MQTT Client",
      "frpc": "FRP Tunnel"
    });

    // 로그 지원 서비스 (파일 또는 journal)
    const logServices = ['Core', 'WebServer', 'A35', 'SmartSystems', 'SmartAPI', 'MQTTClient', 'frpc'];
    
    const hasLog = computed(() => logServices.includes(item.value));

    watch(() => props.item, (newVal) => {
      item.value = newVal;
    }, { immediate: true });

    watch(() => props.version, (newVal) => {
      versionInfo.value = newVal || '';
    }, { immediate: true });

    watch(Status, () => {
      const statusMap = {
        "Redis": "redis",
        "InfluxDB": "influxdb",
        "SmartSystems": "smartsystem",
        "SmartAPI": "smartapi",
        "Core": "core",
        "WebServer": "webserver",
        "A35": "a35",
        "MQTTClient": "mqClient",
        "frpc": "frpc"
      };
      
      const key = statusMap[item.value];
      if (key && Status?.value) {
        health.value = Status.value[key] || false;
      }
    }, { immediate: true });

    const serviceOp = async (cmd) => {
      try {
        const response = await axios.get(`/setting/SysService/${cmd}/${item.value}`);
        //console.log(response.data);
        if (response.data.success) {
          message.value = `${item.value} ${cmd}!`;
        } else {
          message.value = `${item.value} ${cmd} Failed`;
        }
      } catch (error) {
        message.value = `${item.value} ${cmd} Failed`;
      }
      emit('service-done', message.value);
    };

    const start = () => serviceOp('start');
    const restart = () => serviceOp('restart');
    const stop = () => serviceOp('stop');
    
    const openLog = () => {
      emit('open-log', item.value);
    };

    return {
      item,
      itemDict,
      health,
      versionInfo,
      hasLog,
      start,
      stop,
      restart,
      openLog,
      isNtek,
    }
  }
}
</script>