<template>
    <div class="col-span-full xl:col-span-6 2xl:col-span-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-lg">
      <!-- Card content -->
      <div class="flex flex-col h-full p-5">
        <div class="grow">
          <header class="flex items-center justify-between mb-4">
            <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold">Smart System Error List</h3>
            <span class="text-sm rounded-full px-3 py-1 bg-red-500/20 text-red-700 font-semibold">
              {{ errorList.length }} Errors
            </span>
          </header>
          
          <div class="flex flex-col space-y-2">
            <!-- 에러가 없을 때 -->
            <div v-if="errorList.length === 0" class="text-center py-4 text-gray-500 dark:text-gray-400">
              No errors detected
            </div>
            
            <!-- 에러 목록 (최근 5개만 표시) -->
            <div 
              v-for="(error, index) in errorList.slice(0, 5)" 
              :key="index"
              class="flex items-center space-x-3 p-2 border-l-4 bg-gray-50 dark:bg-gray-700/30 rounded border-red-500"
            >
              <!-- 에러 아이콘 -->
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                class="flex-shrink-0 text-red-600" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                stroke-linecap="round" 
                stroke-linejoin="round" 
                width="18" 
                height="18" 
                stroke-width="2"
              >
                <path d="M12 9v4"></path>
                <path d="M10.363 3.591l-8.106 13.534a1.914 1.914 0 0 0 1.636 2.871h16.214a1.914 1.914 0 0 0 1.636 -2.87l-8.106 -13.536a1.914 1.914 0 0 0 -3.274 0z"></path>
                <path d="M12 16h.01"></path>
              </svg>
              
              <!-- 에러 메시지만 -->
              <p class="text-sm text-gray-800 dark:text-gray-200 flex-1">
                {{ error }}
              </p>
            </div>
          </div>
        </div>
        
        <!-- Card footer -->
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted } from 'vue'
  
  export default {
    name: 'ErrorListCard',
    props:{
        data:{
            type:Array,
        }
    },
    setup(props) {
      // 더미 에러 데이터 (하드코딩)
    //   const errorList = ref([
    //     {
    //       severity: 'critical',
    //       message: 'Influx service is not running'
    //     },
    //     {
    //       severity: 'warning',
    //       message: 'Influx token cannot be retrieved from influx.json file'
    //     },
    //     {
    //       severity: 'critical',
    //       message: 'Corrupted smart systems files'
    //     },
    //     {
    //       severity: 'info',
    //       message: 'No asset defined in smart system'
    //     },
    //     {
    //       severity: 'warning',
    //       message: 'There are assets but no registered assets'
    //     },
    //     {
    //       severity: 'critical',
    //       message: 'SV500 waveform and event folders does not exist'
    //     }
    //   ])
      const errorList = ref(props.data);
      
      onMounted(() => {
        // TODO: API 호출 로직 추가
        console.log(props.data);
      })
  
      return {
        errorList,
      }
    }
  }
  </script>