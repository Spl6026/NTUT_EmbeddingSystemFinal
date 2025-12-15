<script setup>
import {ref, onMounted, onUnmounted} from 'vue';
import {RouterLink, useRoute} from 'vue-router';

const route = useRoute();
const isSticky = ref(false);
const navbarOpen = ref(false);

const menuData = [
  {label: "Home", href: "/"},
  {label: "History", href: "/history"},
  {label: "Manual Test", href: "/upload"},
];

const handleScroll = () => {
  if (window.scrollY >= 80) {
    isSticky.value = true;
  } else {
    isSticky.value = false;
  }
};

onMounted(() => {
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});
</script>

<template>
  <header
      class="fixed top-0 left-0 w-full z-50 transition-all duration-300"
      :class="[
            isSticky
                ? 'bg-white/95 dark:bg-[#000f30]/95 backdrop-blur-sm shadow-lg h-20'
                : 'bg-transparent h-24'
        ]"
  >
    <div class="max-w-8xl mx-auto px-4 md:px-8 xl:px-20 h-full flex items-center justify-between">

      <RouterLink to="/" class="flex items-center gap-2 group">
        <div
            class="w-10 h-10 rounded-lg bg-[#2f73f2] flex items-center justify-center text-white font-bold text-xl shadow-lg transition-transform group-hover:scale-110">
          V
        </div>
        <div class="flex flex-col">
                    <span class="text-xl font-bold text-[#102d47] dark:text-white tracking-wide">
                        Traffic<span class="text-[#2f73f2]">Hub</span>
                    </span>
        </div>
      </RouterLink>

      <nav class="hidden lg:flex items-center gap-8">
        <RouterLink
            v-for="(item, index) in menuData"
            :key="index"
            :to="item.href"
            class="text-base font-medium transition-colors duration-300"
            :class="[
                        route.path === item.href
                            ? 'text-[#2f73f2]'
                            : 'text-[#102d47] dark:text-white hover:text-[#2f73f2] dark:hover:text-[#2f73f2]'
                    ]"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <button
          @click="navbarOpen = !navbarOpen"
          class="lg:hidden w-10 h-10 flex flex-col justify-center items-center gap-1.5 rounded-xl transition-all duration-300 hover:bg-[#2f73f2]/10 focus:outline-none group"
      >
                <span
                    class="block w-6 h-0.5 bg-[#102d47] rounded-full transition-all duration-300 origin-center"
                    :class="{'rotate-45 translate-y-2': navbarOpen, 'group-hover:bg-[#2f73f2]': !navbarOpen}"
                ></span>

        <span
            class="block w-6 h-0.5 bg-[#102d47] rounded-full transition-all duration-300"
            :class="{'opacity-0 scale-0': navbarOpen, 'group-hover:bg-[#2f73f2]': !navbarOpen}"
        ></span>

        <span
            class="block w-6 h-0.5 bg-[#102d47] rounded-full transition-all duration-300 origin-center"
            :class="{'-rotate-45 -translate-y-2': navbarOpen, 'group-hover:bg-[#2f73f2]': !navbarOpen}"
        ></span>
      </button>

    </div>

    <div
        class="lg:hidden fixed top-0 right-0 h-screen w-full max-w-xs bg-white dark:bg-[#081738] shadow-2xl transform transition-transform duration-300 z-50 pt-24 px-6"
        :class="navbarOpen ? 'translate-x-0' : 'translate-x-full'"
    >
      <nav class="flex flex-col space-y-4">
        <RouterLink
            v-for="(item, index) in menuData"
            :key="index"
            :to="item.href"
            @click="navbarOpen = false"
            class="block py-2 text-lg font-medium border-b border-gray-100 dark:border-gray-800"
            :class="[
                         route.path === item.href
                            ? 'text-[#2f73f2]'
                            : 'text-[#102d47] dark:text-white'
                    ]"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>

    <div
        v-if="navbarOpen"
        @click="navbarOpen = false"
        class="lg:hidden fixed inset-0 bg-black/50 z-40"
    ></div>
  </header>
</template>