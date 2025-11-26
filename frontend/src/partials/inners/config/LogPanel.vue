<template>
    <div class="grow">
      <!-- Panel body -->
      <div class="p-6">
        <h2 class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-5">
          {{ t("config.maintenance.header2") }}
        </h2>
  
        <!-- General -->
        <div class="mb-6">
          <!-- Filters -->
          <div
            class="mt-4 flex gap-2 border-b border-gray-200 dark:border-gray-700/60 p-2 pb-4"
          >
          </div>
        </div>
  
        <!-- Connected Apps cards -->
        <section class="pb-6 border-b border-gray-200 dark:border-gray-700/60">
          <div
            class="flex flex-col space-y-10 sm:flex-row sm:space-x-6 sm:space-y-0 md:flex-col md:space-x-0 md:space-y-10 xl:flex-row xl:space-x-6 xl:space-y-0 mt-9"
          >
            <div class="w-full">
              <LogTable />
  
            </div>
          </div>
        </section>
        <section></section>
      </div>
    </div>
  </template>
  
  <script>
  import { useI18n } from "vue-i18n";
  import LogTable from "./LogTable.vue";
  import { ref, provide, onMounted } from "vue";
  import axios from "axios";
  
  export default {
    name: "LogPanel",
    components: {
        LogTable,
    },
    setup() {
      const { t } = useI18n();
      const sidebarOpen = ref(false);
      const logdata = ref([]);

      onMounted(async()=>{
        await getLog();
      });
      const getLog = async()=>{
        try {
          //const ch = 'Fan';
          const response = await axios.get(`/config/getLog`);
        //   console.log(response.data);
          if (response.data.result == 1) {
            logdata.value = response.data.data;
          }else{
            console.log('No Data');
          }
        }catch (error) {
          console.log("데이터 가져오기 실패:", error);
        }
      }

      provide("logdata", logdata);
  
      return {
        t,
        sidebarOpen,
        logdata,
      };
    },
  };
  </script>
  