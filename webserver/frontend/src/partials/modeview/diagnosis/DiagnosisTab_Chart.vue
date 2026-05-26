<template>
<div v-if="mode != 'Event'" class="grid grid-cols-12 gap-6">
  <div class="col-span-12 flex flex-col gap-6 h-auto">
    <Diagnosis_Barchart v-if="chartdata !== null" :channel="channel" :data="chartdata" :mode="mode" class="h-auto" />
  </div>
  <div class="col-span-12">
    <Diagnosis_TreeTable v-if="items.length > 0" :channel="channel" :data="items" :mode="mode" />
  </div>
</div>
<div v-else class="grid grid-cols-12 gap-6">
  <div class="col-span-8 flex flex-col gap-6 h-auto">
    <Diagnosis_Barchart v-if="chartdata !== null" :channel="channel" :data="chartdata" :mode="mode" class="h-auto" />
  </div>
  <div class="col-span-4 pt-4">
    <Diagnosis_TreeTable v-if="items.length > 0" :channel="channel" :data="items" :mode="mode" />
  </div>
</div>

</template>
<script>
import { ref, watch, computed, onMounted, provide } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import Diagnosis_TreeTable from '../../inners/diagnosis/Diagnosis_TreeTable2.vue'
import Diagnosis_Barchart from './Diagnosis_BarChart2.vue'

export default {
  name: 'DiagnosisTab_Chart',
  props:{
    asset:{
      type: Object,
      default: () => {}
    },
    channel:{
      type:String,
      default: ''
    },
    mode:{
      type:String,
      default: ''
    }
  },
  components: {
    Diagnosis_TreeTable,
    Diagnosis_Barchart,
  },
  setup(props) {
    const { t, locale } = useI18n();
    const channel = ref(props.channel)
    const asset = ref(props.asset);
    const chartdata = ref(null);
    const data_recordtime = ref('');
    const data_state = ref('');
    const items = ref([]);
    const mode=ref(props.mode);

    const fetchDetailData = async () => {

      const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
      try {
        const response = await axios.get(`/api/getDiagnosisDetail/${chName}`);
        if (response.data.success) {
          let itemlist = [], valuelist=[], datalist=[];
          for(let i = 0; i < response.data.data_status.length;i++){

            itemlist.push(response.data.data_status[i]["Titles"][locale.value]);
            valuelist.push(response.data.data_status[i]["Status"]);
            datalist.push(response.data.data_status[i]["Titles"])
          }
          chartdata.value = {"Names" : itemlist, "Values" : valuelist, "Titles": datalist};
          items.value = response.data.data_tree;
          data_recordtime.value = response.data.data_recordtime;
          data_state.value = response.data.data_state;
        }else{
          console.log('No Data');
        }
      }catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };

const fetchPQData = async () => {
  const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;

  const pqDisplayOrder = [
    'VoltagePhaseAngle',
    'VoltageRMS',
    'DC',
    'CurrentRMS',
    'CurrentPhaseAngle',
    'CrestFactor',
    'Unbalance',
    'Harmonics',
    'ZeroSequence',
    'NegativeSequence',
    'Power',
    'PowerFactor',
    'TotalDemandDistortion',
    'PhaseAngle',
    'Events',
  ];

  try {
    const response = await axios.get(`/api/getDiagPQ/${chName}`);

    if (response.data.success) {
      const sortedStatus = [...response.data.data_status].sort((a, b) => {
        const indexA = pqDisplayOrder.indexOf(a.Name);
        const indexB = pqDisplayOrder.indexOf(b.Name);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        return indexA - indexB;
      });

      const sortedTree = [...response.data.data_tree].sort((a, b) => {
        const indexA = pqDisplayOrder.indexOf(a.Name);
        const indexB = pqDisplayOrder.indexOf(b.Name);
        if (indexA === -1) return 1;
        if (indexB === -1) return -1;
        return indexA - indexB;
      });

      let itemlist = [], valuelist = [], datalist = [];
      for (let i = 0; i < sortedStatus.length; i++) {
        itemlist.push(sortedStatus[i]["Titles"][locale.value]);
        valuelist.push(sortedStatus[i]["Status"]);
        datalist.push(sortedStatus[i]["Titles"]);
      }

      chartdata.value = { "Names": itemlist, "Values": valuelist, "Titles": datalist };
      items.value = sortedTree;
      data_recordtime.value = response.data.data_recordtime;
      data_state.value = response.data.data_state;
    } else {
      console.log('No Data');
    }
  } catch (error) {
    console.log("데이터 가져오기 실패:", error);
  }
};
    const fetchFaultData = async () => {

      const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
      try {
        const response = await axios.get(`/api/getFaults/${chName}`);
        if (response.data.success) {
          let itemlist = [], valuelist=[], datalist=[];
          for(let i = 0; i < response.data.data_status.length;i++){
            itemlist.push(response.data.data_status[i]["Title"]);
            valuelist.push(response.data.data_status[i]["Status"]);
            datalist.push(response.data.data_status[i]["Titles"]);
          }
          chartdata.value = {"Names" : itemlist, "Values" : valuelist, "Titles": datalist};
          items.value = response.data.data_tree;
        }else{
          console.log('No Data');
        }
      }catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };

    const fetchEventData = async () => {

      const chName = channel.value == 'Main'? asset.value.assetName_main : asset.value.assetName_sub;
      try {
        const response = await axios.get(`/api/getEvents/${chName}`);
        if (response.data.success) {
          let itemlist = [], valuelist=[], datalist=[];
          for(let i = 0; i < response.data.data_status.length;i++){
            itemlist.push(response.data.data_status[i]["Titles"][locale.value]);
            valuelist.push(response.data.data_status[i]["Status"]);
            datalist.push(response.data.data_status[i]["Titles"]);
          }
          chartdata.value = {"Names" : itemlist, "Values" : valuelist, "Titles": datalist};
          items.value = response.data.data_tree;
        }else{
          console.log('No Data');
        }
      }catch (error) {
        console.log("데이터 가져오기 실패:", error);
      }
    };


    onMounted(async () => {

        if(mode.value == 'Status')
          await fetchDetailData();
        else if(mode.value == 'PowerQuality')
          await fetchPQData();
        else if(mode.value == 'Fault')
          await fetchFaultData();
        else
          await fetchEventData();

    });

    watch(() => props.asset, async(newChannel) => {
      if (newChannel !== asset.value) {
        asset.value = newChannel;
        await fetchDetailData();
      }
    });

    provide('data_recordtime', computed(() => data_recordtime.value));
    provide('data_state', computed(() => data_state.value));

    return {
      channel,
      chartdata,
      items,
      asset,
      fetchDetailData,
      mode,
      data_recordtime,
      data_state,
      t,
    }
  }



}
</script>
<style scoped>
</style>