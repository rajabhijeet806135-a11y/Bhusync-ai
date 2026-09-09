/**
 * BhuSynch AI — Camera Capture Module
 * 
 * Provides camera access for the Mobile Ground-Truthing PWA.
 * Captures geo-tagged photos with device GPS coordinates, bearing,
 * and timestamp metadata for field survey documentation.
 */

const CameraCapture = (() => {
    'use strict';

    let _stream = null;
    let _videoElement = null;
    let _canvasElement = null;
    let _currentPosition = null;
    let _watchId = null;

    const PHOTO_QUALITY = 0.85;
    const MAX_WIDTH = 1920;
    const MAX_HEIGHT = 1440;

    /**
     * Initialize the camera module.
     * Creates video and canvas elements if not already present.
     */
    function init() {
        // Create hidden canvas for snapshot capture
        if (!_canvasElement) {
            _canvasElement = document.createElement('canvas');
        }
        // Start GPS watch for geo-tagging
        _startGPSWatch();
        console.log('[CameraCapture] Initialized.');
    }

    /**
     * Start watching the device GPS position continuously.
     */
    function _startGPSWatch() {
        if (!('geolocation' in navigator)) {
            console.warn('[CameraCapture] Geolocation not available.');
            return;
        }
        _watchId = navigator.geolocation.watchPosition(
            (position) => {
                _currentPosition = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    altitude: position.coords.altitude,
                    accuracy: position.coords.accuracy,
                    heading: position.coords.heading,
                    speed: position.coords.speed,
                    timestamp: position.timestamp
                };
            },
            (error) => {
                console.warn('[CameraCapture] GPS error:', error.message);
            },
            {
                enableHighAccuracy: true,
                maximumAge: 5000,
                timeout: 15000
            }
        );
    }

    /**
     * Stop GPS watch.
     */
    function _stopGPSWatch() {
        if (_watchId !== null) {
            navigator.geolocation.clearWatch(_watchId);
            _watchId = null;
        }
    }

    /**
     * Request camera permission and open the video stream.
     * @param {HTMLVideoElement} videoElement - The video element to attach the stream to.
     * @param {Object} [options] - Camera options
     * @param {string} [options.facingMode='environment'] - 'environment' for rear camera, 'user' for front
     * @returns {Promise<MediaStream>}
     */
    async function openCamera(videoElement, options = {}) {
        const facingMode = options.facingMode || 'environment';

        if (_stream) {
            closeCamera();
        }

        _videoElement = videoElement;

        try {
            _stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: { ideal: facingMode },
                    width: { ideal: MAX_WIDTH },
                    height: { ideal: MAX_HEIGHT }
                },
                audio: false
            });

            _videoElement.srcObject = _stream;
            await _videoElement.play();

            console.log('[CameraCapture] Camera stream opened.');
            return _stream;
        } catch (err) {
            console.error('[CameraCapture] Failed to open camera:', err);
            throw new Error(`Camera access denied or unavailable: ${err.message}`);
        }
    }

    /**
     * Capture a photo from the current video stream.
     * Returns a Blob and metadata (GPS, timestamp, bearing).
     * @returns {Promise<{blob: Blob, metadata: Object}>}
     */
    async function capturePhoto() {
        if (!_stream || !_videoElement) {
            throw new Error('Camera is not open. Call openCamera() first.');
        }

        const videoWidth = _videoElement.videoWidth;
        const videoHeight = _videoElement.videoHeight;

        // Scale down if necessary
        let targetWidth = videoWidth;
        let targetHeight = videoHeight;
        if (videoWidth > MAX_WIDTH) {
            const ratio = MAX_WIDTH / videoWidth;
            targetWidth = MAX_WIDTH;
            targetHeight = Math.round(videoHeight * ratio);
        }

        _canvasElement.width = targetWidth;
        _canvasElement.height = targetHeight;

        const ctx = _canvasElement.getContext('2d');
        ctx.drawImage(_videoElement, 0, 0, targetWidth, targetHeight);

        // Add timestamp watermark
        _addTimestampOverlay(ctx, targetWidth, targetHeight);

        // Convert to blob
        const blob = await new Promise((resolve, reject) => {
            _canvasElement.toBlob(
                (b) => b ? resolve(b) : reject(new Error('Failed to create blob')),
                'image/jpeg',
                PHOTO_QUALITY
            );
        });

        const metadata = {
            lat: _currentPosition ? _currentPosition.lat : null,
            lng: _currentPosition ? _currentPosition.lng : null,
            altitude: _currentPosition ? _currentPosition.altitude : null,
            accuracy: _currentPosition ? _currentPosition.accuracy : null,
            bearing: _currentPosition ? _currentPosition.heading : null,
            timestamp: new Date().toISOString(),
            dimensions: { width: targetWidth, height: targetHeight },
            sizeBytes: blob.size
        };

        console.log('[CameraCapture] Photo captured:', metadata);
        return { blob, metadata };
    }

    /**
     * Add a timestamp and GPS watermark overlay to the canvas.
     */
    function _addTimestampOverlay(ctx, width, height) {
        const now = new Date();
        const timeStr = now.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' });
        let gpsStr = 'GPS: N/A';
        if (_currentPosition) {
            gpsStr = `GPS: ${_currentPosition.lat.toFixed(6)}, ${_currentPosition.lng.toFixed(6)} ±${(_currentPosition.accuracy || 0).toFixed(1)}m`;
        }

        const padding = 10;
        const lineHeight = 18;
        const bgHeight = lineHeight * 2 + padding * 2;

        // Semi-transparent background
        ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
        ctx.fillRect(0, height - bgHeight, width, bgHeight);

        // Text
        ctx.fillStyle = '#FFFFFF';
        ctx.font = '14px monospace';
        ctx.textBaseline = 'top';
        ctx.fillText(`BhuSynch AI  |  ${timeStr}`, padding, height - bgHeight + padding);
        ctx.fillText(gpsStr, padding, height - bgHeight + padding + lineHeight);
    }

    /**
     * Capture a photo using the device file input (fallback for browsers
     * that do not support getUserMedia well).
     * @returns {Promise<{blob: Blob, metadata: Object}>}
     */
    function captureViaInput() {
        return new Promise((resolve, reject) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.capture = 'environment';

            input.onchange = async (event) => {
                const file = event.target.files[0];
                if (!file) {
                    reject(new Error('No file selected'));
                    return;
                }

                // Read EXIF GPS data if available
                const metadata = {
                    lat: _currentPosition ? _currentPosition.lat : null,
                    lng: _currentPosition ? _currentPosition.lng : null,
                    altitude: _currentPosition ? _currentPosition.altitude : null,
                    accuracy: _currentPosition ? _currentPosition.accuracy : null,
                    bearing: _currentPosition ? _currentPosition.heading : null,
                    timestamp: new Date().toISOString(),
                    fileName: file.name,
                    sizeBytes: file.size,
                    mimeType: file.type
                };

                resolve({ blob: file, metadata });
            };

            input.onerror = () => reject(new Error('File input error'));
            input.click();
        });
    }

    /**
     * Close the camera stream and release resources.
     */
    function closeCamera() {
        if (_stream) {
            _stream.getTracks().forEach(track => track.stop());
            _stream = null;
        }
        if (_videoElement) {
            _videoElement.srcObject = null;
        }
        console.log('[CameraCapture] Camera closed.');
    }

    /**
     * Check if camera permission has been granted.
     * @returns {Promise<string>} 'granted', 'denied', or 'prompt'
     */
    async function checkPermission() {
        if (!navigator.permissions) {
            return 'prompt'; // Fallback
        }
        try {
            const result = await navigator.permissions.query({ name: 'camera' });
            return result.state;
        } catch {
            return 'prompt';
        }
    }

    /**
     * Get current GPS position as a one-shot reading.
     * @returns {Promise<Object>} { lat, lng, accuracy, altitude }
     */
    function getCurrentPosition() {
        return new Promise((resolve, reject) => {
            if (!('geolocation' in navigator)) {
                reject(new Error('Geolocation not available'));
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    resolve({
                        lat: pos.coords.latitude,
                        lng: pos.coords.longitude,
                        accuracy: pos.coords.accuracy,
                        altitude: pos.coords.altitude,
                        heading: pos.coords.heading,
                        timestamp: pos.timestamp
                    });
                },
                (err) => reject(err),
                {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 0
                }
            );
        });
    }

    /**
     * Get the most recent cached position from the GPS watch.
     * @returns {Object|null}
     */
    function getLastKnownPosition() {
        return _currentPosition;
    }

    /**
     * Destroy and clean up all camera resources.
     */
    function destroy() {
        closeCamera();
        _stopGPSWatch();
        _canvasElement = null;
        _currentPosition = null;
        console.log('[CameraCapture] Destroyed.');
    }

    // ──────────────────────────────── Public API ────────────────────────────────

    return {
        init,
        openCamera,
        capturePhoto,
        captureViaInput,
        closeCamera,
        checkPermission,
        getCurrentPosition,
        getLastKnownPosition,
        destroy
    };
})();

// Export to window
if (typeof window !== 'undefined') {
    window.CameraCapture = CameraCapture;
}
