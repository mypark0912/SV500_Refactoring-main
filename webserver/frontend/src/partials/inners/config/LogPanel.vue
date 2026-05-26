<template>
    <div class="grow">
      <div class="p-6">
        <h2 class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-5">
          {{ t("config.maintenance.header2") }}
        </h2>
  
        <div class="mb-6">
          <div
            class="mt-4 flex justify-end gap-2 border-b border-gray-200 dark:border-gray-700/60 p-2 pb-4"
          >
            <button
              @click="deleteAllLogs"
              class="btn h-7 px-3 bg-red-600 text-white hover:bg-red-700 rounded-md flex items-center text-xs transition-colors"
            >
              <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete All
            </button>
          </div>
        </div>
  
        <section class="pb-6 border-b border-gray-200 dark:border-gray-700/60">
          <div
            class="flex flex-col sm:flex-row sm:space-x-6 md:flex-col md:space-x-0 xl:flex-row xl:space-x-6 mt-3"
          >
            <div class="w-full">
              <LogTable />
            </div>
          </div>
        </section>
      </div>
    </div>
  </template>
  
  <script>
  import { useI18n } from "vue-i18n";
  import LogTable from "./LogTable.vue";
  import { ref, provide } from "vue";
  import axios from "axios";
  
  export default {
    name: "LogPanel",
    components: {
        LogTable,
    },
    setup() {
      const { t } = useI18n();
      const logdata = ref([]);
      const totalCount = ref(0);
      const totalPages = ref(1);
      const currentPage = ref(1);
      const pageSize = ref(10);
      const loading = ref(false);

      const getLog = async (page = 1, size = 10) => {
        loading.value = true;
        try {
          const response = await axios.get(`/config/getLog`, {
            params: {
              page: page,
              page_size: size
            }
          });
          
          if (response.data.result == 1) {
            logdata.value = response.data.data;
            totalCount.value = response.data.total;
            totalPages.value = response.data.total_pages;
            currentPage.value = response.data.page;
          } else {
            logdata.value = [];
            totalCount.value = 0;
            totalPages.value = 1;
          }
        } catch (error) {
          console.log("데이터 가져오기 실패:", error);
        } finally {
          loading.value = false;
        }
      }

      // provide
      provide("logdata", logdata);
      provide("totalCount", totalCount);
      provide("totalPages", totalPages);
      provide("currentPage", currentPage);
      provide("pageSize", pageSize);
      provide("loading", loading);
      provide("getLog", getLog);
  
      const deleteAllLogs = async () => {
        if (!confirm("모든 로그를 삭제하시겠습니까?")) return;
        try {
          const response = await axios.delete("/config/deleteLog");
          if (response.data.result == 1) {
            alert("모든 로그가 삭제되었습니다.");
            getLog(1, pageSize.value);
          } else {
            alert("로그 삭제에 실패했습니다.");
          }
        } catch (error) {
          console.error("로그 삭제 실패:", error);
          alert("로그 삭제 중 오류가 발생했습니다.");
        }
      };

      return {
        t,
        deleteAllLogs,
      };
    },
  };
  </script>