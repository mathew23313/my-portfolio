window.addEventListener("load", function() {
  document.body.style.display = "block";
  setTimeout(function() {
    document.body.style.opacity = 1;
  }, 50);
  document.getElementById("popup").classList.add("show");
  document.querySelector(".container").classList.add("blur");
  document.getElementById("overlay").classList.remove("hide");

  document.getElementById("close-popup").addEventListener("click", function() {
    document.getElementById("popup").classList.remove("show");
    document.querySelector(".container").classList.remove("blur");
    document.getElementById("overlay").classList.add("hide");
  });
});
