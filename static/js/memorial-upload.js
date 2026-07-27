/* ═══════════════════════════════════════════════════════════════
 * 纪念录式记忆 — 上传器模块
 * 维护有序 photoOrder[] 与 videoUrls[]；HTML5 原生拖拽排序；
 * 复用 /api/media 逐张上传得 URL；inferType() 自动推断记忆类型。
 * 不依赖任何第三方库。
 * ═══════════════════════════════════════════════════════════════ */

(function (global) {
  "use strict";

  // 允许的类型（与后端 ALLOWED_*_EXTS 保持一致）
  var ALLOWED_IMG = ["png", "jpg", "jpeg", "gif", "webp", "bmp"];
  var ALLOWED_VID = ["mp4", "webm", "mov", "avi"];
  // 单文件上限（与后端 MAX_FILE_SIZE = 50MB 一致，PM 拍板视频上限）
  var MAX_SIZE = 50 * 1024 * 1024;

  function extOf(name) {
    if (!name || name.indexOf(".") === -1) return "";
    return name.split(".").pop().toLowerCase();
  }

  /**
   * 初始化上传器。
   * @param {Object} opts
   *   photoInputId  照片 <input type=file multiple> 的 id
   *   videoInputId  视频 <input type=file> 的 id
   *   zoneId        拖拽选择区元素 id
   *   thumbsId      照片预览网格容器 id
   *   videoPreviewId 视频预览容器 id
   *   initialPhotos 既有照片 URL 数组（编辑页还原顺序用）
   */
  function initUploader(opts) {
    opts = opts || {};
    var photoInput = document.getElementById(opts.photoInputId || "memPhotoInput");
    var videoInput = document.getElementById(opts.videoInputId || "memVideoInput");
    var zone = document.getElementById(opts.zoneId || "memUploadZone");
    var thumbs = document.getElementById(opts.thumbsId || "memThumbs");
    var videoPreview = document.getElementById(opts.videoPreviewId || "memVideoPreview");

    // 有序状态：photoOrder 为 [{url, name, uploading, file}]
    var photoOrder = [];
    // 视频状态：videoUrls 为 [{url, name}]
    var videoUrls = [];

    var dragSrcIndex = null;

    // ── 渲染照片缩略图 ──
    function renderThumbs() {
      if (!thumbs) return;
      thumbs.innerHTML = "";
      photoOrder.forEach(function (item, index) {
        var cell = document.createElement("div");
        cell.className = "mem-thumb" + (item.uploading ? " is-uploading" : "");
        cell.setAttribute("draggable", "true");
        cell.dataset.index = String(index);

        var img = document.createElement("img");
        img.src = item.url;
        img.alt = item.name || "照片";
        cell.appendChild(img);

        var handle = document.createElement("span");
        handle.className = "mem-thumb-handle";
        handle.innerHTML = '<i class="fas fa-grip-vertical"></i>';
        cell.appendChild(handle);

        var order = document.createElement("span");
        order.className = "mem-thumb-order";
        order.textContent = String(index + 1);
        cell.appendChild(order);

        var remove = document.createElement("button");
        remove.type = "button";
        remove.className = "mem-thumb-remove";
        remove.innerHTML = "&times;";
        remove.title = "移除";
        remove.addEventListener("click", function (e) {
          e.stopPropagation();
          photoOrder.splice(index, 1);
          renderThumbs();
        });
        cell.appendChild(remove);

        bindDrag(cell, index);
        thumbs.appendChild(cell);
      });
    }

    // ── 拖拽排序（HTML5 Drag & Drop）──
    function bindDrag(cell, index) {
      cell.addEventListener("dragstart", function (e) {
        dragSrcIndex = index;
        cell.classList.add("dragging");
        if (e.dataTransfer) {
          e.dataTransfer.effectAllowed = "move";
          e.dataTransfer.setData("text/plain", String(index));
        }
      });
      cell.addEventListener("dragend", function () {
        cell.classList.remove("dragging");
        dragSrcIndex = null;
      });
      cell.addEventListener("dragover", function (e) {
        e.preventDefault();
        if (e.dataTransfer) e.dataTransfer.dropEffect = "move";
      });
      cell.addEventListener("drop", function (e) {
        e.preventDefault();
        var to = index;
        if (dragSrcIndex === null || dragSrcIndex === to) return;
        var moved = photoOrder.splice(dragSrcIndex, 1)[0];
        photoOrder.splice(to, 0, moved);
        dragSrcIndex = null;
        renderThumbs();
      });
    }

    // 允许拖到网格空白处追加到最后
    if (thumbs) {
      thumbs.addEventListener("dragover", function (e) {
        e.preventDefault();
      });
      thumbs.addEventListener("drop", function (e) {
        e.preventDefault();
        if (dragSrcIndex === null) return;
        var moved = photoOrder.splice(dragSrcIndex, 1)[0];
        photoOrder.push(moved);
        dragSrcIndex = null;
        renderThumbs();
      });
    }

    // ── 上传单个文件到 /api/media ──
    function uploadFile(file) {
      var fd = new FormData();
      fd.append("file", file);
      return fetch("/api/media", { method: "POST", body: fd }).then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok || !data.media || !data.media.file_url) {
            throw new Error(data.msg || "上传失败");
          }
          return data.media.file_url;
        });
      });
    }

    // ── 处理选择的照片 ──
    function handlePhotos(fileList) {
      Array.prototype.slice.call(fileList).forEach(function (file) {
        var ext = extOf(file.name);
        if (ALLOWED_IMG.indexOf(ext) === -1) {
          alert("不支持的图片格式：" + ext + "（支持 " + ALLOWED_IMG.join("/") + "）");
          return;
        }
        if (file.size > MAX_SIZE) {
          alert("图片「" + file.name + "」超过大小上限（约 50MB）");
          return;
        }
        var item = {
          url: URL.createObjectURL(file),
          name: file.name,
          uploading: true,
          file: file,
        };
        photoOrder.push(item);
        renderThumbs();
        uploadFile(file)
          .then(function (url) {
            item.url = url;
            item.uploading = false;
            renderThumbs();
          })
          .catch(function (err) {
            photoOrder = photoOrder.filter(function (x) {
              return x !== item;
            });
            renderThumbs();
            alert("照片「" + file.name + "」上传失败：" + err.message);
          });
      });
    }

    // ── 处理选择的视频 ──
    function handleVideo(file) {
      if (!file) return;
      var ext = extOf(file.name);
      if (ALLOWED_VID.indexOf(ext) === -1) {
        alert("不支持的视频格式：" + ext + "（支持 " + ALLOWED_VID.join("/") + "）");
        return;
      }
      if (file.size > MAX_SIZE) {
        alert("视频「" + file.name + "」超过大小上限（约 20MB）");
        return;
      }
      uploadFile(file)
        .then(function (url) {
          videoUrls.push({ url: url, name: file.name });
          renderVideos();
        })
        .catch(function (err) {
          alert("视频「" + file.name + "」上传失败：" + err.message);
        });
    }

    // ── 渲染视频预览 ──
    function renderVideos() {
      if (!videoPreview) return;
      videoPreview.innerHTML = "";
      videoUrls.forEach(function (item, index) {
        var chip = document.createElement("div");
        chip.className = "mem-video-chip";
        chip.innerHTML =
          '<i class="fas fa-video"></i><span class="mem-video-name">' +
          (item.name || "视频") +
          "</span>";
        var remove = document.createElement("button");
        remove.type = "button";
        remove.className = "mem-thumb-remove";
        remove.innerHTML = "&times;";
        remove.title = "移除";
        remove.addEventListener("click", function () {
          videoUrls.splice(index, 1);
          renderVideos();
        });
        chip.appendChild(remove);
        videoPreview.appendChild(chip);
      });
    }

    // ── 类型自动推断：video > photo > text ──
    function inferType() {
      if (videoUrls.length > 0) return "video";
      if (photoOrder.length > 0) return "photo";
      return "text";
    }

    // ── 事件绑定 ──
    if (photoInput) {
      photoInput.addEventListener("change", function () {
        if (photoInput.files && photoInput.files.length) {
          handlePhotos(photoInput.files);
        }
        photoInput.value = "";
      });
    }
    if (videoInput) {
      videoInput.addEventListener("change", function () {
        if (videoInput.files && videoInput.files.length) {
          handleVideo(videoInput.files[0]);
        }
        videoInput.value = "";
      });
    }
    if (zone) {
      zone.addEventListener("click", function () {
        if (photoInput) photoInput.click();
      });
      ["dragenter", "dragover"].forEach(function (evt) {
        zone.addEventListener(evt, function (e) {
          e.preventDefault();
          e.stopPropagation();
          zone.classList.add("is-dragover");
        });
      });
      ["dragleave", "drop"].forEach(function (evt) {
        zone.addEventListener(evt, function (e) {
          e.preventDefault();
          e.stopPropagation();
          zone.classList.remove("is-dragover");
        });
      });
      zone.addEventListener("drop", function (e) {
        var dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length) {
          handlePhotos(dt.files);
        }
      });
    }

    // ── 初始化既有照片（编辑页）──
    if (opts.initialPhotos && Array.isArray(opts.initialPhotos)) {
      opts.initialPhotos.forEach(function (url) {
        if (url) {
          photoOrder.push({ url: url, name: "", uploading: false, file: null });
        }
      });
      renderThumbs();
    }
    if (opts.initialVideos && Array.isArray(opts.initialVideos)) {
      opts.initialVideos.forEach(function (url) {
        if (url) videoUrls.push({ url: url, name: "" });
      });
      renderVideos();
    }

    // ── 对外暴露的接口 ──
    return {
      getPhotoUrls: function () {
        return photoOrder.map(function (x) {
          return x.url;
        });
      },
      getVideoUrls: function () {
        return videoUrls.map(function (x) {
          return x.url;
        });
      },
      inferType: inferType,
      photoCount: function () {
        return photoOrder.length;
      },
      videoCount: function () {
        return videoUrls.length;
      },
    };
  }

  // ── 全屏灯箱（时间线/详情页共用）──
  global.openLightbox = function (src) {
    if (!src) return;
    var overlay = document.createElement("div");
    overlay.className = "mem-lightbox";
    overlay.innerHTML = '<img src="' + src + '" alt="预览">';
    overlay.addEventListener("click", function () {
      overlay.remove();
    });
    document.body.appendChild(overlay);
  };

  // ── 画廊：缩略图点击切换主图 ──
  global.memSwapMain = function (el) {
    var main = document.getElementById("memMainPhoto");
    if (main && el && el.src) main.src = el.src;
    var thumbs = document.querySelectorAll(".mem-gallery-thumbs .mem-thumb");
    thumbs.forEach(function (t) {
      t.classList.remove("is-active");
    });
    if (el) el.classList.add("is-active");
  };

  // 暴露到全局
  global.initUploader = initUploader;
})(window);
