<script setup>
import {ref, onMounted, onUnmounted, computed} from 'vue';
import apiClient, {getImageUrl} from '@/api.js';

const data = ref(null);
const loading = ref(true);
let timer = null;

const statusClass = computed(() => {
  if (!data.value) return 'bg-white text-[#2f73f2] border-2 border-[#ccd7e1]';
  if (data.value.is_violation) return 'bg-red-50 border-2 border-red-500 text-red-600 shadow-lg shadow-red-200';
  if (data.value.car_detected && !data.value.is_violation) return 'bg-green-50 border-2 border-green-500 text-green-600 shadow-lg shadow-green-200';
  return 'bg-white text-[#102d47] border-2 border-[#ccd7e1]';
});

const fetchData = async () => {
  try {
    const res = await apiClient.get('/api/dashboard/latest');
    if (!res.data.error) {
      data.value = res.data;
    }
  } catch (e) {
    console.error("Connection Error", e);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchData();
  timer = setInterval(fetchData, 2000);
});

onUnmounted(() => clearInterval(timer));
</script>

<template>
  <div class="w-full font-sans">
    <header class="mb-10 text-center md:text-left pb-6">
      <h1 class="text-3xl font-extrabold tracking-tight text-[#102d47]">
        紅線違規停車偵測系統
      </h1>
      <p class="mt-2 text-[#668199] text-sm font-medium uppercase tracking-wide">
        Real-time Traffic Monitoring Dashboard
      </p>
    </header>

    <div v-if="loading" class="text-center text-[#668199] py-10 animate-pulse">
      系統初始化中...
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">

      <div
          class="p-8 rounded-2xl shadow-[0px_3px_20px_0px_#8e9ca90d] flex flex-col justify-center items-center transition-all duration-300 min-h-[220px]"
          :class="statusClass"
      >
        <h2 class="text-lg font-bold opacity-70 uppercase tracking-wider mb-2">System Status</h2>
        <template v-if="data">
          <div class="text-4xl font-extrabold my-4">{{ data.status }}</div>
          <div v-if="data.is_violation"
               class="mt-2 px-6 py-2 bg-red-100 rounded-full text-red-600 font-bold animate-pulse">
            ⚠️ VIOLATION DETECTED
          </div>
        </template>
        <template v-else>
          <div class="text-2xl font-bold my-4 text-[#668199]">Standby</div>
          <div class="text-sm text-[#668199] opacity-70">Waiting for data input...</div>
        </template>
      </div>

      <div v-if="data"
           class="bg-white p-8 rounded-2xl shadow-[0px_3px_20px_0px_#8e9ca90d] border border-gray-100 flex flex-col justify-center">
        <h3 class="text-lg font-bold text-[#102d47] mb-6 border-b border-gray-100 pb-2">Metrics</h3>
        <ul class="space-y-6">
          <li class="flex justify-between items-center">
            <span class="text-gray-500 font-medium text-lg">Car Detected</span>
            <span class="text-xl" :class="data.car_detected ? 'text-[#2f73f2] font-bold' : 'text-gray-400'">
              {{ data.car_detected ? 'YES' : 'NO' }}
            </span>
          </li>
          <li class="flex justify-between items-center">
            <span class="text-gray-500 font-medium text-lg">Red Line Zone</span>
            <span class="text-purple-600 font-bold bg-purple-50 px-3 py-1 rounded">Active</span>
          </li>
          <li class="flex justify-between items-center pt-2 mt-2 border-t border-gray-50">
            <span class="text-sm text-[#668199]">Last Update</span>
            <span class="font-mono text-sm text-[#102d47] font-bold">{{
                new Date(data.timestamp).toLocaleTimeString()
              }}</span>
          </li>
        </ul>
      </div>

      <div v-else
           class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 opacity-60 flex items-center justify-center">
        <span class="text-[#668199] font-medium">Waiting for data stream...</span>
      </div>

      <div v-if="data"
           class="bg-white p-6 rounded-2xl shadow-[0px_3px_20px_0px_#8e9ca90d] border border-gray-100 col-span-1 md:col-span-2">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold text-[#102d47]">📹 Live Camera Feed</h3>
          <div class="flex items-center gap-2 px-3 py-1 bg-red-50 rounded-full border border-red-100">
            <span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
            <span class="text-xs text-red-600 font-bold">LIVE</span>
          </div>
        </div>

        <div
            class="relative bg-gray-100 rounded-xl overflow-hidden min-h-[300px] flex items-center justify-center border border-gray-200">
          <img :src="getImageUrl(data.image_url)" alt="Live View"
               class="w-full max-h-[600px] object-contain block"/>

          <div v-if="data.is_violation"
               class="absolute inset-0 border-4 border-red-500/50 animate-pulse pointer-events-none rounded-xl"></div>
          <div v-if="data.is_violation"
               class="absolute top-6 left-6 bg-red-600 text-white px-6 py-2 font-bold rounded-full shadow-lg backdrop-blur-sm border border-white/20 text-lg">
            VIOLATION DETECTED
          </div>
        </div>
      </div>

    </div>
  </div>
</template>