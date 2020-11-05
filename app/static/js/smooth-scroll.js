const link = document.querySelectorAll("a");
link.forEach(elem => elem.addEventListener("click", smoothscroll));
function smoothscroll(event){
  event.preventDefault();
  const targetId = event.currentTarget.getAttribute("href");
  window.scrollTo({
    top: document.querySelector(targetId).offsetTop,
    behavior: "smooth"
  })
}
