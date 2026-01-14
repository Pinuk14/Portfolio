let index = 0;

function updateCarousel() {
    const track = document.querySelector(".carousel-track");
    const slides = document.querySelectorAll(".slide");
    const width = slides[0].offsetWidth;
    track.style.transform = `translateX(-${index * width}px)`;
}

function nextSlide() {
    const slides = document.querySelectorAll(".slide");
    index = (index + 1) % slides.length;
    updateCarousel();
}

function prevSlide() {
    const slides = document.querySelectorAll(".slide");
    index = (index - 1 + slides.length) % slides.length;
    updateCarousel();
}

window.addEventListener("resize", updateCarousel);
