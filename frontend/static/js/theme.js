const toggleBtn = document.getElementById("themeToggle");
const body = document.body;

// Load saved theme
const savedTheme = localStorage.getItem("theme");
if (savedTheme === "light") {
  body.classList.add("light-theme");
  toggleBtn.innerText = "🌞";
}

// Toggle theme
toggleBtn.addEventListener("click", () => {
  body.classList.toggle("light-theme");

  if (body.classList.contains("light-theme")) {
    localStorage.setItem("theme", "light");
    toggleBtn.innerText = "🌞";
  } else {
    localStorage.setItem("theme", "dark");
    toggleBtn.innerText = "🌙";
  }
});
