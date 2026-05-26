<template>  
    <tbody class="text-sm font-medium divide-y divide-gray-100 dark:divide-gray-700/60">
      <tr v-for="(item, index) in data" :key="index" class="h-14">
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

      <tr v-if="!data || data.length === 0">
        <td colspan="4" class="px-2 py-8 text-center text-gray-500 dark:text-gray-400">
          데이터가 없습니다.
        </td>
      </tr>
    </tbody>
  </template>
  
  <script>
  export default {
    name: 'LogTableItem',
    props: {
      data: {
        type: Array,
        default: () => []
      }
    },
    setup() {
      const getRoleText = (role) => {
         switch(parseInt(role)){
            case 0: return "User"
            case 1: return "Operator"
            case 2: return "Administrator"
            case 3: return "Ntek Administrator"
            default: return "Unknown"
         }
      };
  
      return { getRoleText }
    }
  }
  </script>