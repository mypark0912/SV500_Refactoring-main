<template>
    <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl relative">
      <!-- Loading overlay -->
      <div v-if="loading" class="absolute inset-0 bg-white/50 dark:bg-gray-800/50 flex items-center justify-center z-10">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-500"></div>
      </div>

      <div>
        <!-- Table -->
        <div class="overflow-x-auto">
          <div class="table-container">
            <table
              class="table-auto w-full dark:text-white divide-y divide-gray-100 dark:divide-gray-700/60"
            >
              <thead
                class="text-xs uppercase text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20 border-t border-gray-100 dark:border-gray-700/60"
              >
                <tr>
                  <th class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
                    <div class="font-semibold text-left">Timestamp</div>
                  </th>
                  <th class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
                    <div class="font-semibold text-left">Action</div>
                  </th>
                  <th class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
                    <div class="font-semibold text-left">Account</div>
                  </th>
                  <th class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
                    <div class="font-semibold text-left">UserRole</div>
                  </th>
                </tr>
              </thead>
              <LogTableItem :data="logdata" />
            </table>
          </div>
        </div>

        <!-- Pagination -->
        <div class="px-6 py-4 border-t border-gray-100 dark:border-gray-700/60">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <!-- Items per page -->
            <div class="flex items-center space-x-2 mb-4 sm:mb-0">

            </div>

            <!-- Page navigation -->
            <div class="flex items-center space-x-1">
              <!-- First -->
              <button
                @click="goToPage(1)"
                :disabled="currentPage === 1"
                class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                title="첫 페이지"
              >
                <svg class="w-4 h-4 fill-current text-gray-400" viewBox="0 0 16 16">
                  <path d="M11.854 3.646a.5.5 0 0 1 0 .708L8.207 8l3.647 3.646a.5.5 0 0 1-.708.708l-4-4a.5.5 0 0 1 0-.708l4-4a.5.5 0 0 1 .708 0zM4.5 4a.5.5 0 0 0-.5.5v7a.5.5 0 0 0 1 0v-7a.5.5 0 0 0-.5-.5z"/>
                </svg>
              </button>

              <!-- Prev -->
              <button
                @click="goToPage(currentPage - 1)"
                :disabled="currentPage === 1"
                class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                title="이전 페이지"
              >
                <svg class="w-4 h-4 fill-current text-gray-400" viewBox="0 0 16 16">
                  <path d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/>
                </svg>
              </button>

              <!-- Page numbers -->
              <div class="flex items-center space-x-1">
                <template v-for="page in visiblePages" :key="page">
                  <span v-if="page === '...'" class="px-2 py-1 text-gray-400">...</span>
                  <button
                    v-else
                    @click="goToPage(page)"
                    :class="[
                      'min-w-[2rem] px-2 py-1 rounded text-sm',
                      currentPage === page
                        ? 'bg-violet-500 text-white'
                        : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    ]"
                  >
                    {{ page }}
                  </button>
                </template>
              </div>

              <!-- Next -->
              <button
                @click="goToPage(currentPage + 1)"
                :disabled="currentPage >= totalPages"
                class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                title="다음 페이지"
              >
                <svg class="w-4 h-4 fill-current text-gray-400" viewBox="0 0 16 16">
                  <path d="M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
                </svg>
              </button>

              <!-- Last -->
              <button
                @click="goToPage(totalPages)"
                :disabled="currentPage >= totalPages"
                class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                title="마지막 페이지"
              >
                <svg class="w-4 h-4 fill-current text-gray-400" viewBox="0 0 16 16">
                  <path d="M4.146 3.646a.5.5 0 0 0 0 .708L7.793 8l-3.647 3.646a.5.5 0 0 0 .708.708l4-4a.5.5 0 0 0 0-.708l-4-4a.5.5 0 0 0-.708 0zM11.5 4a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 .5-.5z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, inject, computed, onMounted } from "vue";
  import { useI18n } from "vue-i18n";
  import LogTableItem from "./LogTableItem.vue";

  export default {
    name: "LogTable",
    components: {
      LogTableItem,
    },
    setup() {
      const { t } = useI18n();
      
      // inject
      const logdata = inject('logdata', ref([]));
      const totalCount = inject('totalCount', ref(0));
      const totalPages = inject('totalPages', ref(1));
      const currentPage = inject('currentPage', ref(1));
      const pageSize = inject('pageSize', ref(10));
      const loading = inject('loading', ref(false));
      const getLog = inject('getLog');

      const localPageSize = ref(10);

      // 초기 데이터 로드
      onMounted(() => {
        getLog(1, localPageSize.value);
      });

      // 페이지 변경
      const goToPage = (page) => {
        if (page >= 1 && page <= totalPages.value) {
          getLog(page, localPageSize.value);
        }
      };

      // 페이지 사이즈 변경
      const onPageSizeChange = () => {
        getLog(1, localPageSize.value);
      };

      // 표시할 페이지 번호
      const visiblePages = computed(() => {
        const total = totalPages.value;
        const current = currentPage.value;
        const pages = [];

        if (total <= 7) {
          for (let i = 1; i <= total; i++) {
            pages.push(i);
          }
        } else {
          if (current <= 3) {
            pages.push(1, 2, 3, 4, 5, '...', total);
          } else if (current >= total - 2) {
            pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total);
          } else {
            pages.push(1, '...', current - 1, current, current + 1, '...', total);
          }
        }

        return pages;
      });

      return {
        t,
        logdata,
        totalCount,
        totalPages,
        currentPage,
        loading,
        localPageSize,
        visiblePages,
        goToPage,
        onPageSizeChange,
      };
    },
  };
  </script>
  
  <style scoped>
  .bg-white.dark\:bg-gray-800 {
    min-height: 700px;
    display: flex;
    flex-direction: column;
  }
  
  .bg-white.dark\:bg-gray-800 > div {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  
  .overflow-x-auto {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  
  .table-container {
    position: relative;
    display: flex;
    flex-direction: column;
    flex: 1;
  }
  </style>