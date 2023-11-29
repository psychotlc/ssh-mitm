<template lang="pug">
.server-create-page

    .server-create-page-body
        .server-create-wrapper
            .server-create-toolbar
                el-input(
                    placeholder="serverPort"
                    v-model="filters.serverPort"
                )
                el-input(
                    placeholder="targetHost"
                    v-model="filters.targetHost"
                )
                el-input(
                    placeholder="targetPort"
                    v-model="filters.targetPort"
                )
                el-input(
                    placeholder="sshVersion"
                    v-model="filters.sshVersion"
                )
                el-button(
                    type="primary"
                    @click="startServer()"
                ) {{!serverStarted ? "Запустить" : "Остановить"}}
        
            .log-container 
                span(ref="log")
        
</template>

<script>

import io from 'socket.io-client';

export default{
    name: 'server-index',
    data(){
        return{
            filters:{
                serverPort: null,
                targetHost: null,
                targetPort: null,
                sshVersion: null,
            },
            serverStarted: false,
            logData: ""
        }
    },

    methods: {
        startServer(){
            if (!this.filters.serverPort){
                this.$notify.error({
                    title: 'Error',
                    message: 'serverPort is required'
                });
                return
            }
            if (!this.filters.targetHost){
                this.$notify.error({
                    title: 'Error',
                    message: 'targetHost is required'
                });
                return
            }
            if (!this.filters.targetPort){
                this.$notify.error({
                    title: 'Error',
                    message: 'targetPort is required'
                });
                return
            }
            
            fetch(
                'http://127.0.0.1:5000/start_server',
                {
                    method: 'POST',
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(this.filters)
                }
            ).then((res) => {
                return res.json()
            }).then((res) => {
                console.log(res)
            })
            .catch((err) => {
                console.error(err)
            })

            
            
        }
    },

    mounted() {

        const socket = io.connect('http://localhost:5000');

        socket.on('log_from_server', (log) => {
            this.logData += log + "<br>";

            this.$refs.log.innerHTML = this.logData


        });
    },

}
</script>

<style lang="scss">
.server-create-page{
    height:100vh;
    .server-create-page-body{
        height:100vh;
        display:flex;
        justify-content:center;
        align-items:center;
        .server-create-wrapper{
            border: 1px solid black;
            border-radius: 5px;
            height: 700px;
            .server-create-toolbar{
                padding: 12px;
                border-bottom: 1px solid black;
                column-gap: 12px;
                display:flex;
                .el-input{
                    max-width:120px;
                }
            }
        }
    }
}
</style>