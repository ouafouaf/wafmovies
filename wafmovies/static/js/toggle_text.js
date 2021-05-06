function ShowMore() {
    var dots = document.getElementById("dots");
    var moreText = document.getElementById("showmore");
    var btnText = document.getElementById("ShowMoreBtn");
  
    if (dots.style.display === "none") {
      dots.style.display = "inline";
      btnText.innerHTML = "(Show more)";
      moreText.style.display = "none";
    } else {
      dots.style.display = "none";
      btnText.innerHTML = "(Show less)";
      moreText.style.display = "inline";
    }
  }