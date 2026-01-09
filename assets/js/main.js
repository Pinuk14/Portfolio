const hoverImage = document.getElementById("hover-image");
const hoverImgTag = hoverImage.querySelector("img");

document.querySelectorAll(".hover-target").forEach(item => {

    item.addEventListener("mouseenter", () => {
        const imgSrc = item.getAttribute("data-image");
        hoverImgTag.src = imgSrc;
        hoverImage.classList.add("active");
    });

    item.addEventListener("mouseleave", () => {
        hoverImage.classList.remove("active");
    });

    item.addEventListener("mousemove", (e) => {
        hoverImage.style.top = e.clientY + "px";
        hoverImage.style.left = e.clientX + "px";
    });

});
