import {createRouter, createWebHistory} from 'vue-router'
import Index from "@/views/index.vue";
import Upload from "@/views/upload.vue";
import History from "@/views/history.vue";

const routes = [
    {
        path: '/',
        name: 'index',
        component: Index
    },
    {
        path: '/upload', // 新增這個路由
        name: 'upload',
        component: Upload
    },
    {
        path: '/history',
        name: 'history',
        component: History
    },
    {
        path: '/:pathMatch(.*)*',
        redirect: '/',
        beforeEnter: (to, from, next) => {
            if (to.path.startsWith('/php')) {
                window.location.href = to.fullPath;
            } else {
                next();
            }
        }

    }
]

const router = createRouter({
    history: createWebHistory(),
    routes,
});

export default router;