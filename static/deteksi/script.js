document.addEventListener('DOMContentLoaded', function () {
  const uploadBox = document.getElementById('uploadBox');
  const imageInput = document.getElementById('imageInput');
  const imagePreview = document.getElementById('preview');
  const detectButton = document.getElementById('detectButton');
  const loadingDiv = document.getElementById('loadingDiv');
  const uploadPlaceholder = document.getElementById('upload-placeholder');
  const homeBtn = document.getElementById('home-btn');

  const cameraContainer = document.getElementById('camera-container');
  const video = document.getElementById('video');
  const captureButton = document.getElementById('captureButton');
  const cancelCameraButton = document.getElementById('cancelCameraButton');
  const hiddenCanvas = document.getElementById('hiddenCanvas');

  let uploadedFile = null;
  let stream = null;

  if (homeBtn) {
    homeBtn.addEventListener('click', () => {
      window.location.href = '/';
    });
  }

  // Trigger Modal Pilihan
  uploadBox.addEventListener('click', (e) => {
    if (stream) return;

    Swal.fire({
      title: 'Pilih Metode Unggah',
      html: `
      <div class="swal2-option-grid">
        <div class="swal2-option-item" id="swal-opt-camera">
          <i class="fas fa-camera"></i>
          <b>Kamera</b>
        </div>
        <div class="swal2-option-item" id="swal-opt-file">
          <i class="fas fa-file-image"></i>
          <b>Galeri/File</b>
        </div>
      </div>
    `,
      showConfirmButton: false,
      showCloseButton: true,
      didOpen: () => {
        const cameraBtn = document.getElementById('swal-opt-camera');
        const fileBtn = document.getElementById('swal-opt-file');

        cameraBtn.addEventListener('click', (ev) => {
          ev.stopPropagation();
          // Tutup modal dulu
          Swal.close();
          // Jalankan kamera setelah modal benar-benar hilang
          requestAnimationFrame(() => startCamera());
        });

        fileBtn.addEventListener('click', (ev) => {
          ev.stopPropagation();

          Swal.close();

          // Tunggu DOM benar-benar repaint
          setTimeout(() => {
            // Pastikan container swal benar-benar hilang
            document.querySelector('.swal2-container')?.remove();
            imageInput.click();
          }, 0);
        });
      },
    });
  });

  async function startCamera() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      video.srcObject = stream;

      uploadPlaceholder.style.display = 'none';
      imagePreview.style.display = 'none';
      imagePreview.classList.remove('fade-in');

      cameraContainer.style.display = 'flex';
    } catch (err) {
      Swal.fire('Error', 'Gagal mengakses kamera. Pastikan izin diberikan.', 'error');
    }
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      stream = null;
    }
    cameraContainer.style.display = 'none';
  }

  cancelCameraButton.onclick = (e) => {
    e.stopPropagation();
    stopCamera();
    if (uploadedFile) {
      imagePreview.style.display = 'block';
      imagePreview.classList.add('fade-in');
    } else {
      uploadPlaceholder.style.display = 'flex';
    }
  };

  captureButton.onclick = (e) => {
    e.stopPropagation();
    hiddenCanvas.width = video.videoWidth;
    hiddenCanvas.height = video.videoHeight;
    const ctx = hiddenCanvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    const dataUrl = hiddenCanvas.toDataURL('image/jpeg');

    fetch(dataUrl)
      .then((res) => res.blob())
      .then((blob) => {
        const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
        handleImageUpload(file);
        stopCamera();
      });
  };

  imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      handleImageUpload(file);
      // Reset input file agar bisa pilih file yang sama lagi jika perlu
      imageInput.value = '';
    }
  });

  function handleImageUpload(file) {
    if (file && file.type.startsWith('image/')) {
      uploadedFile = file;
      const reader = new FileReader();
      reader.onload = (e) => {
        imagePreview.src = e.target.result;
        imagePreview.style.display = 'block';
        imagePreview.classList.add('fade-in');
        uploadPlaceholder.style.display = 'none';
        detectButton.disabled = false;
      };
      reader.readAsDataURL(file);
    }
  }

  detectButton.addEventListener('click', async () => {
    if (!uploadedFile) return;

    loadingDiv.style.display = 'flex';
    detectButton.disabled = true;

    const formData = new FormData();
    formData.append('image', uploadedFile);

    try {
      const response = await fetch('/detect', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      // ✅ DETEKSI BERHASIL
      if (response.ok && result.detections) {
        sessionStorage.setItem('detectionResult', JSON.stringify(result));
        sessionStorage.setItem('uploadedImage', imagePreview.src);

        Swal.fire({
          icon: 'success',
          title: 'Deteksi Berhasil',
          text: 'Gambar berhasil dianalisis',
        }).then(() => {
          window.location.href = '/chatbot';
        });
        return;
      }

      // ⚠️ UNCERTAIN
      if (result.status === 'UNCERTAIN') {
        Swal.fire({
          icon: 'warning',
          title: 'Gambar Kurang Jelas',
          text: result.message,
        });
        return;
      }

      // ⚠️ OUT OF SCOPE (THRESHOLD)
      if (result.status === 'OUT_OF_SCOPE') {
        Swal.fire({
          icon: 'info',
          title: 'Tidak Dapat Diklasifikasikan',
          text: result.message + ` (Confidence: ${(result.confidence * 100).toFixed(2)}%)`,
        });
        return;
      }

      // ❌ INVALID
      if (result.status === 'INVALID') {
        Swal.fire({
          icon: 'error',
          title: 'Gambar Tidak Valid',
          text: result.message,
        });
        return;
      }

      // ❌ FALLBACK ERROR
      Swal.fire('Error', result.error || 'Terjadi kesalahan', 'error');
    } catch (error) {
      Swal.fire('Error', 'Gagal terhubung ke server', 'error');
    } finally {
      loadingDiv.style.display = 'none';
      detectButton.disabled = false;
    }
  });

  uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = '#2d6a4f';
  });
  uploadBox.addEventListener('dragleave', () => {
    uploadBox.style.borderColor = '#e4e4e4';
  });
  uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = '#e4e4e4';
    handleImageUpload(e.dataTransfer.files[0]);
  });
});
