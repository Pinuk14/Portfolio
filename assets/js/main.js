/* =========================
  GLOBAL STATE
========================= */
let projectsData = [];
let reviews = [];
let showAllProjects = false;
let showAllReviews = false;
let currentSlide = 0;
let autoPlayInterval = null;


/* =========================
  INIT
========================= */
document.addEventListener("DOMContentLoaded", async () => {
    await loadStats();
    await loadProjects();
    await loadCurrentProjects(); 
    await loadComments();
});

/* =========================
  STATS (VIEWS + LIKES)
========================= */
async function loadStats() {
    const res = await fetch("/api/stats");
    const data = await res.json();
    document.getElementById("viewCount").textContent = data.views;
    document.getElementById("likeCount").textContent = data.likes;
}

async function likePage() {
    const btn = event.target;
    btn.disabled = true;
    const res = await fetch("/api/like", { method: "POST" });
    if (res.status === 429) {
        alert("You already liked this recently ❤️");
    }
    loadStats();
    setTimeout(() => {
        btn.disabled = false;
    }, 3000);
}


/* =========================
  PROJECTS (FROM JSON)
========================= */
async function loadProjects() {
    const res = await fetch("/assets/data/projects.json");
    projectsData = await res.json();
    projectsData.sort((a, b) => a.rank - b.rank);
    renderProjects();
}

function renderProjects() {
    const grid = document.getElementById("projectsGrid");
    const visible = showAllProjects ? projectsData : projectsData.slice(0, 3);

    grid.innerHTML = visible.map(p => `
        <div class="project-card" onclick="openProjectModal('${p.id}')">
            <div class="project-image">
                <img src="${p.cover}" alt="${p.title}">
            </div>

            <div class="project-content">
                <h4 class="project-title">${p.title}</h4>
                <p class="project-desc">${p.shortDesc}</p>

                <div class="tech-tags">
                    ${p.tech.map(t => `<span class="tech-tag">${t}</span>`).join("")}
                </div>

                <div class="project-links">
                    ${p.links.github ? `<a href="${p.links.github}" target="_blank">GitHub ↗</a>` : ""}
                    ${p.links.demo ? `<a href="${p.links.demo}" target="_blank">Demo ↗</a>` : ""}
                </div>
            </div>
        </div>
    `).join("");

    document.getElementById("viewMoreBtn").textContent =
        showAllProjects ? "Show Less" : "View More Projects";
}

function openProjectModal(projectId) {
    currentSlide = 0;
    const project = projectsData.find(p => p.id === projectId);
    if (!project) return;

    const modal = document.getElementById("projectModal");
    const body = modal.querySelector(".modal-body");

    body.innerHTML = `
        <h2>${project.title}</h2>
        <p style="color:#9ca3af; margin-bottom:1rem;">
            ${project.details}
        </p>

        ${project.media?.images?.length ? `
        <div class="carousel">
            <button class="carousel-btn left" onclick="prevSlide()">‹</button>

            <div class="carousel-track">
                ${project.media.images.map((img, i) => `
                    <div class="carousel-slide ${i === 0 ? "active" : ""}">
                      <img src="${img}" onclick="openFullscreen(this.src)" />
                    </div>
                `).join("")}
            </div>

            <button class="carousel-btn right" onclick="nextSlide()">›</button>
            <div class="carousel-dots">
            ${project.media.images.map((_, i) => `
                <span class="dot ${i === 0 ? "active" : ""}" onclick="goToSlide(${i})"></span>
            `).join("")}
        </div>
        </div>
        ` : ""}
        ${project.media?.video ? `
        <video class="modal-video" src="${project.media.video}" controls></video>
        ` : ""}

        <div class="modal-tech">
            ${project.tech.map(t => `<span>${t}</span>`).join("")}
        </div>

        <div class="modal-links">
            ${project.links.github ? `<a href="${project.links.github}" target="_blank">GitHub ↗</a>` : ""}
            ${project.links.demo ? `<a href="${project.links.demo}" target="_blank">Live Demo ↗</a>` : ""}
        </div>
    `;

    modal.classList.add("active");
    document.body.style.overflow = "hidden";
}

function closeProjectModal() {
    const modal = document.getElementById("projectModal");
    modal.classList.remove("active");
    document.body.style.overflow = "";
}

/* ESC to close */
document.addEventListener("keydown", e => {
    if (e.key === "Escape") closeProjectModal();
});


function toggleProjects() {
    showAllProjects = !showAllProjects;
    renderProjects();
}

/* =========================
  COMMENTS
========================= */
async function loadComments() {
    const res = await fetch("/api/comments");
    reviews = await res.json();
    renderReviews();
}

function renderReviews() {
    const list = document.getElementById("reviewsList");
    const visible = showAllReviews ? reviews : reviews.slice(0, 3);

    list.innerHTML = visible.map(r => `
        <div class="review-card">
            <div class="review-header">
                <h4>${r.name}</h4>
                <span>${r.timestamp}</span>
            </div>
            <p>${r.comment}</p>
        </div>
    `).join("");

    document.getElementById("viewMoreReviewsBtn").textContent =
        showAllReviews ? "Show Less" : "View More Reviews";
}

function toggleReviews() {
    showAllReviews = !showAllReviews;
    renderReviews();
}

async function submitComment() {
    const name = document.getElementById("commenterName").value.trim();
    const comment = document.getElementById("commentText").value.trim();

    if (!name || !comment) return alert("Fill all fields");

    await fetch("/api/comments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, comment })
    });

    document.getElementById("commenterName").value = "";
    document.getElementById("commentText").value = "";

    loadComments();
}

/* =========================
   CURRENT PROJECTS
========================= */
async function loadCurrentProjects() {
    const res = await fetch("/assets/data/current-projects.json");
    const projects = await res.json();
    renderCurrentProjects(projects);
}

function renderCurrentProjects(projects) {
    const grid = document.getElementById("currentProjectsGrid");

    grid.innerHTML = projects.map(p => `
        <div class="card">
            <h4 style="font-size:1.2rem; font-weight:600;">
                ${p.title}
            </h4>

            <p style="color:#9ca3af; font-size:0.9rem; margin:0.5rem 0;">
                ${p.description}
            </p>

            <div class="progress-container">
                <div class="progress-label">
                    <span>Progress</span>
                    <span>${p.progress}%</span>
                </div>

                <div class="progress-bar">
                    <div class="progress-fill ${p.color}" 
                         style="width:${p.progress}%">
                    </div>
                </div>
            </div>
        </div>
    `).join("");
}


function showSlide(index) {
    const slides = document.querySelectorAll(".carousel-slide");
    if (!slides.length) return;

    slides.forEach(s => s.classList.remove("active"));
    currentSlide = (index + slides.length) % slides.length;
    slides[currentSlide].classList.add("active");

    updateDots();
}


function nextSlide() {
    showSlide(currentSlide + 1);
}

function prevSlide() {
    showSlide(currentSlide - 1);
}

function updateDots() {
    document.querySelectorAll(".dot").forEach((d, i) => {
        d.classList.toggle("active", i === currentSlide);
    });
}

function goToSlide(index) {
    showSlide(index);
}

document.addEventListener("keydown", e => {
    if (!document.getElementById("projectModal")?.classList.contains("open")) return;

    if (e.key === "ArrowRight") nextSlide();
    if (e.key === "ArrowLeft") prevSlide();
    if (e.key === "Escape") closeProjectModal();
});

document.addEventListener("mouseover", e => {
    if (e.target.closest(".carousel")) stopAutoPlay();
});

document.addEventListener("mouseout", e => {
    if (e.target.closest(".carousel")) startAutoPlay();
});


function openFullscreen(src) {
    const viewer = document.getElementById("fullscreenViewer");
    document.getElementById("fullscreenImg").src = src;
    viewer.style.display = "flex";
}

function closeFullscreen() {
    document.getElementById("fullscreenViewer").style.display = "none";
}

function startAutoPlay() {
    stopAutoPlay();
    autoPlayInterval = setInterval(nextSlide, 3500);
}

function stopAutoPlay() {
    if (autoPlayInterval) {
        clearInterval(autoPlayInterval);
        autoPlayInterval = null;
    }
}