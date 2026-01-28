<template>
    <div class="grow">
  
      <!-- Panel body -->
      <div class="p-6">
        <h2 class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-5"> System Service </h2>
  
        <!-- General -->
        <div class="mb-6">
          <!-- Filters -->
          <div class="mt-4 flex gap-2 border-b border-gray-200 dark:border-gray-700/60 pb-4">
            <!--div class="flex items-center">
              <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold mr-4"> SV-500 Status</h3>
                <span v-if="health" class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-green-500/20 text-green-700 font-semibold">
                  Active
                </span>
                <span v-else class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-red-500/20 text-red-700 font-semibold">
                  Disabled
                </span>
            </div-->
            <div class="flex items-center gap-4 mb-4">
      <!-- Factory Default 버튼 -->
      <div class="flex items-center gap-3">
        <label 
          for="reference"
          class="text-sm text-gray-700 dark:text-gray-300 font-medium"
        >
          Influxdb Init Status
        </label>
        <span v-if="initInfluxStatus == 'IDLE'" class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-gray-500/20 text-gray-700 font-semibold">
          {{ initInfluxStatus }}
        </span>
        <span v-else-if="initInfluxStatus == 'COMPLETE'" class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-green-500/20 text-green-700 font-semibold">
          {{ initInfluxStatus }}
        </span>
        <span v-else-if="initInfluxStatus == 'FAIL'" class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-red-500/20 text-red-700 font-semibold">
          {{ initInfluxStatus }}
        </span>
        <span v-else class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-yellow-500/20 text-yellow-700 font-semibold">
          {{ initInfluxStatus }}
        </span>
        <button v-if="updateInflux === 0"
        class="btn h-9 px-5 bg-pink-900 text-pink-100 hover:bg-pink-800 dark:bg-pink-100 dark:text-pink-800 dark:hover:bg-white flex items-center"
        @click="init"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="20" height="20" stroke-width="1.25" class="mr-2">
          <path d="M19 14v-2h2l-9 -9l-9 9h2v7a2 2 0 0 0 2 2h2.5"></path>
          <path d="M9 21v-6a2 2 0 0 1 2 -2h2a2 2 0 0 1 1.75 1.032"></path>
          <path d="M15.536 17.586a2.123 2.123 0 0 0 -2.929 0a1.951 1.951 0 0 0 0 2.828c.809 .781 2.12 .781 2.929 0c.809 -.781 -.805 .778 0 0l1.46 -1.41l1.46 -1.419"></path>
          <path d="M15.54 17.582l1.46 1.42l1.46 1.41c.809 .78 -.805 -.779 0 0s2.12 .781 2.929 0a1.951 1.951 0 0 0 0 -2.828a2.123 2.123 0 0 0 -2.929 0"></path>
        </svg>
        Influx Init
      </button>
      <button v-if="updateInflux === 1"
        class="btn h-9 px-5 bg-pink-900 text-pink-100 hover:bg-pink-800 dark:bg-pink-100 dark:text-pink-800 dark:hover:bg-white flex items-center"
        @click="updateInfluxBucket"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="20" height="20" stroke-width="1.25" class="mr-2">
          <path d="M19 14v-2h2l-9 -9l-9 9h2v7a2 2 0 0 0 2 2h2.5"></path>
          <path d="M9 21v-6a2 2 0 0 1 2 -2h2a2 2 0 0 1 1.75 1.032"></path>
          <path d="M15.536 17.586a2.123 2.123 0 0 0 -2.929 0a1.951 1.951 0 0 0 0 2.828c.809 .781 2.12 .781 2.929 0c.809 -.781 -.805 .778 0 0l1.46 -1.41l1.46 -1.419"></path>
          <path d="M15.54 17.582l1.46 1.42l1.46 1.41c.809 .78 -.805 -.779 0 0s2.12 .781 2.929 0a1.951 1.951 0 0 0 0 -2.828a2.123 2.123 0 0 0 -2.929 0"></path>
        </svg>
        Influx Update
      </button>
        </div>

      <!--div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
      <button 
        class="btn h-9 px-5 bg-violet-900 text-violet-100 hover:bg-violet-800 dark:bg-violet-100 dark:text-violet-800 dark:hover:bg-white flex items-center"
        @click="InitInfluxCLI"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="20" height="20" stroke-width="1.25" class="mr-2">
          <path d="M19 14v-2h2l-9 -9l-9 9h2v7a2 2 0 0 0 2 2h2.5"></path>
          <path d="M9 21v-6a2 2 0 0 1 2 -2h2a2 2 0 0 1 1.75 1.032"></path>
          <path d="M15.536 17.586a2.123 2.123 0 0 0 -2.929 0a1.951 1.951 0 0 0 0 2.828c.809 .781 2.12 .781 2.929 0c.809 -.781 -.805 .778 0 0l1.46 -1.41l1.46 -1.419"></path>
          <path d="M15.54 17.582l1.46 1.42l1.46 1.41c.809 .78 -.805 -.779 0 0s2.12 .781 2.929 0a1.951 1.951 0 0 0 0 -2.828a2.123 2.123 0 0 0 -2.929 0"></path>
        </svg>
        Init InfuxCLI
      </button-->
      
      <!-- 구분선 (선택사항) -->
      <!-- <div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
       -->
      <!-- Download 영역 -->
      <!-- <div class="flex items-center gap-3">
        <label 
          for="reference"
          class="text-sm text-gray-700 dark:text-gray-300 font-medium"
        >
         Backup Download
        </label>
        
        <select v-if="devMode != 'device0'"
          id="reference"
          class="h-9 w-56 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
          v-model="modalSelectItem"
        >
          <option value="all">SmartSystem All</option>
          <option value="log">SmartSystem Log</option>
          <option value="project">SmartSystem Project</option>
          <option value="dbbackup">SmartSystem Dbbackup</option>
          <option value="backup">SmartSystem Backup</option>
          <option value="other">Other Backup</option>
        </select>
        <select v-else
          id="reference"
          class="h-9 w-32 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
          v-model="modalSelectItem"
        >
          <option value="all">All</option>
          <option value="log">Log</option>
          <option value="dbbackup">Dbbackup</option>
        </select>
        
        
         <a :href="downloadUrl"
          class="btn h-9 px-5 bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white flex items-center"
          download
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="16" height="16" stroke-width="2" class="mr-2">
            <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2 -2v-2"></path>
            <polyline points="7 11 12 16 17 11"></polyline>
            <line x1="12" y1="4" x2="12" y2="16"></line>
          </svg>
          Download
        </a>
      </div> -->
      <div v-if="frpStatus.exist" class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
        <label v-if="frpStatus.exist"
          for="reference"
          class="text-sm text-gray-700 dark:text-gray-300 font-medium"
        >
          FRP Tunneling Status
      </label>
        <span v-if="frpStatus.exist && frpStatus.status" class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-green-500/20 text-green-700 font-semibold">
          Running
        </span>
        <span v-else-if="frpStatus.exist && !frpStatus.status" class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-red-500/20 text-red-700 font-semibold">
          Stopped
        </span>
      <div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
      <button 
        class="btn h-9 px-5 bg-violet-900 text-violet-100 hover:bg-violet-800 dark:bg-violet-100 dark:text-violet-800 dark:hover:bg-white flex items-center"
        @click="ResetAll"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" width="20" height="20" stroke-width="1.25" class="mr-2">
          <path d="M19 14v-2h2l-9 -9l-9 9h2v7a2 2 0 0 0 2 2h2.5"></path>
          <path d="M9 21v-6a2 2 0 0 1 2 -2h2a2 2 0 0 1 1.75 1.032"></path>
          <path d="M15.536 17.586a2.123 2.123 0 0 0 -2.929 0a1.951 1.951 0 0 0 0 2.828c.809 .781 2.12 .781 2.929 0c.809 -.781 -.805 .778 0 0l1.46 -1.41l1.46 -1.419"></path>
          <path d="M15.54 17.582l1.46 1.42l1.46 1.41c.809 .78 -.805 -.779 0 0s2.12 .781 2.929 0a1.951 1.951 0 0 0 0 -2.828a2.123 2.123 0 0 0 -2.929 0"></path>
        </svg>
        Factory Default
      </button>
      <button
            class="btn h-9 px-5 bg-sky-900 text-sky-100 hover:bg-sky-800 dark:bg-sky-100 dark:text-sky-800 dark:hover:bg-white flex items-center"
            @click.stop="feedbackModalOpen = true"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
              />
              <polyline points="14,2 14,8 20,8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10,9 9,9 8,9" />
            </svg>
            &nbsp; Set Default IP
            <!--Import-->
          </button>
    </div>
          </div>
          <div v-if="message"
            class="text-sm text-gray-800 dark:text-gray-100 mt-2"
          >
            {{ message }}🙌
          </div>
        </div>
  
        <!-- Connected Apps cards -->
        <section class="pb-6 border-b border-gray-200 dark:border-gray-700/60">
          <div class="grid grid-cols-12 gap-6">
            <ServiceCard :item="'Redis'" :mode="'Service'" :state="ChannelState" @service-done="showMessage"/>
            <ServiceCard :item="'InfluxDB'" :mode="'Service'" :state="ChannelState" @service-done="showMessage"/>
            <ServiceCard :item="'Core'" :mode="'Service'" :state="ChannelState" :version="versionDict['Core']" @service-done="showMessage"/>
            <ServiceCard :item="'WebServer'" :mode="'Service'" :state="ChannelState" :version="versionDict['WebServer']" @service-done="showMessage"/>
            <ServiceCard :item="'A35'" :mode="'Service'" :state="ChannelState" :version="versionDict['A35']" @service-done="showMessage"/>
            <ServiceCard2 :item="'fw'" :version="versionDict['fw']" />
            <ServiceCard v-if="'mqClient' in sysStatus" :item="'MQTTClient'" :mode="'Service'" :state="ChannelState" :version="versionDict['MQTTClient']" @service-done="showMessage"/>
            <ServiceCard v-if="devMode != 'device0'" :item="'SmartSystems'" :mode="'Service'" :state="ChannelState" :version="versionDict['SmartSystems']" @service-done="showMessage"/>
            <ServiceCard v-if="devMode != 'device0'" :item="'SmartAPI'" :mode="'Service'" :state="ChannelState" :version="versionDict['SmartSystems']" @service-done="showMessage"/>
            <ServiceDetail v-if="devMode != 'device0' && checkSmartflag" :data="errorSmart" :msg="errorMsg" />
            <!--ServiceCard :item="'System'" :mode="'Service'" :state="ChannelState" @service-done="showMessage"/>
            <ServiceCard v-if="devMode != 'device0'" :item="'Backup Download'" :mode="'Download'" @service-done="showMessage"/-->
          </div>
        </section>

        <!-- Disk Status Section -->
        <section class="mt-6">
          <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold mb-4"> Disk Status</h3>
          
          <!-- Desktop Table View -->
          <div class="hidden md:block">
            <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
              <!-- Table Header -->
              <div class="bg-gray-50 dark:bg-gray-700 px-6 py-3 border-b border-gray-200 dark:border-gray-600">
                <div class="grid grid-cols-4 gap-4 text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  <div>Drive</div>
                  <div class="text-right">Total GB</div>
                  <div class="text-right">Free GB</div>
                  <div class="text-center">Status</div>
                </div>
              </div>
              <!-- Table Body -->
              <div class="divide-y divide-gray-200 dark:divide-gray-600">
                <div v-for="item in diskStatus" :key="item.drive" class="px-6 py-6 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors min-h-[80px]">
                  <div class="grid grid-cols-4 gap-4 items-center">
                    <!-- Drive Name -->
                    <div class="flex items-center">
                      <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mr-3">
                        <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                      </div>
                      <div>
                        <div class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ item.drive }}</div>
                        <div class="text-base text-gray-500 dark:text-gray-400">{{ getUsagePercentage(item) }}% used</div>
                      </div>
                    </div>
                    
                    <!-- Total GB -->
                    <div class="text-right flex flex-col justify-center h-full">
                      <div class="text-lg font-medium text-gray-900 dark:text-gray-100">{{ formatSize(item.totalGB) }}</div>
                      <div class="text-base text-gray-500 dark:text-gray-400">Total</div>
                    </div>
                    
                    <!-- Free GB -->
                    <div class="text-right flex flex-col justify-center h-full">
                      <div class="text-lg font-medium text-gray-900 dark:text-gray-100">{{ formatSize(item.freeGB) }}</div>
                      <div class="text-base text-gray-500 dark:text-gray-400">Available</div>
                    </div>
                    
                    <!-- Status -->
                    <div class="text-center flex justify-center items-center h-full">
                      <span v-if="item.status === 'ok'" 
                            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-base font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                        <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        OK
                      </span>
                      <span v-else 
                            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-base font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                        <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                        </svg>
                        ERROR
                      </span>
                    </div>
                  </div>
                  
                  <!-- Progress Bar -->
                  <div class="mt-3">
                    <div class="w-1/4 bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                      <div class="h-3 rounded-full transition-all duration-300"
                           :class="getProgressBarColor(item)"
                           :style="{ width: getUsagePercentage(item) + '%' }">
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Mobile Card View -->
          <div class="md:hidden space-y-4">
            <div v-for="item in diskStatus" :key="item.drive" 
                 class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <!-- Header -->
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center">
                  <div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mr-3">
                    <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                  </div>
                  <div>
                    <div class="text-2xl font-semibold text-gray-900 dark:text-gray-100">{{ item.drive }}</div>
                  </div>
                </div>
                <span v-if="item.status === 'ok'" 
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  OK
                </span>
                <span v-else 
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                  ERROR
                </span>
              </div>
              
              <!-- Stats -->
              <div class="grid grid-cols-2 gap-4 mb-3">
                <div>
                  <div class="text-lg text-gray-500 dark:text-gray-400">Total</div>
                  <div class="text-2xl font-medium text-gray-900 dark:text-gray-100">{{ formatSize(item.totalGB) }}</div>
                </div>
                <div>
                  <div class="text-lg text-gray-500 dark:text-gray-400">Available</div>
                  <div class="text-2xl font-medium text-gray-900 dark:text-gray-100">{{ formatSize(item.freeGB) }}</div>
                </div>
              </div>
              
              <!-- Progress Bar -->
              <div>
                <div class="flex justify-between text-lg text-gray-600 dark:text-gray-400 mb-1">
                  <span>{{ getUsagePercentage(item) }}% used</span>
                  <span>{{ formatSize(item.totalGB - item.freeGB) }} used</span>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                  <div class="h-3 rounded-full transition-all duration-300"
                       :class="getProgressBarColor(item)"
                       :style="{ width: getUsagePercentage(item) + '%' }">
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
      <LoadingModal
          :isOpen="isResetAll"
          title="Reset System as factory default initialization"
          :message="serviceLoadingMessage"
        />
    </div>
    <ModalBasic
      id="feedback-modal"
      :modalOpen="feedbackModalOpen"
      @close-modal="feedbackModalOpen = false"
      title="IP Address Configuration"
    >
      <!-- Modal content -->
      <div class="px-5 py-4">
        <div class="text-sm">
          <div class="font-medium text-gray-800 dark:text-gray-100 mb-3">
            Enter IP Address
          </div>
        </div>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium mb-1" for="ipaddress"
              >IP Address <span class="text-red-500">*</span></label
            >
            <input
              id="ipaddress"
              class="form-input w-full px-2 py-1"
              v-model="ipAddress"
              type="text"
              placeholder="192.168.1.1"
              required
            />
          </div>
        </div>
        <div class="text-sm">
          <div class="font-medium text-gray-800 dark:text-gray-100 mb-3">
            {{ message }}🙌
          </div>
        </div>
      </div>
      <!-- Modal footer -->
      <div class="px-5 py-4 border-t border-gray-200 dark:border-gray-700/60">
        <div class="flex flex-wrap justify-end space-x-2">
          <button
            class="btn-sm bg-gray-900 text-gray-100 hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-800 dark:hover:bg-white"
            @click.prevent="saveIPAddress"
          >
            Save
          </button>
          <button
            class="btn-sm border-gray-200 dark:border-gray-700/60 hover:border-gray-300 dark:hover:border-gray-600 text-gray-800 dark:text-white"
            @click.stop="feedbackModalOpen = false"
          >
            Cancel
          </button>
        </div>
      </div>
    </ModalBasic>
  </template>
  
  <script>
  import ServiceCard from './ServiceCard.vue';
  import ServiceCard2 from './ServiceCard2.vue';
  import ServiceDetail from './ServiceDetail.vue';
    import ServiceStatus from './ServiceStatus.vue';
    import LoadingModal from "../../../components/LoadingModal.vue";
    import ModalBasic from "../../../pages/common/ModalBasic.vue";
  import { useRoute } from 'vue-router'
  import { onMounted, ref , watch, provide, computed} from 'vue'
  import { useSetupStore } from '@/store/setup'
    import { useAuthStore } from '@/store/auth'

  import axios from 'axios';
  export default {
    name: 'ServicePannel',
    components:{
        ServiceCard,
        ServiceStatus,
        LoadingModal,
        ServiceDetail,
        ServiceCard2,
        ModalBasic,
    },
    setup(){
      const setupStore = useSetupStore();
      const authStore = useAuthStore();
      const message = ref('')
      const health = ref('');
      const isResetAll = ref(false);
      const sysStatus = ref({});
      const diskStatus = ref([]);
      const modalSelectItem = ref('all');
      const serviceLoadingMessage = ref('');
      const initInfluxStatus = ref('');
      const checkSmartflag = ref(false);
      const errorSmart = ref([]);
      const errorMsg = ref('');
      const versionDict = ref({});
      const updateInflux = ref(null);
      const feedbackModalOpen = ref(false);
      const ipAddress = ref('');
      const frpStatus = ref({
        exist:false,
        status:false
      });
      const showMessage = async(text) => {
        message.value = text
        await SysCheck();
      }
      const ChannelState = computed(()=> {
        const re = setupStore.getChannelSetting;
        return re.MainDiagnosis || re.SubDiagnosis
      });

      const devMode = computed(()=> authStore.getOpMode);
      
      // Helper functions for disk status display
      const formatSize = (sizeInGB) => {
        if (sizeInGB >= 1024) {
          return (sizeInGB / 1024).toFixed(1) + ' TB';
        }
        return sizeInGB.toFixed(1) + ' GB';
      };

      const getUsagePercentage = (item) => {
        const used = item.totalGB - item.freeGB;
        return Math.round((used / item.totalGB) * 100);
      };

      const getProgressBarColor = (item) => {
        const usage = getUsagePercentage(item);
        if (usage >= 90) return 'bg-red-500';
        if (usage >= 75) return 'bg-yellow-500';
        return 'bg-green-500';
      };

    const CheckAPI = async () => {
      try {
        const response = await axios.get("/setting/checkAPI");
        if (response.data.success){
          health.value = response.data.data;
        }else{
          health.value = '';
        }
      } catch (error) {
        //console.log(error);
        message.value = "Restful API Service is not running";
      }
    };

    const SysCheck = async () => {
      try {
        const response = await axios.get("/setting/SysCheck");
        if (response.data.success){
           diskStatus.value = response.data.disk;
           sysStatus.value = response.data.data;
           //console.log(sysStatus.value);
           versionDict.value = response.data.versions;

           if(!sysStatus.value["smartsystem"])
            checkSmart(sysStatus.value)
          else
            checkSmartflag.value = false;
        }else{
          message.value = "System Check API is not respond"
        }
      } catch (error) {
        message.value = "System Check Failed";
        //console.log(error);
      }
    };
    const checkSmart = async(data) =>{
      if(!data["smartsystem"]){
        try {
          const response = await axios.get("/setting/checkSmartStatus");
          if (response.data.success){
            const stData = response.data.data;
            if(stData["State"] == 0){
              checkSmartflag.value = true;
              errorMsg.value = stData["Message"];
              if (stData["RunTimeErrors"].length > 0){
                errorSmart.value = stData["RunTimeErrors"];
              }
            }            
          }else{
            console.log(response.data.msg);
            //message.value = "System Check API is not respond"
          }
        } catch (error) {
          //message.value = "System Check Failed";
          //console.log(error);
        }
      }
    }

    const getInfluxStatus = async () => {
      try {
        const response = await axios.get("/setting/initDB/status");

        initInfluxStatus.value = response.data.status;
      } catch (error) {
        message.value = "Failed to check Influx Init Status";
        //console.log(error);
      }
    };

    const updateInfluxBucket = async() =>{
      try{
          const response = await axios.get("/setting/setup-downsampling");
          if(response.data.result){
             updateInflux.value = 2;
          }else{
            console.log(response.data.messages);
          }
        }catch(error){
          console.error(error);
        }
    };

    onMounted(()=>{
      SysCheck();
      getInfluxStatus();
      checkInfluxStatus();
      checkFrp();
    })

    const checkInfluxStatus = async()=>{
      try{
          const response = await axios.get("/setting/checkInfluxStatus");
          console.log(response.data);
          if(response.data.result){
              
             updateInflux.value = response.data.status;
          }else{
            console.log(response.data.message);
          }
        }catch(error){
          console.error(error);
        }
    };

    const init = async () => {
      try {
        const response = await axios.get("/setting/initDB");
        if (response.data.success){
          message.value = "InfluxDB initiated"
          authStore.setInstall(3);
        }else{
          message.value = "InfluxDB initialization Failed"
        }
      } catch (error) {
        message.value = "InfluxDB initialization Failed";
      }

      //emit('service-done', message.value);
    };

    provide('sysStatus',sysStatus);
    provide('health', health);

    function parseFullSystemStatus(rawStr) {
      const lines = rawStr.split('\n');
      const result = {};
      let currentKey = null;
      let buffer = '';

      for (let line of lines) {
        line = line.trim();
        if (line.endsWith(':')) {
          currentKey = line.slice(0, -1);
          buffer = '';
        } else if (line.includes(':') && !line.includes('{')) {
          const [key, value] = line.split(':').map(s => s.trim());
          result[key] = value;
          currentKey = null;
        } else if (currentKey) {
          buffer += line;
          if (currentKey === 'Disk Status') {
            result[currentKey] = parseCustomBlock(buffer);
          }
          else {
            try {
              result[currentKey] = JSON.parse(buffer);
            } catch (e) {
              result[currentKey] = buffer;
            }
          }
          currentKey = null;
        }
      }

      return result;
    }

    function parseCustomBlock(str) {
      const pattern = /(\w+)\s*=\s*([^,}]+)/g;
      const result = {};
      let match;
      while ((match = pattern.exec(str)) !== null) {
        const key = match[1];
        const val = match[2].trim();
        result[key] = isNaN(val) ? val : parseFloat(val);
      }
      return result;
    }

    /*  () => ChannelState.value,
      (newVal, oldVal) => {
        if (newVal) {
          CheckAPI();
        } else {
          console.log('둘 다 비활성화됨');
        }
      },
      { immediate: true }
    );*/

    const ResetAll = async () => {
      const confirmed = confirm('All settings and account database will be erased and initialized.\nDo you want to proceed?');
      if (confirmed) {
        try {
          isResetAll.value = true; // ⭐ 로딩 모달 표시
          serviceLoadingMessage.value = 'Initializing system...';
          const response = await axios.get("/setting/ResetAll");
          if (response.data.success){
            message.value = "Setup initiated"
            serviceLoadingMessage.value = 'Initialization is finished!';
            authStore.setInstall(0);

            if (authStore.logout) {
              await authStore.logout();
              router.push("/signin"); 
            } else {
              console.error("❌ Error: logout 함수가 정의되지 않음!");
            }
          }else{
            console.error("데이터 가져오기 실패:", error);
          }
        } catch (error) {
          console.error("데이터 가져오기 실패:", error);
        }finally{
          isResetAll.value = false;
        }
      }
    };

    const InitInfluxCLI = async() =>{
      try {
          const response = await axios.get("/setting/initInfluxCLI");
          if (response.data.status){
            message.value = "Influx CLI initiated"
          }else{
            console.error("Influx CLI init failed:", error);
          }
        } catch (error) {
          console.error("Influx CLI init failed:", error);
        }
      };

    const downloadUrl = computed(() => {
      //return `http://127.0.0.1:5000/api/getFolder?name=${modalSelectItem.value}`
      const hostname = window.location.hostname
      if (devMode.value != 'device0'){
        if(modalSelectItem.value == 'other')
           return `http://${hostname}:4000/setting/backup/download/${modalSelectItem.value}`
        else
          return `http://${hostname}:5000/api/getFolder?name=${modalSelectItem.value}`
      }
      else
        return `http://${hostname}:4000/setting/backup/download/${modalSelectItem.value}`        
    })

    const saveIPAddress = async() =>{
      try {
        const data = { "ip" : ipAddress.value};
        const resp = await axios.post(
          "/setting/setDefaultIP",
          data,
          {
            headers: { "Content-Type": "application/json" },
            withCredentials: true,
          }
        );
        feedbackModalOpen.value = false;
          if(resp.data.success){

            alert('Default IP Address Changed : ' + ipAddress.value);
          }else{
            alert('Failed to default IP Address Change');
          }
        } catch (error) {
          console.error("Influx CLI init failed:", error);
        }
    }

    const checkFrp = async () => {
      try {
        const response = await axios.get(`/setting/checkFrp`);

        frpStatus.value = response.data;
        console.log(frpStatus.value);
      } catch (error) {
        console.error(error);
      }
    };


      return {
        message,
        showMessage,
        health,
        CheckAPI,
        sysStatus,
        diskStatus,
        ChannelState,
        devMode,
        formatSize,
        getUsagePercentage,
        getProgressBarColor,
        ResetAll,
        downloadUrl,
        modalSelectItem,
        InitInfluxCLI,
        serviceLoadingMessage,
        isResetAll,
        initInfluxStatus,
        checkSmartflag,
        errorSmart,
        versionDict,
        updateInflux,
        updateInfluxBucket,
        feedbackModalOpen,
        ipAddress,
        saveIPAddress,
        init,
        frpStatus,
        errorMsg,
      }

    }
  }
  </script>