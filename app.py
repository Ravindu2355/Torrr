import os
import time
import libtorrent as lt
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Disable CORS errors globally (you can restrict CORS based on your needs)

# Directory for downloaded files
DOWNLOAD_DIR = 'public_downloads/'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# This dictionary will store the download handle for each active torrent by its magnet link
active_torrents = {}
#url_for('static', filename='path/to/file')

@app.route('/download', methods=['GET'])
def download_torrent():
    """Download the content of the magnet link to the public directory and return progress"""
    magnet_link = request.args.get('magnet_link')
    
    if not magnet_link:
        return jsonify({"error": "Magnet link is required."}), 400
    
    # Check if the torrent is already being downloaded
    if magnet_link in active_torrents:
        return jsonify({"error": "Torrent is already being downloaded."}), 400

    # Initialize torrent session and download
    try:
        # Create a session and configure the download path
        ses = lt.session()
        ses.listen_on(6881, 6891)

        # Prepare the params for the torrent handle
        params = {
            'save_path': DOWNLOAD_DIR
        }

        # Add magnet link and start downloading
        torrent_handle = ses.add_magnet(magnet_link)
        active_torrents[magnet_link] = torrent_handle
        
        # Start downloading and track the progress
        return jsonify({"status": "Torrent download started", "magnet_link": magnet_link, "download_path": DOWNLOAD_DIR})
    except Exception as e:
        return jsonify({"error": f"Failed to start download: {str(e)}"}), 500

@app.route('/download_progress', methods=['GET'])
def get_download_progress():
    """Return the download progress of the torrents"""
    progress_data = {}
    
    # Check progress for each active torrent
    for magnet_link, torrent_handle in active_torrents.items():
        status = torrent_handle.status()
        progress_data[magnet_link] = {
            "state": status.state,
            "download_rate_kb_s": status.download_rate / 1000,
            "downloaded_mb": status.total_download / 1024 / 1024,
            "progress_percentage": status.progress * 100
        }

    return jsonify(progress_data)

@app.route('/download_complete', methods=['GET'])
def download_complete():
    """Check if the download is complete for a specific magnet link"""
    magnet_link = request.args.get('magnet_link')

    if not magnet_link:
        return jsonify({"error": "Magnet link is required."}), 400
    
    if magnet_link not in active_torrents:
        return jsonify({"error": "Torrent not found."}), 404

    # Check if the torrent has finished downloading
    torrent_handle = active_torrents[magnet_link]
    if torrent_handle.is_seed():
        # Move the downloaded file to public directory if it finished
        torrent_file = os.path.join(DOWNLOAD_DIR, torrent_handle.name())
        return jsonify({"status": "Download complete", "file_path": torrent_file})
    else:
        return jsonify({"status": "Download still in progress"}), 202

@app.route('/download_file/<filename>', methods=['GET'])
def serve_download(filename):
    """Serve the downloaded file from the public directory"""
    try:
        return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": f"File not found: {str(e)}"}), 404

@app.route('/stop_download', methods=['GET'])
def stop_download():
    """Stop the torrent download by its magnet link"""
    magnet_link = request.args.get('magnet_link')
    
    if not magnet_link:
        return jsonify({"error": "Magnet link is required."}), 400

    if magnet_link not in active_torrents:
        return jsonify({"error": "Torrent not found."}), 404

    # Stop the torrent handle and remove it from active torrents
    torrent_handle = active_torrents.pop(magnet_link)
    torrent_handle.set_max_uploads(0)  # This stops the download
    return jsonify({"status": f"Download for {magnet_link} stopped."})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=8000)
