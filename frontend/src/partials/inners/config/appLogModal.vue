<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/50" @click="close"></div>
    
    <!-- Modal -->
    <div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[80vh] flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="20" height="20" stroke-width="2" class="text-gray-500 dark:text-gray-400">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14,2 14,8 20,8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          <h3 class="text-lg font-semibold text-gray-800 dark:text-gray-100">
            {{ displayName }} Logs
          </h3>
          <span v-if="logSource" class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
            {{ logSource }}
          </span>
        </div>
        
        <div class="flex items-center gap-3">
          <!-- 줄 수 선택 -->
          <select
            v-model="lines"
            class="h-8 w-32 px-3 text-xs border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300"
            @change="fetchLogs"
          >
            <option :value="5">5 lines</option>
            <option :value="10">10 lines</option>
            <option :value="20">20 lines</option>
            <option :value="50">50 lines</option>
          </select>
          
          <!-- 새로고침 버튼 -->
          <button
            class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
            @click="fetchLogs"
            :disabled="loading"
            title="Refresh"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="18" height="18" stroke-width="2" :class="{ 'animate-spin': loading }">
              <path d="M20 11a8.1 8.1 0 0 0 -15.5 -2m-.5 -4v4h4"></path>
              <path d="M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4"></path>
            </svg>
          </button>
          
          <!-- 닫기 버튼 -->
          <button
            class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
            @click="close"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="18" height="18" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Body -->
      <div class="flex-1 overflow-auto p-5">
        <!-- 로딩 -->
        <div v-if="loading" class="flex items-center justify-center py-10">
          <svg class="animate-spin h-8 w-8 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        
        <!-- 에러 -->
        <div v-else-if="error" class="text-center py-10">
          <div class="text-red-500 dark:text-red-400 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
          </div>
          <p class="text-gray-600 dark:text-gray-400">{{ error }}</p>
        </div>
        
        <!-- 로그 내용 -->
        <div v-else-if="logLines.length > 0" class="font-mono text-sm">
          <div
            v-for="(line, index) in logLines"
            :key="index"
            class="py-1 px-2 hover:bg-gray-50 dark:hover:bg-gray-700/50 rounded border-b border-gray-100 dark:border-gray-700/50 last:border-0"
            :class="getLineClass(line)"
          >
            {{ line }}
          </div>
        </div>
        
        <!-- 로그 없음 -->
        <div v-else class="text-center py-10 text-gray-500 dark:text-gray-400">
          No logs available
        </div>
      </div>
      
      <!-- Footer -->
      <div class="px-5 py-3 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400">
        <div class="flex items-center justify-between">
          <span v-if="fileName">File: {{ fileName }}</span>
          <span v-else-if="logSource === 'journal'">Source: systemd journal</span>
          <span>{{ logLines.length }} lines</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, computed } from 'vue';
import axios from 'axios';

export default {
  name: 'LogModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    service: {
      type: String,
      default: ''
    }
  },
  emits: ['close'],
  
  setup(props, { emit }) {
    const loading = ref(false);
    const error = ref('');
    const logLines = ref([]);
    const fileName = ref('');
    const logSource = ref('');
    const lines = ref(10);

    // 서비스별 API 매핑
    const serviceConfig = {
      'Core': { api: 'Core', display: 'Core' },
      'WebServer': { api: 'WebServer', display: 'WebServer' },
      'A35': { api: 'A35', display: 'A35' },
      'SmartSystems': { api: 'SmartSystems', display: 'SmartSystem', logType: 'ss' },
      'SmartAPI': { api: 'SmartSystems', display: 'Smart RestAPI', logType: 'api' },
      'MQTTClient': { api: 'mqClient', display: 'MQTT Client' },
      'frpc': { api: 'frpc', display: 'FRP Tunnel' }
    };

    const displayName = computed(() => {
      return serviceConfig[props.service]?.display || props.service;
    });

    watch(() => props.isOpen, (newVal) => {
      if (newVal && props.service) {
        fetchLogs();
      }
    });

    const fetchLogs = async () => {
      if (!props.service) return;
      
      loading.value = true;
      error.value = '';
      logLines.value = [];
      fileName.value = '';
      logSource.value = '';

      try {
        const config = serviceConfig[props.service];
        if (!config) {
          error.value = 'Unknown service';
          return;
        }

        let url = `/config/applog/recent/${config.api}?lines=${lines.value}`;
        
        // SmartSystems / SmartAPI 로그 타입 추가
        if (config.logType) {
          url += `&log_type=${config.logType}`;
        }

        const response = await axios.get(url);
        
        if (response.data.success) {
          logLines.value = response.data.lines || [];
          fileName.value = response.data.file || '';
          logSource.value = response.data.source || 'file';
        } else {
          error.value = response.data.message || 'Failed to fetch logs';
        }
      } catch (err) {
        error.value = err.message || 'Failed to fetch logs';
      } finally {
        loading.value = false;
      }
    };

    const getLineClass = (line) => {
      const lower = line.toLowerCase();
      if (lower.includes('error') || lower.includes('❌') || lower.includes('fail')) {
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
      }
      if (lower.includes('warning') || lower.includes('⚠️') || lower.includes('warn')) {
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20';
      }
      if (lower.includes('success') || lower.includes('✅')) {
        return 'text-green-600 dark:text-green-400';
      }
      return 'text-gray-700 dark:text-gray-300';
    };

    const close = () => {
      emit('close');
    };

    return {
      loading,
      error,
      logLines,
      fileName,
      logSource,
      displayName,
      lines,
      fetchLogs,
      getLineClass,
      close
    };
  }
};
</script>