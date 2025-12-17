<script setup>
import Navbar from './components/navbar.vue';
import {RouterView} from 'vue-router';
</script>

<template>
  <div class="min-h-screen bg-[#F8FAFC] text-[#102d47] font-sans flex flex-col items-center">
    <Navbar/>
    <main class="w-full max-w-7xl pt-28 pb-10 px-4 md:px-8 mx-auto">
      <RouterView/>
    </main>

  </div>
</template>