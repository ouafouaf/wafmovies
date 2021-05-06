function autocomplete(searchEle, arr) {
    var currentFocus;
    searchEle.addEventListener("input", function(e) {
       var divCreate,
       b,
       i,
       fieldVal = this.value;
       closeAllLists();
       if (!fieldVal) {
          return false;
       }
       currentFocus = -1;
       divCreate = document.createElement("DIV");
       divCreate.setAttribute("id", this.id + "autocomplete-list");
       divCreate.setAttribute("class", "autocomplete-items");
       this.parentNode.appendChild(divCreate);
       currentItem = 0;
       for (i = 0; i <arr.length; i++) {
          maxItems = 8;
          if (currentItem >= maxItems) {
             return false;
          }
          if ( arr[i].substr(0, fieldVal.length).toUpperCase() == fieldVal.toUpperCase() ) {
             b = document.createElement("DIV");
             b.innerHTML = "<strong>" + arr[i].substr(0, fieldVal.length) + "</strong>";
             b.innerHTML += arr[i].substr(fieldVal.length);
             b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";
             b.addEventListener("click", function(e) {
                searchEle.value = this.getElementsByTagName("input")[0].value;
                closeAllLists();
             });
             divCreate.appendChild(b);
             currentItem += 1;
          }
       }
    });
    searchEle.addEventListener("keydown", function(e) {
       var autocompleteList = document.getElementById(
          this.id + "autocomplete-list"
       );
       if (autocompleteList)
          autocompleteList = autocompleteList.getElementsByTagName("div");
       if (e.keyCode == 40) {
          currentFocus++;
          addActive(autocompleteList);
       }
       else if (e.keyCode == 38) {
          //up
          currentFocus--;
          addActive(autocompleteList);
       }
       else if (e.keyCode == 13) {
          e.preventDefault();
          if (currentFocus > -1) {
             if (autocompleteList) autocompleteList[currentFocus].click();
          }
       }
    });
    function addActive(autocompleteList) {
       if (!autocompleteList) return false;
          removeActive(autocompleteList);
       if (currentFocus >= autocompleteList.length) currentFocus = 0;
       if (currentFocus < 0) currentFocus = autocompleteList.length - 1;
       autocompleteList[currentFocus].classList.add("autocomplete-active");
    }
    function removeActive(autocompleteList) {
       for (var i = 0; i < autocompleteList.length; i++) {
          autocompleteList[i].classList.remove("autocomplete-active");
       }
    }
    function closeAllLists(elmnt) {
       var autocompleteList = document.getElementsByClassName(
          "autocomplete-items"
       );
       for (var i = 0; i < autocompleteList.length; i++) {
          if (elmnt != autocompleteList[i] && elmnt != searchEle) {
             autocompleteList[i].parentNode.removeChild(autocompleteList[i]);
          }
       }
    }
    document.addEventListener("click", function(e) {
       closeAllLists(e.target);
    });
 } 




$(document).ready(function(){
    var countries=[];
    var genres=[];
    var people=[];
    var shows=[];
    
    function loadCountries(){
        $.getJSON('/api/countries', function(data, status, xhr){
            for (var i = 0; i < data.length; i++ ) {
                countries.push(data[i].name);
            }
        });
    };
    
    function loadGenres(){
        $.getJSON('/api/genres', function(data, status, xhr){
            for (var i = 0; i < data.length; i++ ) {
                genres.push(data[i].name);
            }
        });
    };
    
    function loadPeople(){
        $.getJSON('/api/people', function(data, status, xhr){
            for (var i = 0; i < data.length; i++ ) {
                people.push(data[i].name);
            }
        });
    };
    
    function loadShows(){
        $.getJSON('/api/shows', function(data, status, xhr){
            for (var i = 0; i < data.length; i++ ) {
                shows.push(data[i].name);
            }
        });
    };
    
    loadCountries();
    autocomplete(document.getElementById("country_input"), countries);
    loadGenres();
    autocomplete(document.getElementById("genre_input"), genres);
    loadPeople();
    autocomplete(document.getElementById("people_input"), people);
    loadShows();
    autocomplete(document.getElementById("title_input"), shows);

}); 
