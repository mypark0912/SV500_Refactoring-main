<template>
    <div class="grow">
  
      <!-- Panel body -->
      <div class="p-4">
        <div class="mt-2 grid grid-cols-2 gap-4 border-b border-gray-200 dark:border-gray-700/60 p-2 pb-4">
            <div v-if="showMainChannel">
              <h2 class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-5"> Main Channel</h2>
            </div>
            <div v-if="showSubChannel">
              <h2 class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-5"> Sub Channel</h2>
            </div>            
        </div>


  
        <!-- Connected Apps cards -->
        <section class="mt-2 pb-2 border-b border-gray-200 dark:border-gray-700/60">
            <div class="grid grid-cols-2 gap-4">
                <GroupTable v-if="showMainChannel" :channels="channels.main" />
                <GroupTable v-if="showSubChannel" :channels="channels.sub" />
            </div>
          
        </section>
        <!--section class="mt-2 pb-6 border-b border-gray-200 dark:border-gray-700/60">
          <CaliCard v-for="item in items" :item="item"/>
        </section-->

      </div>
  
    </div>
  </template>
  
  <script>
  import CaliCard from './CaliCard2.vue';
  import CaliCard_New from './CaliCard4.vue';
  import FormBlock from './FormBlock.vue';
  import GroupTable from './GroupTable.vue';
  import { useRoute } from 'vue-router'
  import { ref , watch, reactive, onMounted,inject,onUnmounted} from 'vue'
  import { useSetupStore } from "@/store/setup"; // ✅ Pinia Store 사용
  import axios from 'axios';
  export default {
    name: 'CaliPanel',
    props:['items','channel'],
    components:{
        CaliCard,
        CaliCard_New,
        FormBlock,
        GroupTable,
    },
    setup(props){
        const setupStore = useSetupStore();
        const route = useRoute();
        const items = ref(props.items);
        const channel = ref(props.channel);
        const selectSetup_main = ref(0);
        const selectSetup_sub = ref(0);
        const tvalue = ref('');
        const showMainChannel = inject('showMainChannel', ref(true));
        const showSubChannel = inject('showSubChannel', ref(true));
        const selectItem = ref('Time');
        let updateInterval = null;
        const channels = reactive({
      "main":{       
        "Phase Voltage": {
            "view":[
              { subTitle: "U_A", value: 0, error: 0 },
              { subTitle: "U_B", value: 0, error: 0 },
              { subTitle: "U_C", value: 0, error: 0 },
              { subTitle: "Upp", value: 0, error: 0 }
            ],
          },
          "Phase Current":{
              "view": [
              { subTitle: "I_A", value: 0, error: 0 },
              { subTitle: "I_B", value: 0, error: 0 },
              { subTitle: "I_C", value: 0, error: 0 },
              { subTitle: "In", value: 0, error: 0 }
            ],
          },
        "Power Angle": {
            "view":[
              { subTitle: "Angle_A", value: 0, error: 0 },
              { subTitle: "Angle_B", value: 0, error: 0 },
              { subTitle: "Angle_C", value: 0, error: 0 }
            ],
          },
          "Active Power":{
            "view" :[
              { subTitle: "Watt_A", value: 0, error: 0 },
              { subTitle: "Watt_B", value: 0, error: 0 },
              { subTitle: "Watt_C", value: 0, error: 0 }
            ]
          },
          "Reactive Power":{
            "view":[
              { subTitle: "Var_A", value: 0, error: 0 },
              { subTitle: "Var_B", value: 0, error: 0 },
              { subTitle: "Var_C", value: 0, error: 0 }
            ]
          },
          "Apparent Power":{
            "view":[
              { subTitle: "VA_A", value: 0, error: 0 },
              { subTitle: "VA_B", value: 0, error: 0 },
              { subTitle: "VA_C", value: 0, error: 0 }
            ]
          },
      },
      "sub":{       
        "Phase Voltage": {
            "view":[
              { subTitle: "U_A", value: 0, error: 0 },
              { subTitle: "U_B", value: 0, error: 0 },
              { subTitle: "U_C", value: 0, error: 0 },
              { subTitle: "Upp", value: 0, error: 0 }
            ],
          },
          "Phase Current":{
              "view": [
              { subTitle: "I_A", value: 0, error: 0 },
              { subTitle: "I_B", value: 0, error: 0 },
              { subTitle: "I_C", value: 0, error: 0 },
              { subTitle: "Ig", value: 0, error: 0 },
              { subTitle: "In", value: 0, error: 0 }
            ],
          },
        "Power Angle": {
            "view":[
              { subTitle: "Angle_A", value: 0, error: 0 },
              { subTitle: "Angle_B", value: 0, error: 0 },
              { subTitle: "Angle_C", value: 0, error: 0 }
            ],
          },
          "Active Power":{
            "view" :[
              { subTitle: "Watt_A", value: 0, error: 0 },
              { subTitle: "Watt_B", value: 0, error: 0 },
              { subTitle: "Watt_C", value: 0, error: 0 }
            ]
          },
          "Reactive Power":{
            "view":[
              { subTitle: "Var_A", value: 0, error: 0 },
              { subTitle: "Var_B", value: 0, error: 0 },
              { subTitle: "Var_C", value: 0, error: 0 }
            ]
          },
          "Apparent Power":{
            "view":[
              { subTitle: "VA_A", value: 0, error: 0 },
              { subTitle: "VA_B", value: 0, error: 0 },
              { subTitle: "VA_C", value: 0, error: 0 }
            ]
          },
      },
    })
        const Forms = ref({
            "row1":{
                "lbl":"U Ref",
                "text":"",
                "btn0":"Send",
                "btn1":"Set U",
                "btn2":"Clear U",
            },
            "row2":{
                "lbl":"Upp Ref",
                "text":"",
                "btn0":"Send",
                "btn1":"Set Upp",
                "btn2":"Clear Upp"
            },
            "row3":{
                "lbl":"I Ref",
                "text":"",
                "btn0":"Send",
                "btn1":"Set I",
                "btn2":"Clear I",
            },
            "row4":{
                "lbl":"In Ref",
                "text":"",
                "btn0":"Send",
                "btn1":"Set In",
                "btn2":"Clear In"
            },
            "row5":{
              "lbl":"Phase Angle",
              "text":"",
              "btn0":"Send",
              "btn1":"Set Phase",
              "btn2":"Clear Phase",
            },
            "row6":{
              "btn1":"Set Power",
              "btn2":"Clear Power"
            }
        })
    

    onMounted(async()=>{
      await fetchData();
      updateInterval = setInterval(() => {
        fetchData();
        }, 1000);
    });

    onUnmounted(()=>{
      if (updateInterval) {
        clearInterval(updateInterval);
      }
    });

    const dataMapping = [
  { index: 0, category: "Phase Voltage", dataCount: 4 },
  { index: 1, category: "Phase Current", dataCount: 4 },
  { index: 2, category: "Power Angle", dataCount: 3 },
  { index: 3, category: "Active Power", dataCount: 3 },
  { index: 4, category: "Reactive Power", dataCount: 3 },
  { index: 5, category: "Apparent Power", dataCount: 3 }
];

// 자동화된 데이터 업데이트 함수
function updateChannelData(response) {
  // main과 sub 채널 동시 처리
  ['main', 'sub'].forEach(channelType => {
    const sourceData = channelType === 'main' ? response.mainData : response.subData;
    
    if (!sourceData) return;
    
    // 매핑 테이블에 따라 자동 업데이트
    dataMapping.forEach(({ index, category, dataCount }) => {
      if (sourceData[index]?.data) {
        const targetView = channels[channelType][category].view;
        
        // 데이터 배열의 각 값을 view 배열에 할당
        for (let i = 0; i < dataCount && i < targetView.length; i++) {
          if (sourceData[index].data[i] !== undefined) {
            //targetView[i].value = sourceData[index].data[i]["value"];
            channels[channelType][category].view[i] = {
              ...channels[channelType][category].view[i],
              value: sourceData[index].data[i]["value"]
            };
          }
        }
      }
    });
  });
}
    const fetchData = async (ch) => {
      try {
        const response = await axios.get(`/config/calibrateNow`);
        //console.log(response.data.mainData);
        updateChannelData(response.data);
        
      } catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };

    watch(() => props.channel, (newChannel) => {
      if (newChannel !== channel.value) {
        channel.value = newChannel;
      }
    }, { immediate: true });

  // route.params.channel 변경 감시
    watch(() => route.params.channel, (newChannel) => {
      if (newChannel !== channel.value) {
        channel.value = newChannel;
      }
    }, { immediate: true });


    

      return {
          items,
          channel,
          selectSetup_main,
          selectSetup_sub,
          tvalue,
          selectItem,
          Forms,
          channels,
          showMainChannel,
          showSubChannel,

      }
    }
  }
  </script>

<style scoped>
/* 다크모드에서 select option 스타일링 추가 */
@media (prefers-color-scheme: dark) {
  select option {
    background-color: rgb(31 41 55); /* gray-800 */
    color: rgb(243 244 246); /* gray-100 */
  }
  
  select option:hover,
  select option:focus,
  select option:checked {
    background-color: rgb(55 65 81); /* gray-700 */
  }
}

/* 라이트모드에서 option 스타일링 */
@media (prefers-color-scheme: light) {
  select option {
    background-color: white;
    color: rgb(17 24 39); /* gray-900 */
  }
  
  select option:hover,
  select option:focus,
  select option:checked {
    background-color: rgb(243 244 246); /* gray-100 */
  }
}
</style>