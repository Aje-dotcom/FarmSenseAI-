// camera_manager.js
class FarmSensorCamera {
  constructor(videoElementId) {
    this.video = document.getElementById(videoElementId);
    this.stream = null;
    this.currentFacingMode = "environment"; // Default: Rear camera for crops/IoT
    this.barcodeDetector = ('BarcodeDetector' in window) 
      ? new BarcodeDetector({ formats: ['qr_code'] }) 
      : null;
  }

  async startCamera(facingMode = this.currentFacingMode) {
    this.currentFacingMode = facingMode;
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
    }
    const constraints = {
      video: {
        facingMode: { ideal: this.currentFacingMode },
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      },
      audio: false
    };
    this.stream = await navigator.mediaDevices.getUserMedia(constraints);
    this.video.srcObject = this.stream;
    await this.video.play();
  }

  toggleCamera() {
    const nextMode = this.currentFacingMode === "environment" ? "user" : "environment";
    return this.startCamera(nextMode);
  }

  captureFrameBlob() {
    const canvas = document.createElement("canvas");
    canvas.width = this.video.videoWidth;
    canvas.height = this.video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(this.video, 0, 0, canvas.width, canvas.height);
    return new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.85));
  }

  async scanFrameForQR() {
    if (!this.barcodeDetector) return null;
    try {
      const barcodes = await this.barcodeDetector.detect(this.video);
      return barcodes.length > 0 ? barcodes[0].rawValue : null;
    } catch {
      return null;
    }
  }
}