function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  const colors = {
    success: "bg-green-600",
    error: "bg-red-600",
    info: "bg-gray-700"
  };
  toast.className = `text-white px-4 py-2 rounded shadow ${colors[type]} animate-fadeIn`;
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
