// Source:
// https://attacomsian.com/blog/javascript-download-file
const download = (path, filename) => {
    // Create a new link
    const anchor = document.createElement('a');
    anchor.href = path;
    anchor.download = filename;

    // Append to the DOM
    document.body.appendChild(anchor);

    // Trigger `click` event
    anchor.click();

    // Remove element from DOM
    document.body.removeChild(anchor);
};

const HomePage = {
    template: "#page-home"
};

const ResultPage = {
    template: "#page-results",
    data: function() {
        return {
            isLoading: true,
            videos: [],
            error: null
        }
    },
    computed: {
        hasError: function () {
            return this.error !== null;
        },

        videoCount: function () {
            if (this.videos.length === 1) {
                return `${this.videos.length} Unlisted Video`
            }
            else {
                return `${this.videos.length} Unlisted Videos`
            }
        }
    },
    methods: {
        findUnlistedVideos: function () {
            this.isLoading = true;
            window.fetch(
                $SCRIPT_ROOT + "/api/playlist/" + this.$route.params.playlistId + "?before=2017-01-01&privacy=unlisted",
                { method: "POST" })
                .then(resp =>
                    new Promise((resolve, reject) => {
                        resp.json()
                            .then(json => {
                                resolve([resp.status, json]);
                            })
                            .catch(reason => {
                                reject(reason);
                            });
                    }))
                .then(result => {
                    let [status, json] = result;
                    // let [status, json] = result;
                    if (status === 200) {
                        this.videos = json;
                        this.error = null;
                    }
                    else {
                        this.videos = [];
                        this.error = json.error;
                    }
                    this.isLoading = false;
                });
        },
        downloadVideoUrls: function() {
            const blob = new Blob([
                this.videos.map(video => `${video.title} - ${video.url}`).join("\n")
            ], { type: "text/plain" });
            const url = URL.createObjectURL(blob);
            download(url, "Playlist.txt");
            URL.revokeObjectURL(url);
        }
    },
    created: function () {
        // Listen for changes to our route, so that we can populate the playlistUrl if it doesn't
        this.$watch(
            () => this.$route,
            (route) => {
                // If we're viewing the results of a playlist, pre-populate the playlistUrl with the
                // playlist ID that's in our route.
                if (route.name === "results") {
                    this.findUnlistedVideos();
                }
            },
            { immediate: true}
        );
    }
};

const AppRoutes = [
    { path: "/", component: HomePage, name: "home" },
    { path: "/p/:playlistId", component: ResultPage, name: "results" }
];

const Router = VueRouter.createRouter({
    history: VueRouter.createWebHashHistory(),
    routes: AppRoutes
});

const App = Vue.createApp({
    data: function() {
        return {
            playlistUrl: ""
        }
    },
    computed: {
        isUrlValid: function () {
            if (this.playlistUrl === "") {
                return false;
            }

            try {
                var potentialUrl = new URL(this.playlistUrl);
                if (potentialUrl.hostname !== "www.youtube.com") {
                    return false;
                }

                if (!potentialUrl.pathname.includes("playlist")) {
                    return false;
                }

                if (!potentialUrl.searchParams.has("list")) {
                    return false;
                }

                return true;
            }
            catch (error) {
                // This is not a parsable URL.
                return false;
            }
        }
    },
    methods: {
        findUnlistedVideos: function () {
            // Extract the playlist ID from the playlist URL
            let playlistUrl = new URL(this.playlistUrl);
            let playlistId = playlistUrl.searchParams.get("list");

            this.$router.push({ name: "results", params: { playlistId: playlistId }});
        }
    },
    mounted: function () {
        // Listen for changes to our route, so that we can populate the playlistUrl if it doesn't
        this.$watch(
            () => this.$route,
            (route) => {
                // If we're viewing the results of a playlist, pre-populate the playlistUrl with the
                // playlist ID that's in our route.
                if (route.name === "results") {
                    let playlistId = route.params.playlistId;
                    this.playlistUrl = "https://www.youtube.com/playlist?list=" + playlistId;
                }
                else if (route.name === "home") {
                    // Clear out the playlist URL if we're navigating
                    this.playlistUrl = "";
                }
            },
            { immediate: true}
        );
    }
});
App.config.compilerOptions.delimiters = ["${", "}"];
App.use(Router);
App.mount("#app");
