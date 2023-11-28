<template lang="pug">
.server-create-page

    .server-create-page-body
        .server-create-wrapper
            .server-create-toolbar
                el-input(
                    placeholder="server_port"
                    v-model="filters.server_port"
                )
                el-input(
                    placeholder="target_host"
                    v-model="filters.target_host"
                )
                el-input(
                    placeholder="target_port"
                    v-model="filters.target_port"
                )
                el-input(
                    placeholder="ssh_version"
                    v-model="filters.ssh_version"
                )
                el-button(
                    type="primary"
                    @click="startServer()"
                ) {{!server_started ? "Запустить" : "Остановить"}}
        
</template>

<script>

export default{
    name: 'server-index',
    data(){
        return{
            filters:{
                server_port: null,
                target_host: null,
                target_port: null,
                ssh_version: null,
            },
            server_started: false
        }
    },

    methods: {
        startServer(){
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

            
            
        }
    }

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