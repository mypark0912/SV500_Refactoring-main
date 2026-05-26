<template>
    <div class="col-span-full xl:col-span-6 2xl:col-span-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/60 shadow-sm rounded-lg">
              <!-- Card content -->
              <div class="flex flex-col h-full p-5">
                <div class="grow">
                  <header class="flex items-center justify-between mb-4">
                    <div class="flex items-center">
                    <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold mr-4">{{ itemDict[item] }}</h3>
                    
                    <!-- 기존 System 상태 -->
                    </div>
                    <span class="text-sm text-gray-500 dark:text-gray-400 font-mono">
                      v{{ versionInfo }}
                    </span>
                  </header>
                  <div class="flex flex-col">
                    <div class="flex justify-center space-x-4">

                    </div>
                  </div>
                </div>
                <!-- Card footer -->
              </div>
            </div>
</template>
<script> 
import { ref, watch } from 'vue'


export default {
  name: 'ServiceCard',
  props: ['item','version'],
  setup(props, ){

    const item = ref(props.item);
    const versionInfo = ref(props.version);


    const itemDict = ref({
      "Redis":"Redis",
      "InfluxDB":"Influxdb", 
      "SmartSystems":"SmartSystem",
      "SmartAPI":"Smart RestAPI",
      "Core":"Core",
      "WebServer":"WebServer",
      "A35":"A35",
      "fw":"FW"
    });


    watch(() => props.item, (newChannel) => {
        item.value = newChannel;
    }, { immediate: true });

    watch(() => props.version, (newVersion) => {
      versionInfo.value = newVersion || '';

    }, { immediate: true });


    return {
      item,
      itemDict,
      versionInfo,
    }
  }
}
</script>