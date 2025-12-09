/** @format */
// API key from YouTube
const API_KEY = "AIzaSyA0FVwIGAY1y1L0mATotqRrsWp_kvaAgHA";
// const API_KEY = "pegar aca"; /// (usa tu propia api key)
const switchInput = document.getElementById("modeSwitch");
const switchLabel = document.getElementById("switchLabel");
const qualitySelect = document.getElementById("quality");

// Opciones para los dos modos
const videoOptions = [
  { value: 6, text: "La Mejor (4K-vp9)" },
  { value: 5, text: "Ultra Full HD (1440p-vp9)" },
  { value: 4, text: "Full HD (1080p)" },
  { value: 3, text: "HD (720p)" },
  { value: 2, text: "SD (480p)" },
  { value: 1, text: "(360p)" },
  { value: 0, text: "Solo Audio" },
];

const ShortOptions = [
  { value: "s6", text: "La Mejor (4K-vp9)" },
  { value: "s5", text: "Ultra Full HD (2560p)" },
  { value: "s4", text: "Full HD (1920p)" },
  { value: "s3", text: "HD (1280p)" },
  { value: "s2", text: "SD Plus (1080p-poco compatible)" },
  { value: "s1", text: "SD (854)" },
  { value: 0, text: "Solo Audio" },
];

function swit() {
  const Short = switchInput.checked;
  switchLabel.textContent = Short ? "Formato: Short" : "Formato: Video";

  // Limpiar las opciones actuales
  qualitySelect.innerHTML = "";

  // cambiar las opciones
  const options = Short ? ShortOptions : videoOptions;
  options.forEach((opt) => {
    const optionElement = document.createElement("option");
    optionElement.value = opt.value;
    optionElement.textContent = opt.text;
    qualitySelect.appendChild(optionElement);
  });

  // 🔹 Seleccionar una opción por defecto
  if (Short) {
    qualitySelect.value = "s3"; // HD (720) en modo short
  } else {
    qualitySelect.value = 3; // Full HD (1080p) en modo video
  }
}

//borra el texto de las barra de buqueda
function cleanText() {
  document.querySelector("#searchInput").value = "";
  document.querySelectorAll(".video-card").forEach((element) => {
    element.remove();
  });
  document.getElementById("zona_de_resultados").style.display = "none";
  document.querySelector(".marcas1").style.marginTop = "0";
}

function cleanText2() {
  document.querySelector("#video_url").value = "";
}
///
/// busqueda y resultados
async function searchVideos() {
  const searchInput = document.getElementById("searchInput").value;
  const resultsContainer = document.getElementById("searchResults");
  //  Si el input está vacío, o tine pocos carateres. no buscar
  if (searchInput === "" || searchInput.length < 3) {
    return;
  }
  document.getElementById("loaderContainer").style.display = "flex";
  document.getElementById("zona_de_resultados").style.display = "flex";
  try {
    const response = await fetch(
      `https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=24&q=${encodeURIComponent(
        searchInput
      )}&type=video&key=${API_KEY}`
    );
    const data = await response.json();
    resultsContainer.innerHTML = data.items
      .map(
        (item) => `
          <div class="video-card">
            <img 
              src="${item.snippet.thumbnails.high.url}"
              alt="${item.snippet.title}"
              class="thumbnail"
            />
            <div class="video-info">
              <div class="video-title">${item.snippet.title}</div>
              <div class="button-group">
                <button 
                  onclick="copyVideoUrl('https://www.youtube.com/watch?v=${item.id.videoId}')"
                  class="copy-link"
                >
                  Copiar Url
                </button>
                <button 
                  onclick="showVideoOverlay('${item.id.videoId}')"
                  class="watch-overlay"
                >
                  Ver
                </button>
              </div>
            </div>
          </div>
        `
      )
      .join("");
  } catch (error) {
    console.error("Error al buscar videos:", error);
    resultsContainer.innerHTML =
      "<p>Error al buscar videos. Por favor, intenta de nuevo.</p>";
  } finally {
    document.getElementById("zona_de_resultados").style.display = "grid";
    document.querySelector(".marcas1").style.marginTop = "4%";
    document.getElementById("loaderContainer").style.display = "none";
  }
}

/// boton copiar
function copyVideoUrl(url) {
  const urlInput = document.getElementById("video_url");
  urlInput.value = url;
  urlInput.scrollIntoView({ behavior: "smooth" });
  urlInput.focus();
}

// Función para mostrar el video como overlay
function showVideoOverlay(videoId) {
  try {
    // Prevenir cualquier navegación preload en el service worker
    if (navigator.serviceWorker && navigator.serviceWorker.controller) {
      // Notificar al service worker que estamos mostrando un overlay
      navigator.serviceWorker.controller.postMessage({
        type: "PREVENT_NAVIGATION_PRELOAD",
        url: window.location.href,
      });
    }

    // Crear el contenedor del overlay
    const overlay = document.createElement("div");
    overlay.id = "video-overlay";

    // Crear un contenedor para el iframe y el indicador de carga
    const iframeContainer = document.createElement("div");
    iframeContainer.className = "iframe-container";

    // Crear el indicador de carga
    const loadingElement = document.createElement("div");
    loadingElement.className = "loading-indicator";
    loadingElement.textContent = "Cargando video...";

    iframeContainer.appendChild(loadingElement);

    // Crear el iframe para el video con un pequeño retraso
    // para evitar problemas con el Service Worker
    const iframe = document.createElement("iframe");

    setTimeout(() => {
      iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`;
      iframe.allow =
        "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      iframe.allowFullscreen = true;

      // Remover el indicador de carga cuando el iframe esté listo
      iframe.onload = function () {
        if (iframeContainer.contains(loadingElement)) {
          iframeContainer.removeChild(loadingElement);
        }
      };

      iframeContainer.appendChild(iframe);
    }, 100);

    // Crear el botón para cerrar el overlay
    const closeButton = document.createElement("button");
    closeButton.id = "cerrar";
    closeButton.textContent = "Cerrar";
    closeButton.onclick = removeVideoOverlay;

    // Agregar elementos al overlay
    overlay.appendChild(iframeContainer);
    overlay.appendChild(closeButton);

    // Agregar el overlay al cuerpo del documento
    document.body.appendChild(overlay);

    // Permitir cerrar el overlay haciendo clic fuera del video
    overlay.addEventListener("click", function (event) {
      if (event.target === overlay) {
        removeVideoOverlay();
      }
    });
  } catch (error) {
    console.error("Error al mostrar el video:", error);
    alert("Hubo un problema al cargar el video. Por favor, intenta de nuevo.");
  }
}

// Función para eliminar el overlay
function removeVideoOverlay() {
  try {
    const overlay = document.getElementById("video-overlay");
    if (overlay) {
      // Buscar el iframe y detener la reproducción del video antes de eliminar
      const iframe = overlay.querySelector("iframe");
      if (iframe) {
        // Detener la reproducción cambiando el src
        iframe.src = "";
      }

      // Eliminar el overlay del DOM
      document.body.removeChild(overlay);

      // Restaurar el scroll de la página
      document.body.style.overflow = "auto";

      // Notificar al service worker que el overlay ha sido cerrado
      if (navigator.serviceWorker && navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({
          type: "RESUME_NAVIGATION_PRELOAD",
          url: window.location.href,
        });
      }
    }
  } catch (error) {
    console.error("Error al cerrar el overlay:", error);
    // En caso de error
    const overlay = document.getElementById("video-overlay");
    if (overlay && overlay.parentNode) {
      overlay.parentNode.removeChild(overlay);
      document.body.style.overflow = "auto";
    }
  }
}

// Evento para escuchar al presionar Enter
document
  .getElementById("searchInput")
  .addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      searchVideos();
    }
  });

// Soporte para Service Worker
if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    // Establecer comunicación con el Service Worker existente
    navigator.serviceWorker.ready
      .then(function (registration) {
        console.log("Service Worker listo");

        // Establecer comunicación con el Service Worker
        navigator.serviceWorker.addEventListener("message", function (event) {
          console.log("Mensaje recibido del Service Worker:", event.data);
        });
      })
      .catch(function (error) {
        console.log("Error con Service Worker:", error);
      });
  });

  // Manejar errores de Service Worker relacionados con navigation preload
  window.addEventListener("unhandledrejection", function (event) {
    if (
      event.reason &&
      event.reason.toString().includes("navigation preload")
    ) {
      console.warn("Advertencia de navigation preload detectada y manejada");
      event.preventDefault(); // Prevenir que el error aparezca en consola
    }
  });
}

//notas
const js = {
  version_js: "Js: v1.2.4.0",
};

console.log(js["version_js"]);
