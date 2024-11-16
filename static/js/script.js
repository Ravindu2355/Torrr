// Global variable to store the magnet link
let currentMagnetLink = '';

// Function to start downloading the torrent
function startDownload() {
    const magnetLink = document.getElementById("magnet-link").value;
    if (!magnetLink) {
        alert("Please enter a magnet link!");
        return;
    }

    currentMagnetLink = magnetLink;
    document.getElementById("progress-section").style.display = "block";
    document.getElementById("stop-section").style.display = "block";
    document.getElementById("file-link").innerHTML = '';

    // Send a GET request to start the download
    fetch(`/download?magnet_link=${magnetLink}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                console.log("Download started.");
                trackProgress();
            }
        })
        .catch(err => {
            console.error("Error starting download:", err);
            alert("Error starting download.");
        });
}

// Function to track the download progress
function trackProgress() {
    const progressInfo = document.getElementById("progress-info");

    const interval = setInterval(() => {
        fetch('/download_progress')
            .then(response => response.json())
            .then(data => {
                if (data[currentMagnetLink]) {
                    const progress = data[currentMagnetLink];
                    progressInfo.innerHTML = `
                        State: ${progress.state}<br>
                        Download Rate: ${progress.download_rate_kb_s.toFixed(1)} KB/s<br>
                        Downloaded: ${progress.downloaded_mb.toFixed(1)} MB<br>
                        Progress: ${progress.progress_percentage.toFixed(1)}%
                    `;
                    
                    // Check if download is complete
                    if (progress.progress_percentage >= 100) {
                        clearInterval(interval);
                        checkDownloadComplete();
                    }
                }
            })
            .catch(err => console.error("Error fetching progress:", err));
    }, 1000);
}

// Function to check if the download is complete
function checkDownloadComplete() {
    fetch(`/download_complete?magnet_link=${currentMagnetLink}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === "Download complete") {
                document.getElementById("file-link").innerHTML = `
                    <a href="/download_file/${data.file_path.split('/').pop()}" download>Click here to download the file</a>
                `;
            } else {
                console.log("Download still in progress...");
            }
        })
        .catch(err => console.error("Error checking download completion:", err));
}

// Function to stop the torrent download
function stopDownload() {
    fetch(`/stop_download?magnet_link=${currentMagnetLink}`)
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                alert(data.status);
                document.getElementById("progress-section").style.display = "none";
                document.getElementById("stop-section").style.display = "none";
            }
        })
        .catch(err => console.error("Error stopping download:", err));
}

