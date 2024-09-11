<concordance-media-window class="concordance-media-window">
    <div if={show} class="mediaWindowWrapper z-depth-5">
        <div class="close right" onclick={onCloseClick}>
            <i class="material-icons grey-text material-clickable">close</i>
        </div>
        <div class="mediaWindowContent">
            <div class="center-align">
                <audio if={link.mediatype == "audio"} ref="audio" controls autoplay>
                    <source src={link.url}>
                    Your browser does not support playing audio files.
                </audio>
                <video if={link.mediatype == "video"} ref="video" controls autoplay>
                    <source src={link.url}>
                    Your browser does not support playing video files.
                </video>
                <img if={link.mediatype == "image"} ref="image" src="{link.url}" loading="lazy">
            </div>
            <div class="fileInfo dividerTop grey-text">
                {_("file")}: {fileName}
                <br>
                <span>
                    URL: {link.url}
                </span>
                <a href={link.url} class="btn btn-floating btn-flat btn-small" target="_blank">
                    <i class="material-icons">open_in_new</i>
                </a>
            </div>
        </div>
    </div>

    <script>
        require("./concordance-media-window.scss")

        this.show = false
        this.content = null

        onShow(link){
            let wasShown = this.show
            this.show = true
            this.link = link
            this.fileName = link.url.substring(link.url.lastIndexOf('/') + 1)
            if(this.fileName.indexOf("?") != -1){
                this.fileName = this.fileName.split("?")[0]
            }
            this.update()
            this.root.classList.add("show")
            if(wasShown && (link.mediatype == "audio" || link.mediatype == "video")){
                this.refs[link.mediatype].load()
                this.refs[link.mediatype].play()
            }
        }

        onCloseClick(evt){
            evt.preventUpdate = true
            this.close()
        }

        close(){
            if(this.show){
                this.show = false
                this.root.classList.remove("show")
                delay(this.update, 200)
            }
        }

        this.on("mount", () => {
            Dispatcher.on("concordanceOpenMedia", this.onShow)
        })
        this.on("unmount", () => {
            Dispatcher.off("concordanceOpenMedia", this.onShow)
        })
    </script>
</concordance-media-window>
