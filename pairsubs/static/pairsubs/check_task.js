// CSRF Setup (from Django doc)
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

//=======================

$("div.status-info").hide()
$("#learn-link").hide()
$("#search-link").hide()

// Check subtitles download task
var timerId = setInterval(function() {
   check_data();
}, 2000);


var check_data = function() {
  $.ajax({
    url: "check/",
    data: { task_id: task_id },
    type: 'POST',
    success:
      function(data, status){
	  console.log("Data: " + data.status + "\nStatus: " + status);
          if (data.status == "SUCCESS"){
            show_status(data.result);
          }
      }
  });
};

var show_status = function(result) {
  // result[0] - "Success" or "Fail"
  // result[1] - id of created PairOfSubs
  // result[2] - task log
  console.log(result);
  $("#loader").hide();
  clearInterval(timerId);
  $("div.status-info").show()
  if (result[0] == "Success"){
    $("div.status-info").text("Success!\n"+result[2]);
    $("#learn-link").show();
    // add id into link parameter
    $("#learn-link").attr('href', function(i,a){
              return a.replace( /(id=)/ig, '$1'+result[1] );
            });
  }else{
    $("div.status-info").text("Fail!\n"+result[2]);
    $("#search-link").show();
  };
};

