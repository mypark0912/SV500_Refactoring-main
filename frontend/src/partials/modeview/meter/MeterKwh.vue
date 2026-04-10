<template>
    <div class="col-span-full xl:col-span-3 meter-card">
      <div class="meter-card-header">
        <h3 class="meter-card-title meter-accent-teal">{{ t(`meter.cardContext.${data[index].subTitle}`) }} {{ title }}</h3>
      </div>
      <div class="meter-card-body">
        <div class="flex items-start ml-4">
          <!--div class="text-xs font-bold text-black-400 dark:text-black-500 uppercase mb-1">{{ data[0].subTitle }}</div-->
          <div class="text-xl font-bold text-gray-800 dark:text-gray-100 mr-2">{{data[index].data[0].value.toFixed(2) }} {{ data[0].data[0].unit }}</div>
        </div>
      </div>
    </div>
  </template>
    
    <script>
    import { watch, ref, computed } from 'vue';
    import { useI18n } from 'vue-i18n'  // ✅ 추가
    //import AccordionTableItem from '../../components/AccordionTableItem.vue'
    export default {
      name: 'MeterDetail3',
      props: {
        channel:String,
        title:String,
        data: Object, // ✅ props.data의 타입을 명시
        mode:String,
      },
      setup(props){
        const channel = ref(props.channel);
        const title = computed(() => {
          if (props.title === 'Energy') return t('meter.cardTitle.title_energy');
          //return t('meter.cardTitle.title_thd');
        });
        const index = computed(()=> props.mode == 'export'? 0 : 1);
        const data = ref([]);
        const { t } = useI18n();
        watch(
          () => props.data,
          (newData) => {
            if (newData && Array.isArray(newData) && newData.length > 0) {
              data.value = [...newData];
            }
          },
          { immediate: true }
        );

        return {
          channel, // ✅ props.channel 직접 반환
          data,
          title,
          t,
          index,
        };
      }
    }
    </script>
    <style scoped>
      @import '../../../css/meter-card.css';
    </style>