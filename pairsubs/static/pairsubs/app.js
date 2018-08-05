console.log("Hello");
var count = 3;
console.log("0");
var state = 'show';

jQuery.fn.visible = function() {
      return this.css('visibility', 'visible');
};

jQuery.fn.invisible = function() {
      return this.css('visibility', 'hidden');
};

function get_data (){
    console.log('get_data')
    if (typeof sub_id === 'undefined'){
      data = {};
    }else{
      data =  {'id': sub_id};
    }

      $.get({url: 'get_data/',
             data: data,
             success: new_text
            });
}

function new_text (data) {
    console.log('new_text');
    $('#answer').invisible();
    text = "";
  console.log(data);
  console.log(data.sub_info);
  console.log(data.subs);
    for (let item of data.data.subs[0]) {
      text+=("<p>"+item+"</p>");
    }
    $('#question').html(text);
    text = "";
    for (let item of data.data.subs[1]) {
      text+=("<p>"+item+"</p>");
    }
    $('#answer').html(text);
    $('#answer-button').text('Show');
}


function clickHandler (num) {
    console.log('show_answer');
    if (state == 'show') {
      $('#answer').visible();
      $('#answer-button').text('Next');
      state = 'next';
    }else{
      state = 'show';
      get_data();
   }
}


console.log("1");
$('#answer-button').click(clickHandler);
get_data()
