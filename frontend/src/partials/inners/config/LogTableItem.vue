<template>  
    <tbody class="text-sm font-medium divide-y divide-gray-100 dark:divide-gray-700/60">
      <!-- Data rows -->
      <tr v-for="(item, index) in logdata" :key="index" class="h-14">
        <td class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
          <div class="font-medium text-gray-800 dark:text-gray-100">{{ item.logdate }}</div>
        </td>
        <td class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
          <div class="text-left font-medium text-green-600">{{ item.action }}</div>
        </td>
        <td class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
          <div class="text-left">{{ item.account }}</div>
        </td>
        <td class="px-2 first:pl-5 last:pr-5 py-3 whitespace-nowrap">
          <div class="text-left">{{ getRoleText(item.userRole) }}</div>
        </td>
      </tr>
    </tbody>
  </template>
  
  <script>
  import { ref, inject } from 'vue'
  import { useI18n } from "vue-i18n";
  
  export default {
    name: 'LogTableItem',
    setup() {
      const { t } = useI18n();
      const sidebarOpen = ref(false)
      const logdata = inject('logdata');

      const getRoleText = (role)=>{
        
         switch(parseInt(role)){
            case 0:
                return "User"
            case 1:
                return "Operator"
            case 2:
                return "Administrator"
            case 3:
                return "Ntek Administrator"
         }
      };
  
      return {
        t,
        sidebarOpen,
        logdata,
        getRoleText,
      }
    }
  }
  </script>
  
  <style scoped>
  /* 테이블 컨테이너에 최소 높이 설정 제거 */
  .table-container {
    /* min-height: 700px; 제거 */
    position: relative;
    display: flex;
    flex-direction: column;
  }
  
  /* 테이블 자체 최소 높이 제거 */
  .table-container table {
    /* min-height: 350px; 제거 */
    width: 100%;
  }
  
  /* 테이블이 늘어나지 않도록 설정 */
  .table-container table tbody {
    height: auto;
  }
  
  /* 빈 상태 메시지 스타일 - 테이블 아래에 표시 */
  .empty-state {
    text-align: center;
    padding: 2rem;
    margin-top: 2rem;
  }
  
  /* 다크 모드에서도 잘 보이도록 */
  .dark .empty-state {
    color: #9ca3af;
  }
  </style>