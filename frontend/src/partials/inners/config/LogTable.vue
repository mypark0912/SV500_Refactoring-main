<template>
    <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl relative">
      <div>
        <!-- Table -->
        <div class="overflow-x-auto">
          <div class="table-container">
            <table
              class="table-auto w-full dark:text-white divide-y divide-gray-100 dark:divide-gray-700/60"
            >
              <!-- Table header -->
              <thead
                class="text-xs uppercase text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20 border-t border-gray-100 dark:border-gray-700/60"
              >
                <tr>
                  <th class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
                    <div class="font-semibold text-left">
                      Timestamp
                    </div>
                  </th>
                  <th class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
                    <div class="font-semibold text-left">
                      Action
                    </div>
                  </th>
                  <th class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
                    <div class="font-semibold text-left">
                      Account
                    </div>
                  </th>
                  <th class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
                    <div class="font-semibold text-left">
                        UserRole
                    </div>
                  </th>
                </tr>
              </thead>
              <!-- Table body -->
              <EventTableItem />
            </table>
            
    
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref } from "vue";
  import { useI18n } from "vue-i18n";
  import EventTableItem from "./LogTableItem.vue";

  
  export default {
    name: "EventTable",
    components: {
      EventTableItem,
    },
    setup() {
      const { t } = useI18n();
      const sidebarOpen = ref(false);
      
      
  
      return {
        t,
        sidebarOpen,
      };
    },
  };
  </script>
  
  <style scoped>
  /* 전체 래퍼에 최소 높이 설정 */
  .bg-white.dark\:bg-gray-800 {
    min-height: 700px;
    display: flex;
    flex-direction: column;
  }
  
  /* 내부 div도 flex로 설정하여 공간 채우기 */
  .bg-white.dark\:bg-gray-800 > div {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  
  /* overflow-x-auto 영역도 flex로 설정 */
  .overflow-x-auto {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  
  /* 테이블 컨테이너 - 최소 높이 제거, flex 사용 */
  .table-container {
    /* min-height 제거 */
    position: relative;
    display: flex;
    flex-direction: column;
    flex: 1;
  }
  
  /* 테이블 자체 - 최소 높이 제거 */
  .table-container table {
    /* min-height 제거 */
    width: 100%;
  }
  
  /* 테이블이 늘어나지 않도록 설정 */
  .table-container table tbody {
    height: auto;
  }
  
  /* 빈 상태 메시지 스타일 */
  .empty-state {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    padding: 2rem;
  }
  
  /* 다크 모드에서도 잘 보이도록 */
  .dark .empty-state {
    color: #9ca3af;
  }
  </style>
  