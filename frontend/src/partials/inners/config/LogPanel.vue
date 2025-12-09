<template>
    <div class="grow">
      <div class="p-6">
        <h2 class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-5">
          {{ t("config.maintenance.header2") }}
        </h2>
  
        <div class="mb-6">
          <div
            class="mt-4 flex gap-2 border-b border-gray-200 dark:border-gray-700/60 p-2 pb-4"
          >
          </div>
        </div>
  
        <section class="pb-6 border-b border-gray-200 dark:border-gray-700/60">
          <div
            class="flex flex-col space-y-10 sm:flex-row sm:space-x-6 sm:space-y-0 md:flex-col md:space-x-0 md:space-y-10 xl:flex-row xl:space-x-6 xl:space-y-0 mt-9"
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
  
      return {
        t,
      };
    },
  };
  </script>