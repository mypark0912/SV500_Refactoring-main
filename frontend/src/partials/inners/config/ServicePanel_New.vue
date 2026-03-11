<template>
  <div class="grow">
    <!-- Panel body -->
    <div class="p-6">
      <h2 class="text-2xl text-gray-800 dark:text-gray-100 font-bold mb-5">System Service</h2>

      <!-- General -->
      <div class="mb-6">
        <!-- Filters -->
        <div class="mt-4 flex gap-2 border-b border-gray-200 dark:border-gray-700/60 pb-4">
          <div class="flex items-center gap-4 mb-4">
            <!-- Influx Init Status -->
            <div class="flex items-center gap-3">
              <label class="text-sm text-gray-700 dark:text-gray-300 font-medium">
                Influxdb Init Status
              </label>
              <span v-if="initInfluxStatus === 'IDLE'" class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-gray-500/20 text-gray-700 font-semibold">
                {{ initInfluxStatus }}
              </span>
              <span v-else-if="initInfluxStatus === 'COMPLETE'" class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-green-500/20 text-green-700 font-semibold">
                {{ initInfluxStatus }}
              </span>
              <span v-else-if="initInfluxStatus === 'FAIL'" class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-red-500/20 text-red-700 font-semibold">
                {{ initInfluxStatus }}
              </span>
              <span v-else class="text-sm rounded-full px-3 py-1 min-w-[100px] w-fit text-center whitespace-nowrap transition-all bg-yellow-500/20 text-yellow-700 font-semibold">
                {{ initInfluxStatus }}
              </span>
              
              <button
                v-if="updateInflux === 0"
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
              
              <button
                v-if="updateInflux === 1"
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

            <div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
            
            <!-- Factory Default 버튼 -->
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
            
            <!-- Set Default IP 버튼 -->
            <button
              class="btn h-9 px-5 bg-sky-900 text-sky-100 hover:bg-sky-800 dark:bg-sky-100 dark:text-sky-800 dark:hover:bg-white flex items-center"
              @click.stop="feedbackModalOpen = true"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10,9 9,9 8,9"/>
              </svg>
              &nbsp; Set Default IP
            </button>
            <div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>
            <button
              class="btn h-9 px-5 bg-teal-900 text-teal-100 hover:bg-teal-800 dark:bg-teal-100 dark:text-teal-800 dark:hover:bg-white flex items-center"
              @click.stop="openParquetModal"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              &nbsp; PARQUET Download
            </button>
            <button
              class="btn h-9 px-5 bg-pink-900 text-pink-100 hover:bg-pink-800 dark:bg-pink-100 dark:text-pink-800 dark:hover:bg-white flex items-center"
              @click.stop="csvModalOpen = true"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              &nbsp; CSV Download
            </button>
          </div>
        </div>
        
        <div v-if="message" class="text-sm text-gray-800 dark:text-gray-100 mt-2">
          {{ message }} 🙌
        </div>
      </div>

      <!-- Service Cards -->
      <section class="pb-6 border-b border-gray-200 dark:border-gray-700/60">
        <div class="grid grid-cols-12 gap-6">
          <ServiceCard item="Redis" :version="versionDict['Redis']" @service-done="showMessage" @open-log="openLogModal"/>
          <ServiceCard item="InfluxDB" :version="versionDict['InfluxDB']" @service-done="showMessage" @open-log="openLogModal"/>
          <ServiceCard item="Core" :version="versionDict['Core']" @service-done="showMessage" @open-log="openLogModal"/>
          <ServiceCard item="WebServer" :version="versionDict['WebServer']" @service-done="showMessage" @open-log="openLogModal"/>
          <ServiceCard item="A35" :version="versionDict['A35']" @service-done="showMessage" @open-log="openLogModal"/>
          <ServiceCard2 item="fw" :version="versionDict['fw']"/>
          
          <!-- MQTTClient (조건부) -->
          <ServiceCard
            v-if="'mqClient' in sysStatus"
            item="MQTTClient"
            :version="versionDict['MQTTClient']"
            @service-done="showMessage"
            @open-log="openLogModal"
          />
          
          <!-- frpc (조건부) -->
          <ServiceCard
            v-if="frpStatus.exist"
            item="frpc"
            @service-done="showMessage"
            @open-log="openLogModal"
          />
          
          <!-- SmartSystems (조건부) -->
          <ServiceCard
            v-if="devMode !== 'device0'"
            item="SmartSystems"
            :version="versionDict['SmartSystems']"
            @service-done="showMessage"
            @open-log="openLogModal"
          />
          <ServiceCard
            v-if="devMode !== 'device0'"
            item="SmartAPI"
            :version="versionDict['SmartSystems']"
            @service-done="showMessage"
            @open-log="openLogModal"
          />
          
          <!-- SmartSystem 에러 상세 -->
          <!--ServiceDetail
            v-if="devMode !== 'device0'"
            :data="errorSmart"
            :msg="stateSmart"
          /-->
        </div>
      </section>

      <!-- Disk Status Section -->
      <section class="mt-6">
        <h3 class="text-lg text-gray-800 dark:text-gray-100 font-semibold mb-4">Disk Status</h3>
        
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
                    <span
                      v-if="item.status === 'ok'"
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-base font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                    >
                      <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                      </svg>
                      OK
                    </span>
                    <span
                      v-else
                      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-base font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
                    >
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
                    <div
                      class="h-3 rounded-full transition-all duration-300"
                      :class="getProgressBarColor(item)"
                      :style="{ width: getUsagePercentage(item) + '%' }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Mobile Card View -->
        <div class="md:hidden space-y-4">
          <div
            v-for="item in diskStatus"
            :key="item.drive"
            class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
          >
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
              <span
                v-if="item.status === 'ok'"
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
              >
                OK
              </span>
              <span
                v-else
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
              >
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
                <div
                  class="h-3 rounded-full transition-all duration-300"
                  :class="getProgressBarColor(item)"
                  :style="{ width: getUsagePercentage(item) + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
    
    <!-- Loading Modal -->
    <LoadingModal
      :isOpen="isResetAll"
      title="Reset System as factory default initialization"
      :message="serviceLoadingMessage"
    />
    
    <!-- IP Address Modal -->
    <ModalBasic
      id="feedback-modal"
      :modalOpen="feedbackModalOpen"
      @close-modal="feedbackModalOpen = false"
      title="IP Address Configuration"
    >
      <div class="px-5 py-4">
        <div class="text-sm">
          <div class="font-medium text-gray-800 dark:text-gray-100 mb-3">
            Enter IP Address
          </div>
        </div>
        <div class="space-y-3">
          <div>
            <label class="block text-sm font-medium mb-1" for="ipaddress">
              IP Address <span class="text-red-500">*</span>
            </label>
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
      </div>
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
    
    <!-- Log Modal -->
    <LogModal
      :isOpen="logModalOpen"
      :service="logModalService"
      @close="logModalOpen = false"
    />

    <!-- Parquet Download Modal -->
    <ModalBasic
      id="parquet-modal"
      :modalOpen="parquetModalOpen"
      @close-modal="parquetModalOpen = false"
      title="PARQUET Download"
    >
      <div style="min-width: 560px;">
        <!-- Tabs -->
        <div class="flex border-b border-gray-200 dark:border-gray-700/60">
          <button
            class="px-5 py-3 text-sm font-medium transition-colors"
            :class="parquetTab === 'report'
              ? 'text-teal-600 dark:text-teal-400 border-b-2 border-teal-500'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
            @click="switchParquetTab('report')"
          >
            Report
          </button>
          <button
            class="px-5 py-3 text-sm font-medium transition-colors"
            :class="parquetTab === 'trend'
              ? 'text-teal-600 dark:text-teal-400 border-b-2 border-teal-500'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'"
            @click="switchParquetTab('trend')"
          >
            DiagnosisTrend
          </button>
        </div>

        <div class="px-5 py-4" style="max-height: 450px; overflow-y: auto;">
          <!-- Loading -->
          <div v-if="parquetLoading" class="flex items-center justify-center py-8">
            <svg class="animate-spin h-6 w-6 text-teal-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            <span class="text-sm text-gray-500 dark:text-gray-400">Loading...</span>
          </div>

          <!-- ========== Report Tab ========== -->
          <template v-else-if="parquetTab === 'report'">
            <div v-if="Object.keys(reportFiles).length === 0" class="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
              No report files found.
            </div>
            <div v-else>
              <div class="flex justify-end mb-3">
                <button
                  class="btn-sm bg-teal-600 text-white hover:bg-teal-700 dark:bg-teal-500 dark:hover:bg-teal-600 flex items-center"
                  @click="downloadAllReports"
                  :disabled="parquetDownloading"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-1">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  Download All
                </button>
              </div>
              <div v-for="(items, channel) in reportFiles" :key="channel" class="mb-4">
                <h4 class="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-2">
                  Channel: {{ channel }}
                </h4>
                <div class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <table class="w-full text-sm">
                    <thead>
                      <tr class="bg-gray-50 dark:bg-gray-700">
                        <th class="text-left px-3 py-2 font-medium text-gray-600 dark:text-gray-300">Date</th>
                        <th class="text-left px-3 py-2 font-medium text-gray-600 dark:text-gray-300">EN50160</th>
                        <th class="text-left px-3 py-2 font-medium text-gray-600 dark:text-gray-300">Diagnosis</th>
                        <th class="text-center px-3 py-2 font-medium text-gray-600 dark:text-gray-300 w-24">Download</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-600">
                      <tr v-for="item in items" :key="item.date" class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        <td class="px-3 py-2 text-gray-800 dark:text-gray-200 font-mono">{{ formatDate(item.date) }}</td>
                        <td class="px-3 py-2 text-gray-600 dark:text-gray-400 text-xs truncate max-w-[160px]" :title="item.en50160">{{ item.en50160 }}</td>
                        <td class="px-3 py-2 text-xs truncate max-w-[160px]" :title="item.diagnosis || ''">
                          <span v-if="item.diagnosis" class="text-gray-600 dark:text-gray-400">{{ item.diagnosis }}</span>
                          <span v-else class="text-gray-400 dark:text-gray-600">-</span>
                        </td>
                        <td class="px-3 py-2 text-center">
                          <button
                            class="inline-flex items-center text-teal-600 hover:text-teal-800 dark:text-teal-400 dark:hover:text-teal-300"
                            @click="downloadReport(channel, item.date)"
                            :disabled="parquetDownloading"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                              <polyline points="7 10 12 15 17 10"/>
                              <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </template>

          <!-- ========== DiagnosisTrend Tab ========== -->
          <template v-else-if="parquetTab === 'trend'">
            <div v-if="trendFiles.length === 0" class="text-center py-8 text-sm text-gray-500 dark:text-gray-400">
              No trend files found.
            </div>
            <div v-else>
              <div class="flex justify-end mb-3">
                <button
                  class="btn-sm bg-teal-600 text-white hover:bg-teal-700 dark:bg-teal-500 dark:hover:bg-teal-600 flex items-center"
                  @click="downloadAllTrends"
                  :disabled="parquetDownloading"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-1">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  Download All
                </button>
              </div>
              <div class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <table class="w-full text-sm">
                <thead>
                  <tr class="bg-gray-50 dark:bg-gray-700">
                    <th class="text-left px-3 py-2 font-medium text-gray-600 dark:text-gray-300">File Name</th>
                    <th class="text-center px-3 py-2 font-medium text-gray-600 dark:text-gray-300 w-24">Download</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-600">
                  <tr v-for="file in trendFiles" :key="file" class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td class="px-3 py-2 text-gray-800 dark:text-gray-200">{{ file }}</td>
                    <td class="px-3 py-2 text-center">
                      <button
                        class="inline-flex items-center text-teal-600 hover:text-teal-800 dark:text-teal-400 dark:hover:text-teal-300"
                        @click="downloadTrend(file)"
                        :disabled="parquetDownloading"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                          <polyline points="7 10 12 15 17 10"/>
                          <line x1="12" y1="15" x2="12" y2="3"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            </div>
          </template>
        </div>

        <!-- Footer -->
        <div class="px-5 py-3 border-t border-gray-200 dark:border-gray-700/60">
          <div class="flex justify-end">
            <button
              class="btn-sm border-gray-200 dark:border-gray-700/60 hover:border-gray-300 dark:hover:border-gray-600 text-gray-800 dark:text-white"
              @click.stop="parquetModalOpen = false"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </ModalBasic>

    <!-- CSV Download Modal -->
    <ModalBasic
      id="csv-modal"
      :modalOpen="csvModalOpen"
      @close-modal="csvModalOpen = false"
      title="CSV Download"
    >
      <div class="px-5 py-4">
        <div class="space-y-4">
          <!-- Channel -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Channel</label>
            <select v-model="csvChannel" class="form-select w-full px-2 py-1">
              <option value="Main">Main</option>
              <option value="Sub">Sub</option>
            </select>
          </div>
          <!-- Date Range -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Date</label>
              <input type="date" v-model="csvStartDate" class="form-input w-full px-2 py-1" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End Date</label>
              <input type="date" v-model="csvEndDate" class="form-input w-full px-2 py-1" />
            </div>
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            Leave empty for last 2 days. Downloads meter trend, energy trend, and demand (if enabled) as ZIP.
          </p>
        </div>
      </div>
      <div class="px-5 py-4 border-t border-gray-200 dark:border-gray-700/60">
        <div class="flex flex-wrap justify-end space-x-2">
          <button
            class="btn-sm bg-emerald-600 text-white hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600 flex items-center"
            :disabled="csvDownloading"
            @click.prevent="downloadTrendCsv"
          >
            <svg v-if="csvDownloading" class="animate-spin w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            {{ csvDownloading ? 'Downloading...' : 'Download' }}
          </button>
          <button
            class="btn-sm border-gray-200 dark:border-gray-700/60 hover:border-gray-300 dark:hover:border-gray-600 text-gray-800 dark:text-white"
            @click.stop="csvModalOpen = false"
          >
            Cancel
          </button>
        </div>
      </div>
    </ModalBasic>
  </div>
</template>

<script>
import { onMounted, ref, provide, computed } from 'vue';
import { useAuthStore } from '@/store/auth';
import axios from 'axios';

import ServiceCard from './ServiceCard_New.vue';
import ServiceCard2 from './ServiceCard2.vue';
import ServiceDetail from './ServiceDetail.vue';
import LoadingModal from '../../../components/LoadingModal.vue';
import ModalBasic from '../../../pages/common/ModalBasic.vue';
import LogModal from './appLogModal.vue';

export default {
  name: 'ServicePannel',
  components: {
    ServiceCard,
    ServiceCard2,
    ServiceDetail,
    LoadingModal,
    ModalBasic,
    LogModal,
  },
  
  setup() {
    const authStore = useAuthStore();
    
    // 상태
    const message = ref('');
    const sysStatus = ref({});
    const diskStatus = ref([]);
    const versionDict = ref({});
    const initInfluxStatus = ref('');
    const updateInflux = ref(null);
    const isResetAll = ref(false);
    const serviceLoadingMessage = ref('');
    //const checkSmartflag = ref(false);
    const errorSmart = ref([]);
    const stateSmart = ref({});
    const feedbackModalOpen = ref(false);
    const ipAddress = ref('');
    const frpStatus = ref({ exist: false, status: false });
    
    // 로그 모달 상태
    const logModalOpen = ref(false);
    const logModalService = ref('');

    // CSV 다운로드 모달 상태
    const csvModalOpen = ref(false);
    const csvChannel = ref('Main');
    const csvStartDate = ref('');
    const csvEndDate = ref('');
    const csvDownloading = ref(false);

    // Parquet 모달 상태
    const parquetModalOpen = ref(false);
    const parquetTab = ref('report');
    const reportFiles = ref({});
    const trendFiles = ref([]);
    const parquetLoading = ref(false);
    const parquetDownloading = ref(false);

    const devMode = computed(() => authStore.getOpMode);

    // Provide for child components
    provide('sysStatus', sysStatus);
    provide('health', ref(''));

    // Methods
    const showMessage = async (text) => {
      message.value = text;
      await SysCheck();
    };

    const openLogModal = (service) => {
      logModalService.value = service;
      logModalOpen.value = true;
    };

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

    const SysCheck = async () => {
      try {
        const response = await axios.get('/setting/SysCheck');
        if (response.data.success) {
          diskStatus.value = response.data.disk;
          sysStatus.value = response.data.data;
          versionDict.value = response.data.versions;

          // if (!sysStatus.value['smartsystem']) {
          //   checkSmartflag.value = true;
          // } else {
          //   checkSmartflag.value = false;
          // }
        } else {
          message.value = 'System Check API is not respond';
        }
      } catch (error) {
        message.value = 'System Check Failed';
      }
    };

    // const checkSmart = async (data) => {
    //   if (!data['smartsystem']) {
    //     try {
    //       const response = await axios.get('/setting/checkSmartStatus');
    //       if (response.data.success) {
    //         const stData = response.data.data;
    //         stateSmart.value = {
    //             'state': stData['State'],
    //             'msg': stData['Message']
    //         };
    //         if (stData['RunTimeErrors'].length > 0) {
    //             errorSmart.value = stData['RunTimeErrors'];
    //           }
    //       }
    //     } catch (error) {
    //       // ignore
    //     }
    //   }
    // };

    const getInfluxStatus = async () => {
      try {
        const response = await axios.get('/setting/initDB/status');
        initInfluxStatus.value = response.data.status;
      } catch (error) {
        message.value = 'Failed to check Influx Init Status';
      }
    };

    const checkInfluxStatus = async () => {
      try {
        const response = await axios.get('/setting/checkInfluxStatus');
        if (response.data.result) {
          updateInflux.value = response.data.status;
        }
      } catch (error) {
        console.error(error);
      }
    };

    const checkFrp = async () => {
      try {
        const response = await axios.get('/setting/checkFrp');
        frpStatus.value = response.data;
        sysStatus.value['frpc'] = frpStatus.value.status;
      } catch (error) {
        console.error(error);
      }
    };

    const init = async () => {
      try {
        const response = await axios.get('/setting/initDB');
        if (response.data.success) {
          message.value = 'InfluxDB initiated';
          authStore.setInstall(3);
        } else {
          message.value = 'InfluxDB initialization Failed';
        }
      } catch (error) {
        message.value = 'InfluxDB initialization Failed';
      }
    };

    const updateInfluxBucket = async () => {
      try {
        const response = await axios.get('/setting/setup-downsampling');
        if (response.data.result) {
          updateInflux.value = 2;
        }
      } catch (error) {
        console.error(error);
      }
    };

    const ResetAll = async () => {
      const confirmed = confirm(
        'All settings and account database will be erased and initialized.\nDo you want to proceed?'
      );
      if (confirmed) {
        try {
          isResetAll.value = true;
          serviceLoadingMessage.value = 'Initializing system...';
          
          const response = await axios.get('/setting/ResetAll');
          if (response.data.success) {
            message.value = 'Setup initiated';
            serviceLoadingMessage.value = 'Initialization is finished!';
            authStore.setInstall(0);

            if (authStore.logout) {
              await authStore.logout();
              router.push('/signin');
            }
          }
        } catch (error) {
          console.error('데이터 가져오기 실패:', error);
        } finally {
          isResetAll.value = false;
        }
      }
    };

    const fetchReportList = async () => {
      parquetLoading.value = true;
      try {
        const response = await axios.get('/setting/backup/parquet/report/list');
        reportFiles.value = response.data.success ? response.data.data : {};
      } catch (error) {
        console.error('Report list failed:', error);
        reportFiles.value = {};
      } finally {
        parquetLoading.value = false;
      }
    };

    const fetchTrendList = async () => {
      parquetLoading.value = true;
      try {
        const response = await axios.get('/setting/backup/parquet/trend/list');
        trendFiles.value = response.data.success ? response.data.data : [];
      } catch (error) {
        console.error('Trend list failed:', error);
        trendFiles.value = [];
      } finally {
        parquetLoading.value = false;
      }
    };

    const openParquetModal = () => {
      parquetModalOpen.value = true;
      parquetTab.value = 'report';
      fetchReportList();
    };

    const switchParquetTab = (tab) => {
      parquetTab.value = tab;
      if (tab === 'report') fetchReportList();
      else fetchTrendList();
    };

    const formatDate = (d) => {
      if (d && d.length === 8) return `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}`;
      return d;
    };

    const triggerDownload = (blob, filename) => {
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    };

    const downloadReport = async (channel, date) => {
      try {
        parquetDownloading.value = true;
        const response = await axios.get('/setting/backup/parquet/report/download', {
          params: { channel, date },
          responseType: 'blob',
        });
        const contentType = response.headers['content-type'] || '';
        const filename = contentType.includes('gzip')
          ? `report_${channel}_${date}.tar.gz`
          : `en50160_weekly_${date}.parquet`;
        triggerDownload(new Blob([response.data]), filename);
      } catch (error) {
        console.error('Report download failed:', error);
        alert('Download failed');
      } finally {
        parquetDownloading.value = false;
      }
    };

    const downloadAllReports = async () => {
      try {
        parquetDownloading.value = true;
        const response = await axios.get('/setting/backup/parquet/report/download-all', {
          responseType: 'blob',
        });
        triggerDownload(new Blob([response.data]), `backup_report_all.tar.gz`);
      } catch (error) {
        console.error('Report download-all failed:', error);
        alert('Download failed');
      } finally {
        parquetDownloading.value = false;
      }
    };

    const downloadAllTrends = async () => {
      try {
        parquetDownloading.value = true;
        const response = await axios.get('/setting/backup/parquet/trend/download-all', {
          responseType: 'blob',
        });
        triggerDownload(new Blob([response.data]), `backup_trend_all.tar.gz`);
      } catch (error) {
        console.error('Trend download-all failed:', error);
        alert('Download failed');
      } finally {
        parquetDownloading.value = false;
      }
    };

    const downloadTrend = async (filename) => {
      try {
        parquetDownloading.value = true;
        const response = await axios.get('/setting/backup/parquet/trend/download', {
          params: { filename },
          responseType: 'blob',
        });
        triggerDownload(new Blob([response.data]), filename);
      } catch (error) {
        console.error('Trend download failed:', error);
        alert('Download failed');
      } finally {
        parquetDownloading.value = false;
      }
    };

    const downloadTrendCsv = async () => {
      try {
        csvDownloading.value = true;

        const pad = (n) => String(n).padStart(2, '0');
        const tzOffset = (() => {
          const off = new Date().getTimezoneOffset();
          const sign = off <= 0 ? '+' : '-';
          const h = pad(Math.floor(Math.abs(off) / 60));
          const m = pad(Math.abs(off) % 60);
          return `${sign}${h}:${m}`;
        })();

        let startDate, endDate;
        if (csvStartDate.value && csvEndDate.value) {
          startDate = `${csvStartDate.value}T00:00:00${tzOffset}`;
          endDate = `${csvEndDate.value}T23:59:59${tzOffset}`;
        } else {
          const now = new Date();
          const twoDaysAgo = new Date(now.getTime() - 2 * 24 * 60 * 60 * 1000);
          startDate = `${twoDaysAgo.getFullYear()}-${pad(twoDaysAgo.getMonth()+1)}-${pad(twoDaysAgo.getDate())}T00:00:00${tzOffset}`;
          endDate = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T23:59:59${tzOffset}`;
        }

        const response = await axios.post(
          `/api/downloadTrendCsv/${csvChannel.value}`,
          { startDate, endDate },
          { responseType: 'blob' }
        );

        const disposition = response.headers['content-disposition'] || '';
        const match = disposition.match(/filename="?(.+?)"?$/);
        const filename = match ? match[1] : `trend_${csvChannel.value}.zip`;
        triggerDownload(new Blob([response.data]), filename);
        csvModalOpen.value = false;
      } catch (error) {
        console.error('CSV download failed:', error);
        alert('CSV Download failed');
      } finally {
        csvDownloading.value = false;
      }
    };

    const saveIPAddress = async () => {
      try {
        const data = { ip: ipAddress.value };
        const resp = await axios.post('/setting/setDefaultIP', data, {
          headers: { 'Content-Type': 'application/json' },
          withCredentials: true,
        });
        feedbackModalOpen.value = false;
        
        if (resp.data.success) {
          alert('Default IP Address Changed : ' + ipAddress.value);
        } else {
          alert('Failed to default IP Address Change');
        }
      } catch (error) {
        console.error('IP 설정 실패:', error);
      }
    };

    onMounted(async() => {
      await SysCheck();
      getInfluxStatus();
      checkInfluxStatus();
      checkFrp();
    });

    return {
      message,
      sysStatus,
      diskStatus,
      versionDict,
      devMode,
      initInfluxStatus,
      updateInflux,
      isResetAll,
      serviceLoadingMessage,
      //checkSmartflag,
      errorSmart,
      stateSmart,
      feedbackModalOpen,
      ipAddress,
      frpStatus,
      logModalOpen,
      logModalService,
      parquetModalOpen,
      parquetTab,
      reportFiles,
      trendFiles,
      parquetLoading,
      parquetDownloading,
      showMessage,
      openLogModal,
      formatSize,
      getUsagePercentage,
      getProgressBarColor,
      init,
      updateInfluxBucket,
      ResetAll,
      saveIPAddress,
      openParquetModal,
      switchParquetTab,
      formatDate,
      downloadReport,
      downloadAllReports,
      downloadTrend,
      downloadAllTrends,
      csvModalOpen,
      csvChannel,
      csvStartDate,
      csvEndDate,
      csvDownloading,
      downloadTrendCsv,
    };
  },
};
</script>